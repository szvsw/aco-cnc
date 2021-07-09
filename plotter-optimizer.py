# import numpy as np
import random
import time
import logging
from math import exp, sqrt

logging.basicConfig(level=logging.INFO)

class Vertex:
	def __init__(self):
		# self.loc =  [ random.random()*50,random.random()*50 ] # This line, paired with the commented out section in linesegment, helps vaguely replicate real world dataset
		self.loc =  [ random.random()*1000,random.random()*1000 ] 
		self.partner = None
		self.parentSegment = None
		self.id = None
		self.trails = {}
		self.sortedTrails = []

	def connect(self, vertex):
		self.partner = vertex
		vertex.partner = self
	
	def sortTrails(self):
		self.sortedTrails.sort(key=lambda trail : trail.length)

class LineSegment:
	def __init__(self):
		self.vertices = [Vertex(), Vertex()]
		# translation = (random.random()*950,random.random()*950)
		# for vertex in self.vertices:
		# 	for i in range(2):
		# 		vertex.loc[i] = vertex.loc[i]+translation[i]
		self.vertices[0].connect(self.vertices[1])
		self.length = pow(pow(self.vertices[0].loc[0]-self.vertices[1].loc[0],2)+ pow(self.vertices[0].loc[1]-self.vertices[1].loc[1],2),0.5)

		self.polarity = None
	

