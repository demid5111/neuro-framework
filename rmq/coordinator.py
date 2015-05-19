#!/usr/bin/env python
import os
from subprocess import call
import threading
import time

import pika

from constants import Constants, Message, Level


class Coordinator():
	def __init__(self, NUMBER=None):
		self.GLOBAL_STEP_COUNTER = 0
		self.GLOBAL_MEMBERS_COUNTER = 0



		self.connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
		self.channel = self.connection.channel()

		self.result = self.channel.queue_declare(exclusive=True, durable=True)
		self.queue_name = self.result.method.queue

		myMessage = "Hello, World! I am admin!"
		self.send_message(message=myMessage)
		self.start_listener()

		print "\nNow create as much machines as needed"

		self.create_machines(number=NUMBER)

		time.sleep(3)		#to make sure everything is initialized correctly


	def receive_message (self,ch, method, properties, body):

		if method.routing_key == Message.new_member:
			# GLOBAL_MEMBERS_COUNTER = len(ch.consumer_tags)
			self.GLOBAL_MEMBERS_COUNTER += 1
			print "We have new member. Now we are: {}".format(self.GLOBAL_MEMBERS_COUNTER)

			self.send_message(message=' '.join([Message.new_id,str(self.GLOBAL_MEMBERS_COUNTER)]))

		elif Level.info in method.routing_key:
			print "Nice to see you, Number {}!".format(method.routing_key.split('.')[0])
		else:
			print "[x] {}".format(body)


	def send_message (self,message):
		self.channel.exchange_declare(exchange=Constants.fanoutExchangeFromAdmin,
														 type='fanout')
		print "[*] Sending Task: " + message

		# global GLOBAL_STEP_COUNTER
		# if GLOBAL_STEP_COUNTER == 0:
		# 	print "Step {}. Calculate weights myself".format(GLOBAL_STEP_COUNTER)
		# elif GLOBAL_STEP_COUNTER == 1:
		# 	print "Step {}. Slice weights matrix".format(GLOBAL_STEP_COUNTER)

		self.channel.basic_publish(exchange=Constants.fanoutExchangeFromAdmin,
													routing_key=Constants.routing_key_from_admin,
													properties=pika.BasicProperties(type="task", delivery_mode=2),
													body = message)

	def receive_messages(self):
		print "[*] Waiting for messages..."

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
			call("start cmd /K C:\Python27\python.exe sub_tm.py {}".format(i+1),cwd=dir,shell=True)

	def kill_machines(self,me_also=False):
		self.send_message(message=Message.kill_everyone)
		if me_also:
			os._exit(1)




if __name__ == "__main__":

	myCoordinator = Coordinator(3)

	time.sleep(3)

	myCoordinator.kill_machines(me_also=True)