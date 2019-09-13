## Ship class
'''
A class about ships! The only mobile things (other than the camera, so this
might be a lengthy module. So far, will have 4 subclasses: light, med, heavy,
and settler. Will also include non-Empire ships (merchants, police, pirates)
'''

'''
BUGS:
FEATURES:
attacking/conquering planets
'''

import pygame as pg
import unimath as um

class Ship(pg.sprite.Sprite):
	
	def __init__(self, team, home):
		pg.sprite.Sprite.__init__(self)
		# self.type = 0	   # string
		# self.speed = 0	  # pixels per second
		# self.armor = 0	  # damage
		# self.regen = 0	  # armor per second
		# self.hp = 0		  # damage
		# self.power = 0	  # attack damage
		# self.accuracy = 0   # likelihood of hitting the target (/1)
		# self.accel = 0	  # pixels per second per second
		# self.resources = {} # resources dict
		# self.population = 0 # population
		self.direction = 0  # rads
		self.team = team
		self.home = home
		self.base = home
		self.index = 0
		self.rect = 0
		self.control = False
		self.comms = True
		self.completed = True
		self.boarded = False
		self.taskQueue = []
		self.currentTask = 0
		self.target = (0,0,team.usize)
		self.setBaseTarget(self.target)
		# self.commsLength = 0
		# self.visionLength = 0
		self.location = [0,0]
		self.velocity = [0,0]
		self.initImage()
		self.bulletGroup = pg.sprite.Group()
		self.actionGroup = {}
		self.planetsSeen = []
	
	def move(self, targets, time):
		if self.home != 0:
			self.home = 0
		self.mv(targets, time)
		target, usize = (targets[0], targets[1]), targets[2]
		if um.get_dist_points(self.location, target, usize) < 5:
			try:
				slow = self.actionGroup['special'][0]
				if slow == self: raise KeyError
				else: self.completed = (slow.currentTask == slow.stop)
			except KeyError:
				'''
				print "move KeyError"
				print "%s on team %d" %(self.type, self.team.index)
				print self.baseTarget
				print targets
				print self.currentTask, '\n'
				'''
				self.completed = True
		else: self.completed = False
	
	def mv(self, targets, time):
		target = (targets[0], targets[1])
		usize = targets[2]
		try:
			y = (target[1]-self.location[1]+usize/2)%usize - usize/2
			x = (target[0]-self.location[0]+usize/2)%usize - usize/2
		except Exception:
			print "ERROR in moving. target:"
			print target
			print targets
			print self.currentTask
		self.finalDirection = um.atan2(y,x)
		finalVel = [um.cos(self.finalDirection)*self.speed,
			um.sin(self.finalDirection)*self.speed]
		if um.magnitude(self.velocity)**2 / (2.0*self.accel) >= um.magnitude([x,y]):
			finalVel = [0,0] 
		diffVel = [finalVel[0]-self.velocity[0], finalVel[1]-self.velocity[1]]
		if um.magnitude(diffVel) > self.accel:
			self.velocity[0] += diffVel[0]*self.accel*time/(um.magnitude(diffVel))
			self.velocity[1] += diffVel[1]*self.accel*time/(um.magnitude(diffVel))
		else: self.velocity[0], self.velocity[1] = finalVel[0]+0.001, finalVel[1]+0.001

	def update(self, time, usize):
		if self.hp <= 0:
			return self.delete()
		self.location[0] += self.velocity[0]*time
		self.location[1] += self.velocity[1]*time
		self.location[0] = self.location[0] % self.target[2]
		self.location[1] = self.location[1] % self.target[2]
		self.direction = um.atan2(self.velocity[1], self.velocity[0]+0.0001)
		try:
			test1 = (self == self.actionGroup['special'][0])
		except KeyError: test1 = False
		if self.completed:
			self.getNextTask()
			if test1:
				if self.type != 'carrier': pass #print "%s on team %d onto next task." %(self.type, self.team.index)
				for s in self.actionGroup['ships']:
					if len(s.taskQueue) > len(self.taskQueue):
						s.completed = True
		self.currentTask(self.target, time)
		self.regenArmor(time/1.5)
		self.cooldown = min(self.cooldown + time/1.5 * 1000, self.__class__.cooldown)
		self.updateDiscovery()

	def updateDiscovery(self):
		vis = self.team.getVis(self)
		for v in vis:
			if isinstance(v, Ship): continue
			elif v in self.team.discoveredPlanets: continue
			elif v in self.planetsSeen: continue
			else: 
				self.planetsSeen.append(v)
				#print "Ship index %d found planet index %d" %(self.index, v.index)
		if self.comms:
			for p in self.planetsSeen:
				if p in self.team.discoveredPlanets: continue
				else: self.team.discoveredPlanets.append(p)
			self.planetsSeen = []
		
	def regenArmor(self, time):
		if self.armor < self.__class__.armor:
			self.armor += self.regen*time
		if self.armor > self.__class__.armor:
			self.armor = self.__class__.armor
	
	def setBaseTarget(self, target):
		'''
		print "%s on team %d baseTarget changed to" %(self.type, self.team.index)
		print target, '\n'
		'''
		self.baseTarget = target
		
	def jump(self, target, time):
		self.move(target, time)
	
	def attack(self, target, time):
		'''target: x,y,usize or ship, null, usize'''
		if isinstance(target[0], Ship):
			other = target[0]
			self.atk(target, time)
			if other.hp <= 0 or other not in self.team.visible+self.actionGroup['visible']: 
				try:
					self.target = [target[1][0], target[1][1], target[2]]
				except Exception:
					print "ERROR in attack. basetarget:"
					print self.baseTarget
					print "target"
					print target
					self.team.u.quit()
		else:
			targ = self.getTarget(*self.target)
			if targ:
				self.target = [targ, [target[0], target[1]], target[2]]
				self.attack(self.target, time)
			else:
				self.move(target, time)
	
	def atk(self, target, time):
		other = target[0]
		usize = target[2]
		dx, dy = um.get_short_path(self.location, other.location, usize)
		my_dir = um.atan2(self.velocity[1], self.velocity[0])
		other_dir = um.atan2(other.velocity[1], other.velocity[0])
		velocity = um.magnitude(self.velocity)
		theta = um.atan2(dy, dx)
		my_rad = um.magnitude(self.velocity)**2/self.accel # balancing will happen later
		lead = -2*um.cos(my_dir-other_dir) + 1 # 1 if opposite directions, -1 if same
		omega = um.magnitude(self.velocity)/my_rad
		
		center_x = other.location[0]+3*(other.velocity[0]-self.velocity[0])
		center_y = other.location[1]+3*(other.velocity[1]-self.velocity[1])
		
		if abs(my_dir - theta) < 5*um.pi/180: #arctan(0.1) ~ 5 deg
			self.fire()
		self.mv((center_x,
			center_y,
			usize), time)
	
	def settle(self, target, time):
		self.move(target, time)
	
	def chain(self, target, time):  
		if len(self.taskQueue) > 0:
			if self.currentTask == self.chain and self.taskQueue[0][0] == self.chain:
				'''Give a new task queue that sets up a sweep motion, followed by
				the rest of the task queue. Sweeping will move out to the first
				chain angle, then when everyone is at the first angle,
				will sweep out to the second'''
				angles = [self.baseTarget[1][0]] + self.taskQueue[0][1][1]
				lis = [[self.sweep, [self.baseTarget[0],
					angles,
					self.baseTarget[2]]]]
				lis.extend(self.taskQueue)
				self.taskQueue = lis
				self.completed = True
				return
		if isinstance(target[0], list):	 # still not coming from AG
			try:
				targ = [target[0][0] + 1000 * um.cos(target[1][0]),
						target[0][1] + 1000 * um.sin(target[1][0]),
						target[2]]
			except Exception:
				print target
		else: targ = self.target
		if um.get_dist_points(self.location, targ[0:2], targ[2]) < 5:
			self.stop(targ, time)
			self.completed = False
		else:
			self.mv(targ, time)
	
	def sweep(self, target, time):
		self.chain(target, time)
	
	def patrol(self, target, time):
		'''
		if self.type != 'carrier' and self == self.actionGroup['special'][0]: pass
		
			print "Slow %s on team %d is patrolling" %(self.type, self.team.index)
			print target
			print self.baseTarget
		'''
		if isinstance(target[0], list): # has been updated
			'''
			if self.completed and len(self.baseTarget[1]) > 0:
				self.baseTarget[1].append(self.baseTarget[0])
				if len(self.taskQueue) == 0:
					for loc in self.baseTarget[1]:
						self.addToTaskQueue(self.patrol, loc)
				if self.taskQueue[0][0] == self.patrol:
					try:
						self.completed = False
						self.target[0] = self.taskQueue[0][1][0:2]
						self.taskQueue = self.taskQueue[1:]
					except TypeError:
						print "Could not update baseTarget for %s on team %d" %(self.type, self.team.index)
						print self.taskQueue
						self.target[0] = self.taskQueue[0][1][0:2]
			'''
			targ = self.getTarget(target[0][0], target[0][1], target[2])
			if targ:
				self.target = [targ, [target[0]]+target[1], target[2]]
			else:
				self.move([target[0][0], target[0][1], target[2]], time)
		elif isinstance(target[0], Ship):  # currently attacking
			if target[0].hp <= 0 or target[0] not in self.actionGroup['visible']:
				'''
				print "%s on team %d back to patrolling" %(self.type, self.team.index)
				print "is slow? %d" %(self == self.actionGroup['special'][0])
				print target
				print "target[0] team index: %d; hp: %d" %(target[0].team.index, target[0].hp)
				'''
				self.patrol(self.baseTarget, time)
			else:
				self.atk(target, time)
				#if isinstance(target[1][0], (list, tuple)): # as it should be
				#	self.target = [target[1][0], target[1][1:], target[2]]
				# print "basetarget is now"
				# print self.baseTarget
		else: # target = [start_x, start_y, usize]
			self.move(target,time)
			'''
			try:
				self.target = [target[:2], [self.location], target[2]]
			except IndexError:
				print "patrol indexError: target:", target
				print "for %s on team %d" %(self.type, self.team.index)
			
			self.patrol(self.target, time)
			
		if self.type != 'carrier' and self == self.actionGroup['special'][0]:
			print "Completed? %d" %self.completed, '\n'
			'''
	
	def stop(self, target, time):
		if um.magnitude(self.velocity) > .1:
			self.velocity = [self.velocity[0]/1000.0, self.velocity[1]/1000.0]
		self.completed = 1
	
	def retreat(self, target, time):
		if self.comms:
			self.completed = True
		else:
			self.dock([self.base.index, None, target[2]], time)
	
	def dock(self, target, time):
		'''target: x,y,usize or planet_index, None, usize'''
		
		if target[1] == None:
			try:
				targ_planet = self.team.planets[target[0]]
			except KeyError:
				self.currentTask = self.move
				self.baseTarget = [self.team.u.planets[target[0]].location[0],
									self.team.u.planets[target[0]].location[1],
									target[2]]
				return
			usize = target[2]
			if um.get_dist_planets(self, targ_planet, usize) > 65:
				self.move([targ_planet.location[0], targ_planet.location[1], usize], time)
			else:
				self.location = [targ_planet.location[0], targ_planet.location[1]]
				targ_planet.cache['units'].append(self.index)
				self.home = targ_planet
				self.completed = True
		else:
			self.move(target, time)
			for p in self.team.planets.values():
				if um.get_dist_planets(self, p, 100):
					self.target = [p.index, None, target[2]]
					return
			
	def board(self, target, time):
		''' target: [ship to board, null, usize] or x,y,usize'''
		if self.boarded != False:
			self.location[0], self.location[1] = self.boarded.location[0], self.boarded.location[1]
			self.velocity = [0.01, 0.01]
			return
		if target[1] == None:
			targ_ship = target[0]
			usize = target[2]
			if um.get_dist_planets(self, targ_ship, usize) > 20:
				self.move([targ_ship.location[0], targ_ship.location[1], usize],
					time)
			elif len(targ_ship.boarders) < targ_ship.__class__.capacity:
				self.boarded = targ_ship
				targ_ship.boarders.append(self)
				self.team.removeFromAG([self])
		else:
			self.move(target, time)
			targ = self.getCarrier(target[0], target[1], target[2])
			if targ != 0:
				self.target = (targ, None, target[2])
	
	def setCurrentTask(self):
		try:
			task, target = self.taskQueue[0]
		except Exception:
			print "Error extracting task, target from"
			print self.taskQueue[0]
		self.taskQueue = self.taskQueue[1:]
		self.currentTask = task
		self.setBaseTarget(target)
		self.target = target
		self.completed = False
	
	def addToTaskQueue(self, task, target):
		self.taskQueue.append((task,target))
	
	def newTaskQueue(self, task, target):
		if self.boarded == False:
			self.taskQueue = [(task,target)]
			self.completed = True

	def getNextTask(self):
		if len(self.taskQueue) == 0:				
			if self.attitude == "neutral":
				if self.comms:
					self.newTaskQueue(self.stop, [0,0,self.team.usize])
				else:
					self.newTaskQueue(self.move, [self.base.location[0],
						self.base.location[1], self.team.usize])
			elif self.attitude == "aggressive":
				visible = self.team.getVis(self)
				i = 0
				while i < len(visible):
					v = visible[i]
					if not isinstance(v, Ship):
						visible.remove(v)
					else: i += 1
				if len(visible) > 0:
					self.newTaskQueue(self.attack,
					[visible[0], [self.location[0], self.location[1]],
					self.team.usize])
				elif self.comms:
					self.newTaskQueue(self.stop, [0,0,self.team.usize])
				else: self.newTaskQueue(self.retreat, [0,0,self.team.usize])
		elif self.currentTask == self.patrol:
			self.addToTaskQueue(self.patrol, self.baseTarget)
		self.setCurrentTask()
		
	def delete(self):
		print "Killing off %s, no. %d, on team %d" %(self.type, self.index, self.team.index)
		self.team.kill_ship(self)
		if self.type == "carrier":
			for s in self.boarders:
				s.delete()
		self.kill()
		del self
	
	def initImage(self):
		if self.type in ['light', 'merchant', 'settler']:
			self.img = [pg.Surface((20,10)),pg.Surface((20,10)),pg.Surface((20,10)),pg.Surface((20,10))]
			for i in range(4):
				self.img[i].fill((15,0,15))
				self.img[i].set_colorkey((15,0,15))
				pg.draw.ellipse(self.img[i], self.team.color, pg.Rect(0,0,20,10))
				if i % 2 == 1:
					pg.draw.circle(self.img[i], (15,0,15), (10,5),5)
				if i > 1:
					pg.draw.circle(self.img[i], (255,255,255), (10,5), 5,2)
				self.img[i].set_colorkey((15,0,15))
		if self.type in ['battleship', 'carrier']:
			self.img = [pg.Surface((30,10)),pg.Surface((30,10)),pg.Surface((30,10)),pg.Surface((30,10))]
			for i in range(len(self.img)):
				self.img[i].fill(self.team.color)
				self.img[i].set_colorkey((15,0,15))
				if i % 2 == 1:
					pg.draw.circle(self.img[i], (15,0,15), (15,5), 5)
				if i > 1:
					pg.draw.circle(self.img[i], (255,255,255), (15,5), 5,2)
				self.img[i].set_colorkey((15,0,15))
		
	def updateImage(self, view_x, view_y, zoom, usize):
		self.image = self.img[self.control + 2*self.comms].copy()
		if zoom not in [0, 1]:
			self.image = pg.transform.scale(self.image,
				(int((20+10*(self.type in ['carrier', 'battleship']))/zoom),
				int(10/zoom)))
		self.image = pg.transform.rotate(self.image, -self.direction/um.pi*180.0)
		self.getRect()
		self.image = self.image.convert()
	
	def getRect(self):
		if self.rect == 0:
			self.old_rect = self.image.get_rect()
		else:
			self.old_rect = self.rect
		self.rect = self.image.get_rect()
		self.rect.center = self.location
		
	def getTarget(self, mouse_x, mouse_y, usize):
		max_dist = self.team.usize
		target = 0
		for s in self.team.visible:
			if s.team.index == self.team.index: continue
			if s.type in ["planet", "bullet"]: continue
			dist = um.get_dist_points(s.location, (mouse_x, mouse_y), usize)
			if dist < max_dist:
				max_dist = dist
				target = s
		if target == 0:
			visible = self.team.getVis(self)
			i = 0
			while i < len(visible):
				v = visible[i]
				if not isinstance(v, Ship):
					visible.remove(v)
				else:
					target = v
					break
		return target
	
	def getCarrier(self, mouse_x, mouse_y, usize):
		max_dist = self.team.usize
		target = 0
		for s in self.team.visible:
			if s.team.index != self.team.index: continue
			if not s.type == "carrier": continue
			dist = um.get_dist_points(s.location, (mouse_x, mouse_y), usize)
			if dist < max_dist:
				max_dist = dist
				target = s
		return target
		
	def getSpeed(self, speed):
		return speed - 0.5 + um.random.random()
	
	def hurt(self, damage):
		if self.boarded == False:
			if self.armor > damage:
				self.armor -= damage
			else:
				self.hp -= damage - self.armor
				self.armor = 0
	
	def fire(self):
		if self.cooldown == self.__class__.cooldown:
			self.cooldown = 0
			Bullet(self, self.velocity[0], self.velocity[1])
	
	def getPlanet(self, target):
		x, y, usize = target
		min_p = 0
		min_d = 2*usize
		for p in self.team.commsNetwork:
			if isinstance(p, Ship): continue
			d = um.get_dist_points((x,y), p.location, usize)
			if d < min_d:
				min_d = d
				min_p = p
		if min_p != 0:
			return [min_p], 0, usize
		else: return target
			
