## planet class
'''
A basic class that dictates the behaviour of planets in general.
Will need to be displayed, so implements pygame.sprite
Will eventually have subclasses that determine behaviour of different
	types of planets.
'''
'''
BUGS:
planets start with -1 buildings
FEATURES:
ui for choosing production of buildings and ships
cost of building a building
'''
#TODO adding a button for production goto START HERE

import pygame as pg
import random as rand
import unimath as um
import ship

STARTING_VISION = 300

class Planet(pg.sprite.Sprite):
	type = "planet"
	
	def __init__(self, universe, index):
		pg.sprite.Sprite.__init__(self)
		self.name = ''
		self.usize = universe.size
		self.index = index
		self.capital = 0
		self.population = 0
		self.resources = {}
		self.cache = {'units':[]}
		self.buildings = {'under construction':[]}
		self.tasks = []
		self.workDivision = 0
		self.isBuilding = False
		self.buildingSelect = 0
		self.workRemaining = 0
		self.government = 0
		self.commsLength = STARTING_VISION
		self.visionLength = STARTING_VISION
		self.trade = {}
		self.hover = 0
		self.rect = 0
		self.comms = 1
		self.MINERATE = 0.5 #rand.random()
		self.docility = rand.randint(1,400000)+0.01
		self.location = [rand.randint(1,universe.size),
			rand.randint(1,universe.size)]
		for p in universe.planets.values():
			d = um.get_dist_planets(self,p,universe.size)
			if d < 1000:
				return self.__init__(universe, index)
		for res in ['energy','material','luxury','food']:
			self.cache[res] = 0
			self.resources[res] = rand.randint(1,100000)
		self.land = rand.randint(5,15)
		self.team = 0
		self.update(0,0)
		
		# button setup
		self.buttons = []
		list = BUILDINGS.keys()
		for i in range(len(list)):
			l = list[i]
			if l == 'under construction': continue
			self.buttons.append(Button(l, [100, 100+50*i], 'new building', l))
		self.on_click = None
		self.on_click_args = None
	
	def build(self, toBuild):
		if self.land < 1: return
		if isinstance(toBuild, basestring):
			self.build(BUILDINGS[toBuild])
		elif issubclass(toBuild, Building):
			self.land -= 1
			self.tasks.append({'build': toBuild, 'work': toBuild.workRequired,
				'energy': toBuild.energy, 'material': toBuild.material})
	
	def finishBuild(self):
		print "Planet %d is done building!" %self.index
		toBuild = self.tasks[0]['build']
		self.buildings['under construction'] = []
		try:
			self.buildings[toBuild.type].append(toBuild(self))
		except KeyError:
			self.buildings[toBuild.type] = [toBuild(self)]
		if toBuild.type == 'production':
			self.buildings['production'][-1].askBuild('stop')
		self.tasks = self.tasks[1:]
		self.isBuilding = False
		self.workDivision -= 1
	
	def buildCapital(self):
		self.build(ProductionBuilding)
		self.capital = 1
	
	def update(self, time, usize): #TODO
		self.updatePopulation(time)
		self.getGovernment()
		self.doWork(time)
	
	def updatePopulation(self, time):
		increase = (1-self.docility / 400000) * self.population * \
			(1 - self.population / (max(0,self.cache['food']) + 1)) * time / 100.
		self.addPopulation(increase)
		self.addResources({'food': - time*self.population * .00025})
		
	def doWork(self, time):
		self.visionLength = self.commsLength = STARTING_VISION
		self.mtrt=self.enrt=self.fdrt=self.lxrt = self.MINERATE
		for key, val in self.buildings.items():
			for b in val:
				b.work(time)
		self.gather(time)
		work = True
		if len(self.tasks) > 0:
			if not self.isBuilding:
				self.workRemaining = self.tasks[0]['work']
				self.isBuilding = True
				self.workDivision += 1
				self.buildings['under construction'] = \
					[UnderConstructionBuilding(self, 
					self.tasks[0]['build'].type)]
				# print self.buildings
			for res in ['energy', 'material']:
				if self.tasks[0][res] > self.cache[res]:
					work = False
			if work:
				rate = self.population*self.government / self.workDivision
				for res in ['energy', 'material']:
					self.tasks[0][res] -= rate*time/self.tasks[0]['work']
				self.workRemaining -= rate*time
			if self.workRemaining < 0:
				self.finishBuild()
	
	def updateImage(self, view_x, view_y, zoom, usize):
		self.backcolor = pg.Color(125*um.dictSum(self.resources)/400000,
			max(125,125*um.log10(1+self.population)/10),125*self.land/15,255)
		self.forecolor = pg.Color(
			0,
			125+int(130*self.government),
			int(min(255,125+130*um.dictSum(self.cache)/25000.)),
			255)
		self.getImage(zoom)
	
	def getImage(self, zoom):
		if zoom == 0:
			self.image = pg.Surface((100,100))
		else:
			self.image = pg.Surface((int(100/zoom), int(100/zoom)))
			self.image.fill((0,0,0))
			pg.draw.circle(self.image,self.backcolor,(int(50/zoom),
				int(50/zoom)),int(40/zoom),0)
			pg.draw.circle(self.image,self.forecolor,(int(50/zoom),
				int(50/zoom)),int(50/zoom),int(10/zoom))
			if self.hover:
				pg.draw.circle(self.image, (255,255,255),
					(int(50/zoom),int(50/zoom)),int(50/zoom),int(5/zoom))
			if self.team != 0:
				self.image.blit(pg.transform.scale(self.team.logo,
					(int(50/zoom), int(50/zoom))),
					(int(25/zoom), int(25/zoom)))
			self.image = self.image.convert()
			self.image.set_colorkey((0,0,0))
		if self.rect == 0:
			self.old_rect = self.image.get_rect()
		else:
			self.old_rect = self.rect
		self.rect = self.image.get_rect()
		self.rect.center = self.location
	
	def getGovernment(self):
		inter = um.dictLength(self.buildings)/um.log10(self.population+2)*\
			(self.docility/um.dictSum(self.resources))**0.5
		inter = inter + (1-inter)/2*self.capital
		self.government = min(1, inter)
	
	def addToTeam(self, team):
		print "Planet %d settled by team %d" %(self.index, team.index)
		self.team = team
		self.team.usize = self.usize
	
	def addPopulation(self, pop):
		self.population += pop

	def addResources(self, resourceDict):
		for key, val in resourceDict.items():
			self.cache[key] += val
	
	def gather(self, time):
		for res,rate in [('material',self.mtrt), ('energy',self.enrt),
			('food',self.fdrt), ('luxury',self.lxrt)]:
			amt = min(self.resources[res], rate*time * self.population / 1000.)
			self.resources[res] -= amt
			self.cache[res] += amt * 0.5 * (self.government + 1)
	
	def drawFocus(self, screen):
		min_d = min(screen[0], screen[1])
		img = pg.Surface(screen)
		pg.draw.circle(img, self.backcolor,(screen[0]/2,screen[1]/2),min_d/4,0)
		pg.draw.circle(img, self.forecolor,(screen[0]/2,screen[1]/2),5*min_d/16, min_d/16)
		count = 0
		mouse = pg.mouse.get_pos()
		self.on_click = self.nothing
		for i in range(len(self.buttons)):
			b = self.buttons[i]
			img.blit(b.image, b.location)
			if b.location[0] <= mouse[0] <= b.location[0]+b.width:
				if b.location[1] <= mouse[1] <= b.location[1]+b.height:
					b.mouse_on()
					self.on_click = b.on_click
					self.on_click_args = b.on_click_args
				else: b.mouse_off()
			else: b.mouse_off()
		for k, lis in self.buildings.items():
			if k == 'under construction' and self.workRemaining <= 0: continue
			for b in lis:
				count += 1
				b.update(screen, count, mouse)
				img.blit(b.image, (b.rect.x, b.rect.y))
		'''
		if self.team != 0:
			logo = pg.transform.scale(self.team.logo, (min_d/5, min_d/5))
			img.blit(logo, (screen[0]/2-min_d/10, screen[1]/2-min_d/10))
		'''
		logo = pg.transform.scale(self.team.logo, (min_d/5, min_d/5))
		img.blit(logo, (screen[0]/2-min_d/10, screen[1]/2-min_d/10))
		return img
	
	def askBuild(self):
		attempt = 0
		list = BUILDINGS.keys()
		'''
		while attempt not in list:
			if attempt != 0:
				print "That is not a valid response"
			print list
			try:
				attempt = input("What would you like to build?\n")
			except Exception: pass
		'''
		return attempt
	
	def nothing(_):
		return None

