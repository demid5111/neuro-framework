#!/usr/bin/env python
import sys

import pika

from constants import directExchangeToAdmin, fanoutExchangeFromAdmin, routing_key_from_admin, routing_key_to_admin


MY_ID = sys.argv[1]

def receive_message (ch, method, properties, body):
	print method.routing_key
	if "admin" in body:
		print "Hey, Admin!"
	else:
		print "[x] {}".format(body)

	send_message(channel=ch,message="Nice to meet you from {}!".format(MY_ID))

def send_message (channel,message):

	print "[*] Sending Task: " + message

	channel.exchange_declare(exchange=directExchangeToAdmin,
													 type='direct')
	channel.basic_publish(exchange=directExchangeToAdmin,
												routing_key=routing_key_to_admin,
												properties=pika.BasicProperties(type="task", delivery_mode=2),
												body = message)


def begin_listen(channel,queue_name):
	channel.exchange_declare(exchange=fanoutExchangeFromAdmin,
													 type='fanout')
	channel.queue_bind(exchange=fanoutExchangeFromAdmin, queue=queue_name, routing_key=routing_key_from_admin)
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