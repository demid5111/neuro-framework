#!/usr/bin/env python
from __future__ import print_function

_author__ = 'Demidovskij Alexander'
__copyright__ = "Copyright 2015, The Neuro-Framework Project"
__license__ = "GPL"
__version__ = "1.0.1"
__email__ = "monadv@yandex.ru"
__status__ = "Development"

"""
Coordination agent for the DTM.
It is also derived from the basic TM class for being able to store global information
"""


import json
import os
from subprocess import call
import threading
import time
import traceback
import sys

import pika

from constants import Constants, Message, Level, Field
from service_functions import output, read_clique_in_matrix, pack_msg_json, check_clique, check_symmetry
from tabu.tabu_machine import TabuMachine


class Coordinator(TabuMachine):
	def __init__(self, NUMBER=None):
		TabuMachine.__init__(self)
		self.neighbourhood_options = []
		self.readiness = []
		self.GLOBAL_STEP_COUNTER = 0
		self.GLOBAL_MEMBERS_COUNTER = 0
		self.AVAILABLE_MACHINES = NUMBER
		self.states = []
		##############################################
		### Connection issues(begin)
		##############################################
		self.connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
		self.channel = self.connection.channel()

		self.result = self.channel.queue_declare(exclusive=True, durable=True)
		self.queue_name = self.result.method.queue

		myMessage = "Hello, World! I am admin!"
		self.send_message(message=myMessage)
		self.start_listener()
		##############################################
		### Connection issues (end)
		##############################################

		print("\nNow create as much machines as needed")

		self.create_machines(number=self.AVAILABLE_MACHINES)

		time.sleep(3)  # to make sure everything is initialized correctly

		self.distribution = []  # distribution[i] is the number of the neurons on the ith machine

	def receive_message(self, ch, method, properties, body):
		"""
		Standard interface for the pika module for the agent to get messages
		:param ch:
		:param method:
		:param properties:
		:param body:
		:return:
		"""
		sender_id = int(method.routing_key.split('.')[0])

		try:
			data = json.loads(body)

			if Level.info in method.routing_key:
				print("Nice to see you, Number {}!".format(sender_id))
			elif Message.initialized in method.routing_key or Message.ready in method.routing_key:
				self.readiness[sender_id] = True
				print("[x] Number {}, see that you are ready!".format(sender_id))
			elif Message.calculate_energy in method.routing_key:
				if self.currentEnergy == float("inf"):
					self.currentEnergy = data[Field.current_energy]
				else:
					self.currentEnergy += data[Field.current_energy]
				self.readiness[sender_id] = True
				print("[x] Got energy from Number {}, his value = {}, global energy = {}"
							.format(sender_id, data[Field.current_energy], self.currentEnergy))
			elif Message.report_best_neighbour in method.routing_key:
				index = data[Message.report_best_neighbour]
				deltas = data[Message.energy_diff]
				state = data[Field.myCurrentState]
				self.neighbourhood_options[sender_id] = (index, deltas, state)
				self.readiness[sender_id] = True
				print("[x] Got best member from Number {}, index = {}, deltas = {}, state = {}"
							.format(sender_id, index, deltas, state))

			elif Message.report_oldest_neuron in method.routing_key:
				index = data[Constants.body][Field.myOldestNeuron]
				deltas = data[Constants.body][Field.myChangedDelta]
				iteration = data[Constants.body][Field.myIterationNumber]
				self.neighbourhood_options[sender_id] = (index,iteration,deltas)
				self.readiness[sender_id] = True
				print("[x] Got oldest member from Number {}, index = {}, deltas = {}, iteration = {}"
							.format(sender_id, index, deltas, iteration))
		except ValueError, e:
			# if method.routing_key == Message.new_member:
			# # GLOBAL_MEMBERS_COUNTER = len(ch.consumer_tags)
			# self.GLOBAL_MEMBERS_COUNTER += 1
			# 	print ("We have new member. Now we are: {}".format(self.GLOBAL_MEMBERS_COUNTER))
			#
			# 	self.send_message(message=' '.join([Message.new_id,str(self.GLOBAL_MEMBERS_COUNTER)]))
			# else:
			print("[x] {}".format(body))
		# print (traceback.print_exc())


	def send_message(self, message):
		"""
		Standard interface for the pika module for the agent to send messages
		:param ch:
		:param method:
		:param properties:
		:param body:
		:return:
		"""
		self.channel.exchange_declare(exchange=Constants.fanoutExchangeFromAdmin,
																	type='fanout')
		print("[*] Sending Task: " + message)

		self.channel.basic_publish(exchange=Constants.fanoutExchangeFromAdmin,
															 routing_key=Constants.routing_key_from_admin,
															 properties=pika.BasicProperties(type="task", delivery_mode=2),
															 body=message)

	def receive_messages(self):
		"""
		Starts listening, the agent subscribes to the direct exchange
		"""
		print("[*] Waiting for messages...")

		self.channel.exchange_declare(exchange=Constants.directExchangeToAdmin,
																	type='topic')
		self.channel.queue_bind(exchange=Constants.directExchangeToAdmin, queue=self.queue_name,
														routing_key=Constants.key_all_messages)

		self.channel.basic_consume(self.receive_message, queue=self.queue_name, no_ack=False)

		self.channel.start_consuming()


	def start_listener(self):
		"""
		Creates special thread to listen to messages from other agents
		As it receives and sends messages asynchronously, it  can be performed in different thread only.
				"""
		self.receiver_thread = threading.Thread(target=self.receive_messages)
		self.receiver_thread.start()
		self.receiver_thread.join(0)

	def create_machines(self, number):
		"""
		Creates subTMs
		:param number: number of subTMs to create
		"""
		dir = os.path.dirname(os.path.realpath(__file__))
		for i in range(number):
			call("start cmd /K C:\Python27\python.exe sub_tm.py {}".format(i), cwd=dir, shell=True)

	def kill_machines(self, me_also=False):
		"""
		Makes other agents stop working  either at the end of calculation
		or when some error in coordinator occured
		:param me_also:
		"""
		self.send_message(message=Message.kill_everyone)
		if me_also:
			os._exit(1)


	def split_neurons_over_machines(self):
		assert self.AVAILABLE_MACHINES > 0
		assert self._size > self.AVAILABLE_MACHINES
		self.distribution = [0 for i in range(self.AVAILABLE_MACHINES)]
		for i in range(len(self.distribution)):
			n1 = int(self._size / self.AVAILABLE_MACHINES)
			n2 = self._size % self.AVAILABLE_MACHINES
			if i < n2:
				self.distribution[i] = n1 + 1
			else:
				self.distribution[i] = n1

	def is_network_ready(self):
		"""
		Checks if every machine in network has completed a task
		:return:
		"""
		isReady = True
		for i in self.readiness:
			if not i:
				isReady = False
				break
		return isReady
	
	def prepare_readiness_list(self):
		self.readiness = [False for i in range(self.AVAILABLE_MACHINES)]
	
	def erase_readiness(self):
		self.readiness = [False for i in self.readiness]

	def initialize_options_list(self):
		assert self.AVAILABLE_MACHINES > 0
		self.neighbourhood_options = [() for i in range(self.AVAILABLE_MACHINES)]

	def make_auction(self):
		"""
		Get the element with the lowest value from the list of tuples by the secong element in it
		:return: index of the element
		"""
		res = sorted(self.neighbourhood_options, key=lambda tup: tup[1])  # get the lowest
		return res[0]  # tuple is (index,deltas,state)





