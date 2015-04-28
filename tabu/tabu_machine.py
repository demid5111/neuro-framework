from copy import copy
import random
from math import exp

from service_functions import output


__author__ = 'demid5111'

class TabuMachine():
	def __init__(self):
		self.__k = 0      # number of  iterations
		self.__h = 0      # number of iterations without changing local minimum
		self.__c = 0      # number of going into far spaces of solution
		self.__C = 0      # limit for self.c
		self.__beta = 0   # defines the limit for number of local iterations
		#TODO: should the size of tabu be equal to the number of neurons
		self.__l = 2      # defines the size of the tabu list
		self.__smallPunishment = 10   # if there is no only one vertice to make a clique then punish via @link countTax
		self.__alpha = 0.5       # coefficient to increase the punishment for vertices with very small edges with other
		self._tabu_list = [] # defines the tabu list
		self._size = 0   # number of neurons in the single layer
		self.myOuts = []    # outputs of neurons
		self.myIns = []     # input of neurons
		self.myWeights = []  # weights matrix among neurons
		self.currentState =[]  # current state S
		self.localMinimumState = []  # local minimum state S0
		self._globalMinimumState = []    # global minimim state S00
		self.myA = 1
		self.myB = 1
		self.currentEnergy = float("inf")
		self.currentTax = float("inf")
		self.localMinimumEnergy = float("inf")
		self._globalMinimumEnergy = float("inf")

	#############################################################################
	# Getters and setters (Begin)
	#############################################################################
	def setSize(self,size):
		assert size > 0
		self._size = size

	def set_tabu_size(self,l):
		assert l > 0
		self.__l = l

	def set_beta(self,beta):
		self.__beta = beta
		assert self.__l > 0
		assert self.__beta * self._size > self.__l

	def increment_k(self):
		self.__k += 1

	def increment_h(self):
		self.__h += 1

	def erase_h(self):
		self.__h = 0

	def setC(self,C):
		assert C > 0
		self.__C = C

	def setCurrentEnergy(self,energy,isLocalMin=False):
		assert energy >= 0
		self.currentEnergy = energy
		if isLocalMin:
			self.localMinimumEnergy = energy

	def setCurrentTax(self,tax):
		assert tax >= 0
		self.currentTax = tax

	def getCurrentState(self):
		return self.currentState

	def get_global_minimum_state(self):
		return self._globalMinimumState

	def get_global_minimum_energy(self):
		return self._globalMinimumEnergy

	def get_clique_size(self,state):
		return sum(state)
	#############################################################################
	# Getters and setters (Finish)
	#############################################################################

	def changeCurrentState(self,indexToChange):
		self.currentState[indexToChange] = 1 - self.currentState[indexToChange]

	def initializeIns(self):
		assert self._size > 0
		self.currentState = [random.randint(0,1) for i in range(self._size)]

	def createTabuList(self):
		self._tabu_list = [float("inf") for i in range(self._size)]

	def fillWeightMatrix(self,adjMatrix):
		assert len(adjMatrix) == self._size
		assert len(adjMatrix[0]) == self._size
		self.print_matrix(adjMatrix)
		# return
		self.myWeights = self.initZeroMatrix(self._size,self._size)
		for i in range(0,self._size):
			for j in range(0,self._size):
				#TODO: decide whether to use -2 * A as multiplier or not
				self.myWeights[i][j] = -2*self.myA*(1-adjMatrix[i][j])*(1-self.kron(i,j))

	def kron(self,i,j):
		return 1 if i == j else 0

	def initZeroMatrix(self,rows,cols):
		tmpMatrix = []
		for i in range(rows):
			tmp = [0 for j in range(cols)]
			tmpMatrix.append(tmp)
		return tmpMatrix

	def countEnergy(self,state):
		assert len(state) == self._size
		tmp = 0
		for i in range(0,self._size):
			for j in range(0,self._size):
				tmp += self.myWeights[i][j]* state [i] * state [j]

		return (-1/2) * tmp - self.myB * sum(state)

	def countTax(self,state):
		assert len(state) == self._size
		actives = []
		taxes = []
		for i in range(0, self._size):
			if state[i] == 1:
				actives.append(i)

		for i in range(0,self._size):
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

	def check_for_energy_tax_update(self):
		isChanged = False
		if self.currentEnergy < self._globalMinimumEnergy:
			output("\t New global optimum registered: old value = {}, new value = {}"\
					 .format(str(self._globalMinimumEnergy),str(self.currentEnergy)),isDebug=True)
			self._globalMinimumEnergy = self.currentEnergy
			self._globalMinimumState = self.currentState
			isChanged = True
		if self.currentEnergy < self.localMinimumEnergy:     #should we update global as well? Now I do it
			output("\t New local optimum registered: old value = {}, new value = {}"\
					 .format(str(self.localMinimumEnergy),str(self.currentEnergy)),isDebug=True)
			self.localMinimumEnergy = self.currentEnergy
			self.localMinimumState = self.localMinimumState
			isChanged = True
		return isChanged

	def countNeighbourhoodStates(self,state):
		assert len(state) > 0
		energies = [float("inf") for i in range (self._size)]
		taxes = [float("inf") for i in range (self._size)]

		for i in range (0,self._size):
			newState = copy(state)
			newState[i] = 1 - newState[i]
			energies[i] = self.countEnergy(newState)
			taxes[i] = self.countTax(newState)

		return energies,taxes

	def choose_best_neighbour(self,energies,taxes):
		rejected = []     #list of prohibited indexes which are rejected because of tabu and energy
		nIndex = -1
		while(True):
			nIndex = self._find_absolute_best(energies=energies,taxes=taxes,rejected=rejected)		#index of best neighbor
			if (nIndex < 0):
				nIndex = self._find_pareto_frontier(energies=energies,taxes=taxes,rejected=rejected)    #always returns index

			if self.is_tabu(nIndex):
				print("!!!!!!!!!!!!!!!!IS TABU")
				output(message="\t Neuron is in tabu. Need to check the aspiration criteria",isDebug=True)
				tmpState = self.currentState
				tmpState[nIndex] = 1 - tmpState[nIndex]
				if self.aspiration_criteria_satisfied(tmpState):
					break
				else:
					rejected.append(nIndex)
			else:
				break
		return nIndex

		# else:
		# 	return
		#
		# #TODO: make the list of indexes filled correctly
		# myIndexes = []
		# for i in myIndexes:
		# 	if myTM.is_tabu(i):
		# 		output(message="\t Neuron is in tabu. Need to check the aspiration criteria",isDebug=True)
		# 		tmpState = self.currentState
		# 		tmpState[i] = 1 - tmpState[i]
		# 		if self.aspiration_criteria_satisfied(tmpState):
		# 			return i
		# 	else:
		# 		return i


	def _find_absolute_best(self,energies,taxes,rejected):
		""" Check if there is the minimum for both criteria: the lowest energy and the lowest tax
		:rtype : the index of the best minimum neighbour
		"""
		myBest = -1
		minEnergy = min(energies)
		minTax = min(taxes)
		i = 0
		for energy,tax in zip (energies,taxes):
			if i in rejected:
				continue
			if energy == minEnergy and tax == minTax:
				myBest = i
				break
			i += 1
		return myBest


	def _find_pareto_frontier(self,energies,taxes,rejected):
		indexes = [i for i in range(self._size)]
		mylist = sorted([[energies[i],taxes[i],indexes[i]] for i in range(len(energies))],reverse=False)	#find pareto frontier
		p_front = [mylist[0]]
		for pair in mylist[1:]:
			#TODO: check it: do we really want to get bigger values?
			if pair[1] <= p_front[-1][1]:
				p_front.append(pair)
		assert  len(p_front) > 0
		p_index = -1
		while(True):
			p_index = random.randint(0,len(p_front))
			if p_index in rejected:
				continue
			else:
				break
		assert p_index != -1
		nIndex = p_front[p_index][2]
		#TODO: check if bug is fixed: wrong collection of the index - not random!!
		return nIndex

	def moveNeuronToTabu(self,index):
		assert self.check_tabu_list
		self._tabu_list[index] = self.__k

	def is_smtp_over(self):
		"""
			Check if we have any more iterations in this space
			:rtype : boolean
		"""
		if self.__h >= self.__beta*self._size:
			return True
		return False

	def is_lmtp_over(self):
		"""
			Check if we have any more jumps in this space
			:rtype : boolean
		"""
		if self.__c >= self.__C:
			return True
		return False

	def get_oldest_neuron(self):
		"""find the neuron in the tabu list who remains unchanged more than others
		:rtype: index of that neuron"""
		assert self.check_tabu_list
		numIter = min(self._tabu_list)
		return self._tabu_list.index(numIter)

	def check_tabu_list(self):
		return len(self._tabu_list) > 0 and len(self._tabu_list) == self._size

	def is_tabu(self, index):
		"""
		checks if the neuron is in tabu list
		:rtype : boolean
		"""
		if abs(self.__k - self._tabu_list[index]) <= self.__l:
			return True
		return False

	def aspiration_criteria_satisfied(self,state):
		newEnergy = self.countEnergy(state)
		if newEnergy < self.currentEnergy:
			return True
		return False

	def print_matrix(self,matrix):
		for i in range(len(matrix)):
			output( str(matrix[i]),isDebug=True)
			# print('\n')