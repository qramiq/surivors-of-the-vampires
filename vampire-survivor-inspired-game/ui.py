import pygame
from constants import WIDTH, HEIGHT, WHITE, BLACK, GREEN, GOLD, RED, WARRIOR, MAGE, ARCHER

class Button:
    def __init__(self, x, y, width, height, text, color, text_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        font = pygame.font.Font(None, 36)
        text = font.render(self.text, True, self.text_color)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class StartScreen:
    def __init__(self, font):
        self.font = font
        self.title = self.font.render("Vampire Survivors Inspired Game", True, WHITE)
        self.start_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50, "Start Game", GREEN, BLACK)
        self.shop_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50, "Shop", GREEN, BLACK)
        self.stats_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 90, 200, 50, "Statistics", GREEN, BLACK)
        self.settings_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 160, 200, 50, "Settings", GREEN, BLACK)

    def draw(self, screen):
        screen.fill(BLACK)
        screen.blit(self.title, (WIDTH // 2 - self.title.get_width() // 2, HEIGHT // 4))
        self.start_button.draw(screen)
        self.shop_button.draw(screen)
        self.stats_button.draw(screen)
        self.settings_button.draw(screen)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button.is_clicked(event.pos):
                return "character_select"
            elif self.shop_button.is_clicked(event.pos):
                return "shop"
            elif self.stats_button.is_clicked(event.pos):
                return "stats"
            elif self.settings_button.is_clicked(event.pos):
                return "settings"
        return None

class CharacterSelect:
    def __init__(self, font):
        self.font = font
        self.title = self.font.render("Select Your Character", True, WHITE)
        self.warrior_button = Button(WIDTH // 2 - 250, HEIGHT // 2, 150, 50, WARRIOR, GREEN, BLACK)
        self.mage_button = Button(WIDTH // 2 - 75, HEIGHT // 2, 150, 50, MAGE, GREEN, BLACK)
        self.archer_button = Button(WIDTH // 2 + 100, HEIGHT // 2, 150, 50, ARCHER, GREEN, BLACK)

    def draw(self, screen):
        screen.fill(BLACK)
        screen.blit(self.title, (WIDTH // 2 - self.title.get_width() // 2, HEIGHT // 4))
        self.warrior_button.draw(screen)
        self.mage_button.draw(screen)
        self.archer_button.draw(screen)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.warrior_button.is_clicked(event.pos):
                return WARRIOR
            elif self.mage_button.is_clicked(event.pos):
                return MAGE
            elif self.archer_button.is_clicked(event.pos):
                return ARCHER
        return None

class Shop:
    def __init__(self, font, upgrades):
        self.font = font
        self.upgrades = upgrades
        self.items = [
            {"name": "Health Up", "base_cost": 10, "effect": lambda player, level: setattr(player, "max_health", player.max_health + 20 * level)},
            {"name": "Speed Up", "base_cost": 15, "effect": lambda player, level: setattr(player, "speed", player.speed + 0.5 * level)},
            {"name": "Damage Up", "base_cost": 20, "effect": lambda player, level: setattr(player, "damage", player.damage + 5 * level)},
            {"name": "Attack Speed Up", "base_cost": 25, "effect": lambda player, level: setattr(player, "attack_speed", player.attack_speed + 0.1 * level)},
            {"name": "Cooldown Reduction", "base_cost": 30, "effect": lambda player, level: setattr(player, "cooldown_reduction", player.cooldown_reduction + 0.05 * level)},
        ]
        self.buttons = []
        self.update_buttons()
        self.back_button = Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 40, "Back to Menu", GREEN, BLACK)
        self.reset_button = Button(WIDTH // 2 - 100, HEIGHT - 160, 200, 40, "Reset Upgrades", RED, WHITE)

    def update_buttons(self):
        self.buttons = [
            Button(WIDTH // 2 - 200, HEIGHT // 2 - 150 + i * 60, 400, 40, f"{item['name']} (Cost: {self.calculate_cost(i)})", GREEN, BLACK)
            for i, item in enumerate(self.items)
        ]

    def calculate_cost(self, index):
        base_cost = self.items[index]['base_cost']
        level = self.upgrades.get(self.items[index]['name'], 0)
        return int(base_cost * (1.5 ** level))

    def reset_upgrades(self):
        refund = sum(self.calculate_refund(item['name']) for item in self.items)
        for item in self.items:
            self.upgrades[item['name']] = 0
        self.update_buttons()
        return refund

    def calculate_refund(self, upgrade_name):
        level = self.upgrades.get(upgrade_name, 0)
        base_cost = next(item['base_cost'] for item in self.items if item['name'] == upgrade_name)
        return sum(int(base_cost * (1.5 ** i)) for i in range(level))

    def draw(self, screen, total_coins):
        screen.fill(BLACK)
        title_text = self.font.render("Shop", True, WHITE)
        coins_text = self.font.render(f"Total Coins: {total_coins}", True, GOLD)
        screen.blit(title_text, (WIDTH // 2 - 50, 70))
        screen.blit(coins_text, (WIDTH // 2 - 100, 120))

        for i, button in enumerate(self.buttons):
            button.draw(screen)
            level_text = self.font.render(f"Level: {self.upgrades.get(self.items[i]['name'], 0)}", True, WHITE)
            screen.blit(level_text, (button.rect.right + 10, button.rect.centery - 10))

        self.back_button.draw(screen)
        self.reset_button.draw(screen)

    def handle_purchase(self, total_coins, button_index):
        if button_index < len(self.items):
            item = self.items[button_index]
            cost = self.calculate_cost(button_index)
            if total_coins >= cost:
                self.upgrades[item['name']] = self.upgrades.get(item['name'], 0) + 1
                total_coins -= cost
                self.update_buttons()
                return total_coins, self.upgrades
        return total_coins, self.upgrades

    def handle_event(self, event, total_coins):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, button in enumerate(self.buttons):
                if button.is_clicked(event.pos):
                    return self.handle_purchase(total_coins, i)
            if self.back_button.is_clicked(event.pos):
                return "menu", self.upgrades
            if self.reset_button.is_clicked(event.pos):
                refund = self.reset_upgrades()
                return ("reset", refund)
        return total_coins, self.upgrades

class Statistics:
    def __init__(self, font):
        self.font = font
        self.back_button = Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 40, "Back to Menu", GREEN, BLACK)

    def draw(self, screen, stats):
        screen.fill(BLACK)
        title_text = self.font.render("Statistics", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - 70, 70))

        y = 150
        for key, value in stats.items():
            text = self.font.render(f"{key}: {value}", True, WHITE)
            screen.blit(text, (WIDTH // 2 - 100, y))
            y += 50

        self.back_button.draw(screen)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.is_clicked(event.pos):
                return "menu"
        return None

class Settings:
    def __init__(self, font):
        self.font = font
        self.title = self.font.render("Settings", True, WHITE)
        self.hitbox_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50, "Toggle Hitboxes", GREEN, BLACK)
        self.back_button = Button(WIDTH // 2 - 100, HEIGHT - 100, 200, 40, "Back to Menu", GREEN, BLACK)

    def draw(self, screen, show_hitboxes):
        screen.fill(BLACK)
        screen.blit(self.title, (WIDTH // 2 - self.title.get_width() // 2, HEIGHT // 4))
        self.hitbox_button.draw(screen)
        self.back_button.draw(screen)

        hitbox_status = "ON" if show_hitboxes else "OFF"
        status_text = self.font.render(f"Hitboxes: {hitbox_status}", True, WHITE)
        screen.blit(status_text, (WIDTH // 2 - status_text.get_width() // 2, HEIGHT // 2 + 50))

    def handle_event(self, event, show_hitboxes):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hitbox_button.is_clicked(event.pos):
                return "toggle_hitboxes"
            elif self.back_button.is_clicked(event.pos):
                return "menu"
        return None

