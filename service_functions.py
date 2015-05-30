from __future__ import print_function

_author__ = 'Demidovskij Alexander'
__copyright__ = "Copyright 2015, The Neuro-Framework Project"
__license__ = "GPL"
__version__ = "1.0.1"
__email__ = "monadv@yandex.ru"
__status__ = "Development"

"""
Primitives for pre- and postprocessing information
"""

import json
import os
import random
import re
from rmq.constants import Constants, Level
import time


def output(message, instance=None, isDebug=True, tabsNum=0,newLine=True):
	"""
	Prints the message to console
	:param message: the texdt to be displayed
	:param instance: the object to print
	:param isDebug: the priority of the message
	:param tabsNum: offset of printed message
	:param newLine: if we need to print from new line
	"""
	if not isDebug:
		log = ""
		if instance is not None:
			log = "<{}>".format(instance)
		if not newLine:
			print(message,end="")
		else:
			print(time.strftime("%d/%m/%Y %I:%M:%S {} {}").format(log, str(('\t' * tabsNum) + message)))


def make_int_matrix(rows, cols):
	"""
	Creates arbitrary zero matrix
	:param rows:
	:param cols:
	:return:
	"""
	matrix = []
	for i in range(0, rows):
		tmp = []
		for i in range(0, cols):
			tmp.append(0)
		matrix.append(tmp)
	return matrix


def make_random_matrix(rows, cols):
	"""
	Creates arbitrary random matrix
	:param rows:
	:param cols:
	:return:
	"""
	matrix = []
	for i in range(0, rows):
		tmp = []
		for i in range(0, cols):
			tmp.append(random.randint(0, 1))
		matrix.append(tmp)
	return matrix


def read_clique_in_matrix(fileName):
	"""
	Creates the adjacency binary matrix by the given file
	Specifically looks for files in data subdirectory of the project
	:param fileName:
	:return: the 2-d list
	"""
	isEdge = re.compile('^e\s.*\s.*', re.IGNORECASE)
	isCliqueInfo = re.compile('^p\scol.*', re.IGNORECASE)
	adjMatrix = []
	current_working_directory = os.getcwd()
	isRoot = False
	for i in os.listdir(current_working_directory):
		if os.path.isdir(i):
			isRoot = True
			break
	if isRoot:
		fileName = os.path.join(current_working_directory, "data", fileName)
	else:
		fileName = os.path.join(os.path.dirname(current_working_directory),"data",fileName)
	with open(fileName, "r") as f:
		for line in f.readlines():
			if isCliqueInfo.match(line):
				GRAPH_SIZE = int(line.split()[-2])
				adjMatrix = make_int_matrix(GRAPH_SIZE, GRAPH_SIZE)
			if isEdge.match(line):
				tmp = line.split()
				adjMatrix[int(tmp[-2]) - 1][int(tmp[-1]) - 1] = 1
				adjMatrix[int(tmp[-1]) - 1][int(tmp[-2]) - 1] = 1
	return adjMatrix

def print_matrix(matrix):
	for i in range(len(matrix)):
		output( str(matrix[i]),isDebug=True)
		# print('\n')

def check_clique(vertices, adjMatrix):
	"""
	Checks if the given matrix represents the clique
	:param vertices:
	:param adjMatrix:
	:return: the number of edges missed
	"""
	left = 0
	for i in range(len(vertices)):
		for j in range(len(vertices)):
			if i <= j:
				continue
			if vertices[i] != vertices[j]:
				if adjMatrix[vertices[i]-1][vertices[j]-1] == 0:
					left += 1

	return left

def pack_msg_json(level=Level.info, body={}):
		body[Constants.message_key] = level
		return json.dumps(body)

def check_symmetry(myAdjMatrix):
	"""
	Check if the given matrix is symmetric
	:param myAdjMatrix:
	:return: boolean
	"""
	isSymmetric = True
	for i in range(len(myAdjMatrix)):
		for j in range(len(myAdjMatrix)):
			if j >= i:
				if myAdjMatrix[i][j] != myAdjMatrix[j][i]:
					isSymmetric = False
					break
	return isSymmetric