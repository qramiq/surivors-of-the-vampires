import pygame
import time
import random
import json
import os
import math
from constants import WIDTH, HEIGHT, WHITE, BLACK, GREEN, GOLD, RED, BLUE, WARRIOR, MAGE, ARCHER, SAVE_FILE
from entities import Player, Enemy, Item, Coin, Projectile, MeleeAttack
from ui import StartScreen, CharacterSelect, Shop, Statistics, Settings, Button

CHUNK_SIZE = 800
RENDER_DISTANCE = 2

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return pygame.Rect(entity.rect.x - self.camera.x, entity.rect.y - self.camera.y, entity.rect.width, entity.rect.height)

    def update(self, target):
        self.camera.x = target.rect.centerx - self.width // 2
        self.camera.y = target.rect.centery - self.height // 2

class Chunk:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x * CHUNK_SIZE, y * CHUNK_SIZE, CHUNK_SIZE, CHUNK_SIZE)
        self.enemies = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()

class Game:
    upgrades = {}

    def __init__(self, screen, clock, font):
        self.screen = screen
        self.clock = clock
        self.font = font
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.melee_attacks = pygame.sprite.Group()
        self.player = None
        self.camera = Camera(WIDTH, HEIGHT)
        self.chunks = {}
        self.score = 0
        self.coins_collected = 0
        self.total_coins = 0
        self.game_over = False
        self.current_screen = "menu"
        self.start_screen = StartScreen(font)
        self.character_select = CharacterSelect(font)
        self.shop = Shop(font, Game.upgrades)
        self.statistics = Statistics(font)
        self.settings = Settings(font)
        self.stats = {"Games Played": 0, "Total Score": 0, "Highest Score": 0}
        Game.upgrades = {}
        self.load_game_data()
        self.quit_game = False
        self.wave_timer = 0
        self.wave_interval = 5  # Spawn new wave every 5 seconds
        self.game_start_time = 0
        self.load_assets()
        self.show_hitboxes = False
        self.background = self.create_background()

    def load_assets(self):
        # Ensure the assets directory exists
        if not os.path.exists("assets"):
            os.makedirs("assets")
        
        # List of required sprite files
        required_sprites = [
            "warrior_sprite.png",
            "mage_sprite.png",
            "archer_sprite.png",
            "enemy_sprite.png",
            "item_sprite.png",
            "coin_sprite.png",
            "projectile_sprite.png",
            "melee_attack_sprite.png"
        ]
        
        # Create placeholder images if they don't exist
        for sprite_name in required_sprites:
            if not os.path.exists(f"assets/{sprite_name}"):
                image = pygame.Surface((64, 64))
                image.fill((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
                pygame.image.save(image, f"assets/{sprite_name}")
                print(f"Created placeholder for {sprite_name}")

    def create_background(self):
        background = pygame.Surface((CHUNK_SIZE, CHUNK_SIZE))
        small_rect_size = 50
        colors = [(100, 100, 100), (80, 80, 80)]
        for y in range(0, CHUNK_SIZE, small_rect_size):
            for x in range(0, CHUNK_SIZE, small_rect_size):
                rect = pygame.Rect(x, y, small_rect_size, small_rect_size)
                color = colors[(x // small_rect_size + y // small_rect_size) % 2]
                pygame.draw.rect(background, color, rect)
        return background

    def run(self):
        self.quit_game = False
        while not self.quit_game:
            self.clock.tick(60)
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
        return False  # Indicate that the game should close

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game = True
                return

            if self.current_screen == "menu":
                result = self.start_screen.handle_event(event)
                if result:
                    self.current_screen = result
            elif self.current_screen == "character_select":
                character_type = self.character_select.handle_event(event)
                if character_type:
                    self.reset_game(character_type)
                    self.current_screen = "game"
            elif self.current_screen == "shop":
                result = self.shop.handle_event(event, self.total_coins)
                if isinstance(result, tuple):
                    if result[0] == "menu":
                        self.current_screen = "menu"
                        Game.upgrades = result[1]
                        self.save_game_data()  # Save game data when returning to menu
                    elif result[0] == "reset":
                        self.total_coins += result[1]  # Add the refund to total_coins
                        Game.upgrades = {key: 0 for key in Game.upgrades}  # Reset all upgrades to 0
                        if self.player:
                            self.apply_upgrades()  # Reapply upgrades (which will now all be 0)
                        self.save_game_data()  # Save game data after resetting upgrades
                    else:
                        self.total_coins, Game.upgrades = result
                        self.total_coins = int(self.total_coins)
                        if self.player:
                            self.apply_upgrades()
                        self.save_game_data()  # Save game data after purchasing upgrades
            elif self.current_screen == "stats":
                result = self.statistics.handle_event(event)
                if result:
                    self.current_screen = result
            elif self.current_screen == "settings":
                result = self.settings.handle_event(event, self.show_hitboxes)
                if result == "toggle_hitboxes":
                    self.show_hitboxes = not self.show_hitboxes
                elif result == "menu":
                    self.current_screen = "menu"
            elif self.current_screen == "game":
                if self.game_over and event.type == pygame.MOUSEBUTTONDOWN:
                    if self.restart_button.is_clicked(event.pos):
                        self.current_screen = "character_select"
                    elif self.menu_button.is_clicked(event.pos):
                        self.current_screen = "menu"

    def update(self):
        if self.current_screen == "game" and not self.game_over and self.player:
            keys = pygame.key.get_pressed()
            dx = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            dy = keys[pygame.K_DOWN] - keys[pygame.K_UP]
            self.player.move(dx, dy)

            self.camera.update(self.player)

            current_time = time.time()
            self.wave_timer += self.clock.get_time() / 1000  # Convert to seconds

            if self.wave_timer >= self.wave_interval:
                self.spawn_enemy_wave()
                self.wave_timer = 0

            self.spawn_item()
            self.spawn_coin()

            new_attack = self.player.update(self.enemies)
            if new_attack:
                if isinstance(new_attack, Projectile):
                    self.projectiles.add(new_attack)
                    self.all_sprites.add(new_attack)
                elif isinstance(new_attack, MeleeAttack):
                    self.melee_attacks.add(new_attack)
                    self.all_sprites.add(new_attack)

            for enemy in self.enemies:
                if pygame.sprite.collide_circle(self.player, enemy):
                    self.player.health -= 10
                    enemy.kill()
                    if self.player.health <= 0:
                        self.game_over = True
                        self.total_coins += self.coins_collected
                        self.stats["Games Played"] += 1
                        self.stats["Total Score"] += self.score
                        self.stats["Highest Score"] = max(self.stats["Highest Score"], self.score)
                        self.save_game_data()

            for item in pygame.sprite.spritecollide(self.player, self.items, True):
                self.score += 10
                self.player.experience += 10
                if self.player.experience >= self.player.level * 100:
                    self.player.level += 1
                    self.player.experience = 0
                    self.player.health = min(self.player.max_health, self.player.health + 20)

            for coin in pygame.sprite.spritecollide(self.player, self.coins, True):
                self.coins_collected += 1

            for projectile in self.projectiles:
                for enemy in pygame.sprite.spritecollide(projectile, self.enemies, False, pygame.sprite.collide_circle):
                    if enemy.take_damage(projectile.damage):
                        enemy.kill()
                        self.score += 5
                        self.player.experience += 5
                        if self.player.experience >= self.player.level * 100:
                            self.player.level += 1
                            self.player.experience = 0
                            self.player.health = min(self.player.max_health, self.player.health + 20)
                    projectile.kill()

            for melee_attack in self.melee_attacks:
                for enemy in pygame.sprite.spritecollide(melee_attack, self.enemies, False, pygame.sprite.collide_circle):
                    if enemy.take_damage(melee_attack.damage):
                        enemy.kill()
                        self.score += 5
                        self.player.experience += 5
                        if self.player.experience >= self.player.level * 100:
                            self.player.level += 1
                            self.player.experience = 0
                            self.player.health = min(self.player.max_health, self.player.health + 20)

            # Update all sprites
            for sprite in self.all_sprites:
                if isinstance(sprite, Enemy):
                    sprite.update(self.player)
                elif sprite != self.player:
                    sprite.update()

            self.update_chunks()

    def draw(self):
        self.screen.fill(BLACK)
        if self.current_screen == "game":
            self.draw_background()
            for sprite in self.all_sprites:
                self.screen.blit(sprite.image, self.camera.apply(sprite))
            if self.show_hitboxes:
                self.draw_hitboxes()
            self.draw_ui()
        elif self.current_screen == "menu":
            self.start_screen.draw(self.screen)
        elif self.current_screen == "character_select":
            self.character_select.draw(self.screen)
        elif self.current_screen == "shop":
            self.shop.draw(self.screen, self.total_coins)
        elif self.current_screen == "stats":
            self.statistics.draw(self.screen, self.stats)
        elif self.current_screen == "settings":
            self.settings.draw(self.screen, self.show_hitboxes)

    def draw_background(self):
        start_x = self.camera.camera.x % -CHUNK_SIZE
        start_y = self.camera.camera.y % -CHUNK_SIZE

        for y in range(start_y, HEIGHT, CHUNK_SIZE):
            for x in range(start_x, WIDTH, CHUNK_SIZE):
                self.screen.blit(self.background, (x, y))

    def draw_hitboxes(self):
        for sprite in self.all_sprites:
            if hasattr(sprite, 'radius'):
                hitbox_rect = self.camera.apply(sprite)
                pygame.draw.circle(self.screen, RED, hitbox_rect.center, sprite.radius, 1)

    def draw_ui(self):
        health_text = self.font.render(f"Health: {self.player.health}/{self.player.max_health}", True, WHITE)
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        coins_text = self.font.render(f"Coins: {self.coins_collected}", True, GOLD)
        level_text = self.font.render(f"Level: {self.player.level}", True, WHITE)
        exp_text = self.font.render(f"EXP: {self.player.experience}/{self.player.level * 100}", True, WHITE)

        self.screen.blit(health_text, (10, 10))
        self.screen.blit(score_text, (10, 40))
        self.screen.blit(coins_text, (10, 70))
        self.screen.blit(level_text, (10, 100))
        self.screen.blit(exp_text, (10, 130))

        # Draw timer
        elapsed_time = int(time.time() - self.game_start_time)
        minutes, seconds = divmod(elapsed_time, 60)
        timer_text = self.font.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)
        timer_rect = timer_text.get_rect(center=(WIDTH // 2, 30))
        self.screen.blit(timer_text, timer_rect)

        if self.game_over:
            game_over_text = self.font.render("Game Over", True, RED)
            self.screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
            self.restart_button.draw(self.screen)
            self.menu_button.draw(self.screen)

    def spawn_enemy_wave(self):
        num_enemies = min(5 + self.player.level, 20)  # Increase enemies with player level, max 20
        for _ in range(num_enemies):
            enemy = Enemy(self.get_spawn_position())
            chunk = self.get_chunk(enemy.rect.centerx, enemy.rect.centery)
            chunk.enemies.add(enemy)
            self.enemies.add(enemy)
            self.all_sprites.add(enemy)

    def get_spawn_position(self):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(WIDTH, WIDTH * 1.5)
        x = self.player.rect.centerx + math.cos(angle) * distance
        y = self.player.rect.centery + math.sin(angle) * distance
        return x, y

    def spawn_item(self):
        if random.random() < 0.02:
            item = Item(self.player.rect.center if self.player else None)
            chunk = self.get_chunk(item.rect.centerx, item.rect.centery)
            chunk.items.add(item)
            self.items.add(item)
            self.all_sprites.add(item)

    def spawn_coin(self):
        if random.random() < 0.01:
            coin = Coin(self.player.rect.center if self.player else None)
            chunk = self.get_chunk(coin.rect.centerx, coin.rect.centery)
            chunk.coins.add(coin)
            self.coins.add(coin)
            self.all_sprites.add(coin)

    def get_chunk(self, x, y):
        chunk_x = int(x // CHUNK_SIZE)
        chunk_y = int(y // CHUNK_SIZE)
        if (chunk_x, chunk_y) not in self.chunks:
            self.chunks[(chunk_x, chunk_y)] = Chunk(chunk_x, chunk_y)
        return self.chunks[(chunk_x, chunk_y)]

    def update_chunks(self):
        player_chunk_x = int(self.player.rect.centerx // CHUNK_SIZE)
        player_chunk_y = int(self.player.rect.centery // CHUNK_SIZE)

        for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for dy in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                chunk_x = player_chunk_x + dx
                chunk_y = player_chunk_y + dy
                if (chunk_x, chunk_y) not in self.chunks:
                    self.chunks[(chunk_x, chunk_y)] = Chunk(chunk_x, chunk_y)

        # Remove far chunks
        chunks_to_remove = []
        for chunk_pos, chunk in self.chunks.items():
            if (abs(chunk_pos[0] - player_chunk_x) > RENDER_DISTANCE or
                abs(chunk_pos[1] - player_chunk_y) > RENDER_DISTANCE):
                chunks_to_remove.append(chunk_pos)

        for chunk_pos in chunks_to_remove:
            chunk = self.chunks.pop(chunk_pos)
            self.enemies.remove(chunk.enemies)
            self.items.remove(chunk.items)
            self.coins.remove(chunk.coins)
            self.all_sprites.remove(chunk.enemies, chunk.items, chunk.coins)

    def reset_game(self, character_type):
        self.all_sprites.empty()
        self.enemies.empty()
        self.items.empty()
        self.coins.empty()
        self.projectiles.empty()
        self.melee_attacks.empty()
        self.chunks.clear()
        self.player = Player(character_type)
        self.all_sprites.add(self.player)
        self.camera = Camera(WIDTH, HEIGHT)
        self.camera.update(self.player)  # Center the camera on the player
        self.score = 0
        self.coins_collected = 0
        self.game_over = False
        self.wave_timer = 0
        self.game_start_time = time.time()
        self.apply_upgrades()
        self.restart_button = Button(WIDTH // 2 - 100, HEIGHT // 2, 200, 50, "Restart", GREEN, BLACK)
        self.menu_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 50, "Main Menu", GREEN, BLACK)

    def load_game_data(self):
        try:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                self.total_coins = int(data.get('total_coins', 0))
                self.stats = data.get('stats', {"Games Played": 0, "Total Score": 0, "Highest Score": 0})
                Game.upgrades =Game.upgrades = data.get('upgrades', {})
                self.shop.upgrades = Game.upgrades
        except FileNotFoundError:
            self.total_coins = 0
            self.stats = {"Games Played": 0, "Total Score": 0, "Highest Score": 0}
            Game.upgrades = {}

        # Ensure all upgrade types exist in Game.upgrades
        for item in self.shop.items:
            if item['name'] not in Game.upgrades:
                Game.upgrades[item['name']] = 0

    def save_game_data(self):
        data = {
            'total_coins': self.total_coins,
            'stats': self.stats,
            'upgrades': self.shop.upgrades
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)

    def apply_upgrades(self):
        if self.player:
            self.player.max_health = 100 + Game.upgrades.get("Health Up", 0) * 20
            self.player.health = self.player.max_health
            self.player.speed = 5 + Game.upgrades.get("Speed Up", 0) * 0.5
            self.player.damage = 10 + Game.upgrades.get("Damage Up", 0) * 5
            self.player.attack_speed = 1.0 + Game.upgrades.get("Attack Speed Up", 0) * 0.1
            self.player.cooldown_reduction = Game.upgrades.get("Cooldown Reduction", 0) * 0.05
            self.player.set_attack_interval()

