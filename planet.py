## planet class
'''
A basic class that dictates the behaviour of planets in general.
Will need to be displayed, so implements pygame.sprite
Will eventually have subclasses that determine behaviour of different
    types of planets.
'''

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
        self.cache = {}
        self.buildings = {}
        self.buildingSelect = 0
        self.government = 0
        self.commsLength = STARTING_VISION
        self.visionLength = STARTING_VISION
        self.trade = {}
        self.hover = 0
        self.comms = 0
        self.MINERATE = 0.5 #rand.random()
        self.docility = rand.randint(1,400000)+0.01
        self.location = [rand.randint(1,universe.size),
            rand.randint(1,universe.size)]
        if index == 0:
            self.location = [10,10]
        for p in universe.planets.values():
            if um.get_dist_planets(self,p,universe.size) < 1000:
                return self.__init__(universe, index)
        for res in ['energy','material','luxury','food']:
            self.cache[res] = 0
            self.resources[res] = rand.randint(1,100000)
        self.cache['units'] = {}
        self.land = rand.randint(5,15)
        self.team = 0
        self.update(0, 0,0,0,0)
    
    def build(self, toBuild):
        if (not issubclass(toBuild, Building)) or self.land < 1: return
        try:
            self.buildings[toBuild.type].append(toBuild(self))
        except KeyError:
            self.buildings[toBuild.type] = [toBuild(self)]
        self.land -= 1
    
    def buildCapital(self):
        self.build(ProductionBuilding)
        self.buildings['production'][0].askBuild('stop')
        self.capital = 1
    
    def update(self, time, view_x, view_y, zoom, usize): #TODO
        self.updatePopulation(time)
        self.updateColor()
        self.getGovernment()
        self.doWork(time)
    
    def updatePopulation(self, time):
        increase = (1-self.docility / 400000) * self.population * \
            (1 - self.population / (max(0,self.cache['food']) + 1)) * time / 100.
        self.addPopulation(increase * self.government)
        self.addResources({'food': - time*self.population * .00025})
        
    def doWork(self, time):
        self.visionLength = self.commsLength = STARTING_VISION
        self.mtrt=self.enrt=self.fdrt=self.lxrt = self.MINERATE
        for key, val in self.buildings.items():
            for b in val:
                b.work(time)
        self.gather(time)
    
    def updateColor(self):
        self.backcolor = pg.Color(125*um.dictSum(self.resources)/400000,
            max(125,125*um.log10(1+self.population)/10),125*self.land/15,255)
        self.forecolor = pg.Color(
            int(min(255,125+130*um.dictLength(self.cache['units'])/10.)),
            125+int(130*self.government),
            int(min(255,125+130*um.dictSum(self.cache)/25000.)),
            255)
        self.getImage()
    
    def getImage(self):
        self.image = pg.Surface((100,100))
        self.image.fill((0,0,0))
        pg.draw.circle(self.image,self.backcolor,(50,50),40,0)
        pg.draw.circle(self.image,self.forecolor,(50,50),50,10)
        if self.hover:
            pg.draw.circle(self.image, (255,255,255),(50,50),50,5)
        if self.team != 0:
            self.image.blit(self.team.logo, (25,25))
        self.image = self.image.convert()
        self.image.set_colorkey((0,0,0))
        self.rect = self.image.get_rect()
        self.rect.center = self.location
    
    def getGovernment(self):
        inter = um.dictLength(self.buildings)/um.log10(self.population+2)*\
            (self.docility/um.dictSum(self.resources))**0.5
        inter = inter + (1-inter)/2*self.capital
        self.government = min(1, inter)
    
    def addToTeam(self, team):
        self.team = team
        self.team.usize = self.usize
        self.getImage()
    
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
        for list in self.buildings.values():
            for b in list:
                count += 1
                b.update(screen, count, mouse)
                img.blit(b.image, (b.rect.x, b.rect.y))
        if self.team != 0:
            logo = pg.transform.scale(self.team.logo, (min_d/5, min_d/5))
            img.blit(logo, (screen[0]/2-min_d/10, screen[1]/2-min_d/10))
        return img
    
    def askBuild(self):
        attempt = 0
        list = ['material', 'production', 'vision', 'government', 'comms', 'farming']
        while attempt not in list:
            if attempt != 0:
                print "That is not a valid response"
            print list
            try:
                attempt = input("What would you like to build?\n")
            except Exception: pass
        if attempt == 'material':
            self.build(MiningBuilding)
        elif attempt == 'production':
            self.build(ProductionBuilding)
        elif attempt == 'vision':
            self.build(VisionBuilding)
        elif attempt == 'government':
            self.build(GovernmentBuilding)
        elif attempt == 'comms':
            self.build(CommsBuilding)
        elif attempt == 'farming':
            self.build(FarmingBuilding)

