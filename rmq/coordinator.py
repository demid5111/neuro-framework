__author__ = 'Administrator'


import pika
import sys
from subprocess import call
import os

def close_connection():
	connection.close()

def create_sub_tm(quantity):
	for i in range(quantity):
		call(["C:\Python27\python.exe", os.path.join(os.path.dirname(os.path.realpath(__file__)),"SubTabuMachine.py")],shell=True)

connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='logs',
                         type='fanout')


result = channel.queue_declare(exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='logs',
                   queue=queue_name)

print ' [*] Waiting for logs. To exit press CTRL+C'

def callback(ch, method, properties, body):
    print "main [x] %r" % (body,)

channel.basic_consume(callback,
                      queue=queue_name,
                      no_ack=True)
# message = ' '.join(sys.argv[1:]) or "info: Hello World!"
# channel.basic_publish(exchange='logs',
#                       routing_key='',
#                       body=message)
# print " [x] Sent %r" % (message,)
# message = ' '.join(sys.argv[1:]) or "info: Hello World2!"
# channel.basic_publish(exchange='logs',
#                       routing_key='',
#                       body=message)
# print " [x] Sent %r" % (message,)
create_sub_tm(quantity=3)
channel.start_consuming()


# connection = pika.BlockingConnection(pika.ConnectionParameters(
#         host='localhost'))
# channel = connection.channel()
#
# channel.exchange_declare(exchange='logs',
#                          type='fanout')


# connection.close()
