import os

from service_functions import output, readCliqueInAdjMatrix
from tabu.tabu_machine import TabuMachine


__author__ = 'demid5111'

if __name__ == "__main__":
	###############################################
	# All necessary staff for correct workflow
	###############################################

	current_working_directory = os.getcwd()
	# myAdjMatrix = readCliqueInAdjMatrix("C125.9.clq")
	myAdjMatrix = readCliqueInAdjMatrix("sample6_10.clq")

	myC = 3

	TABU_SIZE = len(myAdjMatrix)/2
	BETA = TABU_SIZE/len(myAdjMatrix)+1
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
	myTM.initializeIns()
	myTM.createTabuList()
	i += 1
	output(message="Step {}. Randomly initialize the neurons states".format(str(i)),isDebug=True)

	i += 1
	output(message="Step {}. Fill weight matrix".format(str(i)),isDebug=True)
	myTM.fillWeightMatrix(myAdjMatrix)
	i += 1
	output(message="Step {}. Count current energy and tax".format(str(i)),isDebug=True)
	energy = myTM.countEnergy(myTM.getCurrentState())
	tax = myTM.countTax(myTM.getCurrentState())
	myTM.setCurrentEnergy(energy)
	myTM.setCurrentTax(tax)
	i += 1
	output(message="Step {}. Update energies if needed".format(str(i)),isDebug=True)
	myTM.check_for_energy_tax_update()
	i += 1
	output(message="Step {}. Count energies of the neighbours states".format(str(i)),isDebug=True)
	energies, taxes = myTM.countNeighbourhoodStates(myTM.getCurrentState())
	i += 1
	j = i
	output(message="Start cycling the TM to find the best solution")
	while(True):
		i = j
		output(message="Step {}. Choose neighbour to move to".format(str(i)),isDebug=True,tabsNum=1)
		energies, taxes = myTM.countNeighbourhoodStates(myTM.getCurrentState())
		bestNeighbour = myTM.choose_best_neighbour(energies=energies,taxes=taxes)
		# TODO: add check if this neuron is in tabu and check aspiration criterion for him
		output(message="\tBest neighbour to move to is: energy={}, tax={}"\
			.format(energies[bestNeighbour],taxes[bestNeighbour]),isDebug=True,tabsNum=1)
		# TODO: add check if this neuron really decreases the energy function
		i += 1
		output(message="Step {}. Change current state, update energies. Move neuron to tabu list"\
			.format(str(i)),isDebug=True,tabsNum=1)
		myTM.changeCurrentState(bestNeighbour)
		myTM.moveNeuronToTabu(bestNeighbour)
		myTM.setCurrentEnergy(energies[bestNeighbour])
		myTM.setCurrentTax(taxes[bestNeighbour])

		i += 1
		output(message="Step {}. Update k,c, Update energies. Check if smtp either lmtp to continue "\
			.format(str(i)), isDebug=True,tabsNum=1)
		myTM.increment_k()
		# myTM.increment_h()
		if myTM.check_for_energy_tax_update():
			myTM.erase_h()
		else:
			myTM.increment_h()
		if myTM.is_smtp_over():
			if myTM.is_lmtp_over():
				output("Global search is over. Get out best solution (global minimum) found so far", isDebug=True, tabsNum=1)
				output("Best energy: value = {}".format(myTM.get_global_minimum_energy()), isDebug=True)
				output("Max clique size: value = {}"\
					.format(myTM.get_clique_size(myTM.get_global_minimum_state())), isDebug=True)
				break
			else:
				output("\t Local search is over. Need to move far away from here",isDebug=True,tabsNum=1)
				oldIndex = myTM.get_oldest_neuron()
				myTM.changeCurrentState(bestNeighbour)
				myTM.moveNeuronToTabu(bestNeighbour)
				myTM.setCurrentEnergy(energies[bestNeighbour],isLocalMin=True)
				myTM.setCurrentTax(taxes[bestNeighbour])
				myTM.erase_h()
		else:
			output("\t Continue local search",isDebug=True,tabsNum=1)
		i += 1
