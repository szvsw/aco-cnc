# import numpy as np
from math import sqrt
import random
import time
import logging
from greedy import Greedy
from annealer import Annealer
from antcolonysystem import AntColonySystem
from linesegment import LineSegment
from trail import Trail


	

class Network:
	def __init__(self,nSegments):
		logging.info(f"Setting up network with {nSegments} pairs of connected points.")
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
	
		


if __name__ == '__main__':
	import csv
	logging.basicConfig(level=logging.INFO)
	# tau0 = 1/(nSegments * nearestNeighbor energy approximation)
	network = Network(nSegments=100)
	greedy = Greedy(network)
	annealer = Annealer(network, maxAttempts=2000000,maxIterations=4000000, initialTemp=10,seedSegments=greedy.segments)
	# annealer.solve()
	exit()
	acs = AntColonySystem(network=network, nAnts=20, tau0=1, alpha=1, beta=10, phi=0.01, ro=0.01, maxIterations= 500)
	acs.solve()
	print(f"e_acs / e_nn = {acs.bestAnt.energy/network.nnSolution['energy']}")
	print(f"t_acs / t_nn = {acs.solutionTime/network.nnSolution['time']}")
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