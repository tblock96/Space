## universe class

'''
A controller for all the planets in the game, as well as the teams, and also
each ship (split up by teams).
'''

import pygame as pg
from pygame.locals import *
import planet
import unimath as um
import sys
import mouseMeter as mM
import team, ship

class Universe(pg.sprite.Sprite):
    
    planets = {}
    teams = {}
    
    def __init__(self, size, numTeams):
        pg.sprite.Sprite.__init__(self)
        self.add(universeGroup)
        self.size = size * 1000
        numPlanets = int(size**2/3)
        for i in range(numPlanets):
            self.planets[i] = planet.Planet(self, i)
        for i in range(numTeams):
            self.teams[i] = team.Team(self, i)
            self.teams[i].getHomePlanet(self.planets)
            if i == 0:
                pass # Testing stuff for the human player
        self.empty = team.Team(self, 100)
        for i in range(numTeams, numPlanets):
            self.empty.acquirePlanet(self.planets,i,10)
        self.initImage()
            
        #TODO
    
    def print_universe(self):
        # t = self.teams[0]
        # #print t.name
        # for p in t.planets.values():
        #    # print p.cache
           pass
    
    def initImage(self):
        self.total = pg.Surface((self.size, self.size))
        self.total.fill((10,0,10))
        for i in range(0,1+int(self.size/500)): # This implementation only valid
                                                # while self.size is limited to 1000s
            x_pos = min(i*500, 2*self.size)
            y_pos = min(i*500, 2*self.size)
            pg.draw.line(self.total,(255,255,255),(x_pos,0),\
                (x_pos,self.size),3)
            pg.draw.line(self.total,(255,255,255),(0,y_pos),\
                (self.size,y_pos),3)
        for p in self.planets.values():
            self.total.blit(p.image, (p.rect.x, p.rect.y))
            self.total.blit(p.image, (p.rect.x-self.size, p.rect.y))
            self.total.blit(p.image, (p.rect.x-self.size, p.rect.y-self.size))
            self.total.blit(p.image, (p.rect.x, p.rect.y-self.size))
        self.total_clean = self.total.copy()
        
    def getImage(self, deltat, loop):

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
        
        for t in self.teams.values():
            t.getCommsNetwork()
            t.captainBroadcast()
            t.spriteGroup.update(timescale*min(0.4,deltat/1000.), view_x,
                view_y, zoom, self.size)
            for s in t.spriteGroup:
                x = (s.rect.right - view_x) % self.size - s.rect.width
                y = (s.rect.bottom - view_y) % self.size - s.rect.height
                self.image.blit(s.image, (x,y))
        
        if dragging:
            x = (drag.rect.right - view_x) % self.size - drag.rect.width
            y = (drag.rect.bottom - view_y) % self.size - drag.rect.height
            self.image.blit(drag.image, (x,y))
        
        self.image = pg.transform.scale(self.image, (screen_width, screen_height))
        self.rect = self.image.get_rect()
        self.rect.x = self.rect.y = 0

        # time_end = pg.time.get_ticks()
        # print "Time after subbing image: %d" %time_end
        
        if loop % 20 == 0:
            fog.getImage(self.teams[0].commsNetwork, view_x, view_y, zoom, self.size)
        self.image.blit(fog.image, (0,0))

        # time_end = pg.time.get_ticks()
        # print "Time after blitting fog image: %d" %time_end
        
        self.image.blit(infoMeter.image, (screen_width-infoMeter.rect.width, 0))
    
    def quit(self):
        sys.exit()
    
    def getFogBase(self):
        fog.getBase(self.teams[0].commsNetwork, view_x, view_y, zoom, self.size)
    
    def updateFog(self):
        fog.getImage(self.teams[0].commsNetwork, view_x, view_y, zoom, self.size)

