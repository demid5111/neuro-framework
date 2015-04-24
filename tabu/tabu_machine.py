import random
from math import exp
import sys

from service_functions import output


__author__ = 'demid5111'

class TabuMachine():
	def __init__(self):
		self.__k = 0      #number of  local iterations
		self.__c = 0      #number of going into far spaces of solution
		self.__C = 0      #limit for self.c
		self.__beta = 0   #defines the limit for number of local iterations
		self.__l = 0      #defines the size of the tabu list
		self.__smallPunishment = 10   #if there is no only one vertice to make a clique then punish via @link countTax
		self.__alpha = 0.5           #coefficient to increase the punishment for vertices with very small edges with other
		self._tabu_list = [] #defines the tabu list
		self._size = 0   #number of neurons in the single layer
		self.myOuts = []    #outputs of neurons
		self.myIns = []     #input of neurons
		self.myWeights = [] #weights matrix among neurons
		self.currentState =[] #current state S
		self.localMinumumState = [] #local minumum state S0
		self.globalMinimumState = []    #global minumim state S00
		self.myA = 1
		self.myB = 1
		self.currentEnergy = sys.maxint
		self.currentTax = sys.maxint
		self.localMinimumEnergy = sys.maxint
		self.globalMinimumEnergy = sys.maxint

	def setSize(self,size):
		assert size > 0
		self.size = size

	def setC(self,C):
		assert  C > 0
		self.C = C

	def setCurrentEnergy(self,energy):
		assert energy >= 0
		self.currentEnergy = energy

	def setCurrentTax(self,tax):
		assert tax >= 0
		self.currentTax = tax

	def getCurrentState(self):
		return self.currentState

	def initializeIns(self):
		assert self.size > 0
		self.currentState = [random.randint(0,1) for i in range(0,self.size)]

	def fillWeightMatrix(self,adjMatrix):
		assert len(adjMatrix) == self.size
		assert len(adjMatrix[0]) == self.size
		self.myWeights = self.initZeroMatrix(self.size,self.size)
		for i in range(0,self.size):
			for j in range(0,self.size):
				#TODO: decide whether to use -2 * A as multiplier or not
				self.myWeights[i][j] = abs(-2*self.myA*(1-adjMatrix[i][j])*(1-self.kron(i,j)))

	def kron(self,i,j):
		return 1 if i == j else 0

	def initZeroMatrix(self,rows,cols):
		tmpMatrix = []
		for i in range(0,rows):
			tmp = [0 for j in range(0,cols)]
			tmpMatrix.append(tmp)
		return tmpMatrix

	def countEnergy(self,state):
		assert len(state) == self.size
		tmp = 0
		for i in range(0,self.size):
			for j in range(0,self.size):
				tmp += self.myWeights[i][j]* state [i] * state [j]

		return tmp - self.myB * sum(state)

	def countTax(self,state):
		assert len(state) == self.size
		actives = []
		taxes = []
		for i in range(0, self.size):
			if state[i] == 1:
				actives.append(i)

		for i in range(0,self.size):
			tax = 0
			for j in range(0,len(actives)):
				if self.myWeights[i][j] == 0:
					tax += 1
			if tax == 0:
				continue
			else:
				taxes.append(self.countTaxForNeuron(tax))
			tax = 0
		return sum(taxes)

	def countTaxForNeuron(self,quantity):
		assert quantity > 0
		if quantity == 1:
			return self.__smallPunishment
		elif quantity == 2:
			return self.__smallPunishment ** 2
		else:
			return self.__alpha*exp(quantity)

	def checkForEnergyTaxUpdate(self):
		if self.currentEnergy < self.globalMinimumEnergy:
			output("\t New global optimum registered: old value = {}, new value = {}"\
				       .format(str(self.globalMinimumEnergy),str(self.currentEnergy)),isDebug=True)
			self.globalMinimumEnergy = self.currentEnergy
			self.globalMinimumState = self.currentState
		if self.currentEnergy < self.localMinimumEnergy:     #should we update global as well? Now I do it
			output("\t New local optimum registered: old value = {}, new value = {}"\
				       .format(str(self.localMinimumEnergy),str(self.currentEnergy)),isDebug=True)
			self.localMinimumEnergy = self.currentEnergy
			self.localMinumumState = self.localMinumumState