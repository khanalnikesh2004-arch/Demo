import pygame
import random
import math
import os
import sys

pygame.init()

# ============================================================
# SOUND
# ============================================================

try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except pygame.error:
    SOUND_ENABLED = False


# ============================================================
# WINDOW
# ============================================================

WIDTH = 900
HEIGHT = 650

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Garden")

clock = pygame.time.Clock()


# ============================================================
# COLORS
# ============================================================

GRASS = (58, 128, 52)
GRASS_LIGHT = (78, 150, 65)
GRASS_DARK = (38, 92, 38)

BLACK = (8, 8, 8)
WHITE = (245, 245, 245)

RED = (210, 38, 38)
RED_LIGHT = (255, 90, 90)

YELLOW = (250, 220, 70)

BROWN = (105, 65, 30)

BUTTON = (30, 78, 35)
BUTTON_HOVER = (50, 110, 50)

SELECTED = (70, 135, 65)


# ============================================================
# SETTINGS
# ============================================================

CELL = 20
BORDER = 20
GAME_TOP = 70

START_SPEED = 5.0
SPEED_INCREASE = 0.55
MAX_SPEED = 17

POINTS_PER_APPLE = 10

HIGH_SCORE_FILE = "highscore.txt"


# ============================================================
# FONTS
# ============================================================

font_small = pygame.font.SysFont(
    "Arial",
    20
)

font_medium = pygame.font.SysFont(
    "Arial",
    28,
    bold=True
)

font_large = pygame.font.SysFont(
    "Arial",
    55,
    bold=True
)

font_huge = pygame.font.SysFont(
    "Arial",
    76,
    bold=True
)


# ============================================================
# SOUND
# ============================================================

def make_sound(frequency, duration):

    if not SOUND_ENABLED:
        return None

    sample_rate = 44100
    samples = int(
        sample_rate * duration
    )

    buffer = bytearray()

    for i in range(samples):

        value = int(
            32767
            * math.sin(
                2 * math.pi
                * frequency
                * i
                / sample_rate
            )
        )

        buffer.extend(
            value.to_bytes(
                2,
                "little",
                signed=True
            )
        )

    return pygame.mixer.Sound(
        buffer=bytes(buffer)
    )


eat_sound = make_sound(650, 0.07)
level_sound = make_sound(900, 0.10)
gameover_sound = make_sound(150, 0.25)


# ============================================================
# HIGH SCORE
# ============================================================

def load_highscore():

    if os.path.exists(HIGH_SCORE_FILE):

        try:

            with open(
                HIGH_SCORE_FILE,
                "r"
            ) as file:

                return int(
                    file.read()
                )

        except:
            return 0

    return 0


def save_highscore(score):

    try:

        with open(
            HIGH_SCORE_FILE,
            "w"
        ) as file:

            file.write(
                str(score)
            )

    except:
        pass


# ============================================================
# BUTTON
# ============================================================

class Button:

    def __init__(
        self,
        x,
        y,
        width,
        height,
        text
    ):

        self.rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        self.text = text

    def draw(
        self,
        selected=False,
        pulse=False
    ):

        mouse = pygame.mouse.get_pos()

        hovered = self.rect.collidepoint(
            mouse
        )

        if selected or hovered:
            color = BUTTON_HOVER
        else:
            color = BUTTON

        rect = self.rect.copy()

        if pulse:

            amount = int(
                math.sin(
                    pygame.time.get_ticks()
                    * 0.005
                ) * 3
            )

            rect.inflate_ip(
                amount,
                amount
            )

            rect.center = self.rect.center

        pygame.draw.rect(
            screen,
            color,
            rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            WHITE,
            rect,
            2,
            border_radius=12
        )

        text = font_medium.render(
            self.text,
            True,
            WHITE
        )

        screen.blit(
            text,
            (
                rect.centerx
                - text.get_width() // 2,
                rect.centery
                - text.get_height() // 2
            )
        )

    def clicked(self, event):

        return (
            event.type
            == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(
                event.pos
            )
        )


# ============================================================
# GRASS
# ============================================================

grass_blades = []

random.seed(25)