class Cezanne:
	def __init__(self,nSegments, nAnts, tau0,alpha,beta,phi,ro,maxGenerations):
		start = time.perf_counter()*1000
		self.maxGenerations = maxGenerations
		self.tau0 = tau0
		self.ro = ro
		self.phi = phi
		self.alpha = alpha
		self.beta = beta
		self.nAnts = nAnts

		self.segments = [LineSegment() for i in range(nSegments)]
		self.vertices = []
		for i in range(nSegments):
			for j in range(2):
				self.vertices.append(self.segments[i].vertices[j])
				self.vertices[-1].parentSegment = self.segments[i]
		
		for i in range(len(self.vertices)):
			self.vertices[i].id = i

		self.startingVertices = [self.vertices[int(random.random()*len(self.vertices))] for i in range(nAnts)]

		self.trails = []
		for vtx1 in self.vertices:
			for vtx2 in self.vertices:
				if vtx2.id in vtx1.trails:
					continue
				trail = Trail(vtx1,vtx2,cezanne=self) 
				vtx1.trails[vtx2.id] = trail
				vtx1.sortedTrails.append(trail)
				vtx2.trails[vtx1.id] = trail
				vtx2.sortedTrails.append(trail)
				self.trails.append(trail)
		
		for vtx in self.vertices:
			vtx.sortTrails()
		
		for i in range(len(self.trails)):
			self.trails[i].id = i
		
		self.bestAnt = None
		self.energyHistory = []

		end = time.perf_counter()*1000
		logging.info(f"Setup took {end-start}ms.")

	def createAntPopulation(self, reuseStarts=True):
		self.ants = [Ant(_id=i, _cezanne=self, _reuseStarts=reuseStarts) for i in range(self.nAnts)] 
		if self.bestAnt == None:
			self.bestAnt = self.ants[0]

	def constructTours(self):
		start = time.perf_counter()*1000
		for i in range(len(self.segments)-1):
			for ant in self.ants:
				ant.advance()

		end = time.perf_counter()*1000
		logging.info(f'Pathfinding took { end-start }ms.')
	
	def evaluateTours(self):
		start = time.perf_counter()*1000
		for ant in self.ants:
			ant.evaluateTour()
			if ant.energy < self.bestAnt.energy:
				self.bestAnt = ant
		end = time.perf_counter()*1000
		logging.info(f'Tour evaluation took { end-start }ms.')
	
	
	def globalUpdatePheromones(self):
		start = time.perf_counter()*1000
		self.bestAnt.markTrail()
		for trail in self.trails:
			trail.depositPheromone(amount=self.bestAnt.pheromoneLevel if trail.isInBestTrail else False, local=False)
			trail.isInBestTrail = False
		end = time.perf_counter()*1000
		logging.info(f'Trail marking took { end-start }ms.')
	
	def markLastTrails(self):
		for ant in self.ants:
			ant.markLastTrail()

	def executeGeneration(self):
		start = time.perf_counter()
		self.createAntPopulation()
		self.constructTours()
		self.evaluateTours()
		self.globalUpdatePheromones()
		self.energyHistory.append(self.bestAnt.energy)
		end = time.perf_counter()
		logging.info(f'Generation took { end-start }s.')
	
	def solve(self, mode='acs'):
		if mode == 'acs':
			start = time.perf_counter()
			for i in range(self.maxGenerations):
				logging.info(f"Starting generation {i}---")
				self.executeGeneration()
				logging.info(f"Best Energy: {self.bestAnt.energy }")
				if i > 50:
					if self.energyHistory[i]  > 0.99* self.energyHistory[i-25]:
						logging.info("Energy has not changed significantly for 50 generations, exiting.")
						break
				logging.info("")
			end = time.perf_counter()
			logging.info(f"{self.maxGenerations} generations took {end-start}s.")
			self.acsTime = end-start
			return self.energyHistory[-1]
		elif mode == 'anneal':
			start = time.perf_counter()*1000
			self.solve(mode='nn')
			seedSegments = [self.nnSolution['vertexHistory'][i*2].parentSegment for i in range(len(self.nnSolution['trailHistory']))]
			for i in range(len(self.nnSolution['trailHistory'])):
				seedSegments[i].polarity = 0 if self.nnSolution['vertexHistory'][i*2].id == seedSegments[i].vertices[0].id else 1
			self.annealer = Annealer(self,seedSegments=seedSegments, maxAttempts=200000,maxIterations=400000, initialTemp=500)
			self.annealer.anneal()
			end = time.perf_counter()*1000
			logging.info(f"Basic annealing took: {end-start}ms")
			logging.info(f"Annealing solution has energy: {self.annealer.best.energy}")
		elif mode == 'nn':
			self.nnSolutions = {}
			start = time.perf_counter()
			self.nnSolution = None
			verticesToSolve = []
			for i in range(50):
				vertex = random.choice(self.vertices)
				while vertex in verticesToSolve:
					vertex = random.choice(self.vertices)
				verticesToSolve.append(vertex)


			for vertex in verticesToSolve:
				#logging.info(f"Determining Solution for Vertex {vertex.id}")
				energy = 0
				trailHistory = []
				unvisited = [i for i in range(len(self.vertices))]
				vertexHistory = [vertex]
				unvisited.remove( vertexHistory[-1].id )
				vertexHistory.append(vertexHistory[-1].partner)
				unvisited.remove( vertexHistory[-1].id )
				while len(unvisited) != 0:
					currentVertex = vertexHistory[-1]
					bestTrail = currentVertex.trails[unvisited[0]]
					for trailID in unvisited:
						trail = currentVertex.trails[trailID]
						if trail.length < bestTrail.length:
							bestTrail = trail
					trailHistory.append(bestTrail)
					energy = energy + bestTrail.length
					nextVertex = bestTrail.vertices[0] if currentVertex == bestTrail.vertices[1] else bestTrail.vertices[1]
					vertexHistory.append(nextVertex)
					unvisited.remove(nextVertex.id)
					nextVertex = nextVertex.partner
					vertexHistory.append(nextVertex)
					unvisited.remove(nextVertex.id)
				self.nnSolutions[vertexHistory[0].id] = {
					'vertexHistory' : vertexHistory,
					'trailHistory' : trailHistory,
					'energy' : energy
				}
				if self.nnSolution == None:
					self.nnSolution = self.nnSolutions[vertexHistory[0].id]
				else:
					if self.nnSolutions[vertexHistory[0].id]['energy'] < self.nnSolution['energy']:
						self.nnSolution = self.nnSolutions[vertexHistory[0].id]
						logging.info(f"Vertex {vertex.id} is a new best vertex for nn, yielding energy: {self.nnSolution['energy']}")


			end = time.perf_counter()
			self.nnSolution['time'] = end-start
			logging.info(f'Neareset Neighbor Solution took {end-start}s')
			return self.nnSolution['energy']
		