class Building(pg.sprite.Sprite):
	
	type = 'undefined'	
	energy, material = 1000, 1000
	workRequired = 15000
	index = 0
	
	def __init__(self, planet):
		pg.sprite.Sprite.__init__(self)
		if not pg.font.get_init(): pg.font.init()
		self.font = pg.font.SysFont('arial', 20)
		self.planet = planet
		self.team = planet.team
		self.task = 0
		self.rate = 0
		self.image = 0
		self.rect = 0
		self.index = Building.index
		Building.index += 1
	
	def work(self, time):
		pass
	
	def askBuild(self):
		pass
	
	def getImage(self, min_d, count, mouse):
		selected = 0
		self.image = pg.Surface((min_d/16,min_d/16))
		self.image.fill((255,0,255,0))
		pg.draw.rect(self.image, (125,125,125), (5,5,min_d/16-10,min_d/16-10))
		if abs(mouse[0] - min_d/32.0 - self.rect.x) < min_d/16.0:
			if abs(mouse[1] - min_d/32.0 - self.rect.y) < min_d/16.0:
				pg.draw.rect(self.image, (255,255,255), (0,0,min_d/16,min_d/16), 10)
				selected = 1
		txt = self.type[0]+str(self.index)
		x,y = self.font.size(txt)
		self.image.blit(self.font.render(txt,0,self.team.color),
			(min_d/32.0-x/2.0,min_d/32.0-y/2.0))
		self.image.set_colorkey((255,0,255))
		self.image = pg.transform.rotate(self.image, -90+count/2.0*45.0)
		self.image = self.image.convert_alpha()
		return selected
	
	def update(self, screen, count, mouse):
		min_d = min(screen[0], screen[1])
		if self.image != 0:
			self.rect = self.image.get_rect()
		else: self.rect = pg.Rect(0,0,min_d/16,min_d/16)
		self.rect.center = (screen[0]/2+5*min_d/16.0*um.cos(count*um.pi/8.0),
					screen[1]/2-5*min_d/16.0*um.sin(count*um.pi/8.0))
		if self.getImage(min_d, count, mouse):
			self.planet.buildingSelect = self
		elif self.planet.buildingSelect == self:
			self.planet.buildingSelect = 0