for _ in range(350):

    grass_blades.append(
        (
            random.randint(
                0,
                WIDTH
            ),
            random.randint(
                70,
                HEIGHT
            ),
            random.random()
            * math.pi
            * 2,
            random.uniform(
                0.7,
                1.3
            )
        )
    )


def draw_grass(time):

    screen.fill(GRASS)

    for x, y, phase, scale in grass_blades:

        sway = math.sin(
            time * 0.002
            + phase
        ) * 3

        pygame.draw.line(
            screen,
            GRASS_DARK,
            (
                x,
                y
            ),
            (
                x + sway,
                y - 8 * scale
            ),
            2
        )

    # Floating particles
    for i in range(25):

        px = (
            i * 73
            + time * 0.015
        ) % WIDTH

        py = (
            i * 47
            + math.sin(
                time * 0.001
                + i
            ) * 20
        ) % HEIGHT

        pygame.draw.circle(
            screen,
            GRASS_LIGHT,
            (
                int(px),
                int(py)
            ),
            2
        )


# ============================================================
# FOOD
# ============================================================

def create_food(snake):

    while True:

        x = random.randrange(
            BORDER + CELL,
            WIDTH - BORDER - CELL,
            CELL
        )

        y = random.randrange(
            GAME_TOP + BORDER,
            HEIGHT - BORDER - CELL,
            CELL
        )

        food = (
            x,
            y
        )

        if food not in snake:
            return food


# ============================================================
# SNAKE
# ============================================================

class Snake:

    def __init__(self):

        self.positions = [
            [400, 330],
            [380, 330],
            [360, 330],
            [340, 330]
        ]

        self.direction = [
            1,
            0
        ]

        self.target_direction = [
            1,
            0
        ]

        self.move_progress = 0

        self.speed = START_SPEED

    def set_direction(
        self,
        dx,
        dy
    ):

        if (
            dx == -self.direction[0]
            and dy == -self.direction[1]
        ):
            return

        self.target_direction = [
            dx,
            dy
        ]

    def update(self, dt):

        self.direction = [
            self.target_direction[0],
            self.target_direction[1]
        ]

        distance = (
            self.speed
            * CELL
            * dt
        )

        self.move_progress += distance

        while self.move_progress >= CELL:

            self.move_progress -= CELL

            head = self.positions[0]

            new_head = [
                head[0]
                + self.direction[0] * CELL,

                head[1]
                + self.direction[1] * CELL
            ]

            self.positions.insert(
                0,
                new_head
            )

            self.positions.pop()

    def grow(self):

        tail = self.positions[-1]

        self.positions.append(
            tail.copy()
        )

    def head(self):

        return self.positions[0]

    def draw(self, time):

        for i, pos in enumerate(
            self.positions
        ):

            x = pos[0]
            y = pos[1]

            # ------------------------
            # HEAD
            # ------------------------

            if i == 0:

                bob = math.sin(
                    time * 0.008
                ) * 1.2

                pygame.draw.rect(
                    screen,
                    BLACK,
                    (
                        x,
                        y + bob,
                        CELL,
                        CELL
                    ),
                    border_radius=8
                )

                # Eyes
                if self.direction == [1, 0]:

                    eyes = [
                        (
                            x + 15,
                            y + 5
                        ),
                        (
                            x + 15,
                            y + 15
                        )
                    ]

                elif self.direction == [-1, 0]:

                    eyes = [
                        (
                            x + 5,
                            y + 5
                        ),
                        (
                            x + 5,
                            y + 15
                        )
                    ]

                elif self.direction == [0, -1]:

                    eyes = [
                        (
                            x + 5,
                            y + 5
                        ),
                        (
                            x + 15,
                            y + 5
                        )
                    ]

                else:

                    eyes = [
                        (
                            x + 5,
                            y + 15
                        ),
                        (
                            x + 15,
                            y + 15
                        )
                    ]

                for eye in eyes:

                    pygame.draw.circle(
                        screen,
                        WHITE,
                        eye,
                        3
                    )

                    pygame.draw.circle(
                        screen,
                        BLACK,
                        eye,
                        1
                    )

                # Animated tongue
                tongue = (
                    4
                    + abs(
                        math.sin(
                            time * 0.012
                        )
                    ) * 7
                )

                cx = x + CELL // 2
                cy = y + CELL // 2

                if self.direction == [1, 0]:

                    pygame.draw.line(
                        screen,
                        RED,
                        (
                            x + CELL,
                            cy
                        ),
                        (
                            x + CELL + tongue,
                            cy
                        ),
                        2
                    )

                elif self.direction == [-1, 0]:

                    pygame.draw.line(
                        screen,
                        RED,
                        (
                            x,
                            cy
                        ),
                        (
                            x - tongue,
                            cy
                        ),
                        2
                    )

                elif self.direction == [0, -1]:

                    pygame.draw.line(
                        screen,
                        RED,
                        (
                            cx,
                            y
                        ),
                        (
                            cx,
                            y - tongue
                        ),
                        2
                    )

                else:

                    pygame.draw.line(
                        screen,
                        RED,
                        (
                            cx,
                            y + CELL
                        ),
                        (
                            cx,
                            y + CELL + tongue
                        ),
                        2
                    )

            # ------------------------
            # BODY
            # ------------------------

            else:

                pygame.draw.rect(
                    screen,
                    BLACK,
                    (
                        x,
                        y,
                        CELL,
                        CELL
                    ),
                    border_radius=6
                )


