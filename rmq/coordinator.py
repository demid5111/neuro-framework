#!/usr/bin/env python
import threading
import time

import pika

from constants import Constants, Message


GLOBAL_STEP_COUNTER = 0
GLOBAL_MEMBERS_COUNTER = 0
isAll = False
def receive_message (ch, method, properties, body):
	global  GLOBAL_MEMBERS_COUNTER
	if body == Message.new_member:
		# GLOBAL_MEMBERS_COUNTER = len(ch.consumer_tags)
		GLOBAL_MEMBERS_COUNTER += 1
		print "We have new member. Now we are: {}".format(GLOBAL_MEMBERS_COUNTER)

		send_message(channel=ch,message=' '.join([Message.new_id,str(GLOBAL_MEMBERS_COUNTER)]))
	print "[x] {}".format(body)

def send_message (channel,message):
	channel.exchange_declare(exchange=Constants.fanoutExchangeFromAdmin,
													 type='fanout')
	print "[*] Sending Task: " + message

	# global GLOBAL_STEP_COUNTER
	# if GLOBAL_STEP_COUNTER == 0:
	# 	print "Step {}. Calculate weights myself".format(GLOBAL_STEP_COUNTER)
	# elif GLOBAL_STEP_COUNTER == 1:
	# 	print "Step {}. Slice weights matrix".format(GLOBAL_STEP_COUNTER)

	channel.basic_publish(exchange=Constants.fanoutExchangeFromAdmin,
												routing_key=Constants.routing_key_from_admin,
												properties=pika.BasicProperties(type="task", delivery_mode=2),
												body = message)

def receive_messages(channel,queue_name):
	print "[*] Waiting for messages..."
	# connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
	# channel = connection.channel()
	#
	# result = channel.queue_declare(exclusive=True, durable=True)
	# queue_name = result.method.queue

	channel.exchange_declare(exchange=Constants.directExchangeToAdmin,
													 type='direct')
	channel.queue_bind(exchange=Constants.directExchangeToAdmin, queue=queue_name,routing_key=Constants.routing_key_to_admin)

	channel.basic_consume(receive_message, queue=queue_name, no_ack=False)

	channel.start_consuming()
	global isAll
	isAll = True

def start_listener(ch,queue):
	t_msg = threading.Thread(target=receive_messages,args=[ch,queue])
	t_msg.start()
	t_msg.join(0)

if __name__ == "__main__":
	myMessage = "Hello, World! I am admin!"

	connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
	channel = connection.channel()

	result = channel.queue_declare(exclusive=True, durable=True)
	queue_name = result.method.queue


	send_message(channel=channel,message=myMessage)
	start_listener(ch=channel,queue=queue_name)
	# start_listener()

	print "\nI'm free to work hard..."

	# while not isAll:
	# 	print "wait"
	# 	if not isAll:
	# 		continue
	# 	else:
	# 		break
	time.sleep(3)
	# send_message(channel=channel,message="Begin initializing")
	# send_message(channel=channel,message="Begin initializing2")
	# send_message(channel=channel,message="Begin initializing2")
	# send_message(channel=channel,message="Begin initializing2")
	# send_message(channel=channel,message="Begin initializing2")
	#
	# print "[*] Waiting for messages..."


	# channel.exchange_declare(exchange=Constants.directExchangeToAdmin,
	# 												 type='direct')
	# channel.queue_bind(exchange=Constants.directExchangeToAdmin, queue=queue_name,routing_key=Constants.routing_key_to_admin)
	#
	# channel.basic_consume(receive_message, queue=queue_name, no_ack=False)
	#
	# channel.start_consuming()

	# receive_messages(channel=channel,queue_name=queue_name)