class Settler(Ship):
	type = "settler"
	armor = 100
	hp = 250
	power = 5
	regen = 0
	accuracy = 0.8
	accel = 2
	population = 1000
	commsLength = 300
	visionLength = 150
	range = 150
	attitude = "neutral"
	cooldown = 1000 # milliseconds
	
	#TODO etc...
	
	
	def __init__(self, team, home):
		Ship.__init__(self, team, home)
		self.speed = self.getSpeed(17) # 1000 pixels per minute
		self.resources = {'energy': 100, 'food': 400, 'material': 200}
	
	def settle(self, target, time):
		'''target: planet_index, None, usize or x,y,usize'''
		if target[1] == None:
			index, _, usize = target
			planet = 0
			for p in self.team.discoveredPlanets:
				if p.index == index:
					planet = p
					break
			if not planet:
				self.completed = 1
				print "Settler told to settle undiscovered planet"
				return
			if um.get_dist_planets(self, planet, usize) > 65:
				self.move([planet.location[0], planet.location[1],
					usize], time)
			else:
				if planet.team.index == 100 and planet in self.team.discoveredPlanets:
					self.team.acquirePlanet([planet], 0, self.population)
					for key, val in self.resources.items():
						planet.cache[key] = val
					print "%s settled planet %d!!!!" %(self.team.name, index)
					self.delete()
				elif planet.team == self.team:
					planet.addPopulation(self.population)
					self.delete()
				else: self.completed = True
		else:
			self.move(target, time)
			if um.get_dist_points(self.location, target[:2], target[2]) < 100:
				min_p = None
				min_d = target[2]
				for p in self.team.visible: # find closest empty planet
					if p.team.index != 100: continue
					if um.get_dist_planets(self, p, target[2]) < min_d:
						min_p = p
				if min_p == None:
					self.completed = True
					print "No empty planets discovered"
				else:
					self.baseTarget = [min_p.index, None, target[2]]
				
