import os

from hopfield.dhnn import HNN
from service_functions import output, readCliqueInAdjMatrix


__author__ = 'demidovs'

if __name__ == "__main__":
  NUM_LAYERS = 10
  LAYER_SIZE = -1
  MY_A = 10
  MY_B = 10
  current_working_directory = os.getcwd()
  adjMatrix = readCliqueInAdjMatrix(os.path.join(current_working_directory,"data","C125.9.clq"))
  output("Matrix read: size={}".format(len(adjMatrix)))
  LAYER_SIZE = len(adjMatrix)
  myNetwork = HNN(A=MY_A,B=MY_B)
  myNetwork.addLayer(LAYER_SIZE)
  myNetwork.setAdjMatrix(adjMatrix)
  myNetwork.initNetwork()
  myNetwork.start()
  output("Initialized HNN")