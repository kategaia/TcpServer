
from .game_state import GameState
from .move_resolver import MoveResolver
import threading
import time
from datetime import datetime

class GameEngine:
    _instance = None
    
    @staticmethod
    def get_instance():
        """Singleton pattern to get game engine instance"""
        if GameEngine._instance is None:
            GameEngine._instance = GameEngine()
        return GameEngine._instance
    
    def __init__(self):
        if GameEngine._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.games = {}  # id_party -> GameState
            self.move_resolvers = {}  # id_party -> MoveResolver
            self.next_game_id = 1
            self.running = True
            self.turn_monitor_thread = threading.Thread(target=self._monitor_turns)
            self.turn_monitor_thread.daemon = True
            self.turn_monitor_thread.start()
            self.game_end_callbacks = []  # list of functions to call when games end
            self.turn_end_callbacks = []  # list of functions to call when turns end
    
    def create_game(self, title, rows, cols, max_time_per_turn, num_turns, num_obstacles, max_players):
        """Create a new game with the specified parameters"""
        id_party = self.next_game_id
        self.next_game_id += 1
        
        game_state = GameState(
            id_party,
            title, 
            rows, 
            cols, 
            max_time_per_turn, 
            num_turns, 
            num_obstacles, 
            max_players
        )
        self.games[id_party] = game_state
        self.move_resolvers[id_party] = MoveResolver(game_state)
        
        return id_party
    
    def add_player_to_game(self, id_party, player_name):
        """Add a player to an existing game"""
        if id_party not in self.games:
            return None, "Game not found"
        
        game_state = self.games[id_party]
        player, error = game_state.add_player(player_name)
        
        if player:
            return {
                "id_player": player.id_player,
                "role": player.role
            }, None
        else:
            return None, error
    
    def start_game(self, id_party):
        """Start a game if it has enough players"""
        if id_party not in self.games:
            return False, "Game not found"
        
        game_state = self.games[id_party]
        if game_state.start_game():
            return True, None
        else:
            return False, "Not enough players to start game"
    
    def get_party_status(self, id_party, id_player=None):
        """Get the current status of a game"""
        if id_party not in self.games:
            return None, "Game not found"
        
        game_state = self.games[id_party]
        
        result = {
            "id_party": game_state.id_party,
            "started": game_state.started,
            "round_in_progress": game_state.current_turn if game_state.started else -1,
        }
        
        # Add move information for the player if provided
        if id_player is not None and id_player in game_state.board.players:
            player = game_state.board.players[id_player]
            if player.is_alive:
                result["move"] = {
                    "next_position": {
                        "row": 0,  # Default values, should be updated based on game state
                        "col": 0
                    }
                }
        
        return result, None
    
    def get_gameboard_status(self, id_party, id_player=None):
        """Get the current status of a game board"""
        if id_party not in self.games:
            return None, "Game not found"
        
        game_state = self.games[id_party]
        visible_cells = game_state.board.get_visible_cells()
        
        return {"visible_cells": visible_cells}, None
    
    def add_move(self, id_party, id_player, move_str):
        """Add a move for a player in a game"""
        if id_party not in self.games or id_party not in self.move_resolvers:
            return False, "Game not found"
            
        game_state = self.games[id_party]
        
        # Check if game has started
        if not game_state.started:
            return False, "Game not started"
            
        # Check if player exists in game
        if id_player not in game_state.board.players:
            return False, "Player not found in game"
            
        # Check if player is alive
        player = game_state.board.players[id_player]
        if not player.is_alive:
            return False, "Player is eliminated"
            
        # Add move to resolver
        move_resolver = self.move_resolvers[id_party]
        if move_resolver.add_move(id_player, move_str):
            return {
                "round_in_progress": game_state.current_turn,
                "move": {
                    "next_position": {
                        "row": int(move_str[0]),
                        "col": int(move_str[1])
                    }
                }
            }, None
        else:
            return False, "Invalid move format"
    
    def _monitor_turns(self):
        """Monitor game turns and resolve moves when turns end"""
        while self.running:
            for id_party, game_state in list(self.games.items()):
                if game_state.started and game_state.is_turn_over():
                    # Resolve moves for this turn
                    if id_party in self.move_resolvers:
                        move_results = self.move_resolvers[id_party].resolve_moves()
                        # Notify any listeners that moves were resolved
                        for callback in self.turn_end_callbacks:
                            callback(id_party, game_state.current_turn, move_results)
                    
                    # Advance to next turn
                    game_state.next_turn()
                    
                    # Check if game is over
                    game_over, winner = game_state.check_game_over()
                    if game_over:
                        # Notify any listeners that game ended
                        for callback in self.game_end_callbacks:
                            callback(id_party, winner)
            
            # Sleep to avoid high CPU usage
            time.sleep(0.5)
    
    def register_game_end_callback(self, callback):
        """Register a callback function to be called when a game ends"""
        self.game_end_callbacks.append(callback)
    
    def register_turn_end_callback(self, callback):
        """Register a callback function to be called when a turn ends"""
        self.turn_end_callbacks.append(callback)
    
    def get_open_games(self):
        """Get list of games that haven't started yet"""
        open_games = []
        for id_party, game_state in self.games.items():
            if not game_state.started:
                open_games.append(id_party)
        return open_games
    
    def get_game_details(self, id_party):
        """Get detailed information about a game"""
        if id_party not in self.games:
            return None
            
        game_state = self.games[id_party]
        return {
            "id_party": game_state.id_party,
            "title": game_state.title,
            "rows": game_state.rows,
            "cols": game_state.cols,
            "max_time_per_turn": game_state.max_time_per_turn,
            "max_turns": game_state.max_turns,
            "num_obstacles": game_state.num_obstacles,
            "max_players": game_state.max_players,
            "current_turn": game_state.current_turn,
            "started": game_state.started,
            "player_count": game_state.player_count
        }
    
    def shutdown(self):
        """Shutdown the game engine"""
        self.running = False
        if self.turn_monitor_thread.is_alive():
            self.turn_monitor_thread.join(timeout=2)