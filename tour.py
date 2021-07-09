import random

class Tour:
	def __init__(self,network,segments=None):
		self.network = network
		if segments == None:
			self.constructRandomTour()
		else:
			self.segments = segments
		self.segmentsToTrails()

	def constructRandomTour(self):
		self.segments = [segment for segment in self.network.segments]
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
	
	
	def reverseSection(self,noWrap=True):
		segments = [segment for segment in self.segments]
		startIndex = int(random.random()*len(segments))
		lengthToReverse = int(random.random()*(len(segments)-startIndex-1))+1 if noWrap else int(random.random()*(len(segments)-1))+1
		elementsToReverse = [segments[(startIndex +i)%len(segments)] for i in range(lengthToReverse)]
		elementsToReverse.reverse()


		for element in elementsToReverse:
			element.polarity = 1 - element.polarity
	
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
	
	def findNeighborSegments(self,all=False):
		actions = [self.invertSegment,self.swapSegments, self.moveSegment, self.reverseSection, self.cutAndPasteSection] if all else [self.reverseSection]
		action = random.choice(actions)
		return action()