class Building(pg.sprite.Sprite):
    
    type = 'undefined'
    
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
        x,y = self.font.size(self.type[0])
        self.image.blit(self.font.render(self.type[0],0,self.team.color),
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

class ProductionBuilding(Building):
    
    type = 'production'
    
    TASKS = {'light': {'resources':{'material':750, 'energy':750}, 'work':10000},
            'battleship': {'resources':{'material':1750, 'energy':2000}, 'work':30000},
            'carrier': {'resources':{'material':2500, 'energy':1000}, 'work':40000},
            'settler': {'resources':{'material':2500, 'energy':1500}, 'work':30000},
            'merchant': {'resources':{'material':2000, 'energy':600}, 'work':15000},
            'stop': {'resources':{'material':0, 'energy':0}, 'work':9999999}}
            
    def __init__(self, planet):
        Building.__init__(self,planet)
        self.currently = 0
        self.workRemaining = 0
    
    def work(self, time):
        rate = self.planet.population * self.planet.government
        if not (self.task and self.currently):
            self.askBuild()
        if self.hasResources():
            if self.task['name'] != 'stop':
                self.workRemaining -= rate * time
            for res, amt in self.task['resources'].items():
                self.planet.cache[res] -= amt * rate * time / self.task['work']
                self.task['resources'][res] -= amt * rate * time / self.task['work']
            if self.workRemaining <= 0:
                if self.task['name'] == 'light':
                    type = ship.Light
                elif self.task['name'] == 'battleship':
                    type = ship.Battleship
                elif self.task['name'] == 'carrier':
                    type = ship.Carrier
                elif self.task['name'] == 'settler':
                    type = ship.Settler
                    self.planet.addPopulation(-1000)
                elif self.task['name'] == 'merchant':
                    type = ship.Merchant
                s = type(self.team, self.planet)
                try:
                    self.planet.cache['units'][self.task['name']].append(s)
                except KeyError:
                    self.planet.cache['units'][self.task['name']] = [s]
                print "Planet %s has finished building a %s" %(self.planet.index,
                    self.task['name'])
                dir = rand.random()*2*um.pi
                s.newTaskQueue(s.move, [self.planet.location[0]+100*um.cos(dir),
                    self.planet.location[1]+100*um.sin(dir), self.planet.usize])
                self.team.acquireShip(s, [self.planet.location[0],
                    self.planet.location[1]])
                self.askBuild(self.task['name'])
        else:
            print "Planet %s does not have enough resources to do its work!" \
                %self.planet.name
            self.task = self.currently = 0
    
    def hasResources(self):
        for res, amt in self.task['resources'].items():
            if self.planet.cache[res] < amt: return False
        return True

    def askBuild(self, last = 0):
        # TODO this graphically
        if last:
            attempt = last
        else:
            print "A building on planet %s needs new production instructions." \
                %self.planet.name
            print "Option Material Energy Work"
        
            for k, v in self.TASKS.items():
                string = k + " "*3
                res = v['resources']
                string = string + str(res['material']) + " "*5 + str(res['energy'])\
                    + " "*5
                string = string + str(v['work'])
                print string
            attempt = 0
            while attempt not in self.TASKS.keys():
                if attempt != 0: print "That is not a valid selection"
                try:
                    attempt = str(input("What would you like to build?\n"))
                except Exception: pass
        self.task = {'resources':{}}
        for k, v in self.TASKS[attempt]['resources'].items():
            self.task['resources'][k] = v
        self.task['work'] = self.TASKS[attempt]['work']
        self.task["name"] = attempt
        self.workRemaining = self.task['work']
        self.currently = True

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
                try:
                    self.planet.cache['units'][self.task['name']].append(s)
                except KeyError:
                    self.planet.cache['units'][self.task['name']] = [s]
                self.team.acquireShip(s, [self.planet.location[0],
                    self.planet.location[1]])
                print "Planet %s has finished building a %s" %(self.planet.name,
                    self.task['name'])
                self.findBuild()
        else:
            print "Planet %s does not have enough resources to do its work!" \
                %self.planet.name
            self.task = self.currently = 0
        if 'merchant' in self.planet.cache['units'].keys():
            # print self.planet.cache['units']
            self.sendAid()
    
    def sendAid(self):
        self.findAidTarget()
        other = self.aidTarget.cache
        total_diff = 0
        diff = {}
        for k,v in self.planet.cache.items():
            if k == "units": continue
            diff_s = max(0, v-other[k])
            total_diff += diff_s
            diff[k] = diff_s
        for s in self.planet.cache['units']['merchant']:
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
                    target[2])      # Wait and then come back in a bit
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
            s.addToTaskQueue(s.dock, (self.planet.location[0], self.planet.location[1], self.planet.usize))
            self.planet.cache['units']['merchant'].remove(s)

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
    
    type = 'food'
    
    def work(self, time):
        self.planet.fdrt += 0.1

class LuxuryBuilding(Building):
    
    type = 'luxury'
    
    def work(self, time):
        self.planet.lxrt += 0.1