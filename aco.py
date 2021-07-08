import numpy as np
import random
import time

class Vertex:
	def __init__(self):
		self.loc = np.array( ( random.random(),random.random() ) )
		self.partner = None
		self.id = None
		self.trails = {}

	def connect(self, vertex):
		self.partner = vertex
		vertex.partner = self

class LineSegment:
	def __init__(self):
		self.vertices = [Vertex(), Vertex()]
		self.vertices[0].connect(self.vertices[1])
		self.length = np.linalg.norm(self.vertices[0].loc-self.vertices[1].loc)

class Cezanne:
	def __init__(self,nSegments, nAnts, tau0,alpha,beta):
		start = time.perf_counter()
		self.tau0 = tau0
		self.alpha = alpha
		self.beta = beta

		self.segments = [LineSegment() for i in range(nSegments)]
		self.vertices = []
		for i in range(nSegments):
			for j in range(2):
				self.vertices.append(self.segments[i].vertices[j])
		
		for i in range(len(self.vertices)):
			self.vertices[i].id = i

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
		
		self.ants = [Ant(i,self) for i in range(nAnts)] 
		end = time.perf_counter()
		print(f"Setup took {end-start}s.")

		start = time.monotonic()
		for i in range(nSegments-1):
			for ant in self.ants:
				nextTrail = ant.selectNextVertex()
				ant.followTrail(nextTrail)

		end = time.perf_counter()
		print(f'Pathfinding took { end-start }s.')

class Trail:
	def __init__(self, vtx1, vtx2, cezanne):
		self.cezanne = cezanne
		self.vertices = [vtx1,vtx2]
		self.id = None
		self.length = np.linalg.norm(self.vertices[0].loc - self.vertices[1].loc)
		self.desirability = pow(1/self.length,self.cezanne.beta) if self.length != 0 else 0
		self.tau = self.cezanne.tau0
		if vtx1 is vtx2:
			self.tau = 0
		if vtx1.partner is vtx2:
			self.tau = 9999999999
	
class Ant:
	def __init__(self, _id, _cezanne):
		self.id = _id
		self.cezanne = _cezanne
		self.reset()

	def reset(self,vertex=None):
		# todo - unvisited should probably be an array of objects not ids...
		self.unvisited = list(range(len(self.cezanne.vertices)))
		if vertex == None:
			self.route = [np.random.choice(self.cezanne.vertices)]
		else:
			self.route = [vertex]
		self.unvisited.remove(self.route[-1].id)

		# Automatically advance the ant to the linked location
		self.route.append(self.route[-1].partner)
		self.unvisited.remove(self.route[-1].id)

	
	def selectNextVertex(self):
		currentVertex = self.route[-1]
		availableTrails = [currentVertex.trails[trailID] for trailID in self.unvisited]
		numerators = [pow(currentVertex.trails[trailID].tau,self.cezanne.alpha)*currentVertex.trails[trailID].desirability for trailID in self.unvisited]
		denominator = np.sum(numerators)
		probabilities = [numerator/denominator for numerator in numerators]
		trail = np.random.choice(availableTrails, p=probabilities)
		return trail
	
	def followTrail(self,trail):
		# Todo: should this protect against selecting a bad trail, i.e. one that does not connect to last location?
		nextVertex = trail.vertices[0] if self.route[-1] is trail.vertices[1] else trail.vertices[1]
		self.route.append(nextVertex)
		self.unvisited.remove(self.route[-1].id)

		# Deposite Pheromones


		# Automatically Advance the route to the next location
		self.route.append(self.route[-1].partner)
		self.unvisited.remove(self.route[-1].id)



if __name__ == '__main__':
	cezanne = Cezanne(nSegments=100, nAnts=100, tau0=1, alpha=1, beta=2)