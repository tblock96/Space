## Team class
'''
Basically just stores everything belonging to the team.
'''
import pygame as pg
import random as rand
import unimath as um
import copy

LOGOS = {"star":[(100,0),(124,80),(200,80),(140,125),(160,200),(100,155),
				(40,200),(60,125),(0,80),(76,80)],
		"trident":0}

class Team():
	
	def __init__(self, u, i, easy):
		self.index = i
		self.u = u
		self.logo = pg.Surface((200,200),pg.SRCALPHA)
		self.logo.fill((0,0,0,0))
		self.getName()
		self.planets = {}
		self.ships = {}
		self.spriteGroup = pg.sprite.Group()
		self.shipGroup = pg.sprite.Group()
		self.usize = self.shipIndex = 0
		self.commsNetwork = []
		self.visible = []
		self.discoveredPlanets = []
		self.actionGroups = []
		self.easy = easy
	
	def update(self, time):
		usize = self.u.size
		self.spriteGroup.update(time, usize)
		self.getCommsNetwork()
		self.captainBroadcast()
	
	def getName(self):
		'''
		# if self.index == 0:
		#	 print "Welcome! What is your team name?"
		#	 self.name = 0
		#	 while self.name == 0:
		#		 try:
		#			 self.name = str(input(''))
		#		 except Exception: print "Not a valid string"
		#	 print "Pick a logo:"
		#	 print LOGOS.keys()
		#	 self.logoName = 0
		#	 while self.logoName not in LOGOS.keys():
		#		 if self.logoName != 0: print "Please pick from the list above."
		#		 try:
		#			 self.logoName = input('')
		#		 except Exception: print "Not a valid string"
		#	 self.color = input("Color:\n")
		#	 self.drawLogo()
		#	 self.logo.convert_alpha()
		#	 self.logo = pg.transform.scale(self.logo, (50,50))
		#	 #TODO put color on all ships
		# else:
		'''
		self.name = "CPU " + str(self.index)
		self.logoName = LOGOS.keys()[rand.randint(0,len(LOGOS.keys())-1)]
		self.color = (rand.randint(0,255),rand.randint(0,255),
			rand.randint(0,255))
	
	def drawLogo(self):
		if self.logoName == "star":
			pg.draw.polygon(self.logo,self.color,LOGOS[self.logoName])
		elif self.logoName == "trident":
			pg.draw.line(self.logo,self.color,(100,0),(100,200),15)
			pg.draw.arc(self.logo,self.color,(52,-40,96,120),3.14159,2*3.14159,15)
		self.logo.convert_alpha()
		self.logo = pg.transform.scale(self.logo, (50,50))
	
	def getHomePlanet(self, planets):
		self.acquirePlanet(planets, self.index, 2000)
		c = self.planets[self.index].cache
		c['material'] = 5000
		c['energy'] = 5000
		c['food'] = 4000
		c['luxury'] = 1000
		self.planets[self.index].buildCapital()
	
	def acquirePlanet(self, planets, index, population = 0):
		planet = planets[index]
		self.planets[planet.index] = planet
		planet.addToTeam(self)
		planet.addPopulation(population)
		self.spriteGroup.add(planet)
	
	def acquireShip(self, ship, location = (0,0), index = -1):
		if index == -1:
			self.ships[self.shipIndex] = ship
			ship.index = self.shipIndex
			self.shipIndex += 1
		else:
			self.ships[index] = ship
			ship.index = index
		ship.location = location
		ship.team = self
		self.spriteGroup.add(ship)
		self.shipGroup.add(ship)
	
	def getCommsNetwork(self):
		if self.easy:
			self.commsNetwork = []
			for s in self.spriteGroup.sprites():
				if s.type != 'bullet': self.commsNetwork.append(s)
		else:
			if self.index == 100:
				return
			self.commsNetwork = []  # final stack
			stack = []  # actually a queue
			stack.append(self.planets[self.index]) # Home network
			while len(stack) > 0:
				s = stack[0]
				if s not in self.commsNetwork:
					stack.extend(self.getComms(s))
					self.commsNetwork.append(s)
				stack = stack[1:]
			for s in self.spriteGroup.sprites():
				if s.type == "bullet": continue
				s.comms = (s in self.commsNetwork)
		self.getTotalVis()
		for g in self.actionGroups:
			g['visible'] = self.getListVis(g['ships'])
	
	def getTotalVis(self, bullets = False): #TODO include enemy bullets
		if self.easy: lis = self.spriteGroup.sprites()
		else: lis = self.commsNetwork
		self.visible = self.getListVis(lis, True) + self.discoveredPlanets
	
	def getListVis(self, lis, bullets = False):
		vis = lis[:]
		for s in lis:
			sVis = self.getVis(s, bullets or self.easy)
			for v in sVis:
				if v not in vis: vis.append(v)
		return vis
			
	def getComms(self, base):
		comms = []
		if base.type == 'bullet': return comms
		sprites = self.spriteGroup.sprites()
		for s in sprites:
			dist = um.get_dist_planets(base, s, self.usize)
			if dist <= max(s.commsLength, base.commsLength):
				comms.append(s)
		return comms
	
	def getVis(self, base, bullets = False):
		'''Return a list of sprites seen by the base sprite'''
		vis = []
		if base.type == 'bullet': return vis
		for t in self.u.teams.values():
			if t == self and not bullets: continue
			for s in t.spriteGroup.sprites():
				if s.type == 'bullet' and not bullets: continue
				dist = um.get_dist_planets(base, s, self.usize)
				if dist <= base.visionLength:
					vis.append(s)
		try:
			for s in self.u.empty.spriteGroup.sprites():
				dist = um.get_dist_planets(base, s, self.usize)
				if dist <= base.visionLength:
					vis.append(s)
		except AttributeError: pass
		return vis
	
	def kill_ship(self, ship):
		self.spriteGroup.remove(ship)
		del self.ships[ship.index]
		if ship in self.commsNetwork: self.commsNetwork.remove(ship)
		self.removeFromAG([ship])
		self.u.send_dead(ship)
	
	def removeFromAG(self, list):
		'''ActionGroup: needs to carry the captain and ships
		special: list of slowest and longest sight, ships: list
		
		Every ship carries appropriate task and target, and captain sends
		live updates to each ship of their new target.'''
		
		redo = []
		for s in list:
			s.actionGroup = {}
			found = False
			for g in self.actionGroups:
				if s in g['ships']:
					if s == g['special'][0]: # slow
						for sh in g['ships']:
							if sh == s: continue
							bT = um.deepcopy(s.baseTarget)
							sh.target = bT
							sh.setBaseTarget(bT)
					g['ships'].remove(s)
					redo.append(g)
					self.actionGroups.remove(g)
					found = True
					break
			if not found:
				for g in redo:
					if s in g['ships']:
						g['ships'].remove(s)
		for g in redo:
			self.makeAG(g['ships'])
	
	def makeAG(self, ships):
		# print "Making AG from:"
		# print ships
		
		#find sight, slow
		if len(ships) == 0: return
		g = {}
		max_vis = 0
		max_score = 0   #score = 1/speed
		captain = 0
		slow = sight = 0
		
		for s in ships:
			if not s.boarded == False:
				ships.remove(s)
				continue
			s.actionGroup = g
			vis = s.visionLength
			score = 1/s.speed
			if score > max_score:
				max_score = score
				slow = s
			if vis > max_vis:
				max_vis = vis
				sight = s
		
		if slow == 0 or sight == 0: return
				
		g['special'] = [slow, sight]
		
		# sort ships by speed
		sorted_ships = []
		for s in ships:
			um.insertBySpeed(s, sorted_ships)
		#sorted_ships now sorted slowest to fastest
		g['ships'] = sorted_ships
		g['visible'] = self.getListVis(g['ships'])
		
		self.actionGroups.append(g)
		for s in ships:
			s.actionGroup = g
		return g
	
	def captainBroadcast(self):
		for g in self.actionGroups:
			slow, sight = g['special']
			if slow.type != 'carrier':
				pass
				'''
				print "Team %d" %self.index
				print slow.target
				print slow.baseTarget
				print slow.currentTask, '\n'
				'''
			same = (slow == sight)
			i = 0
			n = 0
			length = len(g['ships']) - (2-same)
			radius = max(50, 50*length/um.pi)
			theta = um.atan2(slow.velocity[1], slow.velocity[0])
			if slow.currentTask == slow.dock:
				if isinstance(slow.target[0], pg.sprite.Sprite):
					if um.get_dist_planets(slow, slow.target[0], self.usize) < 400:
						for s in g['ships']:
							s.target = slow.target
						return
			if slow.currentTask in [slow.attack, slow.patrol]:
				threats = self.getVis(sight)
				if len(threats) > 0:
					threat_rank = um.get_threat_rank(threats, sight) #strong to weak
					
					if len(threat_rank) > 0:
						sorted_ships = [] # sorted by strength, strongest to weakest
						for s in g['ships']:
							um.insertByStrength(s, sorted_ships)
						if slow.currentTask == slow.attack:
							targ1 = slow.baseTarget[:2]
							for i in range(len(sorted_ships)):
								'''
								# if sorted_ships[i] == slow: continue
								if isinstance(sorted_ships[i].baseTarget[1], (list, tuple)):
									if len(sorted_ships[i].baseTarget[1]) == 1:
										
										print "ERROR IN cptnbrdcst"
										print "%s on team %d at location (%d, %d)" \
											%(sorted_ships[i].type, self.index, sorted_ships[i].location[0],
											sorted_ships[i].location[1])
										print sorted_ships[i].baseTarget
										print "Slow is %s" %slow.type
										print "is slow? %d" %(slow == s)
										print "Slow's task is attack? %d" %(slow.currentTask == slow.attack)
										print slow.baseTarget
										print slow.target, '\n'
										sorted_ships[i].baseTarget[1] = sorted_ships[i].baseTarget[1][0]
										slow.currentTask = slow.patrol
										
									targ1 = sorted_ships[i].baseTarget[1]  
								else:
									targ1 = [sorted_ships[i].baseTarget[0], sorted_ships[i].baseTarget[1]]
										# replace with coordinates to move to after battle
								'''
								sorted_ships[i].target = [threat_rank[i%len(threat_rank)], targ1, self.usize]
						else: # patrol
							for i in range(len(sorted_ships)):
								s = sorted_ships[i]
								if isinstance(slow.baseTarget[0], list):
									targ = [threat_rank[i%len(threat_rank)], [s.baseTarget[0]]+s.baseTarget[1], self.usize]
									s.target = targ
								else:
									targ = [threat_rank[i%len(threat_rank)], s.baseTarget[1], self.usize]
									s.target = targ
					return
			if slow.currentTask in [slow.chain, slow.sweep]:
				buffer = 10
				radius = [0]
				sorted_ships = [] # sorted by comms length (decreasing)
				for s in g['ships']:
					um.insertByCommsLength(s, sorted_ships)
				
				start = slow.baseTarget[0]
				angle = slow.baseTarget[1][0]
				for i in range(len(sorted_ships)):
					if i < (len(sorted_ships))/2.:
						rad = radius[i] + sorted_ships[i].commsLength - buffer
						radius.append(rad+sorted_ships[i].commsLength - buffer)
					if i >= (len(sorted_ships))/2.:
						rad = radius[i - (len(sorted_ships)-1)//2]

					targ = [start[0] + um.cos(angle)*rad,
						start[1] + um.sin(angle)*rad, self.usize]
					sorted_ships[i].target = targ
				max_dist = 0
				for s in g['ships']:
					dist = um.get_dist_points(s.location, s.target[0:2], s.target[2])
					if dist > max_dist: max_dist = dist
				if slow.currentTask == slow.chain:
					if max_dist < buffer and len(slow.taskQueue) > 0:
						slow.completed = True
				if slow.currentTask == slow.sweep:
					if abs(angle-slow.baseTarget[1][1]) < 2*um.pi/180.:
						slow.completed = True
					if max_dist < buffer:
						if (angle-slow.baseTarget[1][1]) % (um.pi*2) > um.pi: #negative
							angle += 2*um.pi/180
						else: angle -= 2*um.pi/180
						slow.baseTarget[1][0] = (angle+um.pi) % (2*um.pi)-um.pi
				return
			if length == 1:
				for s in g['ships']:
					if s in g['special']:
						continue
					angle = -um.pi + theta
					targ = [slow.location[0]+um.cos(angle)*radius,
						slow.location[1]+um.sin(angle)*radius, self.usize]
					s.target = targ
			
			else:
				while n < length:
					try:
						s = g['ships'][i]
					except IndexError:
						print "Index Error cptnbrdcst %d" %i
						print g
					if s in g['special']:
						i += 1
						continue
					angle = (2*(n%2)-1)*um.pi/2.*(1+2.*(n//2)/(length-1))+theta
					targ = [slow.location[0]+um.cos(angle)*radius,
						slow.location[1]+um.sin(angle)*radius, self.usize]
					s.target = targ
					i += 1
					n += 1
			if not same:
				targ = [slow.location[0]+slow.velocity[0]*10,
					slow.location[1]+slow.velocity[1]*10, self.usize]
				sight.target = targ
			slow.target = slow.baseTarget
			
			#TODO other motions (done board, move, unload, dock, jump)
			