# ============================================================
# APPLE
# ============================================================

class Apple:

    def __init__(self, position):

        self.position = position

        self.spawn_time = (
            pygame.time.get_ticks()
        )

    def draw(self):

        x, y = self.position

        elapsed = (
            pygame.time.get_ticks()
            - self.spawn_time
        )

        # Fast pop-in animation
        pop = min(
            elapsed / 100,
            1
        )

        scale = (
            0.55
            + pop * 0.45
        )

        radius = int(
            9 * scale
        )

        pygame.draw.circle(
            screen,
            RED,
            (
                x + 10,
                y + 12
            ),
            radius
        )

        # Highlight
        pygame.draw.circle(
            screen,
            (255, 105, 105),
            (
                x + 6,
                y + 8
            ),
            2
        )

        # Stem
        pygame.draw.line(
            screen,
            BROWN,
            (
                x + 10,
                y + 5
            ),
            (
                x + 12,
                y
            ),
            2
        )

        # Leaf
        pygame.draw.ellipse(
            screen,
            GRASS_DARK,
            (
                x + 11,
                y - 3,
                9,
                5
            )
        )


# ============================================================
# TOP BAR
# ============================================================

def draw_top_bar(
    score,
    highscore,
    level
):

    pygame.draw.rect(
        screen,
        (
            25,
            65,
            28
        ),
        (
            0,
            0,
            WIDTH,
            GAME_TOP
        )
    )

    score_text = font_medium.render(
        f"SCORE  {score}",
        True,
        WHITE
    )

    best_text = font_medium.render(
        f"BEST  {highscore}",
        True,
        YELLOW
    )

    level_text = font_medium.render(
        f"LEVEL  {level}",
        True,
        WHITE
    )

    screen.blit(
        score_text,
        (20, 18)
    )

    screen.blit(
        best_text,
        (
            WIDTH // 2
            - best_text.get_width() // 2,
            18
        )
    )

    screen.blit(
        level_text,
        (
            WIDTH
            - level_text.get_width()
            - 20,
            18
        )
    )


# ============================================================
# ANIMATED SNAKE FOR MENU
# ============================================================

def draw_preview_snake(time):

    base_x = 330
    base_y = 240

    positions = []

    for i in range(8):

        x = (
            base_x
            + i * 22
        )

        y = (
            base_y
            + math.sin(
                time * 0.003
                + i * 0.5
            ) * 18
        )

        positions.append(
            (
                x,
                y
            )
        )

    for x, y in reversed(
        positions[1:]
    ):

        pygame.draw.circle(
            screen,
            BLACK,
            (
                int(x),
                int(y)
            ),
            10
        )

    hx, hy = positions[0]

    pygame.draw.circle(
        screen,
        BLACK,
        (
            int(hx),
            int(hy)
        ),
        13
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (
            int(hx + 5),
            int(hy - 4)
        ),
        3
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (
            int(hx + 5),
            int(hy + 4)
        ),
        3
    )


