# Future imports
from __future__ import annotations

# Standard modules
import random
from typing import List, Tuple

# External modules
import pygame
from pygame.math import Vector2


class Entity:
    """Class that forms the basis of all moving game objects. Can be drawn to the screen and move."""

    # Entity HP
    PLAYER_HP: int = 100
    ENEMY_HP: int = 1
    PROJECTILE_HP: int = 1

    # Spawn location index
    PLAYER_SPAWN: int = 0
    ENEMY_LEFT_SPAWN: int = 1
    ENEMY_MIDDLE_SPAWN: int = 2
    ENEMY_RIGHT_SPAWN: int = 3

    # Spawn locations
    spawn_position: List[Tuple[int, int]] = [
        (6 + 25, 132),
        (10, 4),
        (35, 4),
        (60, 4),
    ]

    def __init__(self, position: Vector2, sprite_path: str, hp: int):
        """Main constructor for entities. Specialised constructors are probably more useful.

        Parameters
        ----------
        position : Vector2
            a list of the x coordinate and the y coordinate of the entity's position.
        sprite_path : str
            the path to the sprite of the entity. Must be valid.
        hp : int
            the initial HP of the entity.
        """
        # Load sprite
        self._sprite = pygame.image.load(sprite_path)
        # Collision box used in collision detection. Based off the entity's sprite.
        self._collision_box = self._sprite.get_rect()[2::]
        # Current position
        self._position = position
        # Entity health
        self._hp = hp

    # Access methods
    @property
    def position(self):
        """pygame.math.Vector2: the position vector of the entity."""
        return self._position

    @property
    def x(self):
        """int: the x coordinate of the entity's position."""
        return self._position[0]

    @x.setter
    def x(self, new_value: int):
        self._position[0] = new_value

    @property
    def y(self):
        """int: the y coordinate of the entity's position."""
        return self._position[1]

    @y.setter
    def y(self, new_value: int):
        self._position[1] = new_value

    @property
    def width(self):
        """int: the width of the entity's sprite."""
        return self._collision_box[0]

    @property
    def height(self):
        """int: the height of the entity's sprite."""
        return self._collision_box[1]

    @property
    def hp(self):
        """int: the current health of the entity."""
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = value if value >= 0 else self._hp

    @property
    def sprite_position(self):
        """Tuple[pygame.Surface, Vector2]: the sprite and current position of the entity."""
        return (self._sprite, self._position)

    def detect_collision(self, other: Entity):
        """Detects collision between entities, returing `True` if a collision has occurred, otherwise `False`, assuming all
        collision boxes are rectangles.

        Parameters
        ----------
        other : Entity
            other entity involved the potential collision.

        Returns
        -------
        result : bool
            `True` if collision has occurred else `False`.
        """
        return self.x > other.x and self.x < (other.x + other.width) and self.y > other.y and self.y < (other.y + other.height)

    # Constructors
    @classmethod
    def spawn_player(cls):
        """Constructs an entity corresponding to the player.

        Returns
        -------
        player: Entity
            the player entity.
        """
        return Entity(Vector2(cls.spawn_position[cls.PLAYER_SPAWN]), "assets/player.png", cls.PLAYER_HP)

    @classmethod
    def spawn_enemy(cls, lane_index: int):
        """Constructs an entity corresponding to an enemy.

        Parameters
        ----------
        lane_index: int
            the index of the lane the enemy should spawn in going from 1 -> 3.

        Returns
        -------
        enemy: Entity
            the enemy entity spawned at the starting position of the given lane.
        """
        return Entity(Vector2(cls.spawn_position[lane_index]), "assets/enemy.png", cls.ENEMY_HP)

    @classmethod
    def spawn_enemy_random(cls):
        """Constructs an entity corresponding to an enemy in a random lane.

        Returns
        -------
        enemy: Entity
            the enemy entity spawned at the starting position of a random lane.
        """
        lane_index = random.randint(1, 3)
        return Entity(Vector2(cls.spawn_position[lane_index]), "assets/enemy.png", cls.ENEMY_HP)

    @classmethod
    def spawn_projectile(cls, position: Vector2):
        """Constructs an entity corresponding to a player projectile.

        Parameters
        ----------
        position: Vector2
            the spawn position of the projectile.

        Returns
        -------
        projectile: Entity
            the projectile entity.
        """
        return Entity(position, "assets/projectile.png", cls.PROJECTILE_HP)
