#!/usr/bin/env python
import sys

import pika

from constants import Constants


MY_ID = sys.argv[1]

def receive_message (ch, method, properties, body):
	print method.routing_key
	if "admin" in body:
		print "Hey, Admin!"
	else:
		print "[x] {}".format(body)

	# send_message(channel=ch,message="Nice to meet you from {}!".format(MY_ID))
	send_message(channel=ch,message="Got it! TODO: " + body)

def send_message (channel,message):

	print "[*] Sending Task: " + message

	channel.exchange_declare(exchange=Constants.directExchangeToAdmin,
													 type='direct')
	channel.basic_publish(exchange=Constants.directExchangeToAdmin,
												routing_key=Constants.routing_key_to_admin,
												properties=pika.BasicProperties(type="task", delivery_mode=1),
												body = message)


def begin_listen(channel,queue_name):

	channel.exchange_declare(exchange=Constants.fanoutExchangeFromAdmin,
													 type='fanout')
	channel.queue_bind(exchange=Constants.fanoutExchangeFromAdmin, queue=queue_name, routing_key=Constants.routing_key_from_admin)
	print "[*] Waiting for messages..."

	channel.basic_consume(receive_message, queue=queue_name, no_ack=False)

	channel.start_consuming()

if __name__ == "__main__":
	myMessage = "Hello, Admin! My number is: {}".format(MY_ID)

	connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
	channel = connection.channel()

	result = channel.queue_declare(exclusive=True, durable=True)
	queue_name = result.method.queue

	send_message(channel=channel,message=myMessage)


	begin_listen(channel=channel,queue_name=queue_name)