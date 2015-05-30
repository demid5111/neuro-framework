from math import exp

from service_functions import make_random_matrix, output


__author__ = 'demidovs'

class Layer():
  def __init__(self,size):
    self.size = size
    self.weightMatrix = []
    self.axons = [0 for x in range(0,size)]
    self.initWeights()

  def __str__(self):
    return "<{}> size = {}"\
            .format(self.__class__.__name__,str(self.size))

  def initWeights(self):
    self.weightMatrix = make_random_matrix(self.size,self.size)

  def getAxon(self):
    return self.axon

  def calculateWeightedSums(self):
    output("calculating sigmoid activation",self,True)
    neuronsSums = []
    for i in range(0, self.size):
      tmpSum = 0
      for j in range(0, self.size):
        if i == j:
          continue
        tmpSum += self.weightMatrix[i][j]*self.axons[j]
      neuronsSums.append(tmpSum)
    return neuronsSums

  def calculateActivationSignmoid(self, neuronSums,T):
    output("calculated sigmoid activation",self,True)
    y = []
    for i in neuronSums:
      tmp =  1/(1 + exp(-i/T))
      y.append(tmp)
    return y


  def updateNeuronsOutput(self,threshold):
    output("updated neurons axons",self,True)

  def updateWeights(self):
    output("updated weigths",self,True)

  def setAxons(self, newAxons):
    self.axons = newAxons

