# import numpy as np
import random
import time

class Vertex:
	def __init__(self):
		self.loc =  [ random.random()*50,random.random()*50 ] 
		self.partner = None
		self.id = None
		self.trails = {}

	def connect(self, vertex):
		self.partner = vertex
		vertex.partner = self

class LineSegment:
	def __init__(self):
		self.vertices = [Vertex(), Vertex()]
		translation = (random.random()*950,random.random()*950)
		for vertex in self.vertices:
			for i in range(2):
				vertex.loc[i] = vertex.loc[i]+translation[i]
		self.vertices[0].connect(self.vertices[1])
		self.length = pow(pow(self.vertices[0].loc[0]-self.vertices[1].loc[0],2)+ pow(self.vertices[0].loc[1]-self.vertices[1].loc[1],2),0.5)

class Cezanne:
	def __init__(self,nSegments, nAnts, tau0,alpha,beta,phi,ro):
		start = time.perf_counter()*1000
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
				vtx2.trails[vtx1.id] = trail
				self.trails.append(trail)
		
		for i in range(len(self.trails)):
			self.trails[i].id = i
		
		self.bestAnt = None
		self.energyHistory = []

		end = time.perf_counter()*1000
		print(f"Setup took {end-start}ms.")

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
		print(f'Pathfinding took { end-start }ms.')
	
	def evaluateTours(self):
		start = time.perf_counter()*1000
		for ant in self.ants:
			ant.evaluateTour()
			if ant.energy < self.bestAnt.energy:
				self.bestAnt = ant
		end = time.perf_counter()*1000
		print(f'Tour evaluation took { end-start }ms.')
	
	
	def globalUpdatePheromones(self):
		start = time.perf_counter()*1000
		self.bestAnt.markTrail()
		for trail in self.trails:
			trail.depositPheromone(amount=self.bestAnt.pheromoneLevel if trail.isInBestTrail else False, local=False)
			trail.isInBestTrail = False
		end = time.perf_counter()*1000
		print(f'Trail marking took { end-start }ms.')
	
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
		print(f'Generation took { end-start }s.')



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

	
	def selectNextTrail(self):
		# todo - implement pseudo-random proporitonal selection with q0 parameter.
		start = time.perf_counter()*1000
		currentVertex = self.tour[-1]
		availableTrails = [currentVertex.trails[trailID] for trailID in self.unvisited]
		numerators = [pow(currentVertex.trails[trailID].tau,self.cezanne.alpha)*currentVertex.trails[trailID].desirability for trailID in self.unvisited]
		denominator = sum(numerators)
		end = time.perf_counter()*1000
		start = time.perf_counter()*1000
		probabilities = [numerator/denominator for numerator in numerators]
		end = time.perf_counter()*1000
		start = time.perf_counter()*1000
		trail = random.choices(availableTrails,weights=probabilities)[0]
		end = time.perf_counter()*1000
		# print(f'C: { end-start }')
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
	cezanne = Cezanne(nSegments=500, nAnts=10, tau0=(1/(25000*500)), alpha=1, beta=2, phi=0.1, ro=0.1)
	start = time.monotonic()
	maxGenerations = 1000
	for i in range(maxGenerations):
		print(f"Starting generation {i}---")
		cezanne.executeGeneration()
		print(f"Best Energy: { cezanne.bestAnt.energy }")
		if i > 100:
			if cezanne.energyHistory[i] == cezanne.energyHistory[i-50]:
				print("Energy has not decreased for 50 generations, exiting.")
				break
		print("")
	end = time.monotonic()
	print(f"{maxGenerations} generations took {end-start}s.")

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