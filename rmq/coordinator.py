#!/usr/bin/env python
import pika

from constants import fanoutExchangeFromAdmin, directExchangeToAdmin, routing_key_to_admin, routing_key_from_admin


def receive_message (ch, method, properties, body):
	print "[x] {}".format(body)

def send_message (channel,message):


	channel.exchange_declare(exchange=fanoutExchangeFromAdmin,
													 type='fanout')
	print "[*] Sending Task:"
	print message

	channel.basic_publish(exchange=fanoutExchangeFromAdmin,
												routing_key=routing_key_from_admin,
												properties=pika.BasicProperties(type="task", delivery_mode=2),
												body = message)

def begin_listen(channel,queue_name):
	print "[*] Waiting for messages..."

	channel.exchange_declare(exchange=directExchangeToAdmin,
													 type='direct')
	channel.queue_bind(exchange=directExchangeToAdmin, queue=queue_name,routing_key=routing_key_to_admin)

	channel.basic_consume(receive_message, queue=queue_name, no_ack=False)

	channel.start_consuming()

if __name__ == "__main__":
	myMessage = "Hello, World! I am admin!"

	connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
	channel = connection.channel()

	result = channel.queue_declare(exclusive=True, durable=True)
	queue_name = result.method.queue


	send_message(channel=channel,message=myMessage)

	begin_listen(channel=channel,queue_name=queue_name)


	# channel.start_consuming()