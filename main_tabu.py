import os

from service_functions import output, readCliqueInAdjMatrix
from tabu.tabu_machine import TabuMachine


__author__ = 'demid5111'

if __name__ == "__main__":
	###############################################
	####All necessary staff for correct workflow
	###############################################
	myC = 3
	current_working_directory = os.getcwd()
	myAdjMatrix = readCliqueInAdjMatrix("C125.9.clq")
	###############################################
	output(message="Starting tabu work",isDebug=True)
	i = 0
	i += 1
	output(message="Step {}. Initialize the Tabu machine: k,c,neurons states, tabu list".format(str(i)),isDebug=True)
	myTM = TabuMachine()
	myTM.setC(C=myC)
	myTM.setSize(len(myAdjMatrix))
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
	myTM.checkForEnergyTaxUpdate()
	i += 1
	output(message="Step {}. Count energies of the neighbours states".format(str(i)),isDebug=True)
	energies, taxes = myTM.countNeighbourhoodStates(myTM.getCurrentState())
	i += 1
	output(message="Step {}. Choose neighbour to move to".format(str(i)),isDebug=True)
	energies, taxes = myTM.countNeighbourhoodStates(myTM.getCurrentState())
	bestNeighbour = myTM.chooseBestNeighbour(energies=energies,taxes=taxes)
	#TODO: add check if this neuron is in tabu and check aspiration criterion for him
	output(message="\t Best neighbour to move to is: energy={}, tax={}"\
		.format(energies[bestNeighbour],taxes[bestNeighbour]),isDebug=True)
	#TODO: add check if this neuron really decreases the energy function
	i += 1
	output(message="Step {}. Change current state, update energies. Move neuron to tabu list".format(str(i)),isDebug=True)
	myTM.changeCurrentState(bestNeighbour)
	myTM.moveNeuronToTabu(bestNeighbour)
	myTM.setCurrentEnergy(energies[bestNeighbour])
	myTM.setCurrentTax(taxes[bestNeighbour])
	myTM.checkForEnergyTaxUpdate()
	i += 1
	output(message="Step {}. Update k,c. Check if smtp either lmtp to continue ".format(str(i)),isDebug=True)
	myTM.incrementK()
	if myTM.is_smtp_over():
		if myTM.is_lmtp_over():
			output("\t Global search is over. Get out best solution (global minimum) found so far",isDebug=True)
		else:
			output("\t Local search is over. Need to move far away from here",isDebug=True)
			#TODO: decide if k index should be a global one
			#TODO: decide if tabu list should be erased with new jump or not
			oldIndex = myTM.get_oldest_neuron()
	else:
		output("\t Continue local search",isDebug=True)
	i += 1