class UnderConstructionBuilding(Building):
	type = 'under construction'
	
	def __init__(self, planet, type = 'under construction'):
		Building.__init__(self, planet)
		Building.index -= 1
		self.index = planet.index
		self.type = type
	
	def getImage(self, min_d, count, mouse):
		selected = 0
		self.image = pg.Surface((min_d/16, min_d/16))
		self.image.fill((255,0,255,0))
		pg.draw.rect(self.image, (125,125,125), (5,5,min_d/16-10,
			(min_d/16-10)*(1- \
			self.planet.workRemaining/BUILDINGS[self.type].workRequired)))
		x,y = self.font.size(self.type[0])
		self.image.blit(self.font.render(self.type[0],0,self.team.color),
			(min_d/32.0-x/2.0,min_d/32.0-y/2.0))
		self.image.set_colorkey((255,0,255))
		self.image = pg.transform.rotate(self.image, -90+count/2.0*45.0)
		self.image = self.image.convert_alpha()
		return selected
		
class ProductionBuilding(Building):
	
	type = 'production'
	
	TASKS = {'light': {'resources':{'material':750, 'energy':750}, 'work':10000},
			'battleship': {'resources':{'material':1750, 'energy':2000}, 'work':30000},
			'carrier': {'resources':{'material':2500, 'energy':1000}, 'work':40000},
			'settler': {'resources':{'material':2500, 'energy':1500}, 'work':30000},
			'merchant': {'resources':{'material':2000, 'energy':600}, 'work':15000},
			'stop': {'resources':{'material':0, 'energy':0}, 'work':9999999}}
	
	energy, material = 1000, 1000
			
	def __init__(self, planet):
		Building.__init__(self,planet)
		self.current_task = 0
		self.workRemaining = 0
		self.task_queue = []
		self.planet.buttons.append(Button('CHOOSE PRODUCTION', [150, len(self.planet.buttons)*50+150], self.askBuild,None)) # START HERE
	
	def work(self, time):
		p = self.planet
		if self.current_task == 0:
			self.get_next_task()
		t = self.current_task
		if t == 0:return
		if self.hasResources():
			rate = p.population * p.government / p.workDivision
			self.workRemaining -= rate * time
			for res, amt in t['resources'].items():
				p.cache[res] -= amt * rate * time / t['work']
				t['resources'][res] -= amt * rate * time / t['work']
			if self.workRemaining <= 0:
				self.planet.workDivision -= 1
				if t['name'] == 'light':
					type = ship.Light
				elif t['name'] == 'battleship':
					type = ship.Battleship
				elif t['name'] == 'carrier':
					type = ship.Carrier
				elif t['name'] == 'settler':
					type = ship.Settler
					p.addPopulation(-1000)
				elif t['name'] == 'merchant':
					type = ship.Merchant
				s = type(self.team, p)
				print "Planet %s has finished building a %s" %(p.index,
					t['name'])
				dir = rand.random()*2*um.pi
				s.newTaskQueue(s.move, [p.location[0]+100*um.cos(dir),
					p.location[1]+100*um.sin(dir), p.usize])
				self.team.acquireShip(s, [p.location[0],
					p.location[1]])
				self.get_next_task()
		else:
			print "Planet %d does not have enough resources to do its work!" \
				%p.index
			self.get_next_task()
	
	def get_next_task(self):
		if len(self.task_queue) > 0:
			attempt = self.task_queue[0]
			self.current_task = {'resources':{}}
			for k, v in self.TASKS[attempt]['resources'].items():
				self.current_task['resources'][k] = v
			self.current_task['work'] = self.TASKS[attempt]['work']
			self.current_task["name"] = attempt
			self.workRemaining = self.current_task['work']
			self.planet.workDivision += 1
			self.task_queue = self.task_queue[1:]
		else: self.current_task = 0
		
	def hasResources(self):
		for res, amt in self.current_task['resources'].items():
			if self.planet.cache[res] < amt: return False
		return True

	def askBuild(self, _):
		num_but = len(self.planet.buttons)
		i = 0
		for k, v in self.TASKS.items():
			string = k+""
			res = v['resources']
			string = string + " m: "+str(res['material']) + " e: " + str(res['energy'])
			string = string + " w: " +str(v['work'])
			self.planet.buttons.append(Button(string, [300,100+50*i], 'new production', [self.index, k]))
			i += 1
		self.planet.buttons.append(Button('DONE', [300, 150+50*i], self.stop_ask_build, [num_but,i+1]))
	
	def stop_ask_build(self, args):
		self.planet.buttons = self.planet.buttons[0:args[0]]+self.planet.buttons[args[0]+args[1]:]
	
	def new_task(self, key):
		self.task_queue.append(key)

