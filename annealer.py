import time
import logging
import random

from tour import Tour
from math import sqrt, exp

class Annealer:
	# todo: try using nn output as seed for anneal
	# todo: add polarity tracking to other solutions
	# todo: explore listbased annealing/metropolis acceptance as well as annealing schedule.
	# explore effects
	#todo: optimize modification operations to update trail list and energy 
	def __init__(self,network, seedSegments=None, maxAttempts=None, maxIterations=2000000, initialTemp=None, tempDecay=0.95):
		self.network = network
		self.best = Tour(self.network) if seedSegments==None else Tour(network=self.network,segments=seedSegments)
		self.candidate = None
		self.temperatureDecay = 0.95
		self.temperature = sqrt(len(self.best.segments)*2) if initialTemp == None else initialTemp
		self.improvements = 0
		self.attempts = 0
		self.iterations = 0
		self.maxAttempts = 100*len(self.best.segments)*2 if maxAttempts == None else maxAttempts
		self.maxIterations = self.maxAttempts*2 if maxIterations == None else maxIterations

	def createCandidate(self):
		self.candidate = Tour(self.network,self.best.findNeighborSegments())
	
	def testCandidate(self):
		cost = self.candidate.energy - self.best.energy
		if cost < 0:
			logging.info(f"Energy improved by {self.best.energy - self.candidate.energy} after {self.attempts} attempts.")
			logging.info(f"New energy level is {self.candidate.energy}")
			self.best = self.candidate
			self.candidate = None
			self.improvements = self.improvements + 1
			self.attempts = 0
		else:
			sample = random.random()
			probability = exp(-cost/self.temperature)
			if sample < probability:
				logging.info(f"Accepting a bad solution due to a sufficiently high temperature.")
				logging.info(f"New energy level is {self.candidate.energy}")
				self.best = self.candidate
				self.candidate = None
			else:
				self.attempts = self.attempts + 1
	
	def runTemperatureScheduler(self):
		if self.improvements > 10 * len(self.best.segments):
			self.temperature = self.temperature * self.temperatureDecay
			self.improvements = 0
			self.attempts = 0
			logging.info(f"Decreasing temperature to {self.temperature}")
	
	def anneal(self):
		while self.attempts < self.maxAttempts and self.iterations < self.maxIterations:
			start = time.perf_counter()*1000
			self.createCandidate()
			self.testCandidate()
			self.runTemperatureScheduler()
			self.iterations = self.iterations + 1
			end = time.perf_counter()*1000
			logging.debug(f"1 annealing iteration took {end-start}ms")