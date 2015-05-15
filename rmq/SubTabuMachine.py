#!/usr/bin/env python
import pika
import sys


def send_message(message):
	connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
	channel = connection.channel()

	channel.exchange_declare(exchange='logs',
													 type='fanout')
	channel.basic_publish(exchange='logs',
                      routing_key='',
                      body=message)
	print " [x] Sent %r" % (message,)
	connection.close()

def begin_consuming():
	connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
	channel = connection.channel()

	channel.exchange_declare(exchange='logs',
													 type='fanout')


	result = channel.queue_declare(exclusive=True)
	queue_name = result.method.queue

	channel.queue_bind(exchange='logs',
										 queue=queue_name)

	print 'Sub [*] Waiting for logs. To exit press CTRL+C'

	def callback(ch, method, properties, body):
			print "sub [x] %r" % (body,)

	channel.basic_consume(callback,
												queue=queue_name,
												no_ack=True)
	channel.start_consuming()

message = ' '.join(sys.argv[1:]) or "info: Hello World!"
print message
begin_consuming()
send_message(message)

# channel.start_consuming()
