#!/usr/bin/env python
from __future__ import print_function
import json
import os
from subprocess import call
import threading
import time
import traceback
import sys

import pika

from constants import Constants, Message, Level, Field
from service_functions import output, readCliqueInAdjMatrix, pack_msg_json
from tabu.tabu_machine import TabuMachine


class Coordinator(TabuMachine):
	def __init__(self, NUMBER=None):
		TabuMachine.__init__(self)
		self.readiness = []
		self.GLOBAL_STEP_COUNTER = 0
		self.GLOBAL_MEMBERS_COUNTER = 0
		self.AVAILABLE_MACHINES = NUMBER

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

		print ("\nNow create as much machines as needed")

		self.create_machines(number=self.AVAILABLE_MACHINES)

		time.sleep(3)		#to make sure everything is initialized correctly

		self.distribution = [] 	# distribution[i] is the number of the neurons on the ith machine

	def receive_message (self,ch, method, properties, body):
		sender_id = int(method.routing_key.split('.')[0])

		try:
			data = json.loads(body)

			if Level.info in method.routing_key:
				print ("Nice to see you, Number {}!".format(sender_id))
			elif Message.initialized in method.routing_key:

				self.readiness[sender_id] = True
				print ("[x] Number {}, see that you are ready!".format(sender_id))
			elif Message.calculate_energy in method.routing_key:
				if self.currentEnergy == float("inf"):
					self.currentEnergy = data[Field.current_energy]
				else:
					self.currentEnergy += data[Field.current_energy]
				self.readiness[sender_id] = True
				print ("[x] Got energy from Number {}, his value = {}, global energy = {}"
							 .format(sender_id,data[Field.current_energy],self.currentEnergy))
		except ValueError, e:
			# if method.routing_key == Message.new_member:
			# 	# GLOBAL_MEMBERS_COUNTER = len(ch.consumer_tags)
			# 	self.GLOBAL_MEMBERS_COUNTER += 1
			# 	print ("We have new member. Now we are: {}".format(self.GLOBAL_MEMBERS_COUNTER))
			#
			# 	self.send_message(message=' '.join([Message.new_id,str(self.GLOBAL_MEMBERS_COUNTER)]))
			# else:
				print ("[x] {}".format(body))
			# print (traceback.print_exc())


	def send_message (self,message):
		self.channel.exchange_declare(exchange=Constants.fanoutExchangeFromAdmin,
														 type='fanout')
		print ("[*] Sending Task: " + message)

		self.channel.basic_publish(exchange=Constants.fanoutExchangeFromAdmin,
													routing_key=Constants.routing_key_from_admin,
													properties=pika.BasicProperties(type="task", delivery_mode=2),
													body = message)

	def receive_messages(self):
		print ("[*] Waiting for messages...")

		self.channel.exchange_declare(exchange=Constants.directExchangeToAdmin,
														 type='topic')
		self.channel.queue_bind(exchange=Constants.directExchangeToAdmin, queue=self.queue_name,routing_key=Constants.key_all_messages)

		self.channel.basic_consume(self.receive_message, queue=self.queue_name, no_ack=False)

		self.channel.start_consuming()


	def start_listener(self):
		self.receiver_thread = threading.Thread(target=self.receive_messages)
		self.receiver_thread.start()
		self.receiver_thread.join(0)

	def create_machines(self, number):
		dir = os.path.dirname(os.path.realpath(__file__))
		for i in range(number):
			call("start cmd /K C:\Python27\python.exe sub_tm.py {}".format(i),cwd=dir,shell=True)

	def kill_machines(self,me_also=False):
		self.send_message(message=Message.kill_everyone)
		if me_also:
			os._exit(1)



	def split_neurons_over_machines(self):
		assert  self.AVAILABLE_MACHINES > 0
		assert self._size > self.AVAILABLE_MACHINES
		self.distribution = [0 for i in range(self.AVAILABLE_MACHINES)]
		for i in range(len(self.distribution)):
			n1 = int(self._size/self.AVAILABLE_MACHINES)
			n2 = self._size % self.AVAILABLE_MACHINES
			if i < n2:
				self.distribution[i] = n1 + 1
			else:
				self.distribution[i] = n1

	def is_network_ready(self):
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


