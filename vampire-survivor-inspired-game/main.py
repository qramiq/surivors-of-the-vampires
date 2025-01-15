import pygame
import json
import os
from game import Game
from constants import WIDTH, HEIGHT, SAVE_FILE

def load_game_data():
    default_upgrades = {"Health Up": 0, "Speed Up": 0, "Damage Up": 0}
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            upgrades = data.get('upgrades', default_upgrades)
            for key in default_upgrades:
                if key not in upgrades:
                    upgrades[key] = 0
            return (
                data.get('total_coins', 0),
                data.get('stats', {"Games Played": 0, "Total Score": 0, "Highest Score": 0}),
                upgrades
            )
    return 0, {"Games Played": 0, "Total Score": 0, "Highest Score": 0}, default_upgrades

def save_game_data(total_coins, stats, upgrades):
    data = {
        'total_coins': total_coins,
        'stats': stats,
        'upgrades': upgrades
    }
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f)

def main():
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Survivors of the Vampires")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    total_coins, stats, upgrades = load_game_data()

    game = Game(screen, clock, font)
    game.total_coins = total_coins
    game.stats = stats
    Game.upgrades = upgrades

    running = True
    while running:
        game.run()
        save_game_data(game.total_coins, game.stats, Game.upgrades)
        
        play_again = ask_play_again(screen, font)
        if not play_again:
            running = False

    pygame.quit()

def ask_play_again(screen, font):
    text = font.render("Play again? (Y/N)", True, (255, 255, 255))
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    screen.fill((0, 0, 0))
    screen.blit(text, text_rect)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    return True
                elif event.key == pygame.K_n:
                    return False

    return False

if __name__ == "__main__":
    main()

