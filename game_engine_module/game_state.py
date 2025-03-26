from enum import Enum
import random
import time
from datetime import datetime

class CellType(Enum):
    EMPTY = 0
    VILLAGER = 1
    WOLF = 2
    OBSTACLE = 3

class Player:
    def __init__(self, id_player, player_name, role):
        self.id_player = id_player
        self.player_name = player_name
        self.role = role
        self.position = None
        self.is_alive = True
        self.is_npc = False

class GameBoard:
    def __init__(self, rows, cols, num_obstacles):
        self.rows = rows
        self.cols = cols
        self.grid = [[CellType.EMPTY for _ in range(cols)] for _ in range(rows)]
        self.players = {}  # id_player -> Player
        self._place_obstacles(num_obstacles)

    def _place_obstacles(self, num_obstacles):
        """Place obstacles randomly on the game board"""
        placed = 0
        while placed < num_obstacles:
            row = random.randint(0, self.rows - 1)
            col = random.randint(0, self.cols - 1)
            if self.grid[row][col] == CellType.EMPTY:
                self.grid[row][col] = CellType.OBSTACLE
                placed += 1

    def add_player(self, player, row=None, col=None):
        """Add a player to the game board at the given position or randomly"""
        if row is None or col is None:
            # Find a random empty cell
            valid_position = False
            while not valid_position:
                row = random.randint(0, self.rows - 1)
                col = random.randint(0, self.cols - 1)
                if self.grid[row][col] == CellType.EMPTY:
                    valid_position = True
        
        # Place the player
        player.position = (row, col)
        self.players[player.id_player] = player
        
        # Update the grid
        cell_type = CellType.VILLAGER if player.role == "villager" else CellType.WOLF
        self.grid[row][col] = cell_type
        
        return True
    
    def move_player(self, player_id, row_offset, col_offset):
        """Move player by the given offset if valid"""
        if player_id not in self.players:
            return False
            
        player = self.players[player_id]
        if not player.is_alive or player.is_npc:
            return False
            
        current_row, current_col = player.position
        new_row = current_row + row_offset
        new_col = current_col + col_offset
        
        # Check if move is valid (single step in one direction)
        if (abs(row_offset) + abs(col_offset) != 1):
            return False
            
        # Check if new position is within bounds
        if new_row < 0 or new_row >= self.rows or new_col < 0 or new_col >= self.cols:
            return False
            
        # Check if new position contains an obstacle
        if self.grid[new_row][new_col] == CellType.OBSTACLE:
            return False
            
        # Update the grid - remove player from old position
        self.grid[current_row][current_col] = CellType.EMPTY
        
        # Update player position
        player.position = (new_row, new_col)
        
        # Update the grid - add player to new position
        cell_type = CellType.VILLAGER if player.role == "villager" else CellType.WOLF
        self.grid[new_row][new_col] = cell_type
        
        return True
    
    def get_visible_cells(self):
        """Return a string representation of the current game board state"""
        result = ""
        for row in self.grid:
            for cell in row:
                result += str(cell.value)
        return result
    
    def resolve_eliminations(self):
        """Resolve eliminations - villagers on the same cell as wolves are eliminated"""
        positions = {}  # (row, col) -> [player_ids]
        
        # Group players by position
        for player in self.players.values():
            if player.is_alive:
                pos = player.position
                if pos not in positions:
                    positions[pos] = []
                positions[pos].append(player.id_player)
        
        # Check for eliminations - if wolf and villager are on the same cell
        eliminated = []
        for pos, player_ids in positions.items():
            if len(player_ids) > 1:
                wolves = [p_id for p_id in player_ids if self.players[p_id].role == "wolf"]
                villagers = [p_id for p_id in player_ids if self.players[p_id].role == "villager"]
                if wolves and villagers:
                    eliminated.extend(villagers)
        
        # Mark eliminated players
        for player_id in eliminated:
            self.players[player_id].is_alive = False
            
        return eliminated

class GameState:
    def __init__(self, id_party, title, rows, cols, max_time_per_turn, num_turns, num_obstacles, max_players):
        self.id_party = id_party
        self.title = title
        self.rows = rows
        self.cols = cols
        self.max_time_per_turn = max_time_per_turn  # in seconds
        self.max_turns = num_turns
        self.max_players = max_players
        self.num_obstacles = num_obstacles
        
        self.board = GameBoard(rows, cols, num_obstacles)
        self.current_turn = 0
        self.started = False
        self.turn_start_time = None
        self.player_count = {"wolf": 0, "villager": 0}
        self.max_per_role = {"wolf": max(1, max_players // 3), "villager": max(1, max_players - (max_players // 3))}
        self.next_player_id = 1
    
    def start_game(self):
        """Start the game if enough players have joined"""
        if self.player_count["wolf"] > 0 and self.player_count["villager"] > 0:
            self.started = True
            self.current_turn = 1
            self.turn_start_time = datetime.now()
            return True
        return False
    
    def add_player(self, player_name):
        """Add a player to the game"""
        if self.started:
            return None, "Game already started"
            
        # Check if max players reached
        total_players = sum(self.player_count.values())
        if total_players >= self.max_players:
            return None, "Maximum players reached"
        
        # Determine role based on current distribution
        if self.player_count["wolf"] < self.max_per_role["wolf"]:
            if self.player_count["villager"] < self.max_per_role["villager"]:
                # Both roles available, randomly choose
                role = random.choice(["wolf", "villager"])
            else:
                # Only wolf role available
                role = "wolf"
        else:
            # Only villager role available
            role = "villager"
        
        # Create new player
        player = Player(self.next_player_id, player_name, role)
        self.next_player_id += 1
        
        # Add player to board
        if self.board.add_player(player):
            self.player_count[role] += 1
            return player, None
        
        return None, "Failed to place player on board"
    
    def is_turn_over(self):
        """Check if the current turn is over (time limit reached)"""
        if self.turn_start_time:
            elapsed = (datetime.now() - self.turn_start_time).total_seconds()
            return elapsed > self.max_time_per_turn
        return False
    
    def next_turn(self):
        """Advance to the next turn"""
        if not self.started:
            return False
            
        # Resolve eliminations from previous turn
        eliminated_players = self.board.resolve_eliminations()
        
        # Check game end conditions
        villagers_alive = sum(1 for p in self.board.players.values() 
                          if p.role == "villager" and p.is_alive)
        
        if villagers_alive == 0 or self.current_turn >= self.max_turns:
            self.started = False
            return True
            
        # Start new turn
        self.current_turn += 1
        self.turn_start_time = datetime.now()
        
        return True
    
    def check_game_over(self):
        """Check if the game is over and who won"""
        villagers_alive = sum(1 for p in self.board.players.values() 
                           if p.role == "villager" and p.is_alive)
        
        if villagers_alive == 0:
            return True, "wolf"
        elif self.current_turn >= self.max_turns:
            return True, "villager"
        else:
            return False, None