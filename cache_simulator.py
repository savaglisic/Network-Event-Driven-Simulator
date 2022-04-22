# -*- coding: utf-8 -*-
"""Cache_Simulator.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZLgE7y3Q2nSQEHxQGyvx0anob-saV27J
"""

import numpy as np
import queue as q
import random as rand

#Event Class for Relevant Event Data
class Event: 
  def __init__(self, _fileIndex, _eventType, _time, _t0):
    self.eventType = _eventType
    self.t0 = _t0
    self.fileIndex = _fileIndex
    self.time = _time

  def getType(self):
    return self.eventType

  def getOriginTime(self):
    return self.t0

  def getTime(self):
    return self.time
  
  def getFile(self):
    return self.fileIndex

#Cache With FIFO Replacement Policy
class FIFOCache:
  def __init__(self, _maxSize, _sim):
    self.maxSize = _maxSize
    self.currSize = 0.
    self.sim = _sim

    self.values = dict()
    self.quValues = q.deque()

  def getSpaceLeft(self):
    return self.maxSize - self.currSize

  def makeSpace(self, _sizeNeeded):
    spaceMade = 0.
    while spaceMade < _sizeNeeded:
      currIndex = self.quValues.popleft()
      spaceMade += self.sim.getFileSize(currIndex)
      self.currSize -= self.sim.getFileSize(currIndex)
      self.values.pop(currIndex)

  def insert(self, _index, _size, _time):  
    if self.getSpaceLeft() < _size:
      self.values[_index] = _time
      self.quValues.append(_index)
    else: 
      self.makeSpace((self.currSize + _size) - self.maxSize)
      self.values[_index] = _time
      self.quValues.append(_index)

    self.currSize += _size
    
  def contains(self, _index):
    return _index in self.values

#Cache With LIFO Replacement Policy
class LIFOCache:
  def __init__(self, _maxSize, _sim):
    self.maxSize = _maxSize
    self.currSize = 0.
    self.sim = _sim

    self.values = dict()
    self.sValues = q.deque()

  def getSpaceLeft(self):
    return self.maxSize - self.currSize

  def makeSpace(self, _sizeNeeded):
    spaceMade = 0.
    while spaceMade < _sizeNeeded:
      currIndex = self.sValues.pop()
      spaceMade += self.sim.getFileSize(currIndex)
      self.currSize -= self.sim.getFileSize(currIndex)
      self.values.pop(currIndex)

  def insert(self, _index, _size, _time):
    if self.getSpaceLeft() < _size:
      self.values[_index] = _time
      self.sValues.append(_index)
    else: 
      self.makeSpace((self.currSize + _size) - self.maxSize)
      self.values[_index] = _time
      self.sValues.append(_index)

    self.currSize += _size
    
  def contains(self, _index):
    return _index in self.values

#Cache With Replacement Policy of Removing Least Popular
class PopCache:
  def __init__(self, _maxSize, _sim):
    self.maxSize = _maxSize
    self.currSize = 0.
    self.sim = _sim

    self.values = dict()
    self.pqValues = q.PriorityQueue()
  
  def getSpaceLeft(self):
    return self.maxSize - self.currSize

  def makeSpace(self, _sizeNeeded):
    spaceMade = 0.
    while spaceMade < _sizeNeeded:
      currIndex = self.pqValues.get()[1]
      spaceMade += self.sim.getFileSize(currIndex)
      self.currSize -= self.sim.getFileSize(currIndex)
      self.values.pop(currIndex)

  def insert(self, _index, _size, _time, _pop):
    if self.getSpaceLeft() < _size:
      self.values[_index] = _time
      self.pqValues.put((_pop, _index))
    else: 
      self.makeSpace((self.currSize + _size) - self.maxSize)
      self.values[_index] = _time
      self.pqValues.put((_pop,_index))

    self.currSize += _size
    
  def contains(self, _index):
    return _index in self.values

