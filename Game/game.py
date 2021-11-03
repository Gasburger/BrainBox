# Standard modules
import sys
from typing import List, Tuple, Dict

# External modules
import pygame
from pygame.math import Vector2
from serial.serialutil import SerialException

# Internal modules
from constants import *
from entity import Entity
from spikerbox import SpikerBox


class Game:
    """Class that handles game logic, physics and rendering."""

    # Width of the game physics
    WIDTH: int = 74
    # Height of the game physics
    HEIGHT: int = 144

    # Pixel offset from player to spawn projectile
    PROJECTILE_OFFSET: Vector2 = Vector2(5, -6)
    # Pixel offset between lanes for player
    PLAYER_LANE_OFFSET: int = 25

    # Time between enemy spawns
    ENEMY_SPAWN_TIME: float = 3.5
    # Vertical speed of the enemies
    ENEMY_SPEED: float = 3e-2
    # Vertical speed of the projectiles
    PROJECTILE_SPEED: float = 6e-2

    def __init__(
        self,
        keyboard: bool = True,
        model_type: str = RFC,
        stream_type: str = WAVSTREAM,
        stream_file: str = "",
        cport: str = "",
    ):
        """Initialises the game.

        Parameters
        ----------
        keyboard : bool
            if true will use keyboard controls else will use SpikerBox controls.
        cport : str
            the serial port of the SpikerBox.
        """
        self._controls: Dict[str, int] = {
            CONTROL_LEFT: 0,
            CONTROL_RIGHT: 0,
            CONTROL_SHOOT: 0,
        }
        self._player: Entity = Entity.spawn_player()
        self._enemies: List[Entity] = []
        self._projectiles: List[Entity] = []
        self._renderer: Renderer = Renderer(Game.WIDTH, Game.HEIGHT)
        self._spawn_timer: int = pygame.time.get_ticks()
        self.keyboard = keyboard
        self._tick = 0
        try:
            self.spikerbox = SpikerBox(1.5, model_type, stream_type, stream_file=stream_file, cport=cport)
        except SerialException as _:
            print("Invalid serial port. Can only use keyboard controls.")
            self.spikerbox = None

    def update(self):
        """Updates the game by one frame."""
        # Get the time since last frame in milliseconds
        self._tick = self._renderer.tick()
        # Spawn enemy
        self.spawn_enemy()
        # Process input
        self.process_input(keyboard=self.keyboard)
        # Shoot projectiles
        self.shoot_projectile()
        # Update positions
        self.move_entities(self._tick)
        # Handle collisions
        self.handle_collision()

    def draw(self):
        """Draws one frame of the game."""
        self._renderer.draw(self.entities())

    def entities(self):
        """Returns a list of all the game entities.

        Returns
        -------
        entities : List[Tuple[pygame.Surface, Vector2]]
            a list of all the game entities.
        """
        # Player
        all_entities = [self._player.sprite_position]
        # Enemies
        all_entities += [enemy.sprite_position for enemy in self._enemies]
        # Projectiles
        all_entities += [projectile.sprite_position for projectile in self._projectiles]
        return all_entities

    def spawn_enemy(self):
        """Spawns an enemy in a random lane given enough time has passed."""
        if (pygame.time.get_ticks() - self._spawn_timer) / 1000 > Game.ENEMY_SPAWN_TIME:
            self._enemies.append(Entity.spawn_enemy_random())
            self._spawn_timer = pygame.time.get_ticks()

    def process_input(self, keyboard: bool = True):
        """Processes game input."""
        if keyboard or self.spikerbox is None:
            self.process_input_keyboard()
        else:
            self.process_input_spikerbox()

    def process_input_keyboard(self):
        """Processes keyboard input."""
        for event in pygame.event.get():
            # Quit
            if event.type == pygame.QUIT:
                sys.exit()
            # Key down events
            if event.type == pygame.KEYDOWN:
                # Escape
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
                # Left and right controls
                if event.key == pygame.K_LEFT:
                    self._controls[CONTROL_LEFT] = 1
                if event.key == pygame.K_RIGHT:
                    self._controls[CONTROL_RIGHT] = 1
                # Shooting controls
                if event.key == pygame.K_SPACE:
                    self._controls[CONTROL_SHOOT] = 1
                # Fullscreen
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                # Switch to SpikerBox input
                if event.key == pygame.K_F10:
                    self.keyboard = False

    def process_input_spikerbox(self):
        """Processes SpikerBox input."""
        for event in pygame.event.get():
            # Quit
            if event.type == pygame.QUIT:
                sys.exit()
            # Key down events
            if event.type == pygame.KEYDOWN:
                # Escape
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
                # Fullscreen
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                # Switch to keyboard input
                if event.key == pygame.K_F10:
                    self.keyboard = True
        # SpikerBox processing
        self._controls = self.spikerbox.process_input(self._controls, self._tick)

    def shoot_projectile(self):
        """Shoot player projectiles."""
        # Shoot a player projectile
        if self._controls[CONTROL_SHOOT] == 1:
            self._projectiles.append(
                Entity.spawn_projectile(
                    self._player.position + Game.PROJECTILE_OFFSET
                    )
                )
            self._controls[CONTROL_SHOOT] = 0

    def move_entities(self, delta_time: int):
        """Updates the position of entities.

        Paramaters
        ----------
        delta_time: int
            the time since the last frame in milliseconds.
        """
        # Move the player left/right
        if self._controls[CONTROL_LEFT] == 1:
            if self._player.x - Game.PLAYER_LANE_OFFSET >= 0:
                self._player.x -= Game.PLAYER_LANE_OFFSET
            self._controls[CONTROL_LEFT] = 0
        if self._controls[CONTROL_RIGHT] == 1:
            if self._player.x + Game.PLAYER_LANE_OFFSET <= Game.WIDTH:
                self._player.x += Game.PLAYER_LANE_OFFSET
            self._controls[CONTROL_RIGHT] = 0

        # Move enemies down
        for enemy in self._enemies:
            enemy.y += Game.ENEMY_SPEED * delta_time
        # Deleting them if they go out of screen
        self._enemies[:] = [enemy for enemy in self._enemies if enemy.y <= Game.HEIGHT]

        # Move projectiles up
        for projectile in self._projectiles:
            projectile.y -= Game.PROJECTILE_SPEED * delta_time
        # Deleting them if they go out of screen
        self._projectiles[:] = [projectile for projectile in self._projectiles if projectile.y >= 0]

    def handle_collision(self):
        """Detects and handles collision between entities."""
        for enemy in self._enemies:
            for projectile in self._projectiles:
                if projectile.hp > 0 and projectile.detect_collision(enemy):
                    enemy.hp -= 1
                    projectile.hp -= 1
            if enemy.hp > 0 and enemy.detect_collision(self._player):
                self._player.hp -= 1
                enemy.hp -= 1
                if self._player.hp <= 0:
                    self.game_over()

        # Filter out dead enemies and projectiles
        self._enemies[:] = [enemy for enemy in self._enemies if enemy.hp > 0]
        self._projectiles[:] = [projectile for projectile in self._projectiles if projectile.hp > 0]

    def game_over(self):
        """Game over."""
        print("YOU LOST")
        sys.exit()


