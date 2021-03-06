## HumanView (Client?)
'''
This is the main view of the human. It takes as input
their team, the universe main image (white grid), and
any other planets that the team has discovered
'''

'''
FEATURES:
Time scaling (1 player) and suggestions (2 player)
Showing where the user has explored
	^ is done for easy mode -- keeping track for when the ship is out of comms will be more complicated
	^ could also implement fog with the lines to blit less area
minimap
loss of comms boots ship from controlGroup
BUGS:

'''

VERSION = '0.03'

LINE_SPACING = 500
FOG_SPACING = 125
BACKGROUND = (15,0,45)
FOG_COLOR = (0,0,0)

import pygame as pg
from pygame.locals import *
import mouseMeter as mM
import unimath as um
import socket, json, sys
import planet, ship, team, universe
import threading, profile, pstats

types = {'settler': ship.Settler, 'merchant': ship.Merchant,
	'light': ship.Light, 'battleship': ship.Battleship,
	'carrier': ship.Carrier, 'planet': planet.Planet,
	'bullet': ship.Bullet}

class HumanView():
	zoom = 1
	dragging = False
	start_x = start_y = 0
	timescale = 1
	planetFocus = 0
	loop = 0
	total = 0
	keysDown = []
	locktime = False
	teamsDiscovered = []
	planetsDiscovered = []
	bullets = {}
	perma_fog = []
	msg = ''

	def __init__(self, host, port, screen_size):
		self.isReady = False
		pg.init()
		self.sock = socket.socket(socket.AF_INET6)
		self.sock.connect((host, port,0,0))
		print self.sock.getsockname()
		self.f = self.sock.makefile()
		self.decoder = json.JSONDecoder()
		
		self.objectGroup = pg.sprite.Group()
		self.controlGroup = pg.sprite.Group()
		self.mouseMeterGroup = pg.sprite.Group()
		self.controlGroup = pg.sprite.Group()
		
		pg.display.init()
		self.screen_width, self.screen_height = screen_size
		self.MOVE_MARGIN = min(screen_size) /10.
		self.screen = pg.display.set_mode(screen_size)
		
		self.drag = mM.dragBubble((self.objectGroup))
		self.infoMeter = mM.InfoMeter((self.objectGroup))
		self.meter = mM.mouseMeter((self.objectGroup, self.mouseMeterGroup))
		self.fog = mM.Fog(self.screen_width, self.screen_height, (self.objectGroup))
		self.message = mM.Message(self.screen_width, self.screen_height, (self.objectGroup))
		self.msgs = []
		
		self.coverSurf = pg.Surface((self.meter.rect.w, self.meter.rect.h))
		self.coverSurf.fill(BACKGROUND)
		
		self.frames = 0
		self.clock = pg.time.Clock()

	def setup(self, line):
		print "Begin setup"
		if line['version'] != VERSION:
			print "Wrong version! Update to " + line['version']
			print "Game may not work as expected!\n\n\n\n\n"
		self.team_index = line['team']
		size = line['size']
		numTeams = line['numTeams']
		self.u = universe.Universe(size/1000, numTeams)
		self.t = self.u.teams[self.team_index]
		self.start_perma_fog(size)
		print "End setup"
	
	def start_perma_fog(self, size):
		num = size / FOG_SPACING
		for i in range(num):
			self.perma_fog.append([1]*num)

	def update_perma_fog(self, comms):
		num = len(self.perma_fog)
		for s in comms:
			radius = int(s.visionLength/FOG_SPACING)
			x,y = int(s.location[0]/FOG_SPACING), int(s.location[1]/FOG_SPACING)
			for i in range(0,radius+1):
				for j in range(0,int((radius**2-i**2)**0.5)+1):
					self.perma_fog[(x+i)%num][(y+j)%num] = self.perma_fog[(x+i)%num][(y+j)%num] * 0.5
					self.perma_fog[(x-i)%num][(y+j)%num] = self.perma_fog[(x-i)%num][(y+j)%num] * 0.5
					self.perma_fog[(x+i)%num][(y-j)%num] = self.perma_fog[(x+i)%num][(y-j)%num] * 0.5
					self.perma_fog[(x-i)%num][(y-j)%num] = self.perma_fog[(x-i)%num][(y-j)%num] * 0.5

	def ready(self):
		self.view_x = self.u.planets[self.team_index].location[0] - self.screen_width/2
		self.view_y = self.u.planets[self.team_index].location[1] - self.screen_height/2
		self.update_commsNetwork()
		self.getFogBase()
		self.updateFog()
		for t in self.u.teams.values():
			for s in t.spriteGroup.sprites():
				s.updateImage(0,0,0,0)
		self.drag.getImage([0,0],[0,0],[0,0],True,0,1)
		self.isReady = True
		
	def update_sprite(self, line):
		type = line['class']
		if type == 'ship':
			self.update_ship(line)
		elif type == 'planet':
			self.update_planet(line)
		elif type == 'bullet':
			self.update_bullet(line)
		elif type == 'building':
			self.update_building(line)
	
	def update_building(self, line):
		b = self.get_building(line)
		if line['type'] == 'production':
			b.update_task_queue(line['task_queue'])
	
	def get_building(self, line):
		planet_index = line['planet']
		p = self.u.planets[planet_index]
		try:
			for b in p.buildings[line['type']]:
				if b.index == line['index']:
					return b
		except KeyError: pass
		print "Making new building of type %s, index %d" %(line['type'], line['index'])
		b = planet.BUILDINGS[line['type']](p)
		try:
			p.buildings[line['type']].append(b)
		except KeyError:
			p.buildings[line['type']] = [b]
		b.index = line['index']
		return b
		
	def update_bullet(self, line):
		index = line['index']
		b = self.get_bullet(index)
		for k, v in line.items():
			if k in ['class', 'msg type', 'index']: continue
			setattr(b, k, v)

	def get_bullet(self, index):
		b = None
		try:
			b = self.bullets[index]
		except KeyError:
			self.bullets[index] = types['bullet']()
			b = self.bullets[index]
			b.index = index
		return b		
		
	def update_planet(self, line):
		index = line['index']
		team_index = line['team']
		p = self.get_planet(index, team_index)
		for k, v in line.items():
			if k in ['class', 'msg type', 'index', 'team']: continue
			setattr(p, k, v)
		
	def get_planet(self, index, team_index):
		p = self.u.planets[index]
		if p.team != 0:
			if p.team.index == team_index:
				return p
		t = self.u.teams[team_index]
		t.acquirePlanet(self.u.planets, index)
		return p

	def update_ship(self, line):
		team_index = line['team']
		ship_index = line['ship']
		s = self.get_ship(team_index, line['type'], ship_index)
		for k, v in line.items():
			if k in ['class', 'msg type', 'team', 'ship', 'type']: continue
			setattr(s, k, v)

	def get_ship(self, team_index, type, ship_index):
		t = self.u.teams[team_index]
		ship = None
		try: ship = t.ships[ship_index]
		except: pass
		if ship == None:
			ship = types[type](t, 0)	# make new ship
			t.acquireShip(ship, (0,0), ship_index)
		if ship.type != type: print "Ship types don't match: index %d, type %s, ship type %s" %(ship_index, type, ship.type)
		return ship
	
	def kill_sprite(self, line):
		type = line['class']
		if type == 'ship':
			team_index = line['team']
			ship_index = line['ship']
			s = self.get_ship(team_index, line['type'], ship_index)
		elif type == 'bullet':
			index = line['index']
			s = self.get_bullet(index)
		s.delete()
			
	def update_team(self, line):
		t = self.t
		t.visible = []
		vis = line['visible']
		for type, team_index, i in vis:
			s = None
			if type == 'planet':
				s = self.u.planets[i]
			else:
				team = self.u.teams[team_index]
				if type == 'bullet':
					s = self.bullets[i]
				else:
					s = self.get_ship(team_index, type, i)
			t.visible.append(s)
		self.update_commsNetwork()
	
	def update_commsNetwork(self):
		self.t.commsNetwork = []
		for s in self.t.spriteGroup.sprites():
			if hasattr(s, 'comms'):
				if s.comms:
					self.t.commsNetwork.append(s)
	
	def receive_loop(self):
		file = open('download.txt', 'w')
		while self.receive(file):
			pass
	
	def receive(self, file):
		line = self.f.readline()
		file.write(line)
		if not line:
			return False
		line = self.decoder.decode(line)
		mt = line['msg type']
		if mt == 'setup':
			self.setup(line)
		elif mt == 'sprite':
			self.update_sprite(line)
		elif mt == 'universe':
			self.update_universe(line)
		elif mt == 'team':
			self.update_team(line)
		elif mt == 'ready':
			self.ready()
		elif mt == 'dead':
			self.kill_sprite(line)
		elif mt == 'check':
			pass #print "Lag: %d" %(line['time'] - self.total)
		return True

	def send_msg(self, file):
		self.sock.send(self.msg)
		file.write(self.msg)
		self.msg = ''
	
	def add_to_msg(self, dict):
		self.msg += json.dumps(dict)+'\n'
	
	def remove_from_AG(self, sprites):
		dict = {'msg type': 'AG', 'action': 'remove'}
		spr = []
		for s in sprites:
			# type, index
			spr.append([s.type, s.index])
		dict['sprites'] = spr
		self.add_to_msg(dict)
	
	def make_AG(self, sprites):
		dict = {'msg type': 'AG', 'action': 'make'}
		spr = []
		for s in sprites:
			spr.append([s.type, s.index])
		dict['sprites'] = spr
		self.add_to_msg(dict)
	
	def addToTaskQueue(self, task, target, ship):
		dict = self.get_task_dict(task, target, ship)
		dict['action'] = 'add'
		self.add_to_msg(dict)
	
	def newTaskQueue(self, task, target, ship):
		dict = self.get_task_dict(task, target, ship)
		dict['action'] = 'new'
		self.add_to_msg(dict)
		
	def get_task_dict(self, task, target, ship):
		dict = {'msg type': 'ship',
			'type': ship.type, 'index': ship.index,
			'task': task, 'target': target}
		return dict
	
	def new_building(self, attempt):
		dict = {'msg type': 'planet', 'index': self.planetFocus.index,
			'attempt': attempt}
		self.add_to_msg(dict)
	
	def update(self, file):
		fogReady = threading.Event()
		t = threading.Thread(name = 'fog', target = self.updateFogLoop, args = [fogReady])
		t.setDaemon(True)
		t.start()
		fog_update_count = 10
		self.total = 0
		self.frames = 1
		usize = self.u.size
		self.image = pg.Surface((self.screen_width, self.screen_height))
		self.image.fill(BACKGROUND)
		self.screen.blit(self.image, (0,0))
		drawn = []
		
		while len(self.t.shipGroup) > 0:
			deltat = self.clock.tick()
			self.total += deltat
			
			vis = self.t.visible[:]
			comms = self.t.commsNetwork[:]
			move_x = move_y = 0
			old_zoom = self.zoom
			old_view_x = self.view_x
			old_view_y = self.view_y
			
			## Control
			mouse_x, mouse_y = pg.mouse.get_pos()
			hoverPlanet = 0
			if pg.mouse.get_focused():
				if not self.planetFocus:		# only move view if not focused on planet
					for mouse,view,screen_dim,i in ((mouse_x,self.view_x,self.screen_width,False),
						(mouse_y,self.view_y,self.screen_height,True)):
						move = 0
						if mouse < self.MOVE_MARGIN:
							m = int(10*um.log10(self.MOVE_MARGIN - mouse)) \
								* self.zoom * deltat / 50.
							move -= m
							view -= m
						if mouse > screen_dim - self.MOVE_MARGIN:
							m = int(10*um.log10(screen_dim - self.MOVE_MARGIN + mouse)) \
								* self.zoom * deltat / 50.
							move += m
							view += m
						if not i:
							self.view_x = view
							move_x = move
						else:
							self.view_y = view
							move_y = move
				
				for p in vis:
					if p.type != 'planet': continue
					if p.rect == 0: continue
					p.hover = 0
					if abs((mouse_x*self.zoom + self.view_x) % usize - p.location[0]) < 55:
						if abs((mouse_y*self.zoom + self.view_y) % usize - p.location[1]) < 55:
							p.hover = 1
							hoverPlanet = p
			
			for s in self.controlGroup.sprites():
				s.control = False
			 
			for e in pg.event.get():
				if e.type == QUIT: sys.exit()
				
				if e.type == KEYDOWN:
					self.keysDown.append(e.key)
				elif e.type == KEYUP:
					try:
						self.keysDown.remove(e.key)
					except ValueError: pass
					
				elif e.type == MOUSEBUTTONDOWN:
				
					self.start_x, self.start_y = ((mouse_x*self.zoom + self.view_x) % usize, \
						(mouse_y*self.zoom + self.view_y) % usize)
						
					ZOOM_STEP = 0.05
					if e.button == 4:
						# zoom in
						self.zoom -= ZOOM_STEP
					elif e.button == 5:
						# zoom out
						self.zoom += ZOOM_STEP
						
					elif e.button == 1:
						if hoverPlanet:
							self.planetFocus = hoverPlanet
							self.back = 0
							self.old_view = self.view_x, self.view_y
						elif self.planetFocus:
							on_click = self.planetFocus.on_click
							on_click_args = self.planetFocus.on_click_args
							'''
								attempt = self.planetFocus.buildingSelect.askBuild()
							'''
							if on_click == 'new building':
								self.new_building(on_click_args)
							elif on_click == 'new production':
								dict = {'msg type': 'building',
									'planet': self.planetFocus.index,
									'building': on_click_args[0],
									'attempt': on_click_args[1]}
								self.add_to_msg(dict)
								self.planetFocus.buildings['production'][0].new_task(on_click_args[1])
							else:
								on_click(on_click_args)
							'''
							elif on_click != None:
								dict = {'msg type': 'building',
									'planet': self.planetFocus.index,
									'building': self.planetFocus.buildingSelect.index,
									'attempt': attempt}
								self.add_to_msg(dict)
							'''
						else:
							self.dragging = True
							
					elif e.button == 3:
						if len(self.controlGroup.sprites()) > 0:
							start = [self.start_x, self.start_y]
							self.remove_from_AG(self.controlGroup.sprites())
							if K_b in self.keysDown:
								for s in self.controlGroup.sprites():
									self.make_AG([s])
							else:
								self.make_AG(self.controlGroup.sprites())
							for s in self.controlGroup.sprites():
								try:
									if K_s in self.keysDown:
										if hoverPlanet:
											task = 'settle'
											target = [hoverPlanet.index, None]
										else: raise Exception
									elif K_u in self.keysDown:
										task = 'unload'
										if hoverPlanet and s.type == 'merchant':
											target = hoverPlanet.location
										elif s.type == 'carrier':
											target = start
										else: raise Exception
									elif K_a in self.keysDown:
										task = 'attack'
										target = start
									elif K_b in self.keysDown:
										task = 'board'
										target = start
									elif K_j in self.keysDown:
										task = 'jump'
										target = start
									elif K_c in self.keysDown:
										task = 'chain'
										centre = um.getCentre(self.controlGroup.sprites(), usize)
										path = um.get_short_path(centre, [self.start_x, self.start_y], usize)
										target = [centre, [um.atan2(path[1], path[0])]]
									elif K_z in self.keysDown:
										task = 'patrol'
										target = start
										#TODO
									else:
										if hoverPlanet:
											task = 'dock'
											target = [hoverPlanet.index, None]
										else: raise Exception
								except Exception:
									task = 'move'
									target = start
								if K_LSHIFT in self.keysDown or K_RSHIFT in self.keysDown:
									self.addToTaskQueue(task, target, s)
								else:
									self.newTaskQueue(task, target, s)
					
					self.view_x = self.view_x + mouse_x * (old_zoom - self.zoom)
					
					self.view_y = self.view_y + mouse_y * (old_zoom - self.zoom)
					
				elif e.type == MOUSEBUTTONUP:
				
					if e.button == 1:
						if self.dragging:
							group = self.t.commsNetwork
							try:
								collide = pg.sprite.spritecollide(self.drag,
									group,0)
								for c in collide:
									if isinstance(c, planet.Planet): collide.remove(c)
							except Exception:
								print group
								print group[0]
								print group[0].rect
							for extraRect in [self.drag.xrect, self.drag.yrect, self.drag.xyrect]:
								indices = extraRect.collidelistall(group)
								for i in indices:
									collide.append(group[i])
							for s in self.controlGroup.sprites():
								if not s in collide:
									s.control = False
									self.controlGroup.remove(s)
							self.controlGroup.add(collide)
							self.dragging = False
				
				#else: print e.type
			for s in self.controlGroup.sprites():
				s.control = True
			
			if K_LSHIFT in self.keysDown:
				shift = True
			else: shift = False
			if K_LCTRL in self.keysDown:
				ctrl = True
			else: ctrl = False
			
			m = 0.3 * self.zoom * deltat
			for k in self.keysDown:
				
				if k == K_UP:
					move_y -= m
					self.view_y -= m
				elif k == K_DOWN:
					move_y += m
					self.view_y += m
				elif k == K_LEFT:
					move_x -= m
					self.view_x -= m
				elif k == K_RIGHT:
					move_x += m
					self.view_x += m
				elif k == 270: #NumPad Plus
					self.zoom -= 0.5
					self.keysDown.remove(k)
				elif k == 269: #NumPad Minus
					self.zoom += 0.5
					self.back = 1
					self.keysDown.remove(k)
				elif k == 268: #NumPad Times
					self.timescale += .2
					self.keysDown.remove(k)
				elif k == 267: #NumPad Divide
					self.timescale -= .2
					self.keysDown.remove(k)
				elif k == K_b:
					if self.planetFocus:
						attempt = self.planetFocus.askBuild()
						#self.new_building(attempt)
				elif k == K_ESCAPE:
					for s in controlGroup.sprites():
						s.control = False
					self.controlGroup.empty()
				elif k == K_p:
					timescale = 0
					self.keysDown.remove(k)
				elif k == K_l:
					if self.locktime:
						self.locktime = 0
					else: self.locktime = self.timescale
					self.keysDown.remove(k)
				else: pass #print k
			
			self.send_msg(file)
			
			## End Control
			
			self.view_x = self.view_x % usize
			self.view_y = self.view_y % usize
			
			if self.planetFocus:
				self.zoom = old_zoom
				if self.back == 0:
					self.screen.blit(self.planetFocus.drawFocus((self.screen_width, self.screen_height)), (0,0))
				if self.back:
					self.planetFocus = 0
					self.view_x, self.view_y = self.old_view
					self.screen.fill(BACKGROUND)
					self.image.fill(BACKGROUND)
				pg.display.flip()
				continue
				
			# Draw background
			'''
			extra_screens = 0
			width = self.screen_width * self.zoom
			height = self.screen_height * self.zoom
			if width > usize - self.view_x:
				width = usize - self.view_x
				extra_screens = 2
			if height > usize - self.view_y:
				height = usize - self.view_y
				extra_screens += 1
			'''
			
				# Clear lines
			LINE_WIDTH = 3
			offset_x = (-(old_view_x) % LINE_SPACING) / old_zoom
			offset_y = (-(old_view_y) % LINE_SPACING) / old_zoom
			
			for i in range(0, self.screen_width, int(LINE_SPACING/old_zoom)):
				pg.draw.line(self.image, BACKGROUND,
					(offset_x+i, 0), (offset_x+i, usize), LINE_WIDTH)
				pg.draw.line(self.screen, BACKGROUND,
					(offset_x+i, 0), (offset_x+i, usize), LINE_WIDTH)
			for i in range(0, self.screen_height, int(LINE_SPACING/old_zoom)):
				pg.draw.line(self.image, BACKGROUND,
					(0, offset_y + i), (usize, offset_y+i), LINE_WIDTH)
				pg.draw.line(self.screen, BACKGROUND,
					(0, offset_y + i), (usize, offset_y+i), LINE_WIDTH)
			
				# Clear fog
			offset_x = int(old_view_x / FOG_SPACING)
			offset_y = int(old_view_y / FOG_SPACING)
			num = usize/FOG_SPACING
			
			for i in range(offset_x, offset_x + int(self.screen_width * old_zoom / FOG_SPACING)+2):
				i = i % num
				for j in range(offset_y, offset_y + int(self.screen_height * old_zoom / FOG_SPACING)+2):
					j = j % num
					if self.perma_fog[i][j] > 0:
						'''
						pg.draw.rect(self.image, BACKGROUND,
						((((i+1)*FOG_SPACING-old_view_x)%usize-FOG_SPACING)/old_zoom,
						(((j+1)*FOG_SPACING-old_view_y)%usize-FOG_SPACING)/old_zoom,
						FOG_SPACING / old_zoom+1,
						FOG_SPACING / old_zoom+1))
						'''
						pg.draw.rect(self.screen, BACKGROUND,
						((((i+1)*FOG_SPACING-old_view_x)%usize-FOG_SPACING)/old_zoom,
						(((j+1)*FOG_SPACING-old_view_y)%usize-FOG_SPACING)/old_zoom,
						FOG_SPACING / old_zoom+1,
						FOG_SPACING / old_zoom+1))
						if self.perma_fog[i][j] < 1: self.perma_fog[i][j] = 0

				# Update fog
			for i in range(offset_x, offset_x + int(self.screen_width * self.zoom / FOG_SPACING)+2):
				i = i % num
				for j in range(offset_y, offset_y + int(self.screen_height * self.zoom / FOG_SPACING)+2):
					j = j % num
					if self.perma_fog[i][j]:
						'''
						pg.draw.rect(self.image, FOG_COLOR,
						((((i+1)*FOG_SPACING-self.view_x)%usize-FOG_SPACING)/self.zoom,
						(((j+1)*FOG_SPACING-self.view_y)%usize-FOG_SPACING)/self.zoom,
						FOG_SPACING / self.zoom+1,
						FOG_SPACING / self.zoom+1))
						'''
						pg.draw.rect(self.screen, FOG_COLOR,
						((((i+1)*FOG_SPACING-self.view_x)%usize-FOG_SPACING)/self.zoom,
						(((j+1)*FOG_SPACING-self.view_y)%usize-FOG_SPACING)/self.zoom,
						FOG_SPACING / self.zoom+1,
						FOG_SPACING / self.zoom+1))
			
				# Update lines
			offset_x = (-self.view_x % LINE_SPACING) / self.zoom
			offset_y = (-self.view_y % LINE_SPACING) / self.zoom
			for i in range(0, self.screen_width, int(LINE_SPACING/self.zoom)):
				pg.draw.line(self.image, (255,255,255),
					(offset_x+i, 0), (offset_x+i, usize), LINE_WIDTH)
				pg.draw.line(self.screen, (255,255,255),
					(offset_x+i, 0), (offset_x+i, usize), LINE_WIDTH)
			for i in range(0, self.screen_height, int(LINE_SPACING/self.zoom)):
				pg.draw.line(self.image, (255,255,255),
					(0, offset_y + i), (usize, offset_y+i), LINE_WIDTH)
				pg.draw.line(self.screen, (255,255,255),
					(0, offset_y + i), (usize, offset_y+i), LINE_WIDTH)
			
			'''
			image = self.u.total.subsurface(self.view_x, self.view_y,
				width, height)
			self.image.blit(image, (0,0))
			if extra_screens >= 2:
				image = self.u.total.subsurface(0, self.view_y, 
					self.screen_width*self.zoom - width, height)
				self.image.blit(image, (width, 0))
			if extra_screens % 2:
				image = self.u.total.subsurface(self.view_x, 0, 
					width, self.screen_height*self.zoom - height)
				self.image.blit(image, (0, height))
			if extra_screens == 3:
				image = self.u.total.subsurface(0,0,
					self.view_x - (usize - self.screen_width*self.zoom),
					self.view_y - (usize - self.screen_height*self.zoom))
				self.image.blit(image, (width, height))
			'''
			# End background
			
			# Draw sprites
			
				# Cover over dragBubble
			if self.drag.rect != 0:
				x = ((self.drag.rect.right - (old_view_x)) % usize - self.drag.rect.width)/old_zoom
				y = ((self.drag.rect.bottom - (old_view_y)) % usize - self.drag.rect.height)/old_zoom
				self.screen.blit(self.image, (x,y), (x,y,self.drag.rect.width/old_zoom, self.drag.rect.height/old_zoom))
			
				# Cover over message
			self.screen.blit(self.image, self.message.location,
				(self.message.location[0], self.message.location[1],
				self.message.rect.width, self.message.rect.height))
				
			done = []
			
			for s in vis:   # find new teams
				if s.type == 'bullet': continue
				if s.team not in self.teamsDiscovered:
					s.team.drawLogo()
					self.teamsDiscovered.append(s.team)
			
			for s in drawn: # cover
			
				x = ((s.rect.right - old_view_x) % usize - s.rect.width*0.5) / old_zoom - s.rect.width*0.5
				y = ((s.rect.bottom - old_view_y) % usize - s.rect.height*0.5)/old_zoom - s.rect.height*0.5
				self.screen.blit(self.image, (x,y), (x,y,s.rect.width,s.rect.height))
				
			for s in vis: # draw
				s.updateImage(self.view_x, self.view_y, self.zoom, usize)
				x = ((s.rect.right - self.view_x) % usize - s.rect.width*0.5)/self.zoom - s.rect.width*0.5
				y = ((s.rect.bottom - self.view_y) % usize - s.rect.height*0.5)/self.zoom - s.rect.height*0.5
				self.screen.blit(s.image, (x,y))
				done.append(s)
			drawn = done[:]
			
			# End sprites
			
			if self.dragging: # draw dragBubble
				self.drag.getImage([self.view_x, self.view_y], [mouse_x, mouse_y], 
					[self.start_x, self.start_y], True, self.zoom, usize)
				x = ((self.drag.rect.right - self.view_x) % usize - self.drag.rect.width)/self.zoom
				y = ((self.drag.rect.bottom - self.view_y) % usize - self.drag.rect.height)/self.zoom
				self.screen.blit(self.drag.image, (x,y))
			
			self.frames += 1
			
			if fogReady.is_set():
				self.fog.image = self.fog.image2
				fogReady.clear()
			#self.image.blit(self.fog.image, (0,0))
			
			self.screen.blit(self.image, (self.screen_width-self.infoMeter.rect.width, 0),
				(self.screen_width-self.infoMeter.rect.width, 0,
				self.infoMeter.rect.width, self.infoMeter.rect.height))
			if hoverPlanet:
				self.infoMeter.getImage(hoverPlanet)
			elif len(self.controlGroup.sprites()) > 0:
				self.infoMeter.getImage(self.controlGroup.sprites())
			else: self.infoMeter.getImage(None)
			self.screen.blit(self.infoMeter.image, (self.screen_width-self.infoMeter.rect.width, 0))
			
			#self.screen.blit(self.image, (0,0))
			
			self.mouseMeterGroup.clear(self.screen, self.image)
			self.mouseMeterGroup.update(self.view_x, self.view_y,
				usize, self.zoom, self.timescale, self.locktime)
			self.mouseMeterGroup.draw(self.screen)
			
			self.message.update(deltat, self.msgs)
			self.msgs = []
			self.screen.blit(self.message.image, self.message.location)
			pg.display.flip()
			
		print "All ships have died! Ending game."
		self.sock.close()
		sys.exit()

	def getFogBase(self):
		pass
		self.fog.getBase(self.t.commsNetwork, self.view_x, self.view_y, self.zoom, self.u.size)

	def updateFog(self):
		self.fog.getImage(self.t.commsNetwork, self.view_x, self.view_y, self.zoom, self.u.size)
	
	def updateFogLoop(self, fogReady):
		while True:
			if fogReady.is_set():
				pg.time.wait(30)
			else:
				self.update_perma_fog(self.t.commsNetwork)
				self.updateFog()
				fogReady.set()

if __name__ == '__main__':
	screen_size = (1000,600)
	if len(sys.argv) == 2:
		host = sys.argv[1]
	else:
		host = str(input("Input host:\n")) #'localhost' #'fda1:df66:551c:0:e018:201f:a004:729e' #str(input("Input host:\n")) #
	port = 50000 # int(input("Input port:\n"))
	hv = HumanView(host, port, screen_size)
	t = threading.Thread(name = 'receive', target = hv.receive_loop)
	t.setDaemon(True)
	t.start()
	while not hv.isReady:
		pass
	file = open('upload.txt', 'w')
	hv.update(file)