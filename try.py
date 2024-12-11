import pygame
import random
from collections import deque, defaultdict
import sys

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900  # Increased height for labels, scores, and graph
GAME_AREA_WIDTH = SCREEN_WIDTH // 2
GAME_AREA_HEIGHT = 600
BLOCK_SIZE = 20
INITIAL_SNAKE_SPEED = 0.3  # Initial snake moves every 0.3 seconds
SPEED_INCREMENT = 0.05  # Speed increases by 0.05 seconds per level
LEVEL_UP_SCORE = 3  # Increase speed every 3 points
BLINK_DURATION = 0.5  # Duration of blink when losing size (in seconds)
MIN_SNAKE_LENGTH = 1  # Minimum length before the snake dies

# Colors
WHITE = (255, 255, 255)
BLACK = (18, 18, 18)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 155, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (40, 40, 40)
BLINK_COLOR = (255, 255, 255)
BLUE = (0, 102, 204)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)

# Initialize pygame
pygame.init()
window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Game: Player vs AI Competition")
clock = pygame.time.Clock()

# Fonts
FONT_SMALL = pygame.font.Font(None, 28)
FONT_MEDIUM = pygame.font.Font(None, 36)
FONT_LARGE = pygame.font.Font(None, 48)
FONT_XLARGE = pygame.font.Font(None, 72)

# Load Sounds
try:
    EAT_SOUND = pygame.mixer.Sound('eat.wav')
    GAME_OVER_SOUND = pygame.mixer.Sound('game_over.wav')
    PAUSE_SOUND = pygame.mixer.Sound('pause.wav')
except:
    EAT_SOUND = None
    GAME_OVER_SOUND = None
    PAUSE_SOUND = None
    print("Sound files not found. Continuing without sound.")


