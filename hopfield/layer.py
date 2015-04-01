from service_functions import makeRandomMatrix

__author__ = 'demidovs'

class Layer():
  def __init__(self,size):
    self.size = size
    self.weightMatrix = []
    self.initWeights()

  def initWeights(self):
    self.weightMatrix = makeRandomMatrix(self.size,self.size)

  def getAxon(self):
    return self.axon
