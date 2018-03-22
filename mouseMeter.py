## mouse position meter
'''
A sprite that shows the location of the mouse in the bottom right corner of
the screen.
'''

import pygame as pg
import unimath as um
from planet import Planet

class mouseMeter(pg.sprite.Sprite):
    
    def __init__(self, groups):
        pg.sprite.Sprite.__init__(self)
        if not pg.font.get_init(): pg.font.init()
        self.backColor = (10,0,10)
        self.textColor = (255,255,255)
        self.font = pg.font.SysFont('arial',14)
        self.getImage(0,0,100,1,1,0)
        self.add(groups)
    
    def getImage(self, view_x, view_y, usize, zoom, timescale, locktime):
        x,y = pg.mouse.get_pos()
        
        text = str((int((x*zoom+view_x)%usize),int((y*zoom+view_y)%usize)))
        text = text + "  Zoom: "
        text = text + str(zoom) + "  Time: " + str(timescale)
        if locktime:
            text = text + " L"
        textIm = self.font.render(text,0,self.textColor)
        textSz = self.font.size(text)
        self.image = pg.Surface(textSz)
        self.image.fill(self.backColor)
        self.image.blit(textIm,(0,0))
        self.rect = self.image.get_rect()
        info = pg.display.Info()
        self.rect.center = (info.current_w-textSz[0],info.current_h-textSz[1])
    
    def update(self, view_x, view_y, usize, zoom, timescale, locktime):
        self.getImage(view_x, view_y, usize,zoom,timescale, locktime)

class dragBubble(pg.sprite.Sprite):
    
    def __init__(self, groups):
        pg.sprite.Sprite.__init__(self)
        self.backColor = (0,25,200,200)
        self.foreColor = (0,25,200,100)
        self.add(groups)
        self.img = pg.Surface((0,0))
    
    def getImage(self, view, mouse, start, dragging, zoom, usize):
        start_x, start_y = start
        mouse_x, mouse_y = mouse
        view_x, view_y = view
        if dragging:
            drag_w, drag_h = (mouse_x*zoom+view_x-start_x+usize/2)%usize-usize/2, \
                            (mouse_y*zoom+view_y-start_y+usize/2)%usize-usize/2
            x = min(start_x, start_x+drag_w)
            y = min(start_y, start_y+drag_h)
            width = abs(drag_w)
            height = abs(drag_h)
            self.rect = pg.Rect(x,y,width,height)
            
            extraRects = 0
            if start_x+drag_w < 0:
                self.xrect = pg.Rect(usize+start_x+drag_w, y,
                    -(start_x+drag_w), height)
                extraRects = 1
            if start_x+drag_w > usize:
                self.xrect = pg.Rect(0, y,
                    start_x + drag_w - usize, height)
                extraRects = 2
            if start_y+drag_h < 0:
                self.yrect = pg.Rect(x, usize+start_y+drag_h,
                    width, -(start_y+drag_h))
                extraRects += 3
            if start_y+drag_h > usize:
                self.yrect = pg.Rect(x, 0,
                    width, start_y + drag_h - usize)
                extraRects += 6
            if extraRects in [0,3,6]:
                self.xrect = pg.Rect(usize*2, usize*2, 0,0)
            if extraRects in [0,1,2]:
                self.yrect = pg.Rect(usize*2, usize*2, 0,0)
            if extraRects == 4: # both negative
                self.xyrect = pg.Rect(usize+start_x+drag_w, usize+start_y+drag_h,
                    -(start_x+drag_w), -(start_y+drag_h))
            elif extraRects == 5: # x positive, y negative
                self.xyrect = pg.Rect(0, usize+start_y+drag_h,
                    start_x+drag_w - usize, -(start_y+drag_h))
            elif extraRects == 7:   # x negative, y positive
                self.xyrect = pg.Rect(usize+start_x+drag_w, 0,
                    -(start_x+drag_w), start_y + drag_h - usize)
            elif extraRects == 8:   # both positive
                self.xyrect = pg.Rect(0, 0,
                    start_x+drag_w-usize, start_y+drag_h-usize)
            else: self.xyrect = pg.Rect(usize*2, usize*2, 0,0)
            
            self.image = pg.Surface((int(self.rect.width), int(self.rect.height)))
            self.image.fill((0,50,200))
            pg.draw.rect(self.image, (0,50,200), (0,0,drag_w,drag_h), 5)
            self.image.set_alpha(100)
            self.image = self.image.convert_alpha()
        else:
            self.image = self.img