# ============================================================
# START SCREEN
# ============================================================

def start_screen():

    start_button = Button(
        WIDTH // 2 - 120,
        390,
        240,
        65,
        "START GAME"
    )

    selected = 0

    while True:

        time = pygame.time.get_ticks()

        draw_grass(time)

        # Dark overlay
        overlay = pygame.Surface(
            (
                WIDTH,
                HEIGHT
            ),
            pygame.SRCALPHA
        )

        overlay.fill(
            (
                0,
                0,
                0,
                40
            )
        )

        screen.blit(
            overlay,
            (0, 0)
        )

        # Animated title
        pulse = (
            math.sin(
                time * 0.003
            ) * 3
        )

        title = font_huge.render(
            "SNAKE",
            True,
            BLACK
        )

        screen.blit(
            title,
            (
                WIDTH // 2
                - title.get_width() // 2,
                85 + pulse
            )
        )

        garden = font_large.render(
            "GARDEN",
            True,
            WHITE
        )

        screen.blit(
            garden,
            (
                WIDTH // 2
                - garden.get_width() // 2,
                155
            )
        )

        # Animated snake
        draw_preview_snake(
            time
        )

        # Subtitle
        subtitle = font_medium.render(
            "Eat. Grow. Survive.",
            True,
            WHITE
        )

        screen.blit(
            subtitle,
            (
                WIDTH // 2
                - subtitle.get_width() // 2,
                320
            )
        )

        # Start button
        start_button.draw(
            selected=(
                selected == 0
            ),
            pulse=True
        )

        pygame.display.update()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            # Mouse
            if start_button.clicked(
                event
            ):

                return

            # Keyboard navigation
            if event.type == pygame.KEYDOWN:

                if event.key in (
                    pygame.K_UP,
                    pygame.K_DOWN
                ):

                    selected = 0

                elif event.key in (
                    pygame.K_RETURN,
                    pygame.K_KP_ENTER
                ):

                    return


# ============================================================
# PAUSE
# ============================================================

def pause_game():

    # No pause screen.
    # Simply wait until SPACE is pressed again.

    while True:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_SPACE:

                    return

        clock.tick(60)


# ============================================================
# GAME OVER MENU
# ============================================================

def game_over(
    score,
    highscore
):

    play_again = Button(
        WIDTH // 2 - 110,
        370,
        220,
        55,
        "PLAY AGAIN"
    )

    menu = Button(
        WIDTH // 2 - 110,
        440,
        220,
        55,
        "MAIN MENU"
    )

    selected = 0

    while True:

        draw_grass(
            pygame.time.get_ticks()
        )

        overlay = pygame.Surface(
            (
                WIDTH,
                HEIGHT
            ),
            pygame.SRCALPHA
        )

        overlay.fill(
            (
                0,
                0,
                0,
                125
            )
        )

        screen.blit(
            overlay,
            (0, 0)
        )

        title = font_large.render(
            "GAME OVER",
            True,
            WHITE
        )

        score_text = font_medium.render(
            f"Score: {score}",
            True,
            WHITE
        )

        best_text = font_medium.render(
            f"Best: {highscore}",
            True,
            YELLOW
        )

        screen.blit(
            title,
            (
                WIDTH // 2
                - title.get_width() // 2,
                165
            )
        )

        screen.blit(
            score_text,
            (
                WIDTH // 2
                - score_text.get_width() // 2,
                255
            )
        )

        screen.blit(
            best_text,
            (
                WIDTH // 2
                - best_text.get_width() // 2,
                300
            )
        )

        play_again.draw(
            selected=(
                selected == 0
            )
        )

        menu.draw(
            selected=(
                selected == 1
            )
        )

        pygame.display.update()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            # Mouse
            if play_again.clicked(
                event
            ):

                return "restart"

            if menu.clicked(
                event
            ):

                return "menu"

            # Keyboard
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_UP:

                    selected = 0

                elif event.key == pygame.K_DOWN:

                    selected = 1

                elif event.key in (
                    pygame.K_RETURN,
                    pygame.K_KP_ENTER
                ):

                    if selected == 0:
                        return "restart"

                    return "menu"


