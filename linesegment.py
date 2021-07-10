from vertex import Vertex

class LineSegment:
	def __init__(self,a=None,b=None):
		self.vertices = [Vertex() if a == None else a, Vertex() if b == None else b]
		# translation = (random.random()*950,random.random()*950)
		# for vertex in self.vertices:
		# 	for i in range(2):
		# 		vertex.loc[i] = vertex.loc[i]+translation[i]
		self.vertices[0].connect(self.vertices[1])
		self.length = pow(pow(self.vertices[0].loc[0]-self.vertices[1].loc[0],2)+ pow(self.vertices[0].loc[1]-self.vertices[1].loc[1],2),0.5)

		self.polarity = None