## universe class
'''
A controller for all the planets in the game, as well as the teams, and also
each ship (split up by teams).
'''

VERSION = '0.01'
import pygame as pg
import planet
import unimath as um
import sys
import mouseMeter as mM
import team, ship, socket, json
import threading

client = True
NUM_HUMANS = 1
SIZE = 4
TEAMS = 3

class Universe(pg.sprite.Sprite):
	
	planets = {}
	teams = {}
	sockets = {}
	files = {}
	
	def __init__(self, size, numTeams, easy = 0):
		pg.sprite.Sprite.__init__(self)
		self.size = size * 1000
		numPlanets = int(size**2/3)
		self.encoder = json.JSONEncoder()
		self.decoder = json.JSONDecoder()
		for i in range(numPlanets):		# init planets
			self.planets[i] = planet.Planet(self, i)
		for i in range(numTeams):		# init teams
			self.teams[i] = team.Team(self, i, easy)
			if not client:
				self.teams[i].getHomePlanet(self.planets)
			if i == 0:
				pass # Testing stuff for the human player
		self.empty = team.Team(self, 100, False)	# empty team
		for i in range(numTeams, numPlanets):	# give empty team planets
			self.empty.acquirePlanet(self.planets,i,10)
	
	def receive_loop(self, index):
		while self.receive(index):
			pass

	def receive(self, index):
		line = self.files[index].readline()
		if not line:
			return False
		line = self.decoder.decode(line)
		mt = line['msg type']
		if mt == 'ship':
			self.update_ship(line, index)
		elif mt == 'planet':
			self.update_planet(line, index)
		elif mt == 'building':
			self.update_building(line, index)
		elif mt == 'AG':
			self.update_AG(line, index)
		return True

	def update_building(self, line, index):
		b = self.get_building(line['planet'], line['building'])
		b.askBuild(line['attempt'])
	
	def get_building(self, planet_index, building_index):
		p = self.planets[planet_index]
		for lis in p.buildings.values():
			for b in lis:
				if b.index == building_index:
					return b
		print "Building %d on planet %d not found." %(building_index,
			planet_index)
		for k, lis in p.buildings.items():
			print k
			for b in lis:
				print b.index
		self.quit()

	def update_planet(self, line, index):
		self.planets[line['index']].build(line['attempt'])

	def update_AG(self, line, index):
		t = self.teams[index]
		if line['action'] == 'remove':
			task = t.removeFromAG
		else:
			task = t.makeAG
		sprites = []
		for s in line['sprites']:
			sprites.append(self.get_ship(index, s[0], s[1]))
		task(sprites)
	
	def update_ship(self, line, index):
		type = line['type']
		ship = line['index']
		s = self.get_ship(index, type, ship)
		target = line['target']
		target.append(self.size)
		task = getattr(s, line['task'])
		if line['action'] == 'new':
			s.newTaskQueue(task, target)
		else:
			s.addToTaskQueue(task, target)
		
	def get_ship(self, team_index, type, ship_index):
		t = self.teams[team_index]
		ship = None
		for s in t.shipGroup.sprites():
			if s.index == ship_index:
				return s
		print "ERROR: Attempt to modify ship No. %d," \
			" type %s, on team %d that does not exist." %(ship_index, type, team_index)
		dict = {'msg type': 'dead', 'class': 'ship', 'type': type,
			'ship': ship_index, 'team': team_index}
		for i in range(NUM_HUMANS):
			self.send(dict, i)

	def send_setup(self, conn, index):
		self.sockets[index] = conn
		self.files[index] = conn.makefile()
		dict = {}
		dict['msg type'] = 'setup'
		dict['size'] = self.size
		dict['team'] = index
		dict['numTeams'] = len(self.teams)
		dict['start loc'] = self.planets[index].location
		dict['version'] = VERSION
		self.send(dict, index)
		for t in self.teams.values():
			for s in t.spriteGroup.sprites():
				self.send_sprite(s, index)
		self.send_team(index)
		self.send_ready(index)
	
	def send_team(self, index):
		dict = {'msg type': 'team'}
		t = self.teams[index]
		vis = []
		for s in t.visible:
			vis.append((s.type, s.team.index, s.index))
		dict['visible'] = vis
		self.send(dict, index)
	
	def send_dead(self, s):
		if client: return
		dict = {'msg type': 'dead'}
		if isinstance(s, ship.Ship):
			dict['class'] = 'ship'
			dict['type'] = s.type
			dict['ship'] = s.index
			dict['team'] = s.team.index
		if isinstance(s, ship.Bullet):
			dict['class'] = 'bullet'
			dict['index'] = s.index
		for i in range(NUM_HUMANS):
			self.send(dict, i)

	def send_sprite(self, s, index):
		dict = {'msg type': 'sprite'}
		if isinstance(s, ship.Ship):
			dict['class'] = 'ship'
			dict['location'] = um.umround(s.location,0)
			dict['direction'] = um.umround(s.direction,1)
			dict['comms'] = s.comms
			dict['ship'] = s.index
			dict['type'] = s.type
			dict['team'] = s.team.index
			dict['hp'] = um.umround(s.hp,1)
			dict['visible'] = (s in self.teams[index].visible)
			if not (isinstance(s.target[0], pg.sprite.Sprite) or isinstance(s.baseTarget[0], pg.sprite.Sprite)):
				dict['target'] = s.target
				dict['baseTarget'] = s.baseTarget
		elif isinstance(s, planet.Planet):
			dict['class'] = 'planet'
			dict['location'] = s.location
			dict['government'] = s.government
			dict['population'] = s.population
			dict['resources'] = s.resources
			dict['cache'] = s.cache
			dict['comms'] = s.comms
			dict['team'] = s.team.index
			dict['index'] = s.index
			dict['visible'] = (s in self.teams[index].visible)
			dict['workRemaining'] = s.workRemaining
		elif isinstance(s, ship.Bullet):
			dict['class'] = 'bullet'
			dict['index'] = s.index
			dict['location'] = s.location
			dict['visible'] = (s in self.teams[index].visible)
		elif isinstance(s, planet.Building):
			dict['class'] = 'building'
			dict['type'] = s.__class__.type
			dict['planet'] = s.planet.index
			dict['index'] = s.index
		self.send(dict, index)
	
	def send_ready(self, index):
		dict = {'msg type': 'ready'}
		self.send(dict, index)
		t = threading.Thread(name = 'client '+str(index),target = self.receive_loop, args = [index])
		t.setDaemon(True)
		t.start()
	
	def send_update(self, index):
		dict = {'msg type': 'update', 'time': 1/30.}
		self.send(dict, index)
	
	def send(self, dict, index):
		self.sockets[index].send(self.encoder.encode(dict)+'\n')
		
	def getImage(self, deltat, loop):
		'''
		# time_end = pg.time.get_ticks()
		# print "Time after team loop: %d" %time_end
			
		extra_screens = 0
		width = screen_width * zoom
		height = screen_height * zoom
		if width > self.size - view_x:
			width = self.size - view_x
			extra_screens = 2
		if height > self.size - view_y:
			height = self.size - view_y
			extra_screens += 1
		
		self.image = pg.Surface((screen_width*zoom, screen_height*zoom))
		image = self.total.subsurface(view_x, view_y, width, height)
		self.image.blit(image, (0,0))
		
		if extra_screens >= 2:
			image = self.total.subsurface(0, view_y, 
				screen_width*zoom - width, height)
			self.image.blit(image, (width, 0))
		if extra_screens % 2:
			image = self.total.subsurface(view_x, 0, 
				width, screen_height*zoom - height)
			self.image.blit(image, (0, height))
		if extra_screens == 3:
			image = self.total.subsurface(0,0,
				view_x - (self.size - screen_width*zoom),
				view_y - (self.size - screen_height*zoom))
			self.image.blit(image, (width, height))
		
		for t in self.teams.values():	# blit s.image
			for s in t.spriteGroup:
				x = (s.rect.right - view_x) % self.size - s.rect.width
				y = (s.rect.bottom - view_y) % self.size - s.rect.height
				self.image.blit(s.image, (x,y))
		
		if dragging:	# blit drag bubble
			x = (drag.rect.right - view_x) % self.size - drag.rect.width
			y = (drag.rect.bottom - view_y) % self.size - drag.rect.height
			self.image.blit(drag.image, (x,y))
		
		self.image = pg.transform.scale(self.image, (screen_width, screen_height))
		self.rect = self.image.get_rect()
		self.rect.x = self.rect.y = 0
		# time_end = pg.time.get_ticks()
		# print "Time after subbing image: %d" %time_end
		fog_update_count = 20
		if loop % fog_update_count == 0:	# update fog 
			fog.getImage(self.teams[0].commsNetwork, view_x, view_y, zoom, self.size)
		self.image.blit(fog.image, (0,0))

		# time_end = pg.time.get_ticks()
		# print "Time after blitting fog image: %d" %time_end
		
		self.image.blit(infoMeter.image, (screen_width-infoMeter.rect.width, 0))
		'''
	
	def quit(self):
		sys.exit()