class Merchant(Ship):
	type = "merchant"
	armor = 120
	hp = 500
	power = 5
	regen = 10
	accuracy = 0.8
	accel = 2
	population = 1000
	commsLength = 300
	visionLength = 150
	range = 300
	capacity = 500
	attitude = "neutral"
	cooldown = 1000 # milliseconds
	
	def __init__(self, team, home):
		Ship.__init__(self, team, home)
		self.speed = self.getSpeed(15)
		self.resources = {}
	
	def loadResources(self, resDict, planet):
		for key, val in resDict.items():
			try:
				self.resources[key] += val
			except KeyError:
				self.resources[key] = val
			planet.addResources({key: -val})
	
	def unload(self, target, time):
		''' Planet index, None, usize '''
		if target[1] != None:
			planets, index, usize = self.getPlanet(target)
			planet_index = planets[index].index
			self.baseTarget = [planet_index, None, target[2]]
			self.unload(self.baseTarget, time)
			return
		else:
			planet_index, _, usize = target
			planet = self.team.planets[planet_index]
			if um.get_dist_planets(self, planet, usize) > 65:
				self.move([planet.location[0], planet.location[1],
					usize], time)
			else:
				if planet.team == self.team:
					planet.addResources(self.resources)
					for key in self.resources.keys():
						self.resources[key] = 0
					self.completed = True
	
