#!/usr/bin/env python
import pika

from constants import Constants, Message


class SubTM():
	def __init__(self):
		self.ID = -1
		self.routing_key = '.'.join([str(self.ID),"report","update_energy"])
		self.connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
		self.channel = self.connection.channel()

		self.result = self.channel.queue_declare(exclusive=True, durable=True)
		self.queue_name = self.result.method.queue

		self.send_message(message=Message.new_member,routing_key=Message.new_member)


		self.begin_listen(queue_name=self.queue_name)

	def receive_message (self, ch, method, properties, body):
		print method.routing_key
		if "admin" in body:
			print "Hey, Admin!"
		else:
			print "[x] {}".format(body)

		if Message.new_id in body:
			if self.ID == -1:
				self.ID = body.split()[-1]
				print "My ID: " + str(self.ID)
				self.send_message(message="I am now enumerated. So, check the connection with my routing_key",
													routing_key=self.make_routing_key(" ", "info"))
			return
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
if __name__ == "__main__":
	# connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
	# channel = connection.channel()
	#
	# result = channel.queue_declare(exclusive=True, durable=True)
	# queue_name = result.method.queue
	#
	# send_message(channel=channel,message=Message.new_member)
	#
	#
	# begin_listen(channel=channel,queue_name=queue_name)

	myTM = SubTM()