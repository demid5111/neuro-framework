_author__ = 'Demidovskij Alexander'
__copyright__ = "Copyright 2015, The Neuro-Framework Project"
__license__ = "GPL"
__version__ = "1.0.1"
__email__ = "monadv@yandex.ru"
__status__ = "Development"

"""
Basic class for TM and DTM. Contains all primitives for calculating, processing and analyzing
the graph instance according to specific rules
"""

from copy import copy
import random
from math import exp
from operator import itemgetter

from service_functions import output


class TabuMachine():
	def __init__(self):
		self._k = 0      # number of  iterations
		self._h = 0      # number of iterations without changing local minimum
		self._c = 0      # number of going into far spaces of solution
		self._C = 0      # limit for self.c
		self._beta = 0   # defines the limit for number of local iterations
		#TODO: should the size of tabu be equal to the number of neurons
		self.__l = 2      # defines the size of the tabu list
		self.__smallPunishment = 10   # if there is no only one vertice to make a clique then punish via @link count_tax
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
		self.localMinimumTax = float("inf")
		self._globalMinimumEnergy = float("inf")


	#############################################################################
	# Getters and setters (Begin)
	#############################################################################
	def setSize(self,size):
		assert size > 0
		self._size = size
		self._diffEi = [float("inf") for i in range(self._size)]
		self._taxes = [float("inf") for i in range(self._size)]

	def set_tabu_size(self,l):
		assert l > 0
		self.__l = l

	def set_beta(self,beta):
		self._beta = beta
		assert self.__l > 0
		assert self._beta * self._size > self.__l

	def increment_k(self):
		self._k += 1

	def increment_h(self):
		self._h += 1

	def erase_h(self):
		self._h = 0

	def setC(self,C):
		assert C > 0
		self._C = C

	def set_energy(self,energy,isLocalMin=False):
		try:
			assert self.currentEnergy >= 0
		except AssertionError:
			output("Energy is negative, value = {}".format(energy),isDebug=True,tabsNum=0)
		self.currentEnergy = energy
		if isLocalMin:
			self.localMinimumEnergy = self.currentEnergy

	def update_energy(self,index,isLocalMin=False):
		self.currentEnergy += self._diffEi[index]
		try:
			assert self.currentEnergy >= 0
		except AssertionError:
			output("Energy is negative, value = {}".format(self.currentEnergy),isDebug=True,tabsNum=0)

		if isLocalMin:
			self.localMinimumEnergy = self.currentEnergy
			self.localMinimumState = copy(self.currentState)

	def set_tax(self,tax):
		assert tax >= 0
		self.currentTax = tax

	def update_tax(self,index):
		self.currentTax = self._taxes[index]
		assert self.currentTax >= 0

	def getCurrentState(self):
		return self.currentState

	def get_global_minimum_state(self):
		return self._globalMinimumState

	def get_global_minimum_energy(self):
		return self._globalMinimumEnergy

	def get_clique_size(self,state):
		return sum(state)

	def get_C(self):
		return self._C

	def get_c(self):
		return self._c

	def increment_c(self):
		self._c += 1

	def change_current_state(self,indexToChange):
		self.currentState[indexToChange] = 1 - self.currentState[indexToChange]

	def initialize_state(self):
		assert self._size > 0
		self.currentState = [random.randint(0,1) for i in range(self._size)]

	def initialize_tabu_list(self):
		assert self._size > 0
		self._tabu_list = [float("inf") for i in range(self._size)]

	#############################################################################
	# Getters and setters (Finish)
	#############################################################################



	def fill_weight_matrix(self,adjMatrix):
		"""
		Fills weight matrix by the HNN formula
		:param adjMatrix:
		"""
		assert len(adjMatrix[0]) == self._size
		self.myWeights = self.init_zero_matrix(self._size,self._size)
		for i in range(0,self._size):
			for j in range(0,self._size):
				#TODO: decide whether to use -2 * A as multiplier or not
				self.myWeights[i][j] = -2 * self.myA * (1 - adjMatrix[i][j])*(1-self.kron(i,j))

	def kron(self,i,j):
		"""
		kroneker function
		:param i:
		:param j:
		:return:
		"""
		return 1 if i == j else 0

	def init_zero_matrix(self,rows,cols):
		"""
		Creates the zero matrix of the given size
		:param rows:
		:param cols:
		:return:
		"""
		tmpMatrix = []
		for i in range(rows):
			tmp = [0 for j in range(cols)]
			tmpMatrix.append(tmp)
		return tmpMatrix

	def count_energy(self,state):
		"""
		Calculates full energy for the given state

		:param state: current state
		:return: energy value
		"""
		assert len(state) == self._size

		tmp = 0
		for i in range(self._size):
			for j in range(self._size):
				tmp += self.myWeights[i][j]* state [i] * state [j]
		return tmp - self.myB * sum(state)

	def count_tax(self,state):
		"""
		Calculates punishment function for the given state

		:param state:
		:return: value of the punishment function for the given state
		"""
		assert len(state) == self._size
		actives = []		#contains indices of elements
		taxes = []
		for i in range(self._size):
			if state[i] == 1:
				actives.append(i)

		for i in actives:
			tax = 0
			for j in actives:
				if i == j:
					continue
				if self.myWeights[i][j] != 0:
					tax += 1
			if tax == 0:
				continue
			else:
				taxes.append(self.count_tax_neuron(tax))
			tax = 0
		return sum(taxes)

	def count_tax_neuron(self,quantity):
		"""
		Calculates punishment for the given neuron

		:param quantity: number of edges missed
		:return: value of the punishment function
		"""
		assert quantity > 0
		if quantity == 1:
			return self.__smallPunishment
		elif quantity == 2:
			return self.__smallPunishment ** 2
		else:
			return self.__alpha*exp(quantity)

	def check_for_energy_tax_update(self):
		"""
		Check if the update of global and local optimums is needed and update  if so
		:return: boolean (if values were changed)
		"""
		isChanged = False
		# TODO: discuss the validity of such approach when checking on the global optimality
		# if self.currentEnergy < self._globalMinimumEnergy and self.currentTax == 0:
		if  self.currentEnergy < self._globalMinimumEnergy and self.contains_several_vertices(self.currentState):
			output("\t New global optimum registered: old value = {}, new value = {}, state = {}"\
					 .format(str(self._globalMinimumEnergy),str(self.currentEnergy),self.getCurrentState()),isDebug=False)
			self._globalMinimumEnergy = self.currentEnergy
			self._globalMinimumState = copy(self.currentState)
			isChanged = True
		if self.currentEnergy < self.localMinimumEnergy and not self.isAllZeros(self.currentState):     #should we update global as well? Now I do it
			output("\t New local optimum registered: old value = {}, new value = {}, state = {}"\
					 .format(self.localMinimumEnergy,self.currentEnergy,self.getCurrentState()),isDebug=False)
			self.localMinimumEnergy = self.currentEnergy
			self.localMinimumState = copy(self.currentState)
			self.localMinimumTax = self.currentTax
			isChanged = True
		return isChanged

	def count_neighbourhood_states(self,state):
		"""
		Calculates the energies and taxes for neighbours
		:param state:
		:return: list of energies and taxes
		"""
		assert len(state) > 0
		energies = [float("inf") for i in range (self._size)]
		taxes = [float("inf") for i in range (self._size)]

		for i in range (0,self._size):
			newState = copy(state)
			newState[i] = 1 - newState[i]
			energies[i] = self.count_energy(newState)
			taxes[i] = self.count_tax(newState)

		return energies,taxes

	def count_energy_diff_states(self,j=-1,isInitial=False):
		"""
		Recalculates energies possible changes
		:param j: index of neuron changed its state
		:return: void, works only with current state
		"""
		assert len(self.currentState) > 0
		if not isInitial:
			for i in range(self._size):
				if i == j:
					self._diffEi[i] = -self._diffEi[i]
				elif i != j and self.currentState[i] == 0:
					self._diffEi[i] += self.myWeights[i][j] * (1 - 2*self.currentState[j])
				else:
					self._diffEi[i] -= self.myWeights[i][j] * (1 - 2*self.currentState[j])
		else:
			for j in range(self._size):
				sum = 0
				for i in range(self._size):
					sum += self.myWeights[i][j]*self.currentState[i]
				self._diffEi[j] = (2 * self.currentState[j] - 1)*(sum - self.myB)

	def choose_best_neighbour(self):#,energies,taxes):
		"""
		Chooses the best neighbour by two criteria: energy and punishment

		:return: index of the best neuron
		"""
		rejected = []     # list of prohibited indexes which are rejected because of tabu and energy
		nIndex = -1
		while(True):
			nIndex = self._find_absolute_best(rejected=rejected)		#index of best neighbor
			if (nIndex < 0):
				nIndex = self._find_pareto_frontier(rejected=rejected)    #always returns index

			if self.is_tabu(nIndex):
				output(message="\t Neuron is in tabu. Need to check the aspiration criteria",isDebug=True)
				# tmpState = self.currentState
				# tmpState[nIndex] = 1 - tmpState[nIndex]
				if self.aspiration_criteria_satisfied(nIndex):
					break
				else:
					rejected.append(nIndex)
			else:
				break
		# output("Neuron is found",isDebug=True)
		return nIndex

	def choose_best_neighbour_simple(self):
		"""
		Chooses best neighbour only by the energy function
		:return: the index of the best neighbour
		"""
		rejected = set([])     #list of prohibited indexes which are rejected because of tabu and energy
		nIndex = -1
		while(True):
			nIndex = self._find_min_diff(rejected=rejected)		#index of best neighbor

			if self.is_tabu(nIndex):
				output(message="\t Neuron is in tabu. Need to check the aspiration criteria",isDebug=True)
				if self.aspiration_criteria_satisfied(nIndex):
					break
				else:
					rejected.add(nIndex)
			else:
				break
		# output("Neuron is found",isDebug=True)
		return nIndex

	def _find_min_diff(self, rejected):
		# TODO: optimize search for a minimum
		"""
		Find the minimum function difference among all neighbours
		:param rejected: list of already processed vertices
		:return: the index of the neighbour
		"""
		indexes = [i for i in range(self._size) if i not in rejected]
		vector = copy(self._diffEi)
		for i in sorted(rejected,reverse=True):
			del vector[i]
		return min(zip(indexes,vector), key=itemgetter(1))[0]

	def _find_absolute_best(self,rejected):
		"""
		Check if there is the minimum for both criteria: the lowest energy and the lowest tax
		:rtype : the index of the best minimum neighbour
		"""
		myBest = -1
		minEnergy = min(self._diffEi)
		minTax = min(self._taxes)
		i = 0
		for energy,tax in zip (self._diffEi,self._taxes):
			if i in rejected:
				continue
			if energy == minEnergy and tax == minTax:
				myBest = i
				break
			i += 1
		return myBest


	def _find_pareto_frontier(self,rejected):
		"""
		Finds the best neuron by two criteria: energy function and punishment function
		:param rejected: the list of already processed vertices in this iteration
		:return: index of the best neuron
		"""
		indexes = [i for i in range(self._size)]
		mylist = sorted([[self._diffEi[i],self._taxes[i],indexes[i]] for i in range(len(self._diffEi))],reverse=False)	#find pareto frontier
		p_front = [mylist[0]]
		for pair in mylist[1:]:
			#TODO: check it: do we really want to get bigger values?
			if pair[1] <= p_front[-1][1]:
				p_front.append(pair)
		assert  len(p_front) > 0
		p_index = -1
		while True:
			p_index = random.randint(0,len(p_front)-1)
			if p_index in rejected:
				continue
			else:
				break
		assert p_index != -1
		assert p_front[p_index]
		nIndex = p_front[p_index][2]
		return nIndex

	def move_neuron_to_tabu(self,index):
		assert self.check_tabu_list
		self._tabu_list[index] = self._k

	def is_smtp_over(self):
		"""
			Check if we have any more iterations in this space
			:rtype : boolean
		"""
		if self._h > self._beta*self._size:
			return True
		return False

	def is_lmtp_over(self):
		"""
			Check if we have any more jumps in this space
			:rtype : boolean
		"""
		if self._c >= self._C:
			return True
		return False

	def get_oldest_neuron(self):
		"""
		find the neuron in the tabu list who remains unchanged more than others
		:return: index of that neuron
		"""
		assert self.check_tabu_list
		if (float("inf") in self._tabu_list):
			return self._tabu_list.index(float("inf"))
		numIter = min(self._tabu_list)
		return self._tabu_list.index(numIter)

	def check_tabu_list(self):
		"""
		Common test on the tabu list
		:return: boolean
		"""
		return len(self._tabu_list) > 0 and len(self._tabu_list) == self._size

	def is_tabu(self, index):
		"""
		checks if the neuron is in tabu list
		:rtype : boolean
		"""
		if abs(self._k - self._tabu_list[index]) <= self.__l:
			return True
		return False

	def aspiration_criteria_satisfied(self,index):
		"""
		Checks if aspiration criteria is satisfied
		:param index: neuron whose state to be changed
		:return: boolean
		"""
		newEnergy = self.currentEnergy + self._diffEi[index]#self.count_energy(state)
		# newTax = self._taxes[index]#self.count_tax(state=state)
		tmpState = copy(self.currentState)
		tmpState[index] = 1 - tmpState[index]
		newTax = self.count_tax(state=tmpState)
		output("Checking aspiration criteria: oldEnergy={}, current tax = {}; new energy = {}, new tax = {}"\
					 				.format(self.currentEnergy,self.currentTax,newEnergy,newTax),isDebug=True,tabsNum=1)
		if newEnergy < self.localMinimumEnergy or newTax < self.localMinimumTax:
			return True
		return False


	
	def get_best_clique(self):
		"""
		As clique is active neurons (with state 1), so calculates the sum of elements as the clique
		size
		:return: size of the clique found
		"""
		return [i+1 for i in range(self._size) if self._globalMinimumState[i] == 1]


	def count_taxes(self):
		"""
			Recalculates taxes for every neighbourhood state
		"""
		for i in range (self._size):
			tmpState = copy(self.currentState)
			tmpState[i] = 1 - tmpState[i]
			self._taxes[i] = self.count_tax(state=tmpState)

	def isAllZeros(self, currentState):
		"""
		Checks if the given list contains only 0
		:param currentState:
		:return: boolean
		"""
		isZeros = True
		for i in currentState:
			if i != 0:
				isZeros = False
				break
		return isZeros

	def contains_several_vertices(self, currentState):
		"""
		Calculates if the best state contains cliques of size more than 3
		:param currentState:
		:return: boolean
		"""
		return True if sum(currentState) > 3 else False