class GovernmentBuilding(ProductionBuilding):
	type = 'government'
	TASKS = {'light': {'resources':{'material':100, 'energy':150}, 'work':500},
			'merchant': {'resources':{'material':500, 'energy':300}, 'work':800},
			'stop': {'resources':{'material':0, 'energy':0}, 'work':9999999}}
	
	def __init__(self, planet):
		ProductionBuilding.__init__(self,planet)
		self.lastBuild = 0
		
	def findBuild(self):
		self.aidTarget = []
		attempt = 'stop'
		if self.lastBuild == 0:
			attempt = 'merchant'
			self.findAidTarget()
			if self.aidTarget == self.planet: attempt = 'stop'
		self.askBuild(attempt)
		self.lastBuild = attempt
	
	def findAidTarget(self):
		self.aidTarget = self.planet
		if self.planet.comms:
			minSum = 4000000
			for p in self.planet.team.planets.values():
				if p != self.planet and p.comms:
					pSum = um.dictSum(p.cache)
					if pSum < minSum:
						minSum = pSum
						self.aidTarget = p
	
	def work(self, time):
		rate = self.planet.population * self.planet.government
		if not (self.task and self.currently):
			self.findBuild()
		if self.hasResources():
			self.workRemaining -= rate * time
			for res, amt in self.task['resources'].items():
				self.planet.cache[res] -= amt * rate * time / self.task['work']
				self.task['resources'][res] -= amt * rate * time / self.task['work']
			if self.workRemaining <= 0 and self.task['name'] != 'stop':
				if self.task['name'] == 'light':
					type = ship.Light
				elif self.task['name'] == 'merchant':
					type = ship.Merchant
				s = type(self.team, self.planet)
				self.planet.cache['units'].append(s.index)
				self.team.acquireShip(s, [self.planet.location[0],
					self.planet.location[1]])
				print "Planet %s has finished building a %s" %(self.planet.name,
					self.task['name'])
				self.findBuild()
		else:
			print "Planet %s does not have enough resources to do its work!" \
				%self.planet.name
			self.task = self.currently = 0
		indices = []
		# print self.planet.cache['units']
		for index in self.planet.cache['units']:
			try:
				if isinstance(self.team.ships[index], ship.Merchant):
					indices.append(index)
			except Exception: pass
		if len(indices):
			# print self.planet.cache['units']
			self.sendAid(indices)
	
	def sendAid(self, indices):
		self.findAidTarget()
		other = self.aidTarget.cache
		total_diff = 0
		diff = {}
		for k,v in self.planet.cache.items():
			if k == "units": continue
			diff_s = max(0, v-other[k])
			total_diff += diff_s
			diff[k] = diff_s
		for index in indices:
			s = self.team.ships[index]
			task, target = s.unload, (self.aidTarget.location[0],
				self.aidTarget.location[1], self.planet.usize)
			if other['food'] < self.aidTarget.population:
				food_load = min(s.capacity,
					self.planet.cache['food']-self.planet.population)
				total_diff -= food_load
				try:
					diff['food'] -= food_load
				except KeyError: pass
				s.loadResources({'food':food_load}, self.planet)
			elif total_diff <= 0:
				dir = um.random.random()*2*um.pi
				task = s.move
				target = (s.location[0]+300*um.cos(dir),
					s.location[1]+300*um.sin(dir),
					target[2])	  # Wait and then come back in a bit
			elif total_diff < s.capacity and total_diff > 0:
				s.loadResources(diff, self.planet)
				total_diff = 0
				diff = {}
			elif total_diff > 0:
				load = {}
				for k,v in diff.items():
					load[k] = v/total_diff*s.capacity
					diff[k] -= load[k]
				total_diff -= um.dictSum(load)
				s.loadResources(load, self.planet)
				
			s.newTaskQueue(task, target)
			s.addToTaskQueue(s.dock, (self.planet.index, None, self.planet.usize))
			self.planet.cache['units'].remove(s.index)

