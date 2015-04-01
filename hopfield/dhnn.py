import random
from hopfield.layer import Layer
from service_functions import output

__author__ = 'demidovs'

class HNN ():
  def __init__(self,A,B):
    self.numLayers = -1
    self.layers = []
    self.maxNumCycles = 50
    self.convergencyPrecision = 0.0001
    self.weightMatrices = []
    self.myA = A
    self.myB = B
    self.adjMatrix = []
    self.outputVec = []
    output ("created",self)

  def __str__(self):
    return "<{}> number of Layers = {}"\
            .format(self.__class__.__name__,str(len(self.layers)))

  def setAdjMatrix(self,matrix):
    self.adjMatrix = matrix


  def addLayer(self,size):
    self.layers.append(Layer(size))
    output("layer added",self)

  def removeLayer(self, index):
    try:
      del self.layers[index]
      return True
    except KeyError:
      return False


  def initNetwork(self):
    self.outputVec = [random.randint(0,1) \
                      for i in range(0,len(self.layers[0].weightMatrix))]
    output("initialized", self)

  def calculateEnergy(self):
    A_term = 0
    B_term = 0
    N = len(self.layers[0].weightMatrix)
    for i in range(0,N):
      for j in range(0,N):
        if i == j:
          continue
        else:
          A_term += (1 - self.adjMatrix[i][j])*self.outputVec[i]*self.outputVec[j]
    B_term = sum(self.outputVec)

    output("calculated energy",self)
    return A_term*self.myA + B_term*self.myB

  def cycle(self):
    output("in cycle", self)
    pass

  def start(self):
    output("started cycling", self)
    i = 0
    while(True):
      if i > self.maxNumCycles:
        break
      else:
        self.cycle()
        self.calculateEnergy()
        self.isConverged()
        i += 1

  def isConverged(self):
    output("checked for convergence",self,True)

  def calculateActivationSignmoid(self):
    output("calculated sigmoid activation",self,True)

  def updateNeuronsOutput(self):
    output("updated neurons axons",self,True)

  def updateWeights(self):
    output("updated weigths",self,True)