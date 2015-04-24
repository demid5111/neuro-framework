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
    output(message="Step {}. Initialize the Tabu machine: k,c,neurons".format(str(i)),isDebug=True)
    myTM = TabuMachine()
    myTM.setC(C=myC)
    myTM.setSize(len(myAdjMatrix))
    i += 1
    output(message="Step {}. Randomly initialize the neurons states".format(str(i)),isDebug=True)
    myTM.initializeIns()
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