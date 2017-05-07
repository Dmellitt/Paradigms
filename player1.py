# -*- coding: utf-8 -*-

from twisted.internet.protocol import Protocol, Factory, ClientFactory
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
import json
import pygame, math

FPS = 60

class Laser(pygame.sprite.Sprite):
	def __init__(self):
		self.source = pygame.image.load('laser.png')
		self.rect = self.source.get_rect()
		self.active = False
		self.xVel = 0
		self.yVel = 0
		self.frameCount = 0
		self.angle = 0
	def fire(self, x, y, angle):
		self.active = True
		self.frameCount = 0
		self.angle = angle+180
		self.rect.center = x+40*math.sin(math.radians(self.angle)), y+40*math.cos(math.radians(self.angle))

	def move(self, ship):
		if self.active:
			self.rect.center = self.rect.centerx+1200/FPS*math.sin(math.radians(self.angle)), self.rect.centery+1200/FPS*math.cos(math.radians(self.angle))
			if self.rect.colliderect(ship.rect):
				ship.getHit()
				self.active = False
			self.frameCount+=1
			if self.frameCount >= FPS*1:
				self.active = False

class Player(pygame.sprite.Sprite):
	def __init__(self, space, file, controls, x, y):
		self.space = space
		self.source = pygame.image.load(file)
		self.fire = pygame.image.load('fire.png')
		self.controls = controls
		self.lasers = []
		self.health = 100
		self.source = pygame.transform.scale(self.source, (self.health, self.health))
		self.fire = pygame.transform.scale(self.fire, (self.health, self.health))
		self.rect = self.source.get_rect()
		self.rect.x = x
		self.rect.y = y
		for a in range(5):
			self.lasers.append(Laser())
		self.thrust = 2000
		self.rotSpeed = 400
		self.accel = 0
		self.xVel = 0
		self.yVel = 0
		self.rot = 0
		self.angle = 0

	def getHit(self):
		if self.health <= 0:
			return
		self.health -= 20
		if self.health <= 0:
			self.image = pygame.image.load('explosion/frames000a.png')
			self.rect = self.image.get_rect(center=self.rect.center)
			self.accel = 0
			self.count = 0
			self.frame = 1
		else:
			self.source = pygame.transform.scale(self.source, (self.health, self.health))
			self.fire = pygame.transform.scale(self.fire, (self.health, self.health))
			self.rect = self.source.get_rect(center=self.rect.center)


	def handle(self, event):
		if self.health <= 0:
			return

		if event.type == pygame.KEYDOWN:
			char = event.key
			if char == pygame.K_a:
				self.rot = self.rotSpeed
			elif char == pygame.K_d:
				self.rot = -self.rotSpeed
			elif char == pygame.K_w:
				self.accel = -self.thrust
			elif char == pygame.K_s:
				self.accel = self.thrust
			elif char == pygame.K_SPACE:
				for a in self.lasers:
					if not a.active:
						a.fire(self.rect.centerx, self.rect.centery, self.angle)
						break
		elif event.type == pygame.KEYUP:
			char = event.key
			if char == pygame.K_a and self.rot > 0:
				self.rot = 0
			elif char == pygame.K_d and self.rot < 0:
				self.rot = 0
			elif char == pygame.K_w and self.accel < 0:
				self.accel = 0
			elif char == pygame.K_s and self.accel > 0:
				self.accel = 0

	def rotate(self):
		self.angle += self.rot/FPS
		self.image = pygame.transform.rotate(self.source, self.angle)
		self.fireImage = pygame.transform.rotate(self.fire, self.angle)
		rot_rect = self.rect.copy()
		rot_rect.center = self.image.get_rect().center
		self.image = self.image.subsurface(rot_rect) 
		self.fireImage = self.fireImage.subsurface(rot_rect) 

	def move(self, ship):
		self.xVel += self.accel/FPS*math.sin(math.radians(self.angle))
		self.yVel += self.accel/FPS*math.cos(math.radians(self.angle))

		self.rect.x += int(self.xVel/FPS)
		if self.rect.x < 0 or self.rect.right > self.space.width or (self.rect.colliderect(ship.rect) and ship.health > 0):
			self.rect.x -= int(self.xVel/FPS)
			self.xVel = 0

		self.rect.y += int(self.yVel/FPS)
		if self.rect.y < 0 or self.rect.bottom > self.space.height or (self.rect.colliderect(ship.rect) and ship.health > 0):
			self.rect.y -= int(self.yVel/FPS)
			self.yVel = 0

	def tick(self, other):
		for a in self.lasers:
			a.move(other)
		if self.health > 0:
			self.move(other)
			self.rotate()
		else:
			if self.frame==17:
				return
			self.count+=1
			if self.count == FPS/20*self.frame:
				if self.frame == 16:
					self.image = pygame.image.load('empty.png')
					self.rect = self.image.get_rect()
					self.rect.x = -10
					self.rect.y = -10
				elif self.frame < 10:
					self.image = pygame.image.load('explosion/frames00'+str(self.frame)+'a.png')
				else:
					self.image = pygame.image.load('explosion/frames0'+str(self.frame)+'a.png')

				self.frame += 1

	def update(self, data):
		try:
			print ('player 1 sending info to player2')
			self.courier = Holder(self)
			self.lasersHolder = []
			for l in self.lasers:
				self.lasersHolder.append(LaserContainer(l).__dict__)
			self.sendData = [self.courier.__dict__, self.lasersHolder]
			print json.dumps(self.sendData)
			self.space.dataFactory.dataConn.forwardData(json.dumps(self.sendData))
		except Exception as err:
			print(err)

	def updatePlayer2(self, input):
		try:
			print('updating opponent player data')
			temp = json.loads(input)
			data = temp[0]
			lasers = temp[1]
			self.space.player2.rect.x = data['x']
			self.space.player2.rect.y = data['y']
			self.space.player2.xVel = data['xVel']
			self.space.player2.yVel = data['yVel']
			self.space.player2.accel = data['accel']
			self.space.player2.rot = data['rot']
			self.space.player2.angle = data['angle']
			self.space.player2.health = data['health']
			for a in range(5):
				self.space.player2.lasers[a].rect.x = lasers[a]['x']
				self.space.player2.lasers[a].rect.y = lasers[a]['y']
				self.space.player2.lasers[a].angle = lasers[a]['angle']
				self.space.player2.lasers[a].xVel = lasers[a]['xVel']
				self.space.player2.lasers[a].yVel = lasers[a]['yVel']
				self.space.player2.lasers[a].frameCount = lasers[a]['frameCount']
				self.space.player2.lasers[a].active = lasers[a]['active']

			self.space.player2.source = pygame.transform.scale(self.source, (self.health, self.health))
			self.space.player2.fire = pygame.transform.scale(self.fire, (self.health, self.health))
			self.space.player2.rect = self.source.get_rect(center=self.rect.center)

		except Exception as err:
			print(err)

	def show(self):
		for a in self.lasers:
			if a.active:
				self.space.screen.blit(a.source, a.rect)
		self.space.screen.blit(self.image, self.rect)
		if self.accel < 0:
			self.space.screen.blit(self.fireImage, self.rect)
		elif self.accel > 0:
			self.fireImage = pygame.transform.rotate(self.fireImage, 180)
			self.space.screen.blit(self.fireImage, self.rect)