class Light(Ship):
	type = 'light'
	armor = 15
	hp = 100
	power = 20
	regen = 20
	accuracy = 0.8
	accel = 3.0
	population = 150
	commsLength = 300
	visionLength = 500
	range = 500
	attitude = "aggressive"
	cooldown = 1000 # milliseconds
	
	def __init__(self, team, home):
		Ship.__init__(self, team, home)
		self.speed = self.getSpeed(25)
		self.velocity = [0.1,0.1]
		self.resources = {}
	
class Battleship(Ship):
	type = "battleship"
	armor = 100
	hp = 300
	power = 90  # spread between 3 shots
	regen = 15
	accuracy = 0.9
	accel = 1.0
	population = 600
	commsLength = 500
	visionLength = 300
	range = 750
	attitude = "aggressive"
	cooldown = 1000 # milliseconds
	
	def __init__(self, team, home):
		Ship.__init__(self, team, home)
		self.speed = self.getSpeed(10)
		self.velocity = [0.1,0.1]
		self.resources = {}	
	
	def atk(self, target, time):
		''' An algorithm for attacking a different ship. Battleships will fire
		broadsides, attempting to stop when they have a good line.
		target: (othership, location, usize)'''
		other = target[0]
		usize = target[2]
		o_x, o_y = other.location[0], other.location[1]
		dx, dy = um.get_short_path(self.location, other.location, usize)
		if um.hypot(dx, dy) > self.range: self.moveToTarget(target, time)
		else: self.aim(target, time)
	
	def moveToTarget(self, target, time):
		''' target: (othership, location, usize)'''
		other = target[0]
		usize = target[2]
		target_x = other.location[0] + 3*other.velocity[0] - 6*self.velocity[0]
		target_y = other.location[1] + 3*other.velocity[1] - 6*self.velocity[1]
		self.mv((target_x, target_y, usize), time)
	
	def aim(self, target, time):
		other = target[0]
		usize = target[2]
		dx, dy = um.get_short_path(self.location, other.location, usize)
		theta = um.atan2(dy, dx)
		my_dir = um.atan2(self.velocity[1], self.velocity[0])
		if abs(abs(theta-my_dir) % um.pi - um.pi/2) < 2*um.pi/180.: #aimed properly
			if um.magnitude(self.velocity) > 0.1:
				target_x = self.location[0] - self.velocity[0]  # slow down
				target_y = self.location[1] - self.velocity[1]
			self.fire()
		else:	   # we know we're in range, but not aimed properly
			dtheta = (theta-my_dir) % (2*um.pi)
			if dtheta < um.pi/2.: # pointing to the right (left on screen)
				right = True
			elif dtheta < um.pi: # pointing back and right
				right = False
			elif dtheta < 3*um.pi/2.: # pointing back and left
				right = True 
			else:	   # pointing front and left
				right = False
			if right:
				target_x = self.location[0] + self.velocity[1]
				target_y = self.location[1] - self.velocity[0]
			else:
				target_x = self.location[0] - self.velocity[1]
				target_y = self.location[1] + self.velocity[0]
			self.mv((target_x, target_y, usize), time)
	
	def fire(self):
		if self.cooldown == self.__class__.cooldown:
			location = self.location
			for i in range(3):
				self.location[0] = location[0] + (self.velocity[0]*20/ \
					um.magnitude(self.velocity))*(1-i)
				self.location[1] = location[1] + (self.velocity[1]*20/ \
					um.magnitude(self.velocity))*(1-i)
				Bullet(self, self.velocity[1], -self.velocity[0])
				Bullet(self, -self.velocity[1], self.velocity[0])
			self.cooldown = 0
			self.location = location
			
