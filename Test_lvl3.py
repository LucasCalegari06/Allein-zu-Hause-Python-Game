import arcade
import math
import random
import os

running_musik = arcade.load_sound(os.path.join(os.path.dirname(os.path.abspath(__file__)),"map/assets/music/Spielmusik.mp3" ))
# Konstanten
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Hausspiel mit Feind"
TILE_SIZE = 16
PLAYER_SPEED = 2.3
ENEMY_SPEED = 3.3
VISION_RANGE = 220  # Maximale Sichtweite des Feindes
VISION_ANGLE = 90   # Sichtkegel in Grad (45 Grad zu jeder Seite)
NOISE_THRESHOLD = 4  # Lärm-Level, bei dem der Feind reagiert
NOISE_MAX = 10  # Maximales Lärm-Level
NOISE_INCREASE = 1  # Erhöhung pro Sekunde Bewegung

class Player(arcade.Sprite):
    def __init__(self):
        super().__init__(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "map/assets/sprite.png"),
            scale=1.0
        )
        self.center_x = 130
        self.center_y = 860
        self.width = 30
        self.height = 30
        self.noise_level = 0
        self.noise_timer = 0
        self.camera = None
        self.has_key1 = False  # Track if player has key1
        self.has_key2 = False  # Track if player has key2
        self.angle = 0  # Initialize angle


class Enemy(arcade.Sprite):
    def __init__(self):
        super().__init__(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "map/assets/gegner.png"),
            scale=1.0
        ) 
        self.center_x = 450  # Start in der Küche
        self.center_y = 128  # Start in der Küche
        self.width = 30
        self.height = 30
        self.waypoint = None
        self.waypoint_timeout = 0
        self.last_position = (self.center_x, self.center_y)
        self.stuck_counter = 0
        self.movement_direction = (0, 0)
        self.vision_active = False
        self.noise_active = False
        self.direction = 0
        self.angle = 0  # Initialize angle


    def draw(self):
        super().draw()
        vision_length = 20
        vision_x = self.center_x + math.cos(math.radians(self.direction)) * vision_length
        vision_y = self.center_y + math.sin(math.radians(self.direction)) * vision_length
        arcade.draw_triangle_filled(
            self.center_x, self.center_y,
            vision_x + 5, vision_y,
            vision_x - 5, vision_y,
            arcade.color.YELLOW
        )

class HouseGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self.player = None
        self.enemy = None
        self.walls = None
        self.objects = None
        self.Ground = None
        self.key1 = None
        self.key2 = None
        self.gate = None
        self.all_sprites = None
        self.physics_engine_player = None
        self.physics_engine_enemy = None
        self.doors = []
        self.rooms = {}
        self.show_message = False
        self.game_Ascending = True
        self.game_over = False
        self.keys_collected = 0
        self.total_keys = 2  # Now requires both keys
        self.show_all_keys_message = False
        self.won_game = False

    def setup(self):
        self.music_player = arcade.play_sound(running_musik, loop=True, volume=1)
        self.all_sprites = arcade.SpriteList()
        self.walls = arcade.SpriteList()
        self.objects = arcade.SpriteList()
        self.Ground = arcade.SpriteList()  
        self.key1 = arcade.SpriteList()
        self.key2 = arcade.SpriteList()
        self.gate = arcade.SpriteList()
        self.player = Player()
        self.all_sprites.append(self.player)
        self.enemy = Enemy()
        self.all_sprites.append(self.enemy)
        self.create_house()
        self.physics_engine_player = arcade.PhysicsEngineSimple(self.player, self.walls)
        self.physics_engine_enemy = arcade.PhysicsEngineSimple(self.enemy, self.walls)
        self.game_over = False
        self.won_game = False
        self.camera = arcade.Camera2D()
        self.keys_collected = 0
        self.show_all_keys_message = False
        self.player.has_key1 = False
        self.player.has_key2 = False

    def create_house(self):
        map_name = os.path.join(os.path.dirname(os.path.abspath(__file__)), "map/tile/lvl3new.tmj")
        try:
            tile_map = arcade.load_tilemap(map_name, scaling=2)
        except Exception as e:
            print(f"Error loading tilemap: {e}")
            return

        # Initialize sprite lists with defaults
        self.walls = tile_map.sprite_lists.get("wall", arcade.SpriteList())
        self.Ground = tile_map.sprite_lists.get("Ground", arcade.SpriteList())
        self.key1 = tile_map.sprite_lists.get("key1", arcade.SpriteList())
        self.key2 = tile_map.sprite_lists.get("key2", arcade.SpriteList())
        self.gate = tile_map.sprite_lists.get("Gate", arcade.SpriteList())

        # Debug: Check if sprite lists are populated
        if not self.key1:
            print("Warning: 'key1' sprite list is empty or not found in tilemap.")
        if not self.key2:
            print("Warning: 'key2' sprite list is empty or not found in tilemap.")
        if not self.walls:
            print("Warning: 'wall' sprite list is empty or not found in tilemap.")
        if not self.Ground:
            print("Warning: 'Ground' sprite list is empty or not found in tilemap.")
        if not self.gate:
            print("Warning: 'Gate' sprite list is empty or not found in tilemap.")

        self.doors = []
        if "doors" in tile_map.object_lists:
            for door in tile_map.object_lists["doors"]:
                if hasattr(door, 'shape') and isinstance(door.shape, list):
                    x, y, width, height = door.shape
                    center_x = x + (width / 2)
                    center_y = y + (height / 2)
                    self.doors.append((center_x, center_y))
        else:
            print("Warning: 'doors' object list not found in tilemap.")

        self.rooms = {}
        if "rooms" in tile_map.object_lists:
            for room in tile_map.object_lists["rooms"]:
                if hasattr(room, 'shape') and isinstance(room.shape, list):
                    x, y, width, height = room.shape
                    center_x = x + (width / 2)
                    center_y = y + (height / 2)
                    room_name = room.name
                    self.rooms[room_name] = (center_x, center_y)
        else:
            print("Warning: 'rooms' object list not found in tilemap.")
                    
    def is_line_box_intersection(self, line_start, line_end, box_center, box_width, box_height):
        box_left = box_center[0] - box_width / 2
        box_right = box_center[0] + box_width / 2
        box_bottom = box_center[1] - box_height / 2
        box_top = box_center[1] + box_height / 2
        x1, y1 = line_start
        x2, y2 = line_end
        if x1 == x2:
            if x1 < box_left or x1 > box_right:
                return False
            ymin = min(y1, y2)
            ymax = max(y1, y2)
            return ymin <= box_top and ymax >= box_bottom
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        x_left = box_left
        x_right = box_right
        y_left = m * x_left + b
        y_right = m * x_right + b
        y_bottom = box_bottom
        y_top = box_top
        x_bottom = (y_bottom - b) / m if m != 0 else float('inf')
        x_top = (y_top - b) / m if m != 0 else float('inf')
        xmin = min(x1, x2)
        xmax = max(x1, x2)
        ymin = min(y1, y2)
        ymax = max(y1, y2)
        if (box_left <= x_left <= box_right and box_bottom <= y_left <= box_top and
            xmin <= x_left <= xmax and ymin <= y_left <= ymax):
            return True
        if (box_left <= x_right <= box_right and box_bottom <= y_right <= box_top and
            xmin <= x_right <= xmax and ymin <= y_right <= ymax):
            return True
        if (box_left <= x_bottom <= box_right and box_bottom <= y_bottom <= box_top and
            xmin <= x_bottom <= xmax and ymin <= y_bottom <= ymax):
            return True
        if (box_left <= x_top <= box_right and box_bottom <= y_top <= box_top and
            xmin <= x_top <= xmax and ymin <= y_top <= ymax):
            return True
        return False

    def check_clear_line_of_sight(self, start_x, start_y, target_x, target_y):
        for wall in self.walls:
            if self.is_line_box_intersection(
                (start_x, start_y),
                (target_x, target_y),
                (wall.center_x, wall.center_y),
                wall.width, wall.height):
                return False
        return True

    def check_vision_cone(self, enemy_x, enemy_y, enemy_direction, player_x, player_y):
        distance = math.sqrt((enemy_x - player_x)**2 + (enemy_y - player_y)**2)
        if distance > VISION_RANGE:
            return False
        if not self.check_clear_line_of_sight(enemy_x, enemy_y, player_x, player_y):
            return False
        dx = player_x - enemy_x
        dy = player_y - enemy_y
        player_angle = math.degrees(math.atan2(dy, dx)) % 360
        angle_diff = min((player_angle - enemy_direction) % 360, (enemy_direction - player_angle) % 360)
        return angle_diff <= VISION_ANGLE / 2

    def find_nearest_door(self, x, y, target_x, target_y):
        best_door = None
        best_distance = float('inf')
        current_to_target_distance = math.sqrt((x - target_x)**2 + (y - target_y)**2)
        for door_x, door_y in self.doors:
            distance_to_door = math.sqrt((x - door_x)**2 + (y - door_y)**2)
            door_to_target_distance = math.sqrt((door_x - target_x)**2 + (door_y - target_y)**2)
            if self.check_clear_line_of_sight(x, y, door_x, door_y) and door_to_target_distance < current_to_target_distance:
                total_distance = distance_to_door + door_to_target_distance
                if total_distance < best_distance:
                    best_distance = total_distance
                    best_door = (door_x, door_y)
        return best_door

    def find_alternative_waypoint(self, x, y, target_x, target_y):
        possible_waypoints = list(self.rooms.values())
        possible_waypoints.extend(self.doors)
        random.shuffle(possible_waypoints)
        for point_x, point_y in possible_waypoints:
            if self.check_clear_line_of_sight(x, y, point_x, point_y):
                return (point_x, point_y)
        angle = random.uniform(0, 2 * math.pi)
        return (x + 50 * math.cos(angle), y + 50 * math.sin(angle))

    def update_noise(self, delta_time):
        if self.player.change_x != 0 or self.player.change_y != 0:
            self.player.noise_timer += delta_time
            if self.player.noise_timer >= 1:
                self.player.noise_level = min(self.player.noise_level + NOISE_INCREASE, NOISE_MAX)
                self.player.noise_timer = 0
        else:
            self.player.noise_level = max(self.player.noise_level - delta_time * 0.5, 0)

    def update_enemy(self):
        enemy_x = self.enemy.center_x
        enemy_y = self.enemy.center_y
        player_x = self.player.center_x
        player_y = self.player.center_y
        current_position = (round(enemy_x), round(enemy_y))
        movement = math.sqrt((current_position[0] - self.enemy.last_position[0])**2 +
                             (current_position[1] - self.enemy.last_position[1])**2)
        if movement < 0.5:
            self.enemy.stuck_counter += 1
        else:
            self.enemy.stuck_counter = 0
        self.enemy.last_position = current_position
        if not self.enemy.vision_active and not self.enemy.noise_active:
            if self.check_vision_cone(enemy_x, enemy_y, self.enemy.direction, player_x, player_y):
                self.enemy.vision_active = True
                self.show_message = True
            elif self.player.noise_level >= NOISE_THRESHOLD:
                self.enemy.noise_active = True
                self.show_message = True
            else:
                if not self.enemy.waypoint or random.random() < 0.02:
                    self.enemy.waypoint = self.find_alternative_waypoint(enemy_x, enemy_y, enemy_x, enemy_y)
                    if self.enemy.waypoint:
                        dx = self.enemy.waypoint[0] - enemy_x
                        dy = self.enemy.waypoint[1] - enemy_y
                        if dx != 0 or dy != 0:
                            self.enemy.direction = math.degrees(math.atan2(dy, dx)) % 360
                self.enemy.change_x = 0
                self.enemy.change_y = 0
        if self.enemy.vision_active or self.enemy.noise_active:
            waypoint_reached = (self.enemy.waypoint and
                               math.sqrt((enemy_x - self.enemy.waypoint[0])**2 +
                                        (enemy_y - self.enemy.waypoint[1])**2) < 10)
            if waypoint_reached or self.enemy.waypoint is None or self.enemy.stuck_counter > 30:
                if self.check_clear_line_of_sight(enemy_x, enemy_y, player_x, player_y):
                    self.enemy.waypoint = (player_x, player_y)
                    self.enemy.stuck_counter = 0
                elif self.enemy.stuck_counter > 30:
                    self.enemy.waypoint = self.find_alternative_waypoint(enemy_x, enemy_y, player_x, player_y)
                    self.enemy.stuck_counter = 0
                else:
                    next_door = self.find_nearest_door(enemy_x, enemy_y, player_x, player_y)
                    if next_door:
                        self.enemy.waypoint = next_door
                    else:
                        self.enemy.waypoint = self.find_alternative_waypoint(enemy_x, enemy_y, player_x, player_y)
                if self.enemy.waypoint:
                    dx = self.enemy.waypoint[0] - enemy_x
                    dy = self.enemy.waypoint[1] - enemy_y
                    if dx != 0 or dy != 0:
                        self.enemy.direction = math.degrees(math.atan2(dy, dx)) % 360
        if self.enemy.waypoint:
            target_x, target_y = self.enemy.waypoint
            dx = target_x - enemy_x
            dy = target_y - enemy_y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                self.enemy.change_x = (dx / distance) * ENEMY_SPEED
                self.enemy.change_y = (dy / distance) * ENEMY_SPEED
            else:
                self.enemy.change_x = 0
                self.enemy.change_y = 0

    def restart(self):
        self.player.center_x = 130
        self.player.center_y = 860
        self.player.change_x = 0
        self.player.change_y = 0
        self.player.noise_level = 0
        self.player.noise_timer = 0
        self.player.has_key1 = False
        self.player.has_key2 = False
        self.enemy.center_x = 450
        self.enemy.center_y = 128
        self.enemy.change_x = 0
        self.enemy.change_y = 0
        self.enemy.waypoint = None
        self.enemy.vision_active = False
        self.enemy.noise_active = False
        self.enemy.stuck_counter = 0
        self.show_message = False
        self.game_over = False
        self.won_game = False
        self.keys_collected = 0
        self.show_all_keys_message = False
        self.create_house()

    def on_draw(self):
        self.clear()
        if self.game_over:
            screen_center_x = self.camera.position[0]
            screen_center_y = self.camera.position[1]
            arcade.draw_text("Game Over!", screen_center_x, screen_center_y + 50, arcade.color.RED, 40, anchor_x="center")
            arcade.draw_text("Drücke 'R' zum Neustart", screen_center_x, screen_center_y, arcade.color.WHITE, 20, anchor_x="center")
        elif self.won_game:
            screen_center_x = self.camera.position[0]
            screen_center_y = self.camera.position[1]
            arcade.draw_text("Du hast gewonnen!", screen_center_x, screen_center_y + 50, arcade.color.GREEN, 40, anchor_x="center")
            arcade.draw_text("Drücke 'R' zum Neustart", screen_center_x, screen_center_y, arcade.color.WHITE, 20, anchor_x="center")
        else:
            self.camera.use()
            self.Ground.draw()
            self.key1.draw()
            self.key2.draw()
            self.gate.draw()
            self.walls.draw()
            self.objects.draw()
            self.all_sprites.draw()
            screen_x = self.camera.position[0] - SCREEN_WIDTH / 2 + 10
            screen_y = self.camera.position[1] + (SCREEN_HEIGHT-20) / 2 - 10
            arcade.draw_text(f"Lärm: {int(self.player.noise_level)}/{NOISE_THRESHOLD}", screen_x, screen_y, arcade.color.WHITE, 12)
            screen_y -= 20
            arcade.draw_text(f"Schlüssel: {self.keys_collected}/{self.total_keys}", screen_x, screen_y, arcade.color.WHITE, 12)
            if self.show_message:
                screen_x = self.camera.position[0]
                screen_y = self.camera.position[1] + SCREEN_HEIGHT / 2 - 80
                arcade.draw_text("Du wurdest erwischt!", screen_x, screen_y, arcade.color.RED, 20, anchor_x="center")
            if self.show_all_keys_message:
                screen_x = self.camera.position[0]
                screen_y = self.camera.position[1] + SCREEN_HEIGHT / 2 - 120
                arcade.draw_text("Du hast alle Schlüssel!", screen_x, screen_y, arcade.color.LIGHT_BLUE, 20, anchor_x="center")

    def on_update(self, delta_time):
        if not self.game_over and not self.won_game:
            self.update_noise(delta_time)
            self.physics_engine_player.update()
            if self.player.change_x != 0 or self.player.change_y != 0:
                if self.player.change_y > 0:  # Moving up
                    self.player.angle = 180
                elif self.player.change_y < 0:  # Moving down
                    self.player.angle = 0
                elif self.player.change_x > 0:  # Moving right
                    self.player.angle = 270
                elif self.player.change_x < 0:  # Moving left
                    self.player.angle = 90
            self.update_enemy()
            self.camera.position = (self.player.center_x, self.player.center_y)
            self.physics_engine_enemy.update()
            # Check for key collisions only if max keys not reached
            if self.keys_collected < self.total_keys:
                # Check for key1 collision
                if not self.player.has_key1 and self.key1:
                    key1_hit_list = arcade.check_for_collision_with_list(self.player, self.key1)
                    for key in key1_hit_list:
                        key.remove_from_sprite_lists()
                        self.player.has_key1 = True
                        self.keys_collected += 1
                # Check for key2 collision
                if not self.player.has_key2 and self.key2:
                    key2_hit_list = arcade.check_for_collision_with_list(self.player, self.key2)
                    for key in key2_hit_list:
                        key.remove_from_sprite_lists()
                        self.player.has_key2 = True
                        self.keys_collected += 1
                # Check if all keys are collected
                if self.keys_collected >= self.total_keys:
                    self.show_all_keys_message = True
            # Check for gate collision
            if arcade.check_for_collision_with_list(self.player, self.gate):
                if self.player.has_key1 and self.player.has_key2:
                    self.won_game = True
            # Check for enemy collision
            if arcade.check_for_collision(self.player, self.enemy):
                self.game_over = True
                
    def on_key_press(self, key, modifiers):
        if self.game_over or self.won_game:
            if key == arcade.key.R:
                self.restart()
        else:
            if key == arcade.key.UP:
                self.player.change_y = PLAYER_SPEED
            elif key == arcade.key.DOWN:
                self.player.change_y = -PLAYER_SPEED
            elif key == arcade.key.LEFT:
                self.player.change_x = -PLAYER_SPEED
            elif key == arcade.key.RIGHT:
                self.player.change_x = PLAYER_SPEED

    def on_key_release(self, key, modifiers):
        if not self.game_over and not self.won_game:
            if key in (arcade.key.UP, arcade.key.DOWN):
                self.player.change_y = 0
            if key in (arcade.key.LEFT, arcade.key.RIGHT):
                self.player.change_x = 0

def main():
    game = HouseGame()
    game.setup()
    arcade.run()

if __name__ == "__main__":
    main()