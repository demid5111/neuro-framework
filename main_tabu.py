from service_functions import output, readCliqueInAdjMatrix, check_clique
from tabu.tabu_machine import TabuMachine


__author__ = 'demid5111'

if __name__ == "__main__":
	###############################################
	# All necessary staff for correct workflow
	###############################################
	output(message="Pre-processing: reading clique",isDebug=False)
	# fileName = "C125.9.clq"
	fileName = "sample6_10.clq"
	i = 0
	i += 1
	output(message="Step {}. Read clique from file {}".format(str(i),fileName),isDebug=True)
	myAdjMatrix = readCliqueInAdjMatrix(fileName)
	# print(myAdjMatrix)
	myC = 5

	TABU_SIZE = int(len(myAdjMatrix)/2)
	BETA = TABU_SIZE/len(myAdjMatrix)+2
	i += 1
	###############################################
	output(message="Starting tabu work",isDebug=True)
	i = 0
	i += 1
	output(message="Step {}. Initialize the Tabu machine: k,c,neurons states, tabu list".format(str(i)),isDebug=True)
	myTM = TabuMachine()
	myTM.setC(C=myC)
	myTM.setSize(len(myAdjMatrix))
	myTM.set_tabu_size(TABU_SIZE)
	myTM.set_beta(BETA)
	myTM.initialize_tabu_list()
	i += 1
	output(message="Step {}. Randomly initialize the neurons states".format(str(i)),isDebug=True)
	myTM.initialize_state()
	i += 1
	output(message="Step {}. Fill weight matrix".format(str(i)),isDebug=True)
	myTM.fillWeightMatrix(myAdjMatrix)
	i += 1
	output(message="Step {}. Count current energy and tax".format(str(i)),isDebug=True)
	energy = myTM.count_energy(myTM.getCurrentState())
	tax = myTM.count_tax(myTM.getCurrentState())
	myTM.set_energy(energy)
	myTM.set_tax(tax)
	i += 1
	output(message="Step {}. Update energies if needed".format(str(i)),isDebug=True)
	myTM.check_for_energy_tax_update()
	i += 1
	output(message="Step {}. Count energies of the neighbours states".format(str(i)),isDebug=True)
	# energies, taxes = myTM.countNeighbourhoodStates(myTM.getCurrentState())
	myTM.count_energy_diff_states(isInitial=True)
	# myTM.count_taxes()
	i += 1
	j = i
	output(message="Start cycling the TM to find the best solution")
	while(True):
		i = j
		output(message="Step {}. Choose neighbour to move to".format(str(i)),isDebug=True,tabsNum=1)
		# energies, taxes = myTM.countNeighbourhoodStates(myTM.getCurrentState())
		# bestNeighbour = myTM.choose_best_neighbour()#energies=energies,taxes=taxes)
		bestNeighbour = myTM.choose_best_neighbour_simple()#energies=energies,taxes=taxes)
		# TODO: add check if this neuron is in tabu and check aspiration criterion for him
		output(message="\tBest neighbour to move to is: energy={}, tax={}"\
			.format(myTM._diffEi[bestNeighbour],myTM._taxes[bestNeighbour]),isDebug=True,tabsNum=1)
		# TODO: add check if this neuron really decreases the energy function
		i += 1
		output(message="Step {}. Change current state, update energies. Move neuron to tabu list"\
			.format(str(i)),isDebug=True,tabsNum=1)
		myTM.changeCurrentState(bestNeighbour)
		myTM.moveNeuronToTabu(bestNeighbour)
		myTM.update_energy(index=bestNeighbour)
		myTM.set_tax(myTM.count_tax(myTM.getCurrentState()))
		i += 1

		output(message="Step {}. Update neighbours energies and taxes"\
			.format(str(i)), isDebug=True,tabsNum=1)
		myTM.count_energy_diff_states(bestNeighbour)
		# myTM.count_taxes()
		i += 1

		output(message="Step {}. Update k,c, Update energies. Check if smtp either lmtp to continue "\
			.format(str(i)), isDebug=True,tabsNum=1)
		myTM.increment_k()
		if myTM.check_for_energy_tax_update():
			myTM.erase_h()
		else:
			myTM.increment_h()
		if myTM.is_smtp_over():
			if myTM.is_lmtp_over():
				output("Global search is over. Get out best solution (global minimum) found so far", isDebug=False, tabsNum=1)
				output("Best energy: value = {}".format(myTM.get_global_minimum_energy()), isDebug=False)
				output("Max clique size: value = {}"\
					.format(myTM.get_clique_size(myTM.get_global_minimum_state())), isDebug=False)
				output("The global minimum state: clique indices: " + str(myTM.get_best_clique()),isDebug=False)
				left = check_clique(vertices=myTM.get_best_clique(),adjMatrix=myAdjMatrix)
				output("Number of edges left: " + str(left),isDebug=False)
				break
			else:
				output("\t Local search is over. Need to move far away from here. c = {}, C = {}"\
							 .format(myTM.get_c(),myTM.get_C()),isDebug=False,tabsNum=1)
				oldIndex = myTM.get_oldest_neuron()
				myTM.changeCurrentState(oldIndex)
				myTM.moveNeuronToTabu(oldIndex)
				myTM.update_energy(oldIndex,isLocalMin=True)
				# myTM.update_tax(bestNeighbour)
				myTM.set_tax(myTM.count_tax(myTM.getCurrentState()))
				myTM.erase_h()
				myTM.increment_c()
				i += 1
				output(message="Step {}. Update neighbours energies and taxes"\
					.format(str(i)), isDebug=True,tabsNum=1)
				myTM.count_energy_diff_states(oldIndex)
				# myTM.count_taxes()
				i += 1
		else:
			output("\t Continue local search",isDebug=True,tabsNum=1)
		i += 1