class Carrier(Ship):
	type = "carrier"
	armor = 100
	hp = 50
	power = 10
	regen = 10
	accuracy = 0.75
	accel = 1.0
	population = 1000
	commsLength = 750
	visionLength = 300
	range = 100
	attitude = "neutral"
	cooldown = 1000 # milliseconds
	jumpTime = 2000
	jumpCooldown = 15000
	capacity = 10
	
	def __init__(self, team, home):
		Ship.__init__(self, team, home)
		self.speed = self.getSpeed(7.5)
		self.velocity = [0.1,0.1]
		self.resources = {}	
		self.boarders = []
		
	def update(self, time, usize):
		Ship.update(self, time, usize)
		self.jumpCooldown = max(self.jumpCooldown - time * 1000,
			0)
	
	def board(self, target, time):
		self.mv(target,time)
		
	def unload(self, target, time):
		'''target: targ_x, targ_y, usize'''
		
		dist = um.get_dist_points(self.location, (target[0], target[1]), target[2])
		if dist > 5:
			self.mv(target, time)
		else:
			angle = 0
			while len(self.boarders) > 0:
				boarder = self.boarders[0]
				boarder.completed = True
				boarder.boarded = False
				boarder.location = [self.location[0]+um.cos(angle)*50,
					self.location[1]+um.sin(angle)*50]
				self.boarders = self.boarders[1:]
				angle += 3*um.pi/5.
			self.completed = True
	
	def jump(self, target, time):
		'''target, targ_x, targ_y, usize'''
		if self.jumpCooldown > 0:	   # Must wait 15 secs from last jump
			self.mv(target, time)
			return
		self.jumpTime -= time*1000	  # Cannot charge jump engine until then
		if self.jumpTime > 0:
			self.mv(target, time)
			return
		self.jumpTime = self.__class__.jumpTime
		self.jumpCooldown = self.__class__.jumpCooldown
		inView = False
		for s in self.team.commsNetwork:
			dist = um.get_dist_points(s.location, [target[0], target[1]], target[2])
			if dist < s.commsLength:
				inView = True
				break
		max_radius = 300*(1.25-inView)
		radius = max_radius*um.random.random()
		angle = um.pi*2*um.random.random()
		off_x = radius*um.cos(angle)
		off_y = radius*um.sin(angle)
		self.location = [target[0]+off_x, target[1]+off_y]
		self.completed = True