def main(u):
	loopcounter = 0
	total = 0
	time_since_last_update = 0
	clock = pg.time.Clock()
	while 1:		# MAIN LOOP
		deltat = clock.tick()
		total += deltat
				
		time_since_last_update += deltat/1000.
		if time_since_last_update > 1/30.:
			for i in range(NUM_HUMANS):
				spr = u.teams[i].spriteGroup.sprites()
				for s in spr:
					u.send_sprite(s, i)
				for s in u.teams[i].visible:
					if s not in spr: u.send_sprite(s, i)
				for p in u.teams[i].planets.values():
					for lis in p.buildings.values():
						for b in lis:
							u.send_sprite(b, i)
				u.send_team(i)
				u.send_update(i)
			time_since_last_update -= 1/30.
			loopcounter += 1
		
		if loopcounter % 500 == 0:
			for i in range(NUM_HUMANS):
				u.send({'msg type': 'check', 'time': total}, i)
				
		for t in u.teams.values():
			t.update(min(deltat*0.002, 0.4))

def get_connections(u, sock):	
	for i in range(NUM_HUMANS):
		print "Waiting for connection %d of %d" %(i+1, NUM_HUMANS)
		conn, addr = sock.accept()
		print "Team %d is at %s" %(i, addr)
		u.send_setup(conn, i)
	main(u)