class Tour:
	def __init__(self,cezanne,segments=None):
		self.cezanne = cezanne
		if segments == None:
			self.constructRandomTour()
		else:
			self.segments = segments
		self.segmentsToTrails()

	def constructRandomTour(self):
		self.segments = [segment for segment in self.cezanne.segments]
		random.shuffle(self.segments)
		for segment in self.segments:
			segment.polarity = random.choice([0,1])
			# todo: make polarities track with tour rather than segments by making a polarizedsegment class

	def segmentsToTrails(self):
		self.trails = []
		self.energy = 0
		for i in range(len(self.segments)-1):
			departureVertex = self.segments[i].vertices[1-self.segments[i].polarity]
			arrivalVertex = self.segments[i+1].vertices[self.segments[i+1].polarity]
			trail = departureVertex.trails[arrivalVertex.id]
			self.trails.append(trail)
			self.energy = self.energy + trail.length

	def cutAndPasteSection(self):
		segments = [segment for segment in self.segments]
		startIndex = int(random.random()*len(segments))
		lengthToCut = int(random.random()*(len(segments)-2))+1
		destinationIndex = int(random.random()*(len(segments)-lengthToCut))
		poppedSegments = [segments.pop(min(startIndex,len(segments))%len(segments)) for i in range(lengthToCut)]
		for i in range(len(poppedSegments)):
			segments.insert(destinationIndex+i, poppedSegments[i])
		return segments
	
	
	def reverseSection(self):
		segments = [segment for segment in self.segments]
		startIndex = int(random.random()*len(segments))
		lengthToReverse = int(random.random()*(len(segments)-1))+1
		elementsToReverse = [segments[(startIndex +i)%len(segments)] for i in range(lengthToReverse)]
		elementsToReverse.reverse()
		for element in elementsToReverse:
			element.polarity = 1-element.polarity
	
		for i in range(lengthToReverse):
			segments[(startIndex+i)%len(segments)] = elementsToReverse[i]
		return segments

	def moveSegment(self):
		segments = [segment for segment in self.segments]
		index = int(random.random()*len(segments))
		segment = segments.pop(index)
		index = int(random.random()*len(segments))
		segments.insert(index,segment)
		return segments


	def swapSegments(self):
		segments = [segment for segment in self.segments]
		firstIndex = int(random.random()*len(segments))
		secondIndex = (int(random.random()*(len(segments)-1)) + firstIndex) % len(segments) # ensure second index is not first.
		segments[firstIndex], segments[secondIndex] = segments[secondIndex], segments[firstIndex]
		return segments
	
	def invertSegment(self):
		segments = [segment for segment in self.segments]
		index = int(random.random()*len(segments))
		segments[index].polarity = 1-segments[index].polarity
		return segments
	
	def findNeighborSegments(self):
		action = random.choice([self.invertSegment,self.swapSegments, self.moveSegment, self.reverseSection, self.cutAndPasteSection])
		return action()

class Annealer:
	# todo: try using nn output as seed for anneal
	# todo: add polarity tracking to other solutions
	# todo: explore listbased annealing/metropolis acceptance as well as annealing schedule.
	# explore effects
	#todo: optimize modification operations to update trail list and energy 
	def __init__(self,cezanne, seedSegments=None, maxAttempts=None, maxIterations=2000000, initialTemp=None, tempDecay=0.95):
		self.cezanne = cezanne
		self.best = Tour(self.cezanne) if seedSegments==None else Tour(cezanne=self.cezanne,segments=seedSegments)
		self.candidate = None
		self.temperatureDecay = 0.95
		self.temperature = sqrt(len(self.best.segments)*2) if initialTemp == None else initialTemp
		self.improvements = 0
		self.attempts = 0
		self.iterations = 0
		self.maxAttempts = 100*len(self.best.segments)*2 if maxAttempts == None else maxAttempts
		self.maxIterations = self.maxAttempts*2 if maxIterations == None else maxIterations

	def createCandidate(self):
		self.candidate = Tour(self.cezanne,self.best.findNeighborSegments())
	
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

		
	
	



class Trail:
	def __init__(self, vtx1, vtx2, cezanne):
		self.cezanne = cezanne
		self.vertices = [vtx1,vtx2]
		self.id = None
		self.length = pow(pow(self.vertices[0].loc[0]-self.vertices[1].loc[0],2)+ pow(self.vertices[0].loc[1]-self.vertices[1].loc[1],2),0.5)
		self.desirability = pow(1/self.length,self.cezanne.beta) if self.length != 0 else 0
		self.tau = self.cezanne.tau0

		self.isInBestTrail = False

		if vtx1 is vtx2:
			self.tau = 0
		if vtx1.partner is vtx2:
			self.tau = 9999999999
		
	def depositPheromone(self,amount=0,local=True):
		evaporationRate = self.cezanne.phi if local else self.cezanne.ro
		amount = self.cezanne.tau0 if local else amount
		self.tau = (1-evaporationRate)*self.tau + evaporationRate * amount
