from os import close
import time
import logging
import random
from math import sqrt

class Greedy:
	def __init__(self,network,closedToOrigin=False):
		#todo : use better termination algorithm rather than sampling a few random vertices
		start = time.perf_counter()
		self.network = network
		self.nnSolutions = {}
		self.nnSolution = None
		verticesToSolve = []
		for i in range(int(sqrt(len(self.network.vertices))+1)):
			vertex = random.choice(self.network.vertices)
			while vertex in verticesToSolve:
				vertex = random.choice(self.network.vertices)
			verticesToSolve.append(vertex)


		for vertex in verticesToSolve:
			#logging.info(f"Determining Solution for Vertex {vertex.id}")
			energy = 0
			trailHistory = []
			unvisited = [i for i in range(len(self.network.vertices))]
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
			if closedToOrigin:
				energy = energy + self.network.origin.trails[vertexHistory[0].id].length + self.network.origin.trails[vertexHistory[-1].id].length
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

		segments = [self.nnSolution['vertexHistory'][i*2].parentSegment for i in range(len(self.nnSolution['trailHistory'])+1)]
		for i in range(len(self.nnSolution['trailHistory'])+1):
			segments[i].polarity = 0 if self.nnSolution['vertexHistory'][i*2].id ==segments[i].vertices[0].id else 1
		self.nnSolution['segments'] = segments

		end = time.perf_counter()
		self.nnSolution['time'] = end-start
		self.segments = self.nnSolution['segments']
		self.energy = self.nnSolution['energy']
		self.trails = self.nnSolution['trailHistory']
		self.vertices = self.nnSolution['vertexHistory']
		logging.info(f'Neareset Neighbor Solution took {end-start}s')
		logging.info(f'Neareset Neighbor Solution has enegy {self.energy}')