class Holder():
	def __init__(self, player):
		print('player 1 made holder class')
		self.health = player.health
		self.x = player.rect.x
		self.y = player.rect.y
		self.accel = player.accel
		self.xVel = player.xVel
		self.yVel = player.yVel
		self.rot = player.rot
		self.angle = player.angle
#		self.lasers = []
#		for l in player.lasers:
#			self.lasers.append(LaserContainer(l))
class LaserContainer():
	def __init__(self,laser):
		self.xVel = laser.xVel
		self.yVel = laser.yVel
		self.active = laser.active
		self.angle = laser.angle
		self.x = laser.rect.x
		self.y = laser.rect.y
		self.frameCount = laser.frameCount

class GameSpace:
	def __init__(self):
		print('player 1 initializing game space')
		pygame.init()
		self.size = self.width, self.height = 1000, 700
		self.black = 0,0,0
		self.screen = pygame.display.set_mode(self.size)
		self.player = Player(self, 'ship.png', 'adws ', 0, 0)
#		#self.player2 = Enemy(self, 'ship2.png', 'ĔēđĒ.', 500, 300)
		self.clock = pygame.time.Clock()
		#Show initial player on screen waiting for player 2
		self.player.rotate()
#		self.screen.fill(self.black)
#		self.player.show()


	def run_game(self):
		event_loop = LoopingCall(self.main)
		update_player2 = LoopingCall(self.player.update,"data\r\n\r\n")
		event_loop.start(1/FPS) #run loop every 1/FPS seconds
		update_player2.start(5)

	def main(self):
		print('running')
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				done = True
			else:
				self.player.handle(event)

		self.player.tick(self.player2)
		self.player2.tick(self.player)

		self.screen.fill(self.black)
		self.player.show()
		self.player2.show()

		pygame.display.update()
		self.clock.tick(FPS)

# TCP Connection to other player
class DataConnection(Protocol):
	def __init__(self, space):
		self.space = space;
	def forwardData(self, data):
		print ('Player 1 sending data: '),data
		self.transport.write(data)
	def dataReceived(self, data):
		print ('Player 1 Received data:'), data
		self.space.player2.updatePlayer2(data)
	def connectionMade(self):
		print('Player 2 has connected')
		self.space.player2 = Player(self.space, 'ship2.png', 'ĔēđĒ.', 500, 300)
		self.space.run_game()										#start game

class DataConnectionFactory(Factory):
	def __init__(self, space):
		self.space = space
		self.dataConn = DataConnection(self.space)
		self.space.dataFactory = self
		print('creating data connection from player 1')
	def buildProtocol(self, addr):
		return self.dataConn

if __name__ == "__main__":
	gs = GameSpace()
	reactor.listenTCP(40022, DataConnectionFactory(gs))
	reactor.run()