# ============================================================
# GAME
# ============================================================

def play_game(
    highscore
):

    snake = Snake()

    food = Apple(
        create_food(
            snake.positions
        )
    )

    score = 0
    level = 1

    running = True
    paused = False

    while running:

        dt = (
            clock.tick(120)
            / 1000.0
        )

        time = pygame.time.get_ticks()

        # ----------------------------------------
        # EVENTS
        # ----------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # SPACE = PAUSE
                if event.key == pygame.K_SPACE:

                    paused = not paused

                # Movement
                elif not paused:

                    if event.key in (
                        pygame.K_UP,
                        pygame.K_w
                    ):

                        snake.set_direction(
                            0,
                            -1
                        )

                    elif event.key in (
                        pygame.K_DOWN,
                        pygame.K_s
                    ):

                        snake.set_direction(
                            0,
                            1
                        )

                    elif event.key in (
                        pygame.K_LEFT,
                        pygame.K_a
                    ):

                        snake.set_direction(
                            -1,
                            0
                        )

                    elif event.key in (
                        pygame.K_RIGHT,
                        pygame.K_d
                    ):

                        snake.set_direction(
                            1,
                            0
                        )

        # ----------------------------------------
        # PAUSED
        # ----------------------------------------

        if paused:

            draw_grass(time)

            draw_top_bar(
                score,
                highscore,
                level
            )

            food.draw()

            snake.draw(
                time
            )

            # Small pause indicator only
            pause_text = font_medium.render(
                "PAUSED",
                True,
                WHITE
            )

            screen.blit(
                pause_text,
                (
                    WIDTH // 2
                    - pause_text.get_width() // 2,
                    80
                )
            )

            pygame.display.update()

            continue

        # ----------------------------------------
        # MOVE
        # ----------------------------------------

        snake.update(dt)

        head = snake.head()

        # Border
        if (
            head[0] < BORDER
            or head[0] >= WIDTH - BORDER
            or head[1] < GAME_TOP + BORDER
            or head[1] >= HEIGHT - BORDER
        ):

            running = False
            break

        # Self collision
        if head in snake.positions[1:]:

            running = False
            break

        # ----------------------------------------
        # FOOD
        # ----------------------------------------

        if head == list(
            food.position
        ):

            snake.grow()

            score += POINTS_PER_APPLE

            if score > highscore:

                highscore = score

                save_highscore(
                    highscore
                )

            # New level every 50 points
            new_level = (
                score // 50
            ) + 1

            if new_level > level:

                level = new_level

                snake.speed += (
                    SPEED_INCREASE
                )

                if snake.speed > MAX_SPEED:

                    snake.speed = MAX_SPEED

                if (
                    SOUND_ENABLED
                    and level_sound
                ):

                    level_sound.play()

            if (
                SOUND_ENABLED
                and eat_sound
            ):

                eat_sound.play()

            # Immediate new apple
            food = Apple(
                create_food(
                    snake.positions
                )
            )

        # ----------------------------------------
        # DRAW
        # ----------------------------------------

        draw_grass(time)

        draw_top_bar(
            score,
            highscore,
            level
        )

        food.draw()

        snake.draw(
            time
        )

        # Border
        pygame.draw.rect(
            screen,
            GRASS_DARK,
            (
                0,
                GAME_TOP,
                WIDTH,
                HEIGHT - GAME_TOP
            ),
            BORDER
        )

        pygame.display.update()

    # Game over sound
    if (
        SOUND_ENABLED
        and gameover_sound
    ):

        gameover_sound.play()

    return game_over(
        score,
        highscore
    )


# ============================================================
# MAIN
# ============================================================

def main():

    highscore = load_highscore()

    while True:

        start_screen()

        result = play_game(
            highscore
        )

        highscore = load_highscore()

        if result == "restart":

            continue

        elif result == "menu":

            continue


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()