class CommsBuilding(Building):
	
	type = 'comms'
	
	def work(self, time):
		self.planet.commsLength *= 2

class VisionBuilding(Building):
	
	type = 'vision'
	
	def work(self, time):
		self.planet.visionLength *= 1.5

class EnergyBuilding(Building):
	
	type = 'energy'
	
	def work(self, time):
		self.planet.enrt += 0.1
		
class MiningBuilding(Building):
	
	type = 'material'
	
	def work(self, time):
		self.planet.mtrt += 0.1
	
class FarmingBuilding(Building):
	
	type = 'farming'
	
	def work(self, time):
		self.planet.fdrt += 0.1

class LuxuryBuilding(Building):
	
	type = 'luxury'
	
	def work(self, time):
		self.planet.lxrt += 0.1

class Button(pg.sprite.Sprite):
	BORDER_SIZE = 5
	TEXT_COLOR = (255,255,255)
	BACK_COLOR = (180,150,25)	# mustard yellow
	
	def __init__(self, text, location, on_click, on_click_args):
		self.text = text
		self.location = location
		self.on_click = on_click
		self.on_click_args = on_click_args
		self.font = pg.font.SysFont('arial', 14)
		self.image = self.get_image()
		self.width = self.image.get_width()
		self.height = self.image.get_height()
	
	def get_image(self):
		x,y = self.font.size(self.text)
		img = pg.Surface((x+2*self.BORDER_SIZE, y+2*self.BORDER_SIZE))
		img.fill(self.BACK_COLOR)
		txt = self.font.render(self.text, True, self.TEXT_COLOR, self.BACK_COLOR)
		img.blit(txt, (self.BORDER_SIZE, self.BORDER_SIZE))
		return img
	
	def mouse_off(self):
		pg.draw.rect(self.image, self.BACK_COLOR, [0,0,self.width-1,self.height-1],self.BORDER_SIZE/2)
	
	def mouse_on(self):
		pg.draw.rect(self.image, self.TEXT_COLOR, [0,0,self.width-1,self.height-1],self.BORDER_SIZE/2)

BUILDINGS = {'production': ProductionBuilding, 'farming': FarmingBuilding,
	'material': MiningBuilding, 'comms': CommsBuilding,
	'government': GovernmentBuilding, 'vision': VisionBuilding,
	'energy': EnergyBuilding, 'under construction': UnderConstructionBuilding}