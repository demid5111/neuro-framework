#!/usr/bin/env python

_author__ = 'Demidovskij Alexander'
__copyright__ = "Copyright 2015, The Neuro-Framework Project"
__license__ = "GPL"
__version__ = "1.0.1"
__email__ = "monadv@yandex.ru"
__status__ = "Development"

"""
Special adaptation of TM for the distributed mode.
"""

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
		self.beginIndex = -1
		self.endIndex = -1
		self.globalCurrentState = []
		#########################################
		### Rabbit MQ specific initialization
		#########################################
		self.connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
		self.channel = self.connection.channel()
		self.result = self.channel.queue_declare(exclusive=True, durable=True)
		self.queue_name = self.result.method.queue
		self.routing_key = '.'.join([str(self.ID), "report", "update_energy"])
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

		"""
		Standard interface for the pika module for the agent to get messages
		:param ch:
		:param method:
		:param properties:
		:param body:
		:return:
		"""
		if "admin" in body:
			print "Hey, Admin!"

		try:
			data = json.loads(body)
			#then it is the switch by the message
			if data[Constants.message_key] == Message.initializing:		# initializing with weights and states
				print "Begin initialization..."
				self.setC(data[Constants.body][Field.myC])
				self.setSize(data[Constants.body][Field.mySizeVec][self.ID])
				self.set_distribution_vec(data[Constants.body][Field.mySizeVec])
				self.set_tabu_size(data[Constants.body][Field.myTabu])
				self.set_beta(data[Constants.body][Field.myBeta])
				self.set_global_current_state(data[Constants.body][Field.myCurrentState])
				self.initialize_tabu_list()
				self.calculate_index_bounds()
				self.initialize_state()

				self.set_weight_matrix(weight_matrix=data[Constants.body][Field.myW])
				data = {}
				data[Constants.body] = {}
				data[Constants.body][Field.myCurrentState] = self.getCurrentState()
				message = pack_msg_json(level=Message.initialized,body=data)
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
				print "Chose index={}, delta = {}".format(index,self._diffEi[index])
				data = {}
				data[Message.report_best_neighbour] = index + self.beginIndex
				data[Message.energy_diff] = self._diffEi[index]
				tmp_state = self.currentState
				tmp_state[index] = 1 - tmp_state[index]
				data[Field.myCurrentState] = tmp_state
				message = pack_msg_json(level=Message.report_best_neighbour,body=data)
				self.send_message(message=message,routing_key=self.make_routing_key(type=Message.report_best_neighbour))

			elif data[Constants.message_key] == Message.global_best_neighbour:
				print "\n",data
				index = data[Constants.body][Field.myChangedNeuron]
				isUpdateNeeded = False
				newJ = -1
				if index >= self.beginIndex and index < self.endIndex:
					newJ = index - self.beginIndex
				for i in range(self.beginIndex,self.endIndex):
					newI = i - self.beginIndex
					print "i = {}, index changed = {}, weight = {}".format(newI,index,self.myWeights[newI][index])
					if self.myWeights[newI][index] != 0:
						isUpdateNeeded = True
						break

				self.set_energy(energy=data[Constants.body][Field.myCurrentEnergy])
				isForce = False
				try:
					isForce = data[Constants.body][Field.isForce]
				except KeyError:
					pass
				if isForce:
					# TODO: make the oldest neuron be the local minimum found so far
					if newJ >= 0:
						self.update_energy(index=newJ,isLocalMin=True)
					self.erase_h()
					self.increment_c()

				isChanged = self.check_for_energy_tax_update()
				if isChanged:
					self.erase_h()
				else:
					self.increment_h()

				self.increment_k()

				if newJ >= 0:
					newJ = index - self.beginIndex
					self.change_current_state(indexToChange=newJ)

					self.move_neuron_to_tabu(index=newJ)
				# self.globalCurrentState = data[Constants.body][Field.myCurrentState]

				if isUpdateNeeded:
					print ("Updating values...")
					# then this is the neuron of the current machine

					self.count_energy_diff_states(j=index)


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

	def send_message(self,message,routing_key):
		"""
		Standard Rabbit MQ interface for sending the message
		:param message:
		:param routing_key:
		"""
		print "[*] Sending Task: " + message

		self.channel.exchange_declare(exchange=Constants.directExchangeToAdmin,
														 type='topic')
		self.channel.basic_publish(exchange=Constants.directExchangeToAdmin,
													routing_key=routing_key,
													properties=pika.BasicProperties(type="task", delivery_mode=1),
													body = message)



	def begin_listen(self,queue_name):
		"""
		Makes this instance (agent) listen to the messages from the broker
		:param queue_name:
		"""
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
		tmp.append("Current global state = {}".format(self.globalCurrentState))
		tmp.append("tabu list = {}".format(self._tabu_list))
		tmp.append("W = {}".format(self.myWeights))
		tmp.append("C = {}".format(self._C))
		tmp.append("beta = {}".format(self._beta))
		tmp.append("h = {}".format(self._h))
		tmp.append("k = {}".format(self._k))
		tmp.append("c = {}".format(self._c))

		res = '\n'.join([tmp[0],'\n\t'.join(tmp[1:])])
		return res

	def set_distribution_vec(self, vec):
		"""
		Copies the the vector with the distributions of neurons among all agents ia a system
		:param vec:
		"""
		self.distribution = copy(vec)

	def set_weight_matrix(self,weight_matrix):
		"""
		Slice matrix and get only the part with corresponding neurons
		:param weight_matrix:
		"""
		assert self.beginIndex >= 0
		assert self.endIndex > 0
		self.myWeights = []

		for i in range(self.beginIndex,self.endIndex):
			self.myWeights.append(copy(weight_matrix[i]))

	def calculate_index_bounds(self):
		"""
		Calculates bounds which represent real values of neurons numbers being owned
		by this agent
		"""
		self.beginIndex = 0
		if self.ID != 0:
			self.beginIndex = sum(self.distribution[:self.ID])
		self.endIndex = self.beginIndex + self.distribution[self.ID]

	def count_energy_diff_states(self, j = -1,isInitial = False):
		""" Recalculates energies possible changes
		:param j: index of neuron changed its state
		:return: void, works only with current state
		"""
		assert len(self.globalCurrentState) > 0
		assert self.beginIndex >= 0
		assert self.endIndex > 0
		if not isInitial:
			for i in range(self.beginIndex,self.endIndex):	# iterate through neurons available
				# print ("My current index is: {}".format(i))
				newI = i - self.beginIndex
				newJ = j - self.beginIndex
				# print newI
				# print newJ
				# print j
				# print self.myWeights[newI][j]
				# print self.currentState
				# print self.currentState[newJ]
				if i == j:
					self._diffEi[newI] = -self._diffEi[newI]
				elif self.currentState[newI] == 0:
					self._diffEi[newI] += self.myWeights[newI][j] * (1 - 2*self.globalCurrentState[j])
				else:
					self._diffEi[newI] -= self.myWeights[newI][j] * (1 - 2*self.globalCurrentState[j])
		else:
			for j in range(self.beginIndex,self.endIndex):
				sum = 0
				for i in range(len(self.globalCurrentState)):
					newJ = j - self.beginIndex
					sum += self.myWeights[newJ][i]*self.globalCurrentState[i]
				self._diffEi[newJ] = (2 * self.globalCurrentState[j] - 1)*(sum - self.myB)

	def count_energy(self,state):
		"""
		Counts the piece of the energy only for owned neurons
		:param state:
		:return: the value of the energy function for this agent (node)
		"""
		assert len(state) == self._size

		tmp = 0
		for i in range(self.beginIndex,self.endIndex):
			newI = i - self.beginIndex
			for j in range(len(self.globalCurrentState)):
				tmp += self.myWeights[newI][j]* self.globalCurrentState [i] * self.globalCurrentState [j]
		print ("My state is: " + str(state[self.begin_index:self.endIndex]))
		return -1/2 * self.myA * tmp + self.myB * sum(state[self.begin_index:self.endIndex])

	def set_global_current_state(self, state):
		self.globalCurrentState = state

	def initialize_state(self):
		"""
		Assignes states for the owned neurons from the global initial messaging list
		"""
		assert self.globalCurrentState
		assert self.beginIndex >= 0
		assert self.endIndex > 0

		self.currentState = copy(self.globalCurrentState[self.beginIndex:self.endIndex])


if __name__ == "__main__":

	myTM = SubTM(sys.argv[1])