class MoveResolver:
    def __init__(self, game_state):
        self.game_state = game_state
        self.pending_moves = {}  # player_id -> (row_offset, col_offset)
    
    def add_move(self, player_id, move_str):
        """Add a player move to be resolved"""
        if len(move_str) != 2:
            return False
            
        try:
            row_offset = int(move_str[0])
            col_offset = int(move_str[1])
            
            # Validate move values (-1, 0, or 1)
            if row_offset not in [-1, 0, 1] or col_offset not in [-1, 0, 1]:
                return False
                
            # Ensure only one direction moved (no diagonal)
            if abs(row_offset) + abs(col_offset) != 1:
                return False
                
            self.pending_moves[player_id] = (row_offset, col_offset)
            return True
        except ValueError:
            return False
    
    def resolve_moves(self):
        """Resolve all pending moves"""
        results = {}
        
        # Process all pending moves
        for player_id, (row_offset, col_offset) in self.pending_moves.items():
            # Apply the move
            success = self.game_state.board.move_player(player_id, row_offset, col_offset)
            
            # Record the result
            if player_id in self.game_state.board.players:
                player = self.game_state.board.players[player_id]
                if success and player.is_alive:
                    new_row, new_col = player.position
                    results[player_id] = {
                        "success": True,
                        "position": {"row": new_row, "col": new_col}
                    }
                else:
                    results[player_id] = {
                        "success": False,
                        "message": "Invalid move or player is dead"
                    }
        
        # Clear pending moves
        self.pending_moves = {}
        
        # Check for eliminations after moves are resolved
        eliminated = self.game_state.board.resolve_eliminations()
        
        # Update results for eliminated players
        for player_id in eliminated:
            if player_id in results:
                results[player_id]["eliminated"] = True
        
        return results