import heapq
import student_consts
import consts
import time

"""
STUDENTS:
Bernardo Figueiredo - 108073
Alexandre Cotorobai - 107849
"""


class DigDugAgent:
    """
    DigDug agent class used for everything related to the AI
    """
    def __init__(self, state) -> None:
        # Initialize the agent with the initial game state
        self.map = state["map"]
        self.size = state["size"]

        self.last_state = None
        self.current_state = None

        self.digdug_x = 1
        self.digdug_y = 1
        self.plan = []                          # Array containing last plan calculated by A*
        self.nearest_enemy = None
        self.focused_enemy = None
        self.bad_coords = []                    # Coordinates that DigDug should avoid
        self.very_bad_coords = []               # Coordinates that DigDug should really avoid
        self.digdug_dir = consts.Direction.EAST
        self.catching_fugitive = False          # Whether DigDug is currently chasing an enemy that is on the surface
        self.started_excavating = False         # Used to force digdug to dig on the right side of the map
        self.im_stuck = 0                       # A counter for how long DigDug has been stuck

    def update_state(self, state) -> None:
        """
        Update the agent state with the new state of the game
        Also updates the map with the new state of the game
        """
        self.update_rocks_pos(state)
        self.update_enemies_pos(state)
        self.digdug_x, self.digdug_y = state["digdug"]

        if self.last_state and self.last_state["digdug"] == state["digdug"]:
            self.im_stuck += 1
        else:
            self.im_stuck = 0

        if not self.started_excavating and (self.digdug_y >= 2 or state["level"] >= 7):
            self.started_excavating = True

        self.map[self.digdug_x][self.digdug_y] = student_consts.TileState.EMPTY

        self.last_state = self.current_state
        self.current_state = state

        self.update_bad_coords()

    def update_enemies_pos(self, state):
        """
        Update the map with the new position of the enemies
        """
        if self.last_state is None:
            for enemy in state["enemies"]:
                self.map[enemy["pos"][0]][enemy["pos"][1]] |= student_consts.TileState[
                    enemy["name"].upper()
                ]
        else:
            for enemy in self.last_state["enemies"]:
                self.map[enemy["pos"][0]][
                    enemy["pos"][1]
                ] &= student_consts.Expressions.BLOCKED
            for enemy in state["enemies"]:
                self.map[enemy["pos"][0]][enemy["pos"][1]] |= student_consts.TileState[
                    enemy["name"].upper()
                ]

    def update_bad_coords(self):
        """
        Update the bad coordinates that DigDug should avoids
        """

        # These offsets are specific tiles around the enemies that DigDug should avoid
        offsets = {
            consts.Direction.NORTH: [
                (0, -2),
                (-1, -2),
                (1, -2),
                (0, -1),
                (-1, -1),
                (1, -1),
                (1, 0),
                (-1, 0),
                (-1, 1),
                (1, 1),
                (1, 2),
                (-1, 2),
                (1, 3),
                (-1, 3),
            ],
            consts.Direction.SOUTH: [
                (0, 2),
                (-1, 2),
                (1, 2),
                (0, 1),
                (-1, 1),
                (1, 1),
                (1, 0),
                (-1, 0),
                (1, -1),
                (-1, -1),
                (1, -2),
                (-1, -2),
                (1, -3),
                (-1, -3),
            ],
            consts.Direction.EAST: [
                (2, 0),
                (2, -1),
                (2, 1),
                (1, 0),
                (1, -1),
                (1, 1),
                (0, 1),
                (0, -1),
                (-1, -1),
                (-1, 1),
                (-2, 1),
                (-2, -1),
                (-3, 1),
                (-3, -1),
            ],
            consts.Direction.WEST: [
                (-2, 0),
                (-2, -1),
                (-2, 1),
                (-1, 0),
                (-1, -1),
                (-1, 1),
                (0, 1),
                (0, -1),
                (1, -1),
                (1, 1),
                (2, -1),
                (2, 1),
                (3, -1),
                (3, 1),
            ],
        }
        fygar_offsets = {
            consts.Direction.NORTH: [],
            consts.Direction.SOUTH: [],
            consts.Direction.EAST: [
                (4, 0),
                (3, 0),
                (2, 0),
                (1, 0),
            ],
            consts.Direction.WEST: [
                (-4, 0),
                (-3, 0),
                (-2, 0),
                (-1, 0),
            ],
        }

        self.very_bad_coords = []
        self.bad_coords = []
        count = 0

        for enemy in self.current_state["enemies"]:
            direction = enemy["dir"]
            x, y = enemy["pos"]
            if enemy["name"] == "Fygar":
                for offset in fygar_offsets[direction]:
                    self.very_bad_coords.append((x + offset[0], y + offset[1]))
            count += 1
                
            for offset in offsets[direction]:
                self.bad_coords.append((x + offset[0], y + offset[1]))

        if count == 1 and not self.catching_fugitive:
            self.catching_fugitive = True

    def update_rocks_pos(self, game_state):
        """
        Update the map with the new position of the rocks
        """
        if self.last_state is None:
            for rock in game_state["rocks"]:
                self.map[rock["pos"][0]][rock["pos"][1]] = student_consts.TileState.ROCK
        else:
            for rock in self.last_state["rocks"]:
                self.map[rock["pos"][0]][
                    rock["pos"][1]
                ] = student_consts.TileState.EMPTY
            for rock in game_state["rocks"]:
                self.map[rock["pos"][0]][rock["pos"][1]] = student_consts.TileState.ROCK

    def map_pprint(self):
        # debuggin purposes
        print([list(row) for row in zip(*self.map)])

    def a_star_search(self, start, goal, cost_func):
        """
        General A* search algorithm
        """
        start = tuple(start)
        goal = tuple(goal)
        startnode = Node(start, None, 0, 0)
        frontier = [startnode]
        heapq.heapify(frontier)
        explored = set()

        while frontier:
            node = heapq.heappop(frontier)
            if node.state == goal:
                return self.get_path(node)

            for newstate in node.get_neighbours(self.size):
                if not node.in_parent(newstate) and newstate not in explored:
                    newnode = Node(
                        newstate,
                        node,
                        node.c + cost_func(newstate),
                        self.heuristic(newstate, goal),
                    )
                    explored.add(newstate)
                    heapq.heappush(frontier, newnode)

        return None

    def get_coord_tilestate(self, x, y):
        return self.map[x][y]

    def get_path(self, node):
        if node.parent is None:
            return []
        path = self.get_path(node.parent)
        path += [node.state]
        return path

    def run_cost(self, coords):
        """
        Cost function used by the A* algorithm 
        when DigDug is running away from an enemy
        """
        x, y = coords
        tilestate = self.get_coord_tilestate(x, y)
        if (
            tilestate & student_consts.TileState.ROCK
            or tilestate & student_consts.Expressions.ENEMY_TYPE
        ):
            return 1000

        run_bad_coords = []

        for enemy in self.current_state["enemies"]:
            # add tile in 1 range of enemy
            ex, ey = enemy["pos"]
            run_bad_coords.append((ex, ey))
            run_bad_coords.append((ex + 1, ey))
            run_bad_coords.append((ex - 1, ey))
            run_bad_coords.append((ex, ey + 1))
            run_bad_coords.append((ex, ey - 1))

        if (x, y) in run_bad_coords:
            return 192

        return self.map[coords[0]][coords[1]] * 3 + 1

    def get_relative_position(self, coords_a, coords_b):
        """
        Get the action that DigDug should take to move from coords_a to coords_b
        """
        if coords_a[1] == coords_b[1]:
            if coords_a[0] > coords_b[0]:
                self.digdug_dir = consts.Direction.WEST
                return "a"
            self.digdug_dir = consts.Direction.EAST
            return "d"
        if coords_a[1] > coords_b[1]:
            self.digdug_dir = consts.Direction.NORTH
            return "w"
        self.digdug_dir = consts.Direction.SOUTH
        return "s"

    def heuristic(self, coords, goal):
        # manhattan distance
        return abs(coords[0] - goal[0]) + abs(coords[1] - goal[1])

    def cost(self, coords):
        """
        Cost function used by the A* algorithm 
        when DigDug is chasing an enemy
        """
        x, y = coords
        tilestate = self.get_coord_tilestate(x, y)
        if (
            tilestate & student_consts.TileState.ROCK
            or tilestate & student_consts.Expressions.ENEMY_TYPE
        ):
            return 1000

        tilestate = self.get_coord_tilestate(x, y - 1)
        if tilestate & student_consts.TileState.ROCK:
            return 200

        ## this makes a barrier to force digdug to start diggin on the right side of the map
        if not self.catching_fugitive and 0 <= x < self.size[0] - 1 and y == 2:
            ## This barrier only thats effect when the enemies are stupid, otherwise he will go on the most optimal path 
            if not self.started_excavating and self.current_state["level"] < 7:
                return 9999
            elif self.current_state["level"] < 7:
                return 500 * self.map[coords[0]][coords[1]]
            else:
                return self.map[coords[0]][coords[1]] * 3 + 1

        if (
            self.catching_fugitive
            and self.nearest_enemy["name"] == "Pooka"
            and self.digdug_y < 2 
        ):
            # if pooka and digdug is at surface,
            self.bad_coords = []

        if (x, y) in self.very_bad_coords:
            return 2 * 96 + 1 

        if (x, y) in self.bad_coords:
            return 96 if self.nearest_enemy["name"] == "Fygar" else 48

        return (
            self.map[coords[0]][coords[1]] * 3 + 1 if not self.catching_fugitive else 0
        )

    def get_next_move(self):
        """
        Get the next move that DigDug should take
        This function calls the A* algorithm to calculate the next move
        Depending on conditions it will calculate the next move to chase an enemy 
        or to run away from an enemy.

        If the distance is inbetween 1 and 3, DigDug will try to kill the enemy

        The attack move is the default move, if no other move is calculated
        """
        self.nearest_enemy, distance = self.get_nearest_enemy(
            self.current_state["digdug"]
        )
        key = "A"

        if distance <= 1:
            self.plan = self.a_star_search(
                self.current_state["digdug"], [0, 0], self.run_cost
            )
            if self.plan != []:
                key = self.get_relative_position(
                    self.current_state["digdug"], self.plan[0]
                )

        if distance > 3:
            if 0 <= self.nearest_enemy["pos"][1] < 2:
                self.catching_fugitive = True
            else:
                self.catching_fugitive = False

            self.plan = self.a_star_search(
                self.current_state["digdug"], self.get_goal(), self.cost
            )

            if self.plan != []:
                key = self.get_relative_position(
                    self.current_state["digdug"], self.plan[0]
                )

        # unstuck
        if self.im_stuck > 20:
            self.plan = self.a_star_search(
                self.current_state["digdug"], self.get_goal(), self.cost
            )

            if self.plan != []:
                key = self.get_relative_position(
                    self.current_state["digdug"], self.plan[0]
                )

        return key

    def get_tile_ahead(self, coords, direction):
        """
        Get the tile that is ahead of the given coords in the given direction
        """
        x, y = coords
        if direction == consts.Direction.NORTH:
            y -= 1
        if direction == consts.Direction.SOUTH:
            y += 1
        if direction == consts.Direction.EAST:
            x += 1
        if direction == consts.Direction.WEST:
            x -= 1

        x = max(0, min(x, self.size[0] - 1))
        y = max(0, min(y, self.size[1] - 1))
        return self.get_coord_tilestate(x, y)

    def get_nearest_enemy(self, coords):
        """
        From all the enemies, get the nearest enemy to the given coords
        """
        enemies = self.current_state["enemies"]
        closest_enemy = enemies[0]
        distance_to_closest_enemy = self.heuristic(coords, closest_enemy["pos"])

        closed_surface_enemy = None
        distance_to_closed_surface_enemy = None

        for enemy in enemies[1:]:
            distance = self.heuristic(coords, enemy["pos"])
            if enemy["pos"][1] < 2:
                if closed_surface_enemy is None or distance < distance_to_closed_surface_enemy:
                    closed_surface_enemy = enemy
                    distance_to_closed_surface_enemy = distance
                continue

            if distance < distance_to_closest_enemy:
                closest_enemy = enemy
                distance_to_closest_enemy = distance

        if closed_surface_enemy is not None:
            return closed_surface_enemy, distance_to_closed_surface_enemy

        return closest_enemy, distance_to_closest_enemy

    def get_goal(self):
        """
        Get the goal that DigDug should go to
        This calculates the position behind the nearest enemy
        """
        x, y = self.nearest_enemy["pos"]
        direction = self.nearest_enemy["dir"]

        if direction == consts.Direction.NORTH:
            y += 1
        if direction == consts.Direction.SOUTH:
            y -= 1
        if direction == consts.Direction.EAST:
            x -= 1
        if direction == consts.Direction.WEST:
            x += 1

        x = max(0, min(x, self.size[0] - 1))
        y = max(0, min(y, self.size[1] - 1))
        return (x, y)


class Node:
    """
    Node class used in the A* algorithm
    Adapted from class
    """
    def __init__(self, state, parent, c, h) -> None:
        self.parent = parent
        self.state = state
        # cost
        self.c = c
        # heuristic
        self.h = h

    def __lt__(self, __value: object) -> bool:
        return self.c + self.h < __value.c + __value.h

    def __gt__(self, __value: object) -> bool:
        return self.c + self.h > __value.c + __value.h

    def __le__(self, __value: object) -> bool:
        return self.c + self.h <= __value.c + __value.h

    def __ge__(self, __value: object) -> bool:
        return self.c + self.h >= __value.c + __value.h

    def get_neighbours(self, map_size):
        """
        Get the neighbours coords of the node
        """
        actions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        neighbours = []

        for dx, dy in actions:
            x = self.state[0] + dx
            y = self.state[1] + dy

            if x < 0 or x >= map_size[0] or y < 0 or y >= map_size[1]:
                continue

            neighbours.append((x, y))

        return neighbours

    def in_parent(self, state):
        if self.parent is None:
            return False
        if self.parent.state == state:
            return True
        return self.parent.in_parent(state)

    def __repr__(self) -> str:
        return f"Node: {self.state} - {self.parent}"
