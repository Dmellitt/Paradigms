import pygame, math

FPS = 60

class Laser(pygame.sprite.Sprite):
    def __init__(self):
        self.source = pygame.image.load('laser.png')
        self.rect = self.source.get_rect()
        self.active = False
        self.xVel = 0
        self.yVel = 0

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
            char = chr(event.key)
            if char == self.controls[0]:
                self.rot = self.rotSpeed
            elif char == self.controls[1]:
                self.rot = -self.rotSpeed
            elif char == self.controls[2]:
                self.accel = -self.thrust
            elif char == self.controls[3]:
                self.accel = self.thrust
            elif char == self.controls[4]:
                for a in self.lasers:
                    if not a.active:
                        a.fire(self.rect.centerx, self.rect.centery, self.angle)
                        break
        elif event.type == pygame.KEYUP:
            char = chr(event.key)
            if char == self.controls[0] and self.rot > 0:
                self.rot = 0
            elif char == self.controls[1] and self.rot < 0:
                self.rot = 0
            elif char == self.controls[2] and self.accel < 0:
                self.accel = 0
            elif char == self.controls[3] and self.accel > 0:
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
            

class GameSpace:
    def main(self):
        pygame.init()
        self.size = self.width, self.height = 1000, 700
        self.black = 0,0,0
        self.screen = pygame.display.set_mode(self.size)

        self.player = Player(self, 'ship.png', 'adws ', 0, 0)
        self.player2 = Player(self, 'ship2.png', 'ĔēđĒ.', 500, 300)
        self.clock = pygame.time.Clock()

        done = False
        while not done:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
                else:
                    self.player.handle(event)
                    self.player2.handle(event)

            self.player.tick(self.player2)
            self.player2.tick(self.player)

            self.screen.fill(self.black)
            self.player.show()
            self.player2.show()
                
            pygame.display.update()
            self.clock.tick(FPS)

if __name__ == "__main__":
    gs = GameSpace()
    gs.main()