if __name__ == "__main__":
	myCoordinator =None

	try:
		myCoordinator = Coordinator(3)

		time.sleep(1)

		###############################################
		# All necessary staff for correct workflow
		###############################################
		output(message="Pre-processing: reading clique",isDebug=False)
		# fileName = "C125.9.clq"
		fileName = "sample6_10.clq"
		i = 0
		i += 1
		output(message="Step {}. Read clique from file {}".format(str(i),fileName),isDebug=True)
		myAdjMatrix = readCliqueInAdjMatrix(fileName)
		# print(myAdjMatrix)
		myC = 5

		TABU_SIZE = int(len(myAdjMatrix)/2)
		BETA = TABU_SIZE/len(myAdjMatrix)+2
		NUMBER_OF_NODES = -1
		if len(sys.argv) > 1:
			if sys.argv[1] < len(myAdjMatrix):
				NUMBER_OF_NODES = sys.argv[1]
		else:
			NUMBER_OF_NODES = int(len(myAdjMatrix)/3)
		i += 1
		###############################################
		output(message="Starting tabu work",isDebug=True)
		i = 0
		i += 1

		output(message="Step {}. Initialize myself".format(str(i)),isDebug=True)

		myCoordinator.setC(C=myC)
		myCoordinator.setSize(len(myAdjMatrix))
		myCoordinator.set_tabu_size(TABU_SIZE)
		myCoordinator.set_beta(BETA)
		myCoordinator.initialize_tabu_list()
		myCoordinator.prepare_readiness_list()
		i += 1

		output(message="Step {}. Split neurons by tabu-machines"
														.format(str(i)),isDebug=True)
		myCoordinator.split_neurons_over_machines()
		output(message="Here is the distribution of neurons: {}".format(myCoordinator.distribution),isDebug=True,tabsNum=1)
		i += 1

		output(message="Step {}. Fill weight matrix".format(str(i)),isDebug=True)
		myCoordinator.fillWeightMatrix(myAdjMatrix)
		i += 1
		output(message="Step {}. Initialize Tabu-machines: slice matrix, slice state, k,c,neurons states, tabu lists"
														.format(str(i)),isDebug=True)

		data = {}
		data[Constants.body] = {}
		data[Constants.body][Field.myC] = myC
		data[Constants.body][Field.mySizeVec] = myCoordinator.distribution
		data[Constants.body][Field.myTabu] = TABU_SIZE
		data[Constants.body][Field.myBeta] =  BETA
		data[Constants.body][Field.myW] = myCoordinator.myWeights

		message = pack_msg_json(message=Message.initializing, body=data)
		myCoordinator.send_message(message=message)
		i += 1

		while True:
			if myCoordinator.is_network_ready():
				break

		print ("Everyone is initialized and ready to start...")
		
		myCoordinator.erase_readiness()

		print ("Step {}. Count current energy and tax".format(str(i)))
		message = pack_msg_json(message=Message.calculate_energy)
		myCoordinator.send_message(message=message)
		# energy = my.count_energy(myTM.getCurrentState())
		# tax = myTM.count_tax(myTM.getCurrentState())
		# myTM.set_energy(energy)
		# myTM.set_tax(tax)
		while True:
			if myCoordinator.is_network_ready():
				break

		print ("Got initial value of energy. It is: {}...".format(myCoordinator.currentEnergy))

		myCoordinator.erase_readiness()
		i += 1

		# myCoordinator.kill_machines(me_also=True)
	except Exception, e:
		myCoordinator.kill_machines()
		print (traceback.print_exc())