if __name__ == "__main__":
    pg.init()
    
    universeGroup = pg.sprite.Group()
    planetGroup = pg.sprite.Group()
    objectGroup = pg.sprite.Group()
    mouseMeterGroup = pg.sprite.Group()
    controlGroup = pg.sprite.Group()
    dragGroup = pg.sprite.Group()

    info = pg.display.Info()
    
    screen_width = 800
    screen_height = 600
    screen = pg.display.set_mode((screen_width, screen_height))
    clock = pg.time.Clock()
    zoom = timescale = 1
    MOVE_MARGIN = 100
    view_x = view_y = locktime = 0

    dragging = False
    start_x = start_y = mouse_x = mouse_y = 0    
    
    drag = mM.dragBubble((objectGroup, dragGroup))
    infoMeter = mM.InfoMeter((objectGroup))
    meter = mM.mouseMeter((objectGroup, mouseMeterGroup))
    fog = mM.Fog(screen_width, screen_height)
    
    # Universe(size, teams)
    u = Universe(4,3)
    u.print_universe()
    pg.display.flip()
    coverSurf = pg.Surface((meter.rect.w, meter.rect.h))
    coverSurf.fill((15,0,15))
    mouseMeterGroup.draw(screen)
    
    
    for t in u.teams.values():
        t.acquireShip(planet.ship.Settler(t, t.planets[t.index]),
            [t.planets.values()[0].location[0]+100,
            t.planets.values()[0].location[1]+100])
        t.acquireShip(planet.ship.Merchant(t, t.planets[t.index]), 
            [t.planets.values()[0].location[0]+100,
            t.planets.values()[0].location[1]])
        t.acquireShip(planet.ship.Carrier(t, t.planets[t.index]),
            [t.planets.values()[0].location[0]+100,
            t.planets.values()[0].location[1]-100])
        t.acquireShip(planet.ship.Battleship(t, t.planets[t.index]),
            [t.planets.values()[0].location[0],
            t.planets.values()[0].location[1]-100])
        if t.index > 0:
            t.acquireShip(planet.ship.Battleship(t, t.planets[t.index]),
                [t.planets.values()[0].location[0],
                t.planets.values()[0].location[1]-100])
            t.removeFromAG(t.shipGroup.sprites())
            ag = t.makeAG(t.shipGroup.sprites())
            for s in ag['ships']:
                s.newTaskQueue(s.patrol, [u.planets[0].location[0], u.planets[0].location[1], u.size])
        t.spriteGroup.update(0,view_x, view_y, zoom, u.size)
        
    keysDown = []
    hoverPlanet = 0
    planetFocus = 0
        
    playerIndex = 0
    
    view_x = u.planets[0].location[0] - screen_width/2
    view_y = u.planets[0].location[1] - screen_height/2
    
    def timescaleInc():
        if timescale <= 1: return 0.1
        elif (-timescale) % 0.5 == 0:
            return 0.5
        else: return (-timescale) % 0.5
    
    loopcounter = 0
    
    u.getFogBase()
    u.updateFog()
    while 1:
        loopcounter = (loopcounter + 1) % 100
        deltat = clock.tick()
        # print deltat
        # time_end = pg.time.get_ticks()
        # print "Time at start of loop: %d" %time_end
        u.print_universe()
        
        if pg.mouse.get_focused():
            mouse_x, mouse_y = pg.mouse.get_pos()
            for mouse,view,screen_dim,i in ((mouse_x,view_x,screen_width,False),
                (mouse_y,view_y,screen_height,True)):
                if mouse < MOVE_MARGIN:
                    view -= int(10*um.log10(MOVE_MARGIN - mouse)) * zoom * deltat / 33
                if mouse > screen_dim - MOVE_MARGIN:
                    view += int(10*um.log10(screen_dim - MOVE_MARGIN + mouse)) * zoom * deltat / 33
                if not i:
                    view_x = view
                else:
                    view_y = view
                    
            # time_end = pg.time.get_ticks()
            # print "Time after checking move: %d" %time_end
            
            hoverPlanet = 0
            for p in u.planets.values():
                if p not in u.teams[0].visible: continue
                p.hover = 0
                if abs((mouse_x*zoom + view_x - p.rect.x) % u.size) < 100:
                    if abs((mouse_y*zoom + view_y - p.rect.y) % u.size) < 100:
                        p.hover = 1
                        hoverPlanet = p

        # time_end = pg.time.get_ticks()
        # print "Time after mouse parsing: %d" %time_end

        view_x = view_x % u.size
        view_y = view_y % u.size
            
        for e in pg.event.get():
            if e.type == QUIT: sys.exit()
            if e.type == KEYDOWN:
                keysDown.append(e.key)
            if e.type == KEYUP:
                try:
                    keysDown.remove(e.key)
                except ValueError: pass
            if e.type == MOUSEMOTION: pass
            if e.type == MOUSEBUTTONDOWN:
                start_x, start_y = ((mouse_x*zoom + view_x) % u.size, \
                    (mouse_y*zoom + view_y) % u.size)
                if e.button == 1:
                    if hoverPlanet:
                        planetFocus = hoverPlanet
                        back = 0
                        old_timescale = timescale
                        old_view = view_x, view_y
                    if planetFocus:
                        if planetFocus.buildingSelect:
                            planetFocus.buildingSelect.askBuild()
                    else:
                        dragging = True
                elif e.button == 3:
                    if len(controlGroup.sprites()) > 0:
                        u.teams[playerIndex].removeFromAG(controlGroup.sprites())
                        if K_b in keysDown:
                            for s in controlGroup.sprites():
                                u.teams[playerIndex].makeAG([s])
                        else:
                            u.teams[playerIndex].makeAG(controlGroup.sprites())
                        for s in controlGroup.sprites():
                            try:
                                if K_s in keysDown:
                                    if hoverPlanet:
                                        task = s.settle
                                        target = u.planets, hoverPlanet.index, u.size
                                    else: raise Exception
                                elif K_u in keysDown:
                                    task = s.unload
                                    if hoverPlanet and s.type == 'merchant':
                                        target = u.planets, hoverPlanet.index, u.size
                                    elif s.type == 'carrier':
                                        target = start_x, start_y, u.size
                                    else: raise Exception
                                elif K_a in keysDown:
                                    task = s.attack
                                    target = [start_x, start_y, u.size]
                                elif K_b in keysDown:
                                    task = s.board
                                    target = [start_x, start_y, u.size]
                                elif K_j in keysDown:
                                    task = s.jump
                                    target = [start_x, start_y, u.size]
                                elif K_c in keysDown:
                                    task = s.chain
                                    centre = um.getCentre(controlGroup.sprites(), u.size)
                                    path = um.get_short_path(centre, [start_x, start_y], u.size)
                                    target = [centre, [um.atan2(path[1], path[0])], u.size]
                                elif K_z in keysDown:
                                    task = s.patrol
                                    target = [start_x, start_y, u.size]
                                    #TODO
                                else:
                                    if hoverPlanet:
                                        task = s.dock
                                        target = hoverPlanet, None, u.size
                                    # TODO follow or attack
                                    else: raise Exception
                            except Exception:
                                task = s.move
                                target = start_x, start_y, u.size
                            if K_LSHIFT in keysDown:
                                s.addToTaskQueue(task, target)
                            else:
                                s.newTaskQueue(task, target)
            if e.type == MOUSEBUTTONUP:
                if e.button == 1:
                    if dragging:
                        group = u.teams[playerIndex].shipGroup
                        collide = pg.sprite.spritecollide(drag,
                            group,0)
                        for extraRect in [drag.xrect, drag.yrect, drag.xyrect]:
                            indices = extraRect.collidelistall(
                                group.sprites())
                            for i in indices:
                                collide.append(group.sprites()[i])
                        for s in controlGroup.sprites():
                            if not s in collide:
                                s.control = False
                                controlGroup.remove(s)
                        controlGroup.add(collide)
                        dragging = False
        

        # time_end = pg.time.get_ticks()
        # print "Time after event parsing: %d" %time_end
        
        for s in controlGroup.sprites():
            s.control = True
            
        drag.getImage((view_x,view_y),(mouse_x,mouse_y),(start_x,start_y),
            dragging,zoom,u.size)
            
        if hoverPlanet:
            infoMeter.getImage(hoverPlanet)
        elif len(controlGroup.sprites()) > 0:
            infoMeter.getImage(controlGroup.sprites())
        else: infoMeter.getImage(None)

        # time_end = pg.time.get_ticks()
        # print "Time after infoMeter image: %d" %time_end
        
        if planetFocus:
            if back == 0:
                screen.blit(planetFocus.drawFocus((screen_width, screen_height)), (0,0))
                timescale = 0.02
            if back:
                planetFocus = 0
                timescale = old_timescale
                view_x, view_y = old_view
        else:
            u.getImage(deltat, loopcounter)
            universeGroup.draw(screen)
            
            # time_end = pg.time.get_ticks()
            # print "Time after universe draw: %d" %time_end
            
        mouseMeterGroup.clear(screen, coverSurf)
        mouseMeterGroup.update(view_x, view_y, u.size, zoom, timescale, locktime)
        mouseMeterGroup.draw(screen)
        
        
        if K_LSHIFT in keysDown:
            shift = True
        else: shift = False
        if K_LCTRL in keysDown:
            ctrl = True
        else: ctrl = False
        
        for k in keysDown:
            
            if k == K_UP:
                view_y -= 0.15 * zoom *deltat
            elif k == K_DOWN:
                view_y += 0.15 * zoom *deltat
            elif k == K_LEFT:
                view_x -= 0.15 * zoom *deltat
            elif k == K_RIGHT:
                view_x += 0.15 * zoom *deltat
            elif k == 270: #NumPad Plus
                zoom -= 0.1
                if zoom < 1: timescale = zoom
                else: timescale = 1+(zoom-1)*5
                keysDown.remove(k)
            elif k == 269: #NumPad Minus
                zoom += 0.1
                if zoom < 1: timescale = zoom
                else: timescale = 1+(zoom-1)*5
                back = 1
                keysDown.remove(k)
            elif k == 268: #NumPad Times
                timescale += timescaleInc()
                keysDown.remove(k)
            elif k == 267: #NumPad Divide
                timescale -= timescaleInc()
                keysDown.remove(k)
            elif k == K_b:
                if planetFocus:
                    planetFocus.askBuild()
            elif k == K_ESCAPE:
                for s in controlGroup.sprites():
                    s.control = False
                controlGroup.empty()
            elif k == K_p:
                timescale = 0
                keysDown.remove(k)
            elif k == K_l:
                if locktime:
                    locktime = 0
                else: locktime = timescale
                keysDown.remove(k)
            else: pass #print k
        

        # time_end = pg.time.get_ticks()
        # print "Time after dealing with keys: %d" %time_end
        
        if locktime: timescale = locktime
            
        pg.display.flip()
        # time_end = pg.time.get_ticks()
        # print "Time after flipping display: %d" %time_end
    