class Ant:
	def __init__(self, _id, _cezanne, _reuseStarts):
		self.id = _id
		self.cezanne = _cezanne
		self.trails = []
		self.unvisited = []
		self.tour = []
		self.reset(vertex=self.cezanne.startingVertices[self.id] if _reuseStarts else None)
		self.energy = 0

	def reset(self,vertex=None):
		# todo - unvisited should probably be an array of objects not ids...
		self.unvisited = list(range(len(self.cezanne.vertices)))
		self.trails = []
		if vertex == None:
			self.tour = [random.choice(self.cezanne.vertices)]
		else:
			self.tour = [vertex]
		self.unvisited.remove(self.tour[-1].id)

		# Automatically advance the ant to the linked location
		self.tour.append(self.tour[-1].partner)
		self.unvisited.remove(self.tour[-1].id)

	
	def selectNextTrail(self,useSortedSearch=False):
		# todo - implement pseudo-random proporitonal selection with q0 parameter.
		currentVertex = self.tour[-1]
		availableTrails = [currentVertex.trails[vtxID] for vtxID in self.unvisited]
		numerators = [pow(currentVertex.trails[vtxID].tau,self.cezanne.alpha)*currentVertex.trails[vtxID].desirability for vtxID in self.unvisited]
		denominator = sum(numerators)
		probabilities = [numerator/denominator for numerator in numerators]

		if useSortedSearch:
			availableTrailIDs = [trail.id for trail in availableTrails]
			cumSum = 0
			sample = random.random()
			for trail in currentVertex.sortedTrails:
				if trail.id in availableTrailIDs:
					ix = availableTrailIDs.index(trail.id)
					cumSum = cumSum + probabilities[ix]
					if sample <  cumSum:
						return trail
		
		trail = random.choices(availableTrails,weights=probabilities)[0]
		return trail
	
	def followTrail(self,trail):
		# Todo: should this protect against selecting a bad trail, i.e. one that does not connect to last location?
		start = time.perf_counter()*1000
		self.trails.append(trail)
		nextVertex = trail.vertices[0] if self.tour[-1] is trail.vertices[1] else trail.vertices[1]
		self.tour.append(nextVertex)
		self.unvisited.remove(self.tour[-1].id)

		# Automatically Advance the tour to the next location
		self.tour.append(self.tour[-1].partner)
		self.unvisited.remove(self.tour[-1].id)
		end = time.perf_counter()*1000
	
	def advance(self):
		nextTrail = self.selectNextTrail()
		self.followTrail(nextTrail)
	
	def markLastTrail(self):
		# Deposite Pheromones
		self.trails[-1].depositPheromone(local=True) # Use local updating which uses tau0 for amount and phi for evap. rate
	
	def evaluateTour(self):
		self.energy = 0
		for trail in self.trails:
			self.energy = self.energy + trail.length
		
		self.pheromoneLevel = 1/self.energy
	
	def markTrail(self):
		i = 0
		k = 0
		for trail in self.trails:
			trail.isInBestTrail = True




if __name__ == '__main__':
	import csv
	# tau0 = 1/(nSegments * nearestNeighbor energy approximation)
	cezanne = Cezanne(nSegments=100, nAnts=20, tau0=1, alpha=1, beta=10, phi=0.01, ro=0.01, maxGenerations = 500)
	cezanne.solve(mode='anneal')
	# print(cezanne.solve(mode='acs'))
	# print(cezanne.solve(mode='nn'))
	# print(f"e_acs / e_nn = {cezanne.bestAnt.energy/cezanne.nnSolution['energy']}")
	# print(f"t_acs / t_nn = {cezanne.acsTime/cezanne.nnSolution['time']}")
	exit()

	with open("./visualize/data/segments.csv", mode='w', newline="") as csv_file:
		csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for segment in cezanne.segments:
			csv_writer.writerow([segment.vertices[0].loc[0],segment.vertices[0].loc[1], segment.vertices[1].loc[0], segment.vertices[1].loc[1]])

	with open("./visualize/data/bestTrail.csv", mode='w', newline="") as csv_file:
		csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for trail in cezanne.bestAnt.trails:
			csv_writer.writerow([trail.vertices[0].loc[0],trail.vertices[0].loc[1],trail.vertices[1].loc[0],trail.vertices[1].loc[1]])

	with open("./visualize/data/energyHistory.csv", mode='w',newline="") as csv_file:
		csv_writer = csv.writer(csv_file)
		for val in cezanne.energyHistory:
			csv_writer.writerow([val])