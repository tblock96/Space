## Ship class
'''
A class about ships! The only mobile things (other than the camera, so this
might be a lengthy module. So far, will have 4 subclasses: light, med, heavy,
and settler. Will also include non-Empire ships (merchants, police, pirates)
'''

import pygame as pg
import unimath as um

class Ship(pg.sprite.Sprite):
    
    def __init__(self, team, home):
        pg.sprite.Sprite.__init__(self)
        # self.type = 0       # string
        # self.speed = 0      # pixels per second
        # self.armor = 0      # damage
        # self.regen = 0      # armor per second
        # self.hp = 0         # damage
        # self.power = 0      # attack damage
        # self.accuracy = 0   # likelihood of hitting the target (/1)
        # self.accel = 0      # pixels per second per second
        # self.resources = {} # resources dict
        # self.population = 0 # population
        self.direction = 0  # rads
        self.team = team
        self.home = home
        self.base = home
        self.control = False
        self.comms = False
        self.completed = True
        self.boarded = False
        self.taskQueue = []
        self.target = (0,0,team.usize)
        self.baseTarget = self.target
        # self.commsLength = 0
        # self.visionLength = 0
        self.location = [0,0]
        self.velocity = [0,0]
        self.initImage()
        self.getImage(0,0,1,1000)
        self.bulletGroup = pg.sprite.Group()
        self.actionGroup = {}
    
    def move(self, targets, time):
        if self.home != 0:
            try:
                self.home.cache['units'][self.type].remove(self)
            except Exception: self.home.cache['units'][self.type] = []
            self.home = 0
        self.mv(targets, time)
        target, usize = (targets[0], targets[1]), targets[2]
        if um.get_dist_points(self.location, target, usize) < 5:
            try:
                slow = self.actionGroup['special'][0]
                if slow == self: raise KeyError
                else: self.completed = False
            except KeyError: self.completed = True
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

    def update(self, time, view_x, view_y, zoom, usize):
        if self.hp <= 0:
            return self.delete()
        self.location[0] += self.velocity[0]*time
        self.location[1] += self.velocity[1]*time
        self.location[0] = self.location[0] % self.target[2]
        self.location[1] = self.location[1] % self.target[2]
        self.direction = um.atan2(self.velocity[1], self.velocity[0]+0.0001)
        self.getImage(view_x, view_y, zoom, usize)
        try:
            test1 = (self == self.actionGroup['special'][0])
        except KeyError: test1 = False
        if self.completed:
            self.getNextTask()
            if test1:
                for s in self.actionGroup['ships']:
                    if len(s.taskQueue) > len(self.taskQueue):
                        s.completed = True
        self.currentTask(self.target, time)
        self.regenArmor(time)
        self.cooldown = min(self.cooldown + time * 1000, self.__class__.cooldown)

    def regenArmor(self, time):
        if self.armor < self.__class__.armor:
            self.armor += self.regen*time
        if self.armor > self.__class__.armor:
            self.armor = self.__class__.armor
    
    def jump(self, target, time):
        self.move(target, time)
    
    def attack(self, target, time):
        if isinstance(target[0], Ship):
            other = target[0]
            self.atk(target, time)
            if other.hp <= 0 or other not in self.team.visible: 
                try:
                    self.baseTarget = [target[1][0], target[1][1], target[2]]
                except Exception:
                    print "ERROR in attack. basetarget:"
                    print self.baseTarget
                    print "target"
                    print target
                    self.team.u.quit()
        else:
            self.move(target, time)
            targ = self.getTarget(self.target[0], self.target[1], self.target[2])
            if targ:
                self.baseTarget = [targ, (target[0], target[1]), target[2]]
    
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
        if isinstance(target[0], list):     # still not coming from AG
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
        if isinstance(target[0], list): # has been updated
            self.move([target[0][0], target[0][1], target[2]], time)
            if self.completed == True:
                self.baseTarget[1].append(self.baseTarget[0])
                if len(self.taskQueue) == 0:
                    for loc in self.baseTarget[1]:
                        self.addToTaskQueue(self.patrol, loc)
                if self.taskQueue[0][0] == self.patrol:
                    self.completed = False
                    self.baseTarget[0] = self.taskQueue[0][1][0:2]
                    self.taskQueue = self.taskQueue[1:]
            targ = self.getTarget(target[0][0], target[0][1], target[2])
            if targ:
                self.baseTarget = [targ, target[0]+target[1], target[2]]
        elif isinstance(target[0], Ship):      # currently attacking
            self.atk(target, time)
            if target[0].hp <= 0 or target[0] not in self.team.visible:
                print "%s on team %d back to patrolling" %(self.type, self.team.index)
                self.baseTarget = [target[1][:1], target[1][1:], target[2]]
                print "basetarget is now"
                print self.baseTarget
        else: # target = [start_x, start_y, usize]
            self.baseTarget = [target[0:2], [], target[2]]
            self.patrol(self.baseTarget, time)
    
    def stop(self, target, time):
        if um.magnitude(self.velocity) > .1:
            self.velocity = [self.velocity[0]/1000.0, self.velocity[1]/1000.0]
        self.completed = True
    
    def retreat(self, target, time):
        if self.comms:
            self.completed = True
        else:
            self.dock([self.base, None, target[2]], time)
    
    def dock(self, target, time):
        '''target: x,y,usize or planet, null, usize'''
        
        if target[1] == None:
            targ_planet = target[0]
            usize = target[2]
            if um.get_dist_planets(self, targ_planet, usize) > 65:
                self.move([targ_planet.location[0], targ_planet.location[1], usize], time)
            else:
                self.location = [targ_planet.location[0], targ_planet.location[1]]
                try:
                    targ_planet.cache['units'][self.type].append(self)
                except KeyError:
                    targ_planet.cache['units'][self.type] = [self]
                self.home = targ_planet
                self.completed = True
        else:
            self.move(target, time)
            for p in self.team.planets.values():
                if um.get_dist_planets(self, p, 100):
                    self.baseTarget = [p, None, target[2]]
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
                self.baseTarget = (targ, None, target[2])
    
    def setCurrentTask(self):
        try:
            task, target = self.taskQueue[0]
        except Exception:
            print "Error extracting task, target from"
            print self.taskQueue[0]
        self.taskQueue = self.taskQueue[1:]
        self.currentTask = task
        self.baseTarget = target
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
        self.setCurrentTask()
        
    def delete(self):
        try:
            self.team.ships[self.type].remove(self)
        except Exception: pass
        if self.type == "carrier":
            for s in self.boarders:
                s.delete()
        if self.actionGroup['special'][0] == self:
            for s in self.actionGroup['ships']:
                s.baseTarget = self.baseTarget
        self.team.removeFromAG([self])
        self.kill()
        del self
    
    def initImage(self):
        if self.type in ['light', 'merchant', 'settler']:
            self.img = [pg.Surface((20,10)), pg.Surface((20,10))]
            for i in range(len(self.img)):
                self.img[i].fill((15,0,15))
                self.img[i].set_colorkey((15,0,15))
                pg.draw.ellipse(self.img[i], self.team.color, pg.Rect(0,0,20,10))
            pg.draw.circle(self.img[1], (15,0,15), (10,5),5)
        if self.type in ['battleship', 'carrier']:
            self.img = [pg.Surface((30,10)), pg.Surface((30,10))]
            for i in range(len(self.img)):
                self.img[i].fill(self.team.color)
                self.img[i].set_colorkey((15,0,15))
            pg.draw.circle(self.img[1], (15,0,15), (15,5), 5)
        
    def getImage(self, view_x, view_y, zoom, usize):
        self.image = self.img[self.control].copy()
        self.image = pg.transform.rotate(self.image, -self.direction/um.pi*180.0)
        self.getRect(view_x, view_y, zoom, usize)
        if self.comms:
            pg.draw.circle(self.image, (255,255,255), 
                (self.rect.width/2, self.rect.height/2), 5, 2)
        # self.image = self.image.convert()
        self.image.set_colorkey((15,0,15))
    
    def getRect(self, view_x, view_y, zoom, usize):
        self.rect = self.image.get_rect()
        self.rect.center = (self.location[0],#+usize*(self.location[0]<view_x),
            self.location[1])# + usize * (self.location[1] < view_y) )
        
    def getTarget(self, mouse_x, mouse_y, usize):
        max_dist = self.team.usize
        target = 0
        for s in self.team.visible:
            if s.team.index == self.team.index: continue
            if s.type == "planet": continue
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
        planets, index, usize = target
        if um.get_dist_planets(self, planets[index], usize) > 65:
            self.move([planets[index].location[0], planets[index].location[1],
                usize], time)
        else:
            if planets[index].team.index == 100 and planets[index] in self.team.visible:
                self.team.acquirePlanet(planets, index, self.population)
                for key, val in self.resources.items():
                    planets[index].cache[key] = val
                print "%s settled planet %d!!!!" %(self.team.name, index)
                self.delete()
            elif planets[index].team == self.team:
                planets[index].addPopulation(self.population)
                self.delete()
            else: self.completed = True

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
        self.speed = self.getSpeed(15) # 1000 pixels per minute
        self.resources = {}
    
    def loadResources(self, resDict, planet):
        for key, val in resDict.items():
            try:
                self.resources[key] += val
            except KeyError:
                self.resources[key] = val
            planet.addResources({key: -val})
    
    def unload(self, target, time):
        planets, index, usize = target
        if um.get_dist_planets(self, planets[index], usize) > 65:
            self.move([planets[index].location[0], planets[index].location[1],
                usize], time)
        else:
            if planets[index].team == self.team:
                planets[index].addResources(self.resources)
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
        target: (othership, location, usize) or (locationx, locationy, usize)'''
        other = target[0]
        usize = target[2]
        o_x, o_y = other.location[0], other.location[1]
        dx, dy = um.get_short_path(self.location, other.location, usize)
        if um.hypot(dx, dy) > self.range: self.moveToTarget(target, time)
        else: self.aim(target, time)
    
    def moveToTarget(self, target, time):
        other = target[0]
        usize = target[2]
        target_x = other.location[0] + 3*other.velocity[0] - 6*self.velocity[0]
        target_y = other.location[1] + 3*other.velocity[1] - 6*self.velocity[1]
        self.move((target_x, target_y, usize), time)
    
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
        else:       # we know we're in range, but not aimed properly
            dtheta = (theta-my_dir) % (2*um.pi)
            if dtheta < um.pi/2.: # pointing to the right (left on screen)
                right = True
            elif dtheta < um.pi: # pointing back and right
                right = False
            elif dtheta < 3*um.pi/2.: # pointing back and left
                right = True 
            else:       # pointing front and left
                right = False
            if right:
                target_x = self.location[0] + self.velocity[1]
                target_y = self.location[1] - self.velocity[0]
            else:
                target_x = self.location[0] - self.velocity[1]
                target_y = self.location[1] + self.velocity[0]
            self.move((target_x, target_y, usize), time)
    
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
    hp = 500
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
    boarders = []
    
    def __init__(self, team, home):
        Ship.__init__(self, team, home)
        self.speed = self.getSpeed(7.5)
        self.velocity = [0.1,0.1]
        self.resources = {}    
        
    def update(self, time, view_x, view_y, zoom, usize):
        Ship.update(self, time, view_x, view_y, zoom, usize)
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
        if self.jumpCooldown > 0:       # Must wait 15 secs from last jump
            self.mv(target, time)
            return
        self.jumpTime -= time*1000      # Cannot charge jump engine until then
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
    velocity = 1. # pixels per millisecond
    type = "bullet"
    
    def __init__(self, ship, vx, vy):
        pg.sprite.Sprite.__init__(self)
        self.damage = ship.power
        if ship.type == 'battleship':
            self.damage /= 3.
        self.angle = um.atan2(vy,vx) - (1-ship.accuracy) \
            + 2 * um.random.random()*(1-ship.accuracy)
        self.vy = um.sin(self.angle) * self.velocity
        self.vx = um.cos(self.angle) * self.velocity
        self.team = ship.team
        self.ship = ship
        self.range = ship.range
        self.location = [0,0]
        self.location[0], self.location[1] = ship.location[0], ship.location[1]
        ship.team.spriteGroup.add(self)
        self.update(0,0,0,1,ship.team.usize)
    
    def update(self, time, view_x, view_y, zoom, usize):
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
        # print "Bullet location: %d, %d" %(self.location[0], self.location[1])
        self.image = pg.Surface((5,5))
        self.image.fill((255,255,255))
        self.rect = self.image.get_rect()
        self.rect.center = self.location
    
    def hit(self, s):
        s.hurt(self.damage)
    
    def delete(self):
        self.kill()
        del self
    
    def hurt(self, damage):
        if damage >= self.damage:
            self.delete()