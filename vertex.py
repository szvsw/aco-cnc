import random
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