def setup():
	pg.init()
	
	# Universe(size, teams)
	easy = input('Comms infinite? (1/0)\n')
	u = Universe(SIZE,TEAMS, easy)
	
	for t in u.teams.values():	# give initial armada
		t.acquireShip(ship.Settler(t, t.planets[t.index]),
			[t.planets.values()[0].location[0]+100,
			t.planets.values()[0].location[1]+100])
		t.acquireShip(ship.Merchant(t, t.planets[t.index]), 
			[t.planets.values()[0].location[0]+100,
			t.planets.values()[0].location[1]])
		t.acquireShip(ship.Carrier(t, t.planets[t.index]),
			[t.planets.values()[0].location[0]+100,
			t.planets.values()[0].location[1]-100])
		t.acquireShip(ship.Battleship(t, t.planets[t.index]),
			[t.planets.values()[0].location[0],
			t.planets.values()[0].location[1]-100])
		if t.index > -1:
			if t.index == 2:
				for _ in range(3):
					t.acquireShip(ship.Battleship(t, t.planets[t.index]),
						[t.planets.values()[0].location[0],
						t.planets.values()[0].location[1]-100])
			t.removeFromAG(t.shipGroup.sprites())
			ag = t.makeAG(t.shipGroup.sprites())
			'''
			for s in ag['ships']:
				s.newTaskQueue(s.patrol, [u.size/2, u.size/2, u.size])
				s.addToTaskQueue(s.patrol, [u.planets[0].location[0], 
					u.planets[0].location[1], u.size])
			'''
		t.update(0)

	sock = socket.socket(socket.AF_INET6)
	sock.bind(('', 50000))
	sock.listen(NUM_HUMANS)
	get_connections(u, sock)
	
if __name__ == "__main__":
	client = False
	SIZE = input("How big (in 1000s) would you like the map to be?\n")
	TEAMS = input("How many teams?\n")
	NUM_HUMANS = input("How many human players?\n")
	setup()