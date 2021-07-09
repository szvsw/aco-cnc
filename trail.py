
class Trail:
	def __init__(self, vtx1, vtx2, network):
		self.network = network
		self.solver = None
		self.polarity = None
		self.vertices = [vtx1,vtx2]
		self.id = None
		self.length = pow(pow(self.vertices[0].loc[0]-self.vertices[1].loc[0],2)+ pow(self.vertices[0].loc[1]-self.vertices[1].loc[1],2),0.5)
		self.isInBestRoute = False

		
	def depositPheromone(self,amount=0,local=True):
		evaporationRate = self.solver.phi if local else self.solver.ro
		amount = self.solver.tau0 if local else amount
		self.tau = (1-evaporationRate)*self.tau + evaporationRate * amount
	
	def initializePheromoneLevel(self):
		self.tau = self.solver.tau0
		if self.vertices[0] is self.vertices[1]:
			self.tau = 0
		if self.vertices[0].partner is self.vertices[1]:
			self.tau = 9999999999
	
	def initializeDesirability(self):
		self.desirability = pow(1/self.length,self.solver.beta) if self.length != 0 else 0
	
	def setSolver(self,solver):
		self.solver = solver
		if self.solver.name == 'acs':
			self.initializePheromoneLevel()
			self.initializeDesirability()