class SnakeGame:
    def __init__(self, x_offset, y_offset, width, height, block_size, is_ai=False, direction_tracker=None):
        self.x_offset = x_offset  # X position offset for rendering
        self.y_offset = y_offset  # Y position offset for rendering
        self.width = width // block_size
        self.height = height // block_size
        self.block_size = block_size
        self.is_ai = is_ai
        self.direction_tracker = direction_tracker if direction_tracker else defaultdict(int)
        self.reset()
        self.speed = INITIAL_SNAKE_SPEED  # Starting speed
        self.is_blinking = False  # Whether snake is blinking
        self.blink_end_time = 0  # When the blink should end
        self.visible = True  # Visibility state for blinking

    def reset(self):
        self.snake_pos = deque([[self.width // 2, self.height // 2]])
        self.direction = 'RIGHT'
        self.spawn_food()
        self.done = False
        self.score = 0
        self.speed = INITIAL_SNAKE_SPEED
        self.is_blinking = False
        self.blink_end_time = 0
        self.visible = True
        if self.is_ai:
            self.ai_direction = 'LEFT'  # Initial direction for AI

    def spawn_food(self):
        while True:
            self.food_pos = [random.randint(1, self.width - 2), random.randint(1, self.height - 2)]
            if self.food_pos not in self.snake_pos:
                break

    def step(self):
        head = self.snake_pos[0].copy()

        # Determine the new position of the snake's head based on direction
        if self.direction == 'RIGHT':
            head[0] += 1
        elif self.direction == 'LEFT':
            head[0] -= 1
        elif self.direction == 'DOWN':
            head[1] += 1
        else:  # UP
            head[1] -= 1

        # Check if the snake has hit the boundary
        if head[0] < 0 or head[0] >= self.width or head[1] < 0 or head[1] >= self.height:
            # Instead of game over, reduce the snake size and trigger blink effect
            if len(self.snake_pos) > MIN_SNAKE_LENGTH:
                self.snake_pos.pop()  # Lose one segment
                self.trigger_blink()  # Trigger the blink effect
                return True  # Continue game
            else:
                self.done = True
                if GAME_OVER_SOUND:
                    GAME_OVER_SOUND.play()
                return False  # Game over if only one segment is left

        # Check if the snake has hit itself
        if head in self.snake_pos:
            self.done = True
            if GAME_OVER_SOUND:
                GAME_OVER_SOUND.play()
            return False  # Game over

        self.snake_pos.appendleft(head)

        # Check if the snake has eaten food
        if head == self.food_pos:
            self.score += 1
            if EAT_SOUND:
                EAT_SOUND.play()
            self.spawn_food()
            self.check_level_up()  # Check if we need to increase the speed
        else:
            self.snake_pos.pop()

        return True  # Continue game

    def change_direction(self, new_direction):
        if new_direction == 'RIGHT' and not self.direction == 'LEFT':
            self.direction = new_direction
        elif new_direction == 'LEFT' and not self.direction == 'RIGHT':
            self.direction = new_direction
        elif new_direction == 'UP' and not self.direction == 'DOWN':
            self.direction = new_direction
        elif new_direction == 'DOWN' and not self.direction == 'UP':
            self.direction = new_direction

    def check_level_up(self):
        # Every LEVEL_UP_SCORE points, increase the speed
        if self.score % LEVEL_UP_SCORE == 0:
            self.speed = max(self.speed - SPEED_INCREMENT, 0.1)  # Increase speed (lower time between moves)

    def trigger_blink(self):
        self.is_blinking = True
        self.blink_end_time = pygame.time.get_ticks() / 1000 + BLINK_DURATION  # Blink for BLINK_DURATION seconds

    def render(self, surface):
        # Draw the boundary box
        pygame.draw.rect(surface, WHITE, pygame.Rect(self.x_offset, self.y_offset, self.width * self.block_size,
                                                     self.height * self.block_size), 2)

        # Draw the grid
        self.draw_grid(surface)

        # Draw the snake, handle blinking effect
        if self.is_blinking:
            current_time = pygame.time.get_ticks() / 1000
            if current_time < self.blink_end_time:
                # Toggle visibility every 100 ms
                if int(current_time * 10) % 2 == 0:
                    self.visible = False
                else:
                    self.visible = True
            else:
                self.is_blinking = False
                self.visible = True

        for i, (x, y) in enumerate(self.snake_pos):
            if not self.visible:
                continue  # Skip drawing to create blink effect
            color = DARK_GREEN if i == 0 else GREEN  # Head is darker
            pygame.draw.rect(surface, color,
                             pygame.Rect(self.x_offset + x * self.block_size, self.y_offset + y * self.block_size,
                                         self.block_size, self.block_size))

        # Draw the food
        pygame.draw.rect(surface, RED,
                         pygame.Rect(self.x_offset + self.food_pos[0] * self.block_size,
                                     self.y_offset + self.food_pos[1] * self.block_size,
                                     self.block_size, self.block_size))

    def draw_grid(self, surface):
        # Vertical lines
        for x in range(0, self.width * self.block_size, self.block_size):
            pygame.draw.line(surface, GRAY,
                             (self.x_offset + x, self.y_offset),
                             (self.x_offset + x, self.y_offset + self.height * self.block_size))
        # Horizontal lines
        for y in range(0, self.height * self.block_size, self.block_size):
            pygame.draw.line(surface, GRAY,
                             (self.x_offset, self.y_offset + y),
                             (self.x_offset + self.width * self.block_size, self.y_offset + y))

    def ai_decision(self):
        """
        AI moves towards the food while avoiding collisions.
        It adapts based on player's direction choices.
        """
        if self.done:
            return

        head = self.snake_pos[0]
        food = self.food_pos

        # Possible directions
        possible_directions = []
        if head[0] < self.width - 1:
            possible_directions.append('RIGHT')
        if head[0] > 0:
            possible_directions.append('LEFT')
        if head[1] < self.height - 1:
            possible_directions.append('DOWN')
        if head[1] > 0:
            possible_directions.append('UP')

        # Remove directions that would cause collision with itself
        safe_directions = []
        for direction in possible_directions:
            new_head = head.copy()
            if direction == 'RIGHT':
                new_head[0] += 1
            elif direction == 'LEFT':
                new_head[0] -= 1
            elif direction == 'DOWN':
                new_head[1] += 1
            elif direction == 'UP':
                new_head[1] -= 1
            if new_head not in self.snake_pos:
                safe_directions.append(direction)

        if not safe_directions:
            # No safe directions, continue current direction
            return

        # Adjust AI direction probabilities based on player's direction choices
        # Favor directions that the player uses less frequently
        direction_weights = {}
        total = 0
        for direction in safe_directions:
            # The less the player uses this direction, the higher the weight
            weight = 1 / (self.direction_tracker[direction] + 1)
            direction_weights[direction] = weight
            total += weight

        # Normalize weights and choose direction probabilistically
        rnd = random.uniform(0, total)
        upto = 0
        chosen_direction = self.direction  # Default to current direction
        for direction, weight in direction_weights.items():
            if upto + weight >= rnd:
                chosen_direction = direction
                break
            upto += weight

        self.change_direction(chosen_direction)


def draw_text(surface, text, size, x, y, color=WHITE, center=True):
    if size == 28:
        font = FONT_SMALL
    elif size == 36:
        font = FONT_MEDIUM
    elif size == 48:
        font = FONT_LARGE
    elif size == 72:
        font = FONT_XLARGE
    else:
        font = FONT_SMALL
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)


def game_over_screen(surface, player_score, player_level, ai_score, ai_level, high_scores):
    surface.fill(BLACK)
    draw_text(surface, "Game Over", 72, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200, YELLOW)
    draw_text(surface, f"Player Score: {player_score} | Level: {player_level}", 36, SCREEN_WIDTH // 4,
              SCREEN_HEIGHT // 2 - 80, WHITE)
    draw_text(surface, f"AI Score: {ai_score} | Level: {ai_level}", 36, 3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 - 80,
              WHITE)
    draw_text(surface, f"High Scores - Player: {high_scores['player']} | AI: {high_scores['ai']}", 36,
              SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20, ORANGE)
    draw_text(surface, "Press R to Restart or Q to Quit", 28, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60, WHITE)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    waiting = False
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
        clock.tick(15)


def draw_graph(surface, direction_counts, x_offset, y_offset, width, height):
    # Draw graph background
    pygame.draw.rect(surface, LIGHT_BLUE, (x_offset, y_offset, width, height))
    pygame.draw.rect(surface, WHITE, (x_offset, y_offset, width, height), 2)

    # Define graph properties
    padding = 20
    graph_width = width - 2 * padding
    graph_height = height - 2 * padding
    bar_width = graph_width // 4 - padding

    directions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
    max_count = max(direction_counts.values()) if direction_counts.values() else 1

    for i, direction in enumerate(directions):
        count = direction_counts.get(direction, 0)
        # Calculate bar height
        bar_height = (count / max_count) * (graph_height - padding) if max_count > 0 else 0
        # Define bar position
        bar_x = x_offset + padding + i * (bar_width + padding)
        bar_y = y_offset + height - padding - bar_height
        # Choose color based on direction
        color = {
            'UP': BLUE,
            'DOWN': RED,
            'LEFT': GREEN,
            'RIGHT': YELLOW
        }.get(direction, WHITE)
        # Draw bar
        pygame.draw.rect(surface, color, (bar_x, bar_y, bar_width, bar_height))
        # Draw direction label
        draw_text(surface, direction, 28, bar_x + bar_width // 2, y_offset + height - padding + 10, WHITE)
        # Draw count label
        draw_text(surface, str(count), 28, bar_x + bar_width // 2, bar_y - 20, WHITE)


def update_high_scores(high_scores, player_score, ai_score):
    if player_score > high_scores['player']:
        high_scores['player'] = player_score
    if ai_score > high_scores['ai']:
        high_scores['ai'] = ai_score
    return high_scores


def main():
    # Initialize direction tracker
    player_direction_tracker = defaultdict(int)

    # Initialize two game areas: left for human, right for AI
    human_game = SnakeGame(x_offset=50, y_offset=100, width=GAME_AREA_WIDTH - 100, height=GAME_AREA_HEIGHT,
                           block_size=BLOCK_SIZE, is_ai=False, direction_tracker=player_direction_tracker)
    ai_game = SnakeGame(x_offset=GAME_AREA_WIDTH + 50, y_offset=100, width=GAME_AREA_WIDTH - 100,
                        height=GAME_AREA_HEIGHT, block_size=BLOCK_SIZE, is_ai=True)

    # High scores
    high_scores = {'player': 0, 'ai': 0}

    # Game state
    running = True
    last_move_time_human = 0
    last_move_time_ai = 0
    paused = False

    while running:
        current_time = pygame.time.get_ticks() / 1000  # Current time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle direction change based on keypress for human player
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    human_game.change_direction('LEFT')
                    player_direction_tracker['LEFT'] += 1
                elif event.key == pygame.K_RIGHT:
                    human_game.change_direction('RIGHT')
                    player_direction_tracker['RIGHT'] += 1
                elif event.key == pygame.K_UP:
                    human_game.change_direction('UP')
                    player_direction_tracker['UP'] += 1
                elif event.key == pygame.K_DOWN:
                    human_game.change_direction('DOWN')
                    player_direction_tracker['DOWN'] += 1
                elif event.key == pygame.K_p:
                    paused = not paused  # Toggle pause
                    if PAUSE_SOUND:
                        PAUSE_SOUND.play()

        if not paused:
            # Move human snake only after enough time has passed
            if current_time - last_move_time_human > human_game.speed and not human_game.done:
                if not human_game.step():  # If the snake hits boundary or itself
                    high_scores = update_high_scores(high_scores, human_game.score, ai_game.score)
                    game_over_screen(window, human_game.score, human_game.score // LEVEL_UP_SCORE + 1,
                                     ai_game.score, ai_game.score // LEVEL_UP_SCORE + 1, high_scores)
                    human_game.reset()
                    ai_game.reset()
                last_move_time_human = current_time  # Reset the timer after each move

            # AI decision and movement
            if current_time - last_move_time_ai > ai_game.speed and not ai_game.done:
                ai_game.ai_decision()  # Determine AI direction
                if not ai_game.step():
                    high_scores = update_high_scores(high_scores, human_game.score, ai_game.score)
                    game_over_screen(window, human_game.score, human_game.score // LEVEL_UP_SCORE + 1,
                                     ai_game.score, ai_game.score // LEVEL_UP_SCORE + 1, high_scores)
                    human_game.reset()
                    ai_game.reset()
                last_move_time_ai = current_time

        # Render the game
        window.fill(BLACK)

        # Draw labels above each game area
        draw_text(window, "Player", 36, human_game.x_offset + (human_game.width * human_game.block_size) // 2, 50, BLUE)
        draw_text(window, "AI", 36, ai_game.x_offset + (ai_game.width * ai_game.block_size) // 2, 50, RED)

        # Render both games
        human_game.render(window)
        ai_game.render(window)

        # Draw scores and levels below each game area
        player_level = human_game.score // LEVEL_UP_SCORE + 1
        ai_level = ai_game.score // LEVEL_UP_SCORE + 1
        draw_text(window, f"Score: {human_game.score}", 28,
                  human_game.x_offset + (human_game.width * human_game.block_size) // 2, GAME_AREA_HEIGHT + 130, WHITE)
        draw_text(window, f"Level: {player_level}", 28,
                  human_game.x_offset + (human_game.width * human_game.block_size) // 2, GAME_AREA_HEIGHT + 160, WHITE)
        draw_text(window, f"Score: {ai_game.score}", 28, ai_game.x_offset + (ai_game.width * ai_game.block_size) // 2,
                  GAME_AREA_HEIGHT + 130, WHITE)
        draw_text(window, f"Level: {ai_level}", 28, ai_game.x_offset + (ai_game.width * ai_game.block_size) // 2,
                  GAME_AREA_HEIGHT + 160, WHITE)

        # Draw the learning graph
        graph_width = SCREEN_WIDTH - 100
        graph_height = 200
        graph_x_offset = 50
        graph_y_offset = GAME_AREA_HEIGHT + 300
        pygame.draw.rect(window, WHITE, (graph_x_offset, graph_y_offset - 2, graph_width, graph_height + 4),
                         2)  # Graph border
        draw_text(window, "AI Learning from Player's Moves", 36, SCREEN_WIDTH // 2, graph_y_offset - 50, ORANGE,
                  center=True)
        draw_graph(window, player_direction_tracker, graph_x_offset, graph_y_offset, graph_width, graph_height)

        # Display pause message
        if paused:
            draw_text(window, "Paused", 72, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, YELLOW, center=True)

        pygame.display.flip()
        clock.tick(60)  # Maintain 60 FPS

    pygame.quit()


if __name__ == "__main__":
    main()
