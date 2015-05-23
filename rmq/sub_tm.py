#!/usr/bin/env python
from copy import copy
import json
import sys

import pika

from constants import Constants, Message, Field, Level
from service_functions import pack_msg_json
from tabu.tabu_machine import TabuMachine


class SubTM(TabuMachine):
	def __init__(self, number=None):
		TabuMachine.__init__(self)
		self.ID = -1
		self.routing_key = '.'.join([str(self.ID), "report", "update_energy"])
		self.beginIndex = -1
		self.endIndex = -1

		self.connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
		self.channel = self.connection.channel()
		self.result = self.channel.queue_declare(exclusive=True, durable=True)
		self.queue_name = self.result.method.queue
		if number:
			self.ID = int(number)

			data = {}
			data[Message.info] = "I am now enumerated. So, check the connection with my routing_key"
			message = pack_msg_json(level=Level.info,body=data)
			self.send_message(message=message,
												routing_key=self.make_routing_key(" ", "info"))
		else:
			self.send_message(message=Message.new_member, routing_key=Message.new_member)
		self.begin_listen(queue_name=self.queue_name)

	def receive_message (self, ch, method, properties, body):

		if "admin" in body:
			print "Hey, Admin!"
		# else:
		# 	print "[x] {}".format(body)
		try:
			data = json.loads(body)
			#then it is the switch by the message
			if data[Constants.message_key] == Message.initializing:
				print "Begin initialization..."
				self.setC(data[Constants.body][Field.myC])
				self.setSize(data[Constants.body][Field.mySizeVec][self.ID])
				self.set_distribution_vec(data[Constants.body][Field.mySizeVec])
				self.set_tabu_size(data[Constants.body][Field.myTabu])
				self.set_beta(data[Constants.body][Field.myBeta])
				self.initialize_tabu_list()
				self.initialize_state()
				self.calculate_index_bounds()
				self.set_weight_matrix(weight_matrix=data[Constants.body][Field.myW])

				print self
				message = pack_msg_json()
				self.send_message(message=message,routing_key=self.make_routing_key(type=Message.initialized))

			elif data[Constants.message_key] == Message.calculate_energy:
				energy = self.count_energy(self.currentState)
				data = {}
				data[Field.current_energy] = energy
				message = pack_msg_json(level=Message.calculate_energy,body=data)
				self.send_message(message=message,routing_key=self.make_routing_key(type=Message.calculate_energy))

			elif data[Constants.message_key] == Message.calculate_deltas:
				self.count_energy_diff_states(isInitial=True)
				index = self.choose_best_neighbour_simple()
				data = {}
				data[Message.report_best_neighbour] = index + self.beginIndex
				data[Message.energy_diff] = self._diffEi[index]
				tmp_state = self.currentState
				tmp_state[index] = 1 - tmp_state[index]
				data[Field.myCurrentState] = tmp_state
				message = pack_msg_json(level=Message.report_best_neighbour,body=data)
				self.send_message(message=message,routing_key=self.make_routing_key(type=Message.report_best_neighbour))

			elif data[Constants.message_key] == Message.global_best_neighbour:
				index = data[Constants.body][Field.myChangedNeuron]
				isUpdateNeeded = False

				if index >= self.beginIndex and index < self.endIndex:
					newJ = index - self.beginIndex
					print newJ
					for i in range(self.beginIndex,self.endIndex):
						newI = i - self.beginIndex
						if self.myWeights[newI][newJ] != 0:
							isUpdateNeeded = True
							break

				self.set_energy(energy=data[Constants.body][Field.myCurrentEnergy])
				isChanged = self.check_for_energy_tax_update()
				if isChanged:
					self.erase_h()
				else:
					self.increment_h()
				self.increment_k()
				if isUpdateNeeded:
					print ("i need to update my values")
					# then this is the neuron of the current machine
					self.changeCurrentState(indexToChange=index)

					self.moveNeuronToTabu(index=index)
					self.count_energy_diff_states(i=index)

				print self

				message = pack_msg_json()
				self.send_message(message=message,routing_key=self.make_routing_key(type=Message.ready))

			elif data[Constants.message_key] == Message.get_oldest_neuron:
				index = self.get_oldest_neuron()
				energy = self._diffEi[index]
				iteration = self._tabu_list[index]
				data = {}
				data[Constants.body] =  {}
				data[Constants.body][Field.myOldestNeuron] = index
				data[Constants.body][Field.myChangedDelta] = energy
				data[Constants.body][Field.myIterationNumber] = index

				message = pack_msg_json(level=Message.report_oldest_neuron,body=data)
				self.send_message(message=message,routing_key=self.make_routing_key(type=Message.report_oldest_neuron))

		except ValueError:
			if Message.new_id in body:
				if self.ID == -1:
					self.ID = body.split()[-1]
					print "My ID: " + str(self.ID)
					message = pack_msg_json(level=Level.info)
					self.send_message(message=message, routing_key=self.make_routing_key(" ", "info"))
				return
			elif Message.kill_everyone in body:
				print "Bye!"
				sys.exit(0)
			else:
				self.send_message(message="Got it! TODO: " + body,routing_key=Message.initializing)

	def send_message (self,message,routing_key):

		print "[*] Sending Task: " + message

		self.channel.exchange_declare(exchange=Constants.directExchangeToAdmin,
														 type='topic')
		self.channel.basic_publish(exchange=Constants.directExchangeToAdmin,
													routing_key=routing_key,
													properties=pika.BasicProperties(type="task", delivery_mode=1),
													body = message)



	def begin_listen(self,queue_name):

		self.channel.exchange_declare(exchange=Constants.fanoutExchangeFromAdmin,
														 type='fanout')
		self.channel.queue_bind(exchange=Constants.fanoutExchangeFromAdmin, queue=self.queue_name,
														routing_key=Constants.routing_key_from_admin)
		print "[*] Waiting for messages..."

		self.channel.basic_consume(self.receive_message, queue=self.queue_name, no_ack=False)

		self.channel.start_consuming()

	def make_routing_key(self,type,level="report"):
		return '.'.join([str(self.ID),level,type])

	def __str__(self):
		tmp = []
		tmp.append("<{} ID={}, Size={}>".format(SubTM.__name__,self.ID,self._size))
		tmp.append("Current state = {}".format(self.currentState))
		tmp.append("W = {}".format(self.myWeights))
		tmp.append("C = {}".format(self._C))
		tmp.append("beta = {}".format(self._beta))
		tmp.append("h = {}".format(self._h))
		tmp.append("k = {}".format(self._k))
		tmp.append("c = {}".format(self._c))

		res = '\n'.join([tmp[0],'\n\t'.join(tmp[1:])])
		return res

	def set_distribution_vec(self, vec):
		self.distribution = copy(vec)

	def set_weight_matrix(self,weight_matrix):
		assert self.beginIndex >= 0
		assert self.endIndex > 0
		self.myWeights = []

		for i in range(self.beginIndex,self.endIndex):
			self.myWeights.append(weight_matrix[i])

	def calculate_index_bounds(self):
		self.beginIndex = 0
		if self.ID != 0:
			self.beginIndex = sum(self.distribution[:self.ID])
		self.endIndex = self.beginIndex + self.distribution[self.ID]

	def count_energy_diff_states(self, j = -1,isInitial = False):
		""" Recalculates energies possible changes
		:param j: index of neuron changed its state
		:return: void, works only with current state
		"""
		assert len(self.currentState) > 0
		if not isInitial:
			for i in range(self.beginIndex,self.endIndex):
				print ("My current index is: {}".format(i))
				if i == j:
					self._diffEi[i] = -self._diffEi[i]
				elif i != j and self.currentState[i] == 0:
					self._diffEi[i] += self.myWeights[i][j] * (1 - 2*self.currentState[j])
				else:
					self._diffEi[i] -= self.myWeights[i][j] * (1 - 2*self.currentState[j])
		else:
			for j in range(self.beginIndex,self.endIndex):
				sum = 0
				for i in range(self.beginIndex,self.endIndex):
					newI = i - self.beginIndex
					newJ = j - self.beginIndex
					sum += self.myWeights[newI][j]*self.currentState[newI]
				self._diffEi[newJ] = (2 * self.currentState[newJ])*(sum - self.myB)

	def count_energy(self,state):
		assert len(state) == self._size

		tmp = 0
		for i in range(self.beginIndex,self.endIndex):
			newI = i - self.beginIndex
			for j in range(self.beginIndex,self.endIndex):
				newJ = j - self.beginIndex
				tmp += self.myWeights[newI][j]* state [newI] * state [newJ]
		return tmp - self.myB * sum(state)

if __name__ == "__main__":

	myTM = SubTM(sys.argv[1])