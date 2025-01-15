import pygame
import random
import math
from constants import WIDTH, HEIGHT, WHITE, BLACK, RED, GREEN, BLUE, WARRIOR, MAGE, ARCHER, GOLD

class Player(pygame.sprite.Sprite):
    def __init__(self, character_type):
        super().__init__()
        self.character_type = character_type
        self.original_image = None
        self.load_sprite()
        self.rect = self.image.get_rect()
        self.radius = int(min(self.rect.width, self.rect.height) * 0.25)  # Circular hitbox, 25% of sprite size
        self.rect.center = (0, 0)  # Start at the center of the world
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.damage = 10
        self.experience = 0
        self.level = 1
        self.attack_range = 100
        self.attack_cooldown = 0
        self.attack_speed = 1.0
        self.cooldown_reduction = 0.0
        self.attack_interval = self.get_attack_cooldown()
        self.set_attack_interval()

    def load_sprite(self):
        sprite_size = (64, 64)  # Increased size for better visibility
        try:
            if self.character_type == WARRIOR:
                self.original_image = pygame.image.load("assets/warrior_sprite.png").convert_alpha()
            elif self.character_type == MAGE:
                self.original_image = pygame.image.load("assets/mage_sprite.png").convert_alpha()
            elif self.character_type == ARCHER:
                self.original_image = pygame.image.load("assets/archer_sprite.png").convert_alpha()
            else:
                raise ValueError(f"Invalid character type: {self.character_type}")
        
            self.original_image = pygame.transform.scale(self.original_image, sprite_size)
        except (pygame.error, FileNotFoundError):
            print(f"Error loading {self.character_type.lower()}_sprite.png. Using fallback sprite.")
            self.original_image = pygame.Surface(sprite_size, pygame.SRCALPHA)
            pygame.draw.circle(self.original_image, BLUE, (sprite_size[0]//2, sprite_size[1]//2), sprite_size[0]//2)
        self.image = self.original_image

    def get_attack_cooldown(self):
        if self.character_type == WARRIOR:
            return 30  # 0.5 seconds at 60 FPS
        elif self.character_type == MAGE:
            return 45  # 0.75 seconds at 60 FPS
        elif self.character_type == ARCHER:
            return 40  # 0.67 seconds at 60 FPS
        else:
            return 60  # Default to 1 second if character type is unknown

    def set_attack_interval(self):
        base_interval = self.get_attack_cooldown()
        self.attack_interval = int(base_interval / self.attack_speed * (1 - self.cooldown_reduction))

    def move(self, dx, dy):
        if self.original_image is not None:
            if dx < 0:  # Moving left
                self.image = pygame.transform.flip(self.original_image, True, False)
            elif dx > 0:  # Moving right
                self.image = pygame.transform.flip(self.original_image, False, False)
        
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed

    def update(self, enemies):
        self.attack_cooldown = max(0, self.attack_cooldown - 1)
        if self.attack_cooldown == 0 and enemies:
            nearest_enemy = min(enemies, key=lambda e: math.hypot(e.rect.centerx - self.rect.centerx, e.rect.centery - self.rect.centery))
            if math.hypot(nearest_enemy.rect.centerx - self.rect.centerx, nearest_enemy.rect.centery - self.rect.centery) <= self.attack_range:
                self.attack_cooldown = self.attack_interval
                return self.attack(nearest_enemy)
        return None

    def attack(self, target):
        dx = target.rect.centerx - self.rect.centerx
        dy = target.rect.centery - self.rect.centery
        angle = math.atan2(dy, dx)
        speed = 5
        return Projectile(self.rect.centerx, self.rect.centery, math.cos(angle) * speed, math.sin(angle) * speed, self.damage, self.attack_range)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, spawn_position):
        super().__init__()
        self.load_sprite()
        self.rect = self.image.get_rect()
        self.radius = int(min(self.rect.width, self.rect.height) * 0.25)  # Circular hitbox, 25% of sprite size
        self.rect.center = spawn_position
        self.speed = random.uniform(1, 3)
        self.health = 30

    def load_sprite(self):
        sprite_size = (48, 48)  # Slightly smaller than the player
        try:
            self.original_image = pygame.image.load("assets/enemy_sprite.png").convert_alpha()
            self.original_image = pygame.transform.scale(self.original_image, sprite_size)
        except pygame.error:
            print("Error loading enemy_sprite.png. Using fallback sprite.")
            self.original_image = pygame.Surface(sprite_size, pygame.SRCALPHA)
            pygame.draw.circle(self.original_image, RED, (sprite_size[0]//2, sprite_size[1]//2), sprite_size[0]//2)
        self.image = self.original_image

    def update(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
    
        if dx < 0:  # Moving left
            self.image = pygame.transform.flip(self.original_image, True, False)
        elif dx > 0:  # Moving right
            self.image = pygame.transform.flip(self.original_image, False, False)

        if dist != 0:
            dx, dy = dx / dist, dy / dist
            self.rect.x += dx * self.speed
            self.rect.y += dy * self.speed

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0

class Item(pygame.sprite.Sprite):
    def __init__(self, player_pos):
        super().__init__()
        self.load_sprite()
        self.rect = self.image.get_rect()
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(WIDTH // 2, WIDTH)
        self.rect.centerx = player_pos[0] + math.cos(angle) * distance
        self.rect.centery = player_pos[1] + math.sin(angle) * distance

    def load_sprite(self):
        sprite_size = (32, 32)
        try:
            self.image = pygame.image.load("assets/item_sprite.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, sprite_size)
        except pygame.error:
            print("Error loading item_sprite.png. Using fallback sprite.")
            self.image = pygame.Surface(sprite_size)
            self.image.fill(GREEN)  # Use green color for item

class Coin(pygame.sprite.Sprite):
    def __init__(self, player_pos):
        super().__init__()
        self.load_sprite()
        self.rect = self.image.get_rect()
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(WIDTH // 2, WIDTH)
        self.rect.centerx = player_pos[0] + math.cos(angle) * distance
        self.rect.centery = player_pos[1] + math.sin(angle) * distance

    def load_sprite(self):
        sprite_size = (16, 16)
        try:
            self.image = pygame.image.load("assets/coin_sprite.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, sprite_size)
        except pygame.error:
            print("Error loading coin_sprite.png. Using fallback sprite.")
            self.image = pygame.Surface(sprite_size)
            self.image.fill(GOLD)  # Use gold color for coin

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy, damage, range):
        super().__init__()
        self.load_sprite()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.range = range
        self.distance_traveled = 0

    def load_sprite(self):
        sprite_size = (16, 16)
        try:
            self.image = pygame.image.load("assets/projectile_sprite.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, sprite_size)
        except pygame.error:
            print("Error loading projectile_sprite.png. Using fallback sprite.")
            self.image = pygame.Surface(sprite_size)
            self.image.fill(WHITE)  # Use white color for projectile

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.distance_traveled += math.hypot(self.dx, self.dy)
        if self.distance_traveled >= self.range:
            self.kill()

class MeleeAttack(pygame.sprite.Sprite):
    def __init__(self, x, y, damage):
        super().__init__()
        self.load_sprite()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.damage = damage
        self.lifetime = 5

    def load_sprite(self):
        sprite_size = (64, 64)
        try:
            self.image = pygame.image.load("assets/melee_attack_sprite.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, sprite_size)
        except pygame.error:
            print("Error loading melee_attack_sprite.png. Using fallback sprite.")
            self.image = pygame.Surface(sprite_size, pygame.SRCALPHA)
            pygame.draw.circle(self.image, WHITE + (100,), (sprite_size[0]//2, sprite_size[1]//2), sprite_size[0]//2)
        self.image.set_alpha(100)

    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