class Renderer:
    """Class that handles rendering with pygame."""

    def __init__(self, width: int, height: int):
        """Main Renderer constructor.

        Parameters
        ----------
        width : int
            the width of the screen.
        height : int
            the height of the screen.
        """
        pygame.init()
        self.clock = pygame.time.Clock()
        self.window = pygame.display.set_mode((width, height), pygame.SCALED)
        self.screen = pygame.Surface((width, height))

        # Fonts
        self.font = pygame.font.SysFont("Arial", 14)

    def draw(self, entities: List[Tuple[pygame.Surface, Vector2]]):
        """Draw the entities to the screen and handles scaling the screen to the window.

        Parameters
        ----------
        entities: List[Tuple[pygame.Surface, Vector2]]
            a list of all entities' sprite and position to be drawn.
        """
        # Clear background to black
        self.screen.fill((0, 0, 0))
        # Draw all entities
        for entity in entities:
            self.screen.blit(*entity)

        # Display FPS
        display_text = self.font.render(str(int(self.clock.get_fps())), 0, pygame.Color("white"))

        # Draw the screen to the window properly scaled
        self.window.blit(pygame.transform.scale(self.screen, self.window.get_rect().size), (0, 0))
        self.window.blit(display_text, (0, 0))

        # Update the display window
        pygame.display.update()

    def tick(self):
        """Return the time in milliseconds.

        Returns
        -------
        tick : int
            time in milliseconds.
        """
        return self.clock.tick()
