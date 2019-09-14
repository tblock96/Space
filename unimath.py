## unimath module
'''
To do all the weird math functions needed (maybe like the physics engine?)
'''
from math import *
import random
import ship as ship_file

def get_dist_planets(p1, p2, usize):
	p1l = p1.location
	p2l = p2.location
	return get_dist_points(p1l,p2l,usize)

def get_dist_points(pt1, pt2, usize):
	distx = -abs(abs(pt1[0]-pt2[0])-usize/2)+usize/2
	disty = -abs(abs(pt1[1]-pt2[1])-usize/2)+usize/2
	return (distx**2+disty**2)**0.5
	
def dictSum(d):
	'''
	Return the sum of all the values in the dict.
	if d.values() contains non-numbers, they are ignored.
	'''
	res = 0
	for v in d.values():
		try:
			res += int(v)
		except Exception: pass
	return res

def magnitude(list):
	'''
	Return the magnitude of the list/tuple
	'''
	res = 0
	for item in list:
		res += item**2
	res = res ** 0.5
	return res

def dictLength(d):
	'''
	Return the sum of the lengths of all the lists in the dict.
	d must be a dictionary in which all values are lists.
	'''
	res = 0
	for l in d.values():
		res += len(l)
	return res

def get_short_path(pt1, pt2, usize):
	'''Returns (dx, dy) where each is the shortest path (given overlapping the
	universe) from pt1 to pt2'''
	distx = -abs((pt1[0]-pt2[0]-usize/2)%usize)+usize/2
	disty = -abs((pt1[1]-pt2[1]-usize/2)%usize)+usize/2
	return (distx, disty)

def insertBySpeed(ship, list):
	'''Updates a list of ships, sorted slowest to fastest'''
	for i in range(len(list)):
		if ship.speed < list[i].speed:
			return list.insert(i, ship)
	list.append(ship)

def insertByStrength(ship, list):
	'''Updates a list of ships, sorted strongest to weakest'''
	for i in range(len(list)):
		if ship.hp*ship.power < list[i].power*list[i].hp:
			return list.insert(i, ship)
	list.append(ship)

def insertByCommsLength(ship, list):
	'''Updates a list of ships, sorted by longest comms Length to shortest'''
	for i in range(len(list)):
		if ship.commsLength > list[i].commsLength:
			return list.insert(i, ship)
	list.append(ship)
	
def getCentre(list, usize):
	'''Given a list of ships, returns their centre of mass'''
	centre = [0,0]
	for i in range(len(list)):
		path = get_short_path(centre, list[i].location, usize)
		centre = [centre[0]+path[0]/(i+1), centre[1]+path[1]/(i+1)]
	return centre

def get_threat_rank(threats, ship):
	'''Returns a rank of threats, based on distance and power'''
	lis = []
	scores = []
	for t in threats:
		if isinstance(t, ship_file.Ship):
			if t.hp <= 0: continue
		inserted = False
		try:
			score = t.power
			if t.type == 'carrier':
				if len(t.boarders) > 0: # biggest threat, biggest chance for win
					score = 1000
		except AttributeError: continue	 # it's a planet!
		for i in range(len(lis)):
			if score > scores[i]:
				scores.insert(i, score)
				lis.insert(i, t)
				inserted = True
				break
		if not inserted:
			scores.append(score)
			lis.append(t)
	return lis

def umround(arg, ndigits):
	'''Returns arg rounded to ndigits.
	arg can be a list or a value'''
	if isinstance(arg, (list, tuple)):
		res = []
		for a in arg:
			res.append(round(a, ndigits))
		return res
	return round(arg, ndigits)

def mean(list):
	return sum(list)/len(list)

def deepcopy(lis):
	'''Deep copies a list to the third level'''
	ret = []
	for i in lis:
		if isinstance(i, (list, tuple)):
			reti = []
			for j in i:
				if isinstance(j, (list, tuple)):
					retj = []
					for k in j:
						retj.append(k)
					reti.append(retj)
				else:
					reti.append(j)
			ret.append(reti)
		else:
			ret.append(i)
	return ret