import os
import random
import re

__author__ = 'demidovs'
import time


def output(message, instance=None, isDebug=True, tabsNum=0):
	log = ""
	if instance is not None:
		log = "<{}>".format(instance)
	print(time.strftime("%d/%m/%Y %I:%M:%S {} {}").format(log, str(('\t' * tabsNum) + message)))


def makeIntMatrix(rows, cols):
	matrix = []
	for i in range(0, rows):
		tmp = []
		for i in range(0, cols):
			tmp.append(0)
		matrix.append(tmp)
	return matrix


def makeRandomMatrix(rows, cols):
	matrix = []
	for i in range(0, rows):
		tmp = []
		for i in range(0, cols):
			tmp.append(random.randint(0, 1))
		matrix.append(tmp)
	return matrix


def readCliqueInAdjMatrix(fileName):
	isEdge = re.compile('^e\s.*\s.*', re.IGNORECASE)
	isCliqueInfo = re.compile('^p\scol.*', re.IGNORECASE)
	adjMatrix = []
	current_working_directory = os.getcwd()
	fileName = os.path.join(current_working_directory, "data", fileName)
	with open(fileName, "r") as f:
		for line in f.readlines():
			if isCliqueInfo.match(line):
				GRAPH_SIZE = int(line.split()[-2])
				adjMatrix = makeIntMatrix(GRAPH_SIZE, GRAPH_SIZE)
			if isEdge.match(line):
				tmp = line.split()
				adjMatrix[int(tmp[-2]) - 1][int(tmp[-1]) - 1] = 1
				adjMatrix[int(tmp[-1]) - 1][int(tmp[-2]) - 1] = 1
	return adjMatrix