class InfoMeter(pg.sprite.Sprite):
    ''' Shows info about highlighted objects (planets, ships)'''
    
    def __init__(self, groups):
        pg.sprite.Sprite.__init__(self)
        if not pg.font.get_init(): pg.font.init()
        self.foreColor = (255,255,255)
        self.backColor = (10,0,10)
        self.font = pg.font.SysFont('arial', 14)
        self.add(groups)
        self.initBlankImg()
        self.getImage()
    
    def initBlankImg(self):
        self.img = pg.Surface((1,1))
        self.img.fill(self.backColor)

    def getImage(self, spr = None):
        if spr == None:
            self.image = self.img
        else:
            if isinstance(spr, Planet): # only planets
                lines = self.getPlanetLines(spr)
            else: # for now, only ships
                if len(spr) == 1:
                    lines = self.getShipLines(spr[0])
                else:
                    lines = self.getMultiShipLines(spr)
            sum_y = 0
            max_x = 0
            sizes = []
            for i in range(len(lines)):
                x, y = self.font.size(lines[i])
                if x > max_x: max_x = x
                sizes.append((x,sum_y))
                sum_y += y
            self.image = pg.Surface((max_x, sum_y))
            self.image.fill(self.backColor)
            for i in range(len(lines)):
                txt = self.font.render(lines[i],True,self.foreColor,self.backColor)
                self.image.blit(txt, (0, sizes[i][1]))
        self.image.set_colorkey(self.backColor)
        self.image.convert_alpha()
        self.rect = self.image.get_rect()
    
    def getPlanetLines(self, spr):
        lines = []
        lines.append('Index: '+str(spr.index))
        lines.append('Team: '+str(spr.team.index))
        lines.append('Population: '+str(int(spr.population)))
        lines.append('Government: '+str(round(spr.government, 2)))
        lines.append('Buildings: '+str(um.dictLength(spr.buildings)))
        lines.append('Resources:')
        lines.append('  Material: '+str(round(spr.resources['material'])))
        lines.append('  Energy: '+str(round(spr.resources['energy'])))
        lines.append('  Food: '+str(round(spr.resources['food'])))
        lines.append('Cache:')
        lines.append('  Material: '+str(round(spr.cache['material'])))
        lines.append('  Energy: '+str(round(spr.cache['energy'])))
        lines.append('  Food: '+str(round(spr.cache['food'])))
        return lines
    
    def getShipLines(self, spr):
        lines = []
        lines.append('Type:     '+spr.type)
        lines.append('HP:       '+str(round(spr.hp)))
        lines.append('velocity: '+str(round(um.magnitude(spr.velocity))))
        return lines
    
    def getMultiShipLines(self, spr):
        lines = []
        types = {}
        hp = 0
        velocity = 0
        for i in range(len(spr)):
            hp += (spr[i].hp)
            velocity += (um.magnitude(spr[i].velocity))
            try:
                types[spr[i].type] += 1
            except KeyError:
                types[spr[i].type] = 1
        hp /= len(spr)
        velocity /= len(spr)
        lines.append('Types:')
        for k, v in types.items():
            lines.append('    '+str(k)+': '+str(v))
        lines.append('Avg HP: '+str(round(hp)))
        lines.append('Avg Vel: '+str(round(velocity)))
        return lines
    
class Fog(pg.sprite.Sprite):
    
    blocked = (30,0,30, 130)
    visible = (255,0,255, 0)
    
    def __init__(self, screen_w, screen_h):
        pg.sprite.Sprite.__init__(self)
        self.buffer = max(screen_w, screen_h)*0.2
        self.screen = (screen_w+2*self.buffer, screen_h+2*self.buffer)
        
    def getBase(self, sprites, view_x, view_y, zoom, usize):
        radius = []
        for i in range(len(sprites)):
            radius.append(sprites[i].visionLength)
        maxradius = max(radius)
        
        self.img = pg.Surface(self.screen, pg.SRCALPHA)
        self.img.fill(self.blocked)
    
    def getImage(self, sprites, view_x, view_y, zoom, usize):
        '''Gets the image of the fog with circles of radius=that sprite's vision
        around each sprite.

        sprites: list of sprites whose vision radii affects the screen
        '''
        
        radius = []
        for i in range(len(sprites)):
            radius.append(sprites[i].visionLength)
        maxradius = max(radius)
        
        self.image = self.img.copy()
        
        # time_end = pg.time.get_ticks()
        # print "Time after initializing image: %d" %time_end
        
        for i in range(len(sprites)):
            x = int(((sprites[i].rect.centerx+radius[i]-view_x) % usize - radius[i])
                / zoom)
            y = int(((sprites[i].rect.centery+radius[i]-view_y) % usize - radius[i])
                / zoom)
            pg.draw.circle(self.image, self.visible, (x,y), int(radius[i]/zoom))
        
        # time_end = pg.time.get_ticks()
        # print "Time after sprite loop: %d" %time_end
            
        # time_end = pg.time.get_ticks()
        # print "Time after subbing fog image: %d" %time_end