class Bullet(pg.sprite.Sprite):
	velocity = 0.5 # pixels per millisecond
	commsLength = visionLength = 0
	type = "bullet"
	index = 0
	
	def __init__(self, ship = 0, vx = 0, vy = 0):
		pg.sprite.Sprite.__init__(self)
		self.ship = ship
		if ship:
			self.angle = um.atan2(vy,vx) - (1-ship.accuracy) \
				+ 2 * um.random.random()*(1-ship.accuracy)
			self.vy = um.sin(self.angle) * self.velocity
			self.vx = um.cos(self.angle) * self.velocity
			self.location = [0,0]
			self.team = ship.team
			self.damage = ship.power
			if ship.type == 'battleship':
				self.damage /= 3.
			self.range = ship.range
			self.location[0], self.location[1] = ship.location[0], ship.location[1]
			ship.team.spriteGroup.add(self)
			self.update(0,ship.team.usize)
		self.index = Bullet.index
		Bullet.index += 1
		self.rect = 0
	
	def update(self, time, usize):
		a = self.vy/self.vx
		b = -1.
		c = -self.location[0]*a+self.location[1]
		lis = self.team.visible + self.team.getVis(self.ship)
		min_dist = self.ship.range
		for s in lis:
			if s.team == self.team: continue
			if not isinstance(s, Ship): continue
			dist = abs(a*s.location[0]+b*s.location[1]+c)/um.magnitude([a,b])
			# print "Dist to "
			# print s
			# print dist
			if dist < 10:
				dist = um.get_dist_planets(self,s,usize)
				min_dist = min(dist, min_dist)
				if dist < self.velocity*time*1000:
					self.hit(s)
		if min_dist < self.velocity*time*1000: self.delete()
		self.location[0] = (self.location[0]+self.vx*time*1000.)%self.team.usize
		self.location[1] = (self.location[1]+self.vy*time*1000.)%self.team.usize
		self.range -= self.velocity * time * 1000
		if self.range <= 0:
			return self.delete()
	
	def updateImage(self, view_x, view_y, zoom, usize):
		self.image = pg.Surface((5,5))
		self.image.fill((255,255,255))
		if self.rect == 0:
			self.old_rect = self.image.get_rect()
		else:
			self.old_rect = self.rect
		self.rect = self.image.get_rect()
		self.rect.center = self.location
	
	def hit(self, s):
		s.hurt(self.damage)
	
	def delete(self):
		self.kill()
		if self.ship:
			self.team.u.send_dead(self)
		del self
	
	def hurt(self, damage):
		if damage >= self.damage:
			self.delete()