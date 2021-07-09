import random
import time
import logging

class AntColonySystem():
	def __init__(self,network,alpha,beta,tau0,nAnts,ro,phi,maxIterations):
		self.name = 'acs'
		self.network = network
		self.maxIterations=maxIterations
		self.tau0 = tau0
		self.ro = ro
		self.phi = phi
		self.alpha = alpha
		self.beta = beta
		self.nAnts = nAnts
		self.iterations = 0

		for trail in self.network.trails:
			trail.setSolver(self)
		self.startingVertices = [self.network.vertices[int(random.random()*len(self.network.vertices))] for i in range(nAnts)]
		self.bestAnt = None
		self.energyHistory = []

	def createAntPopulation(self, reuseStarts=True):
		self.ants = [Ant(id=i, network=self.network, solver=self, reuseStarts=reuseStarts) for i in range(self.nAnts)] 
		if self.bestAnt == None:
			self.bestAnt = self.ants[0]

	def constructRoutes(self):
		start = time.perf_counter()*1000
		for i in range(len(self.network.segments)-1):
			for ant in self.ants:
				ant.advance()
			for ant in self.ants:
				ant.depositLastTrail() # deposit pheromone on last used trail

		end = time.perf_counter()*1000
		logging.info(f'Pathfinding took { end-start }ms.')

	def evaluateRoutes(self):
		start = time.perf_counter()*1000
		for ant in self.ants:
			ant.evaluateRoute()
			if ant.energy < self.bestAnt.energy:
				self.bestAnt = ant
		end = time.perf_counter()*1000
		logging.info(f'Route evaluation took { end-start }ms.')
	
	def globalUpdatePheromones(self):
		start = time.perf_counter()*1000
		self.bestAnt.markTrail()
		for trail in self.network.trails:
			trail.depositPheromone(amount=self.bestAnt.pheromoneLevel if trail.isInBestRoute else False, local=False)
			trail.isInBestRoute = False
		end = time.perf_counter()*1000
		logging.info(f'Trail marking took { end-start }ms.')

	def executeIteration(self):
		start = time.perf_counter()
		self.createAntPopulation()
		self.constructRoutes()
		self.evaluateRoutes()
		self.globalUpdatePheromones()
		self.energyHistory.append(self.bestAnt.energy)
		self.iterations = self.iterations + 1
		end = time.perf_counter()
		logging.info(f'iteration took { end-start }s.')
	
	def solve(self):
		start = time.perf_counter()
		self.iterations = 0
		for i in range(self.maxIterations):
			logging.info(f"Starting iteration {i}---")
			self.executeIteration()
			logging.info(f"Best Energy: {self.bestAnt.energy }")
			if i > 50:
				if self.energyHistory[i]  > 0.99* self.energyHistory[i-25]:
					logging.info("Energy has not changed significantly for 50 iterations, exiting.")
					break
			logging.info("")
		end = time.perf_counter()
		logging.info(f"{self.iterations} iterations took {end-start}s.")
		self.solutionTime = end-start
		return self.energyHistory[-1]

class Ant:
	def __init__(self, id, network, solver, reuseStarts):
		self.id = id
		self.network = network
		self.solver = solver
		self.trails = []
		self.segments = []
		self.unvisited = []
		self.route = []
		self.reset(vertex=self.solver.startingVertices[self.id] if reuseStarts else None)
		self.energy = 0

	def reset(self,vertex=None):
		# todo - unvisited should probably be an array of objects not ids...
		self.unvisited = list(range(len(self.network.vertices)))
		self.trails = []
		self.segments = []
		if vertex == None:
			self.route = [random.choice(self.network.vertices)]
		else:
			self.route = [vertex]
		self.unvisited.remove(self.route[-1].id)

		# Automatically advance the ant to the linked location
		self.route.append(self.route[-1].partner)
		self.unvisited.remove(self.route[-1].id)
		self.segments.append(self.route[0].parentSegment)
		self.segments[0].polarity = 0 if self.route[0].parentSegment.vertices[0] is self.route[0] else 1

	
	def selectNextTrail(self,useSortedSearch=False):
		# todo - implement pseudo-random proporitonal selection with q0 parameter.
		currentVertex = self.route[-1]
		availableTrails = [currentVertex.trails[vtxID] for vtxID in self.unvisited]
		numerators = [pow(currentVertex.trails[vtxID].tau,self.solver.alpha)*currentVertex.trails[vtxID].desirability for vtxID in self.unvisited]
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
		nextVertex = trail.vertices[0] if self.route[-1] is trail.vertices[1] else trail.vertices[1]
		self.route.append(nextVertex)
		self.unvisited.remove(self.route[-1].id)

		# Automatically Advance the route to the next location
		self.route.append(self.route[-1].partner)
		self.unvisited.remove(self.route[-1].id)

		self.segments.append(self.route[-1].parentSegment)
		
		self.segments[-1].polarity = 0 if self.route[-1].parentSegment.vertices[0] is self.route[0] else 1
		end = time.perf_counter()*1000
	
	def advance(self):
		nextTrail = self.selectNextTrail()
		self.followTrail(nextTrail)
	
	def depositLastTrail(self):
		# Deposite Pheromones
		self.trails[-1].depositPheromone(local=True) # Use local updating which uses tau0 for amount and phi for evap. rate
	
	def evaluateRoute(self):
		self.energy = 0
		for trail in self.trails:
			self.energy = self.energy + trail.length
		
		self.pheromoneLevel = 1/self.energy
	
	def markTrail(self):
		i = 0
		k = 0
		for trail in self.trails:
			trail.isInBestRoute = True