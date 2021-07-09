# import numpy as np
import random
import time
import logging
from annealer import Annealer
from acs import Ant, AntColonySolver
from linesegment import LineSegment
from trail import Trail


	

class Network:
	def __init__(self,nSegments):
		start = time.perf_counter()*1000

		self.segments = [LineSegment() for i in range(nSegments)]
		self.vertices = []
		for i in range(nSegments):
			for j in range(2):
				self.vertices.append(self.segments[i].vertices[j])
				self.vertices[-1].parentSegment = self.segments[i]
		
		for i in range(len(self.vertices)):
			self.vertices[i].id = i

		self.trails = []
		for vtx1 in self.vertices:
			for vtx2 in self.vertices:
				if vtx2.id in vtx1.trails:
					continue
				trail = Trail(vtx1,vtx2,network=self) 
				vtx1.trails[vtx2.id] = trail
				vtx1.sortedTrails.append(trail)
				vtx2.trails[vtx1.id] = trail
				vtx2.sortedTrails.append(trail)
				self.trails.append(trail)
		
		for vtx in self.vertices:
			vtx.sortTrails()
		
		for i in range(len(self.trails)):
			self.trails[i].id = i
		

		end = time.perf_counter()*1000
		logging.info(f"Graph setup took {end-start}ms.")
	
	def solve(self, mode='acs'):
		if mode == 'anneal':
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
		


if __name__ == '__main__':
	import csv
	logging.basicConfig(level=logging.INFO)
	# tau0 = 1/(nSegments * nearestNeighbor energy approximation)
	network = Network(nSegments=100)
	# network.solve(mode='anneal')
	acs = AntColonySolver(network=network, nAnts=20, tau0=1, alpha=1, beta=10, phi=0.01, ro=0.01, maxIterations= 500)
	acs.solve()
	# print(network.solve(mode='nn'))
	# print(f"e_acs / e_nn = {network.bestAnt.energy/network.nnSolution['energy']}")
	# print(f"t_acs / t_nn = {network.acsTime/network.nnSolution['time']}")
	exit()

	with open("./visualize/data/segments.csv", mode='w', newline="") as csv_file:
		csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for segment in network.segments:
			csv_writer.writerow([segment.vertices[0].loc[0],segment.vertices[0].loc[1], segment.vertices[1].loc[0], segment.vertices[1].loc[1]])

	with open("./visualize/data/bestTrail.csv", mode='w', newline="") as csv_file:
		csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		for trail in network.bestAnt.trails:
			csv_writer.writerow([trail.vertices[0].loc[0],trail.vertices[0].loc[1],trail.vertices[1].loc[0],trail.vertices[1].loc[1]])

	with open("./visualize/data/energyHistory.csv", mode='w',newline="") as csv_file:
		csv_writer = csv.writer(csv_file)
		for val in network.energyHistory:
			csv_writer.writerow([val])