#Cache With Replacement Policy of Removing Largest
class SizeCache:
  def __init__(self, _maxSize, _sim):
    self.maxSize = _maxSize
    self.currSize = 0.
    self.sim = _sim

    self.values = dict()
    self.pqValues = q.PriorityQueue()
  
  def getSpaceLeft(self):
    return self.maxSize - self.currSize

  def makeSpace(self, _sizeNeeded):
    spaceMade = 0.
    while spaceMade < _sizeNeeded:
      currIndex = self.pqValues.get()[1]
      spaceMade += self.sim.getFileSize(currIndex)
      self.currSize -= self.sim.getFileSize(currIndex)
      self.values.pop(currIndex)

  def insert(self, _index, _size, _time):
    if self.getSpaceLeft() < _size:
      self.values[_index] = _time
      self.pqValues.put((_size, _index))
    else: 
      self.makeSpace((self.currSize + _size) - self.maxSize)
      self.values[_index] = _time
      self.pqValues.put((-1 * _size,_index))

    self.currSize += _size
    
  def contains(self, _index):
    return _index in self.values

#Event-Driven Simulator of Institutional Cache
class CacheSim:
  def __init__(self, _N, _mu, _lamb, _tMax, _cachePolicy, _cacheSize, _Rc, _dMean, _dStdDev, _Ra, _alpha):
    #params
    self.N = _N
    self.mu = _mu
    self.lamb = _lamb
    self.tMax = _tMax
    self.cachePolicy = _cachePolicy
    self.cacheSize = _cacheSize
    self.Rc = _Rc
    self.dMean = _dMean
    self.dStdDev = _dStdDev
    self.Ra = _Ra
    self.alpha = _alpha

    #performance tracking
    self.numResponses = 0.
    self.sumResponseTimes = 0.
    self.numRequests = 0.
    self.numCacheHits = 0.
    
    #utility members
    self.accessLink = q.Queue()
    self.eventQ = q.PriorityQueue()
    self.time = 0
    self.requests = []
    self.fileSizes = []
    self.popularities = []

  #how long before next file request
  def nextRequestTime(self):
    return (np.random.poisson(self.lamb, self.N)[0])

  #load in N file sizes 
  def genFileSizes(self):
    for i in range(self.N):
      self.fileSizes.append(np.random.pareto(self.mu) + 1)

  #get file size of index
  def getFileSize(self, _index):
    return (self.fileSizes[_index])
  
  #draw a D value
  def getD(self):
    return np.random.default_rng().lognormal(self.dMean, self.dStdDev)

  #draw an X value
  def getX(self):
    return np.random.Generator.exponential(1/self.lamb)

  #load file popularities
  def genPopularities(self):
    qValues = []
    qSum = 0.
    
    for i in range(self.N):
      currQ = np.random.pareto(self.mu) + 1
      qValues.append(currQ)
      qSum += currQ

    for j in range(self.N):
      self.popularities.append(qValues[j] / qSum)

  #get popularity of index
  def getPopularity(self, _index):
    return self.popularities[_index]


  #insert event into event queue
  def addEvent(self, _eventTime, _newEvent):
    qTime = _eventTime

    while True:
      try:
        self.eventQ.put((qTime, _newEvent))
        break
      except TypeError:
        qTime += 0.000001
        


  #select a random file based on popularities
  def pickFile(self):
    return rand.choices(np.arange(0, self.N, 1), self.popularities)
  
  #deprecated function to for previous simulation implementation
  def loadRequests(self):
    for i in range(self.tMax):
      numRequests = self.getNumRequests()
      for j in range(numRequests):
        self.requests.append(self.pickFile()[0])

  #simulation loop
  def runSim(self):
    self.genFileSizes()
    self.genPopularities()
  
    self.eventQ.put((self.time, Event(self.pickFile()[0], 0, self.time, self.time)))

    if self.cachePolicy == 0:
      currCache = FIFOCache(self.cacheSize, self)
    elif self.cachePolicy == 1:
      currCache = LIFOCache(self.cacheSize, self)
    elif self.cachePolicy == 2:
      currCache = PopCache(self.cacheSize, self)
    elif self.cachePolicy == 3:
      currCache = SizeCache(self.cacheSize, self)

    while self.time < self.tMax:
      currVal = self.eventQ.get()
      currEvent = currVal[1]
      currTime = currVal[0]

      self.time = currTime

      #new request event
      if currEvent.getType() == 0:
          #check in cache for file
        if currCache.contains(currEvent.getFile()):
          self.numCacheHits += 1.0

          #gen file received event
          newTime1 = currTime + (self.getFileSize(currEvent.getFile()) / self.Rc)
          self.addEvent(newTime1, Event(currEvent.getFile(), 1, newTime1, currEvent.getOriginTime()))
          #self.eventQ.put((newTime1, Event(currEvent.getFile(), 1, newTime1, currEvent.getOriginTime())))
        else:
          if self.cachePolicy == 2:
            currCache.insert(currEvent.getFile(), self.getFileSize(currEvent.getFile()), currTime, self.getPopularity(currEvent.getFile()))
          else:
            currCache.insert(currEvent.getFile(), self.getFileSize(currEvent.getFile()), currTime)
         
          #else: gen arrive at queue event
          newTime2 = currTime + self.getD()
          self.addEvent(newTime2, Event(currEvent.getFile(), 2, newTime2, currEvent.getOriginTime()))
          #self.eventQ.put((newTime2, Event(currEvent.getFile(), 2, newTime2, currEvent.getOriginTime())))
          
        #gen new request event
        newTime3 = currTime + self.nextRequestTime()
        self.addEvent(newTime3, Event(self.pickFile()[0], 0, newTime3, newTime3))
        #self.eventQ.put((newTime3, Event(self.pickFile()[0], 0, newTime3, newTime3)))        

      #file received event
      elif currEvent.getType() == 1:
        responseTime = currEvent.getTime() - currEvent.getOriginTime()
        self.numResponses += 1
        self.numRequests += 1.
        self.sumResponseTimes += responseTime

      #arrive at queue event
      elif currEvent.getType() == 2:
        if self.accessLink.empty():
          newTime4 = currTime + (self.getFileSize(currEvent.getFile()) / self.Ra)
          self.addEvent(newTime4, Event(currEvent.getFile(), 3, newTime4, currEvent.getOriginTime()))
          #self.eventQ.put((newTime4, Event(currEvent.getFile(), 3, newTime4, currEvent.getOriginTime())))
        else:
          self.accessLink.put(currEvent)

      #depart queue event
      elif currEvent.getType() == 3:
        if self.cachePolicy == 2:
          currCache.insert(currEvent.getFile(), self.getFileSize(currEvent.getFile()), currTime, self.getPopularity(currEvent.getFile()))
        else:
          currCache.insert(currEvent.getFile(), self.getFileSize(currEvent.getFile()), currTime)
         
        newTime5 = currTime + (self.fileSizes[currEvent.getFile()] / self.Rc)
        self.addEvent(newTime5, Event(currEvent.getFile(), 1, newTime5, currEvent.getOriginTime()))
        #self.eventQ.put((newTime5, Event(currEvent.getFile(), 1, newTime5, currEvent.getOriginTime())))

        if not self.accessLink.empty():
          dqEvent = self.accessLink.get()
          newTime6 = currTime + (self.fileSizes[dqEvent.getFile()] / self.Ra)
          self.addEvent(newTime6, Event(dqEvent.getFile(), 3, newTime6, dqEvent.getOriginTime()))
          #self.eventQ.put((newTime6, Event(dqEvent.getFile(), 3, newTime6, dqEvent.getOriginTime())))

    print("cache hit rate: ")
    print(self.numCacheHits / self.numRequests)
    print("average response time:")
    print(self.sumResponseTimes / self.numResponses)

"""
  Parameter List Which Can Be Altered to Test Event-Driven Cache Simulation
"""

# N: number of files on the internet
N = 100000

# Mu: mean file size (MB)
Mu = 1

# Lambda: rate of user requests per second
lambdaValue = 5

# Simulation Run Time: how long simulation will run (S)
simulationTime = 10000

# Cache Replacement Policy: 0 refers to FIFO, 1 refers to LIFO,
# 2 refers to remove least popular, 3 refers to remove largest
cachePolicy = 3

# Cache Size: MBs of storage capacity in cache (MB)
cacheSize = 100

# Rc: institution network bandwidth  (Mbps)
Rc = 1000

# Mean D Value: mean propogation time between institution network
# and origin server (S) 
meanD = 0.5

# Standard Deviation of D Value: standard deviation of propogation 
# time between institution network and origin server (S)
stdDevD = 0.4

# Ra: bandwidth of inbound resource limitation (Mbps)
Ra = 15

# Alpha: shape parameter of pareto distribution
Alpha = 2

simulation = CacheSim(N, Mu, lambdaValue, simulationTime, cachePolicy, cacheSize, Rc, meanD, stdDevD, Ra, Alpha)
simulation.runSim()