if __name__ == "__main__":
	myCoordinator = None

	try:
		myCoordinator = Coordinator(3)

		time.sleep(0.2)

		###############################################
		# All necessary staff for correct workflow
		###############################################
		output(message="Pre-processing: reading clique", isDebug=False)
		# fileName = "C125.9.clq"
		fileName = "sample6_10.clq"
		i = 0
		i += 1
		output(message="Step {}. Read clique from file {}".format(str(i), fileName), isDebug=True)
		myAdjMatrix = read_clique_in_matrix(fileName)
		isSymmetric = check_symmetry(myAdjMatrix)
		if not isSymmetric:
			print ("Wrong matrix")
			myCoordinator.kill_machines()
		myC = 10

		TABU_SIZE = int(len(myAdjMatrix) / 2)
		BETA = TABU_SIZE / len(myAdjMatrix) + 2
		NUMBER_OF_NODES = -1
		if len(sys.argv) > 1:
			if sys.argv[1] < len(myAdjMatrix):
				NUMBER_OF_NODES = sys.argv[1]
		else:
			NUMBER_OF_NODES = int(len(myAdjMatrix) / 3)
		i += 1
		###############################################
		output(message="Starting tabu work", isDebug=True)
		i = 0
		i += 1

		output(message="Step {}. Initialize myself".format(str(i)), isDebug=True)

		myCoordinator.setC(C=myC)
		myCoordinator.setSize(len(myAdjMatrix))
		myCoordinator.set_tabu_size(TABU_SIZE)
		myCoordinator.set_beta(BETA)
		myCoordinator.initialize_state()
		myCoordinator.initialize_tabu_list()
		myCoordinator.prepare_readiness_list()
		myCoordinator.initialize_options_list()
		i += 1

		output(message="Step {}. Split neurons by tabu-machines"
					 .format(str(i)), isDebug=True)
		myCoordinator.split_neurons_over_machines()
		output(message="Here is the distribution of neurons: {}".format(myCoordinator.distribution), isDebug=True,
					 tabsNum=1)
		i += 1

		output(message="Step {}. Fill weight matrix".format(str(i)), isDebug=True)
		myCoordinator.fill_weight_matrix(myAdjMatrix)
		i += 1
		output(message="Step {}. Initialize Tabu-machines: slice matrix, slice state, k,c,neurons states, tabu lists"
					 .format(str(i)), isDebug=True)

		data = {}
		data[Constants.body] = {}
		data[Constants.body][Field.myC] = myC
		data[Constants.body][Field.mySizeVec] = myCoordinator.distribution
		data[Constants.body][Field.myTabu] = TABU_SIZE
		data[Constants.body][Field.myBeta] = BETA
		data[Constants.body][Field.myW] = myCoordinator.myWeights
		data[Constants.body][Field.myCurrentState] = myCoordinator.getCurrentState()

		message = pack_msg_json(level=Message.initializing, body=data)
		myCoordinator.send_message(message=message)
		i += 1

		while True:
			if myCoordinator.is_network_ready():
				break

		print("Everyone is initialized and ready to start...")

		myCoordinator.erase_readiness()

		print("Step {}. Count current energy and tax".format(str(i)))
		message = pack_msg_json(level=Message.calculate_energy)
		myCoordinator.send_message(message=message)
		while True:
			if myCoordinator.is_network_ready():
				break

		print("\nGot initial value of energy. It is: {}...".format(myCoordinator.currentEnergy))

		myCoordinator.erase_readiness()
		i += 1


		numCycles = 0
		print ("Begin cycling and looking for the solution")
		while True:
			print("Begin new cycle. Global minimum: {},\n local minimum: {}"
				.format(myCoordinator.get_global_minimum_state(),myCoordinator.localMinimumState))
			numCycles += 1
			# variable = raw_input("Input anything to continue")
			print("Step {}.{}. Evaluate neighbours and choose best on each machine".format(numCycles,i))
			message = pack_msg_json(level=Message.calculate_deltas)
			myCoordinator.send_message(message=message)
			while True:
				if myCoordinator.is_network_ready():
					break

			print("\nGot all best neighbours...{}".format(myCoordinator.neighbourhood_options))

			myCoordinator.erase_readiness()
			i += 1

			print("Step {}.{}. Make simple auction and choose best. "
						"\nNotify everyone to make them update values and move the neuron to tabu"
						"\nUpdate local, global minimums if needed".format(numCycles,i))
			index, delta, state = myCoordinator.make_auction()
			print ("So, the winner is index: {}".format(index))
			newEnergy = myCoordinator.currentEnergy + delta
			myCoordinator.set_energy(newEnergy)
			myCoordinator.move_neuron_to_tabu(index=index)
			myCoordinator.change_current_state(indexToChange=index)
			data = {}
			data[Constants.message_key] = Message.global_best_neighbour
			data[Constants.body] = {}
			data[Constants.body][Field.myChangedNeuron] = index
			data[Constants.body][Field.myChangedDelta] = delta
			data[Constants.body][Field.myChangedState] = state
			data[Constants.body][Field.myCurrentState] = myCoordinator.getCurrentState()
			data[Constants.body][Field.myCurrentEnergy] = newEnergy
			message = pack_msg_json(level=Message.global_best_neighbour,body=data)
			myCoordinator.send_message(message=message)

			while True:
				if myCoordinator.is_network_ready():
					break

			print("\nAll machines updated in the cycle...")

			myCoordinator.erase_readiness()
			i += 1


			print("Step {}.{}. Update k,c, Update energies. Check if smtp either lmtp to continue ".format(numCycles,i))
			myCoordinator.increment_k()
			if myCoordinator.check_for_energy_tax_update():
				myCoordinator.erase_h()
			else:
				myCoordinator.increment_h()
			if myCoordinator.is_smtp_over():
				if myCoordinator.is_lmtp_over():
					output("{}.{} Global search is over. Get out best solution (global minimum) found so far"
								 .format(numCycles,i), isDebug=False, tabsNum=1)
					output("{}.{} Best energy: value = {}".format(numCycles,i,myCoordinator.get_global_minimum_energy()), isDebug=False)
					output("{}.{} Max clique size: value = {}"\
						.format(numCycles,i,myCoordinator.get_clique_size(myCoordinator.get_global_minimum_state())), isDebug=False)
					output("{}.{} The global minimum state:{}\n clique indices: "
								 .format(numCycles,i,myCoordinator.get_global_minimum_state()) + str(myCoordinator.get_best_clique()),isDebug=False)
					left = check_clique(vertices=myCoordinator.get_best_clique(),adjMatrix=myAdjMatrix)
					output("{}.{} Number of edges left: ".format(numCycles,i) + str(left),isDebug=False)
					break
				else:
					output("\t {}.{} Local search is over. Need to move far away from here. c = {}, C = {}"\
								 .format(numCycles,i,myCoordinator.get_c(),myCoordinator.get_C()),isDebug=False,tabsNum=1)
					index = myCoordinator.get_oldest_neuron()
					print ("Step {}.{}. Get oldest neuron and values for it".format(numCycles,i))
					data = {}
					data[Constants.message_key] = Message.get_oldest_neuron
					message = pack_msg_json(level=Message.get_oldest_neuron)
					myCoordinator.send_message(message=message)

					while True:
						if myCoordinator.is_network_ready():
							break

					print("\nAll machines sent their oldest neighbours...")
					myCoordinator.erase_readiness()
					i += 1

					print("Step {}.{}. Make simple auction and choose best. "
						"Notify everyone to make them update values and move the neuron to tabu"
						"Update local, global minimums if needed".format(numCycles,i))
					index, delta, state = myCoordinator.make_auction()
					newEnergy = myCoordinator.currentEnergy + delta
					myCoordinator.set_energy(newEnergy)
					myCoordinator.move_neuron_to_tabu(index=index)
					myCoordinator.change_current_state(indexToChange=index)
					myCoordinator.update_energy(index=index,isLocalMin=True)
					myCoordinator.increment_c()
					myCoordinator.erase_h()

					data = {}
					data[Constants.message_key] = Message.global_best_neighbour
					data[Constants.body] = {}
					data[Constants.body][Field.myChangedNeuron] = index
					data[Constants.body][Field.myChangedDelta] = delta
					data[Constants.body][Field.myChangedState] = state
					data[Constants.body][Field.myCurrentState] = myCoordinator.getCurrentState()
					data[Constants.body][Field.myCurrentEnergy] = newEnergy
					data[Constants.body][Field.isForce] = True
					message = pack_msg_json(level=Message.global_best_neighbour,body=data)
					myCoordinator.send_message(message=message)

					while True:
						if myCoordinator.is_network_ready():
							break

					print("\nAll machines jumped to oldest neighbour...")
					myCoordinator.erase_readiness()
					i += 1
			else:
				print("\n\t Continue local search")
		if myCoordinator.is_lmtp_over():
			myCoordinator.kill_machines()
	except Exception, e:
		myCoordinator.kill_machines()
		print(traceback.print_exc())