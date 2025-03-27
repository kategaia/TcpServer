import grpc
import sys
import os
import time
import logging
import threading
from concurrent import futures

# Ajouter le chemin parent pour pouvoir importer les modules frères
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import des services gRPC générés (à générer à partir de proto files)
# Normalement, ces imports seraient les suivants:
# from proto import game_service_pb2, game_service_pb2_grpc
# Mais comme nous n'avons pas les fichiers proto, nous allons créer des classes fictives

class GameServicer:
    """Implémentation du service gRPC pour le moteur de jeu"""
    
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.logger = logging.getLogger("GameServicer")
    
    def ListGames(self, request, context):
        """Obtenir la liste des parties disponibles"""
        self.logger.info("ListGames request received")
        
        try:
            open_games = self.game_engine.get_open_games()
            
            # Dans une implémentation réelle, on convertirait en message protobuf
            # response = game_service_pb2.ListGamesResponse()
            # for game_id in open_games:
            #     game_info = response.games.add()
            #     game_info.id = game_id
            #     details = self.game_engine.get_game_details(game_id)
            #     if details:
            #         game_info.title = details.get('title', '')
            #         game_info.players_count = sum(details.get('player_count', {}).values())
            # return response
            
            return {"game_ids": open_games}
        except Exception as e:
            self.logger.error(f"Error in ListGames: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            # Dans une implémentation réelle, on retournerait un message protobuf vide
            # return game_service_pb2.ListGamesResponse()
            return {"game_ids": []}
    
    def CreateGame(self, request, context):
        """Créer une nouvelle partie"""
        self.logger.info("CreateGame request received")
        
        try:
            # Dans une implémentation réelle, on extrairait les données du message protobuf
            # title = request.title
            # rows = request.rows
            # cols = request.cols
            # max_time_per_turn = request.max_time_per_turn
            # num_turns = request.num_turns
            # num_obstacles = request.num_obstacles
            # max_players = request.max_players
            
            # Pour l'exemple
            title = request.get('title', 'Default Game')
            rows = request.get('rows', 5)
            cols = request.get('cols', 5)
            max_time_per_turn = request.get('max_time_per_turn', 30)
            num_turns = request.get('num_turns', 10)
            num_obstacles = request.get('num_obstacles', 3)
            max_players = request.get('max_players', 10)
            
            game_id = self.game_engine.create_game(
                title, rows, cols, max_time_per_turn, 
                num_turns, num_obstacles, max_players
            )
            
            # Dans une implémentation réelle, on convertirait en message protobuf
            # response = game_service_pb2.CreateGameResponse()
            # response.game_id = game_id
            # return response
            
            return {"game_id": game_id}
        except Exception as e:
            self.logger.error(f"Error in CreateGame: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            # Dans une implémentation réelle, on retournerait un message protobuf vide
            # return game_service_pb2.CreateGameResponse()
            return {"game_id": -1}
    
    def AddPlayer(self, request, context):
        """Ajouter un joueur à une partie"""
        self.logger.info("AddPlayer request received")
        
        try:
            # Dans une implémentation réelle, on extrairait les données du message protobuf
            # game_id = request.game_id
            # player_name = request.player_name
            
            # Pour l'exemple
            game_id = request.get('game_id')
            player_name = request.get('player_name')
            
            result, error = self.game_engine.add_player_to_game(game_id, player_name)
            
            if error:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                # Dans une implémentation réelle, on retournerait un message protobuf avec une erreur
                # response = game_service_pb2.AddPlayerResponse()
                # response.error = error
                # return response
                return {"error": error}
            
            # Dans une implémentation réelle, on convertirait en message protobuf
            # response = game_service_pb2.AddPlayerResponse()
            # response.player_id = result.get('id_player')
            # response.role = result.get('role')
            # return response
            
            return {"player_id": result.get('id_player'), "role": result.get('role')}
        except Exception as e:
            self.logger.error(f"Error in AddPlayer: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            # Dans une implémentation réelle, on retournerait un message protobuf vide
            # return game_service_pb2.AddPlayerResponse()
            return {"error": str(e)}
    
    def StartGame(self, request, context):
        """Démarrer une partie"""
        self.logger.info("StartGame request received")
        
        try:
            # Dans une implémentation réelle, on extrairait les données du message protobuf
            # game_id = request.game_id
            
            # Pour l'exemple
            game_id = request.get('game_id')
            
            success, error = self.game_engine.start_game(game_id)
            
            if error:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                # Dans une implémentation réelle, on retournerait un message protobuf avec une erreur
                # response = game_service_pb2.StartGameResponse()
                # response.error = error
                # return response
                return {"error": error}
            
            # Dans une implémentation réelle, on convertirait en message protobuf
            # response = game_service_pb2.StartGameResponse()
            # response.success = success
            # return response
            
            return {"success": success}
        except Exception as e:
            self.logger.error(f"Error in StartGame: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            # Dans une implémentation réelle, on retournerait un message protobuf vide
            # return game_service_pb2.StartGameResponse()
            return {"error": str(e)}
    
    def GetGameStatus(self, request, context):
        """Obtenir le statut d'une partie"""
        self.logger.info("GetGameStatus request received")
        
        try:
            # Dans une implémentation réelle, on extrairait les données du message protobuf
            # game_id = request.game_id
            # player_id = request.player_id
            
            # Pour l'exemple
            game_id = request.get('game_id')
            player_id = request.get('player_id')
            
            result, error = self.game_engine.get_party_status(game_id, player_id)
            
            if error:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                # Dans une implémentation réelle, on retournerait un message protobuf avec une erreur
                # response = game_service_pb2.GameStatusResponse()
                # response.error = error
                # return response
                return {"error": error}
            
            # Dans une implémentation réelle, on convertirait en message protobuf
            # response = game_service_pb2.GameStatusResponse()
            # response.game_id = result.get('id_party')
            # response.started = result.get('started')
            # response.current_turn = result.get('round_in_progress')
            # return response
            
            return result
        except Exception as e:
            self.logger.error(f"Error in GetGameStatus: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            # Dans une implémentation réelle, on retournerait un message protobuf vide
            # return game_service_pb2.GameStatusResponse()
            return {"error": str(e)}
    
    def GetGameBoard(self, request, context):
        """Obtenir l'état du plateau de jeu"""
        self.logger.info("GetGameBoard request received")
        
        try:
            # Dans une implémentation réelle, on extrairait les données du message protobuf
            # game_id = request.game_id
            # player_id = request.player_id
            
            # Pour l'exemple
            game_id = request.get('game_id')
            player_id = request.get('player_id')
            
            result, error = self.game_engine.get_gameboard_status(game_id, player_id)
            
            if error:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                # Dans une implémentation réelle, on retournerait un message protobuf avec une erreur
                # response = game_service_pb2.GameBoardResponse()
                # response.error = error
                # return response
                return {"error": error}
            
            # Dans une implémentation réelle, on convertirait en message protobuf
            # response = game_service_pb2.GameBoardResponse()
            # response.visible_cells = result.get('visible_cells')
            # return response
            
            return result
        except Exception as e:
            self.logger.error(f"Error in GetGameBoard: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            # Dans une implémentation réelle, on retournerait un message protobuf vide
            # return game_service_pb2.GameBoardResponse()
            return {"error": str(e)}
    
    def MakeMove(self, request, context):
        """Effectuer un mouvement"""
        self.logger.info("MakeMove request received")
        
        try:
            # Dans une implémentation réelle, on extrairait les données du message protobuf
            # game_id = request.game_id
            # player_id = request.player_id
            # move = request.move
            
            # Pour l'exemple
            game_id = request.get('game_id')
            player_id = request.get('player_id')
            move = request.get('move')
            
            result, error = self.game_engine.add_move(game_id, player_id, move)
            
            if error:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                # Dans une implémentation réelle, on retournerait un message protobuf avec une erreur
                # response = game_service_pb2.MakeMoveResponse()
                # response.error = error
                # return response
                return {"error": error}
            
            # Dans une implémentation réelle, on convertirait en message protobuf
            # response = game_service_pb2.MakeMoveResponse()
            # response.current_turn = result.get('round_in_progress')
            # move_info = response.move
            # move_info.row = result.get('move', {}).get('next_position', {}).get('row')
            # move_info.col = result.get('move', {}).get('next_position', {}).get('col')
            # return response
            
            return result
        except Exception as e:
            self.logger.error(f"Error in MakeMove: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            # Dans une implémentation réelle, on retournerait un message protobuf vide
            # return game_service_pb2.MakeMoveResponse()
            return {"error": str(e)}

class GrpcServer:
    """Serveur gRPC pour la communication entre les modules"""
    
    def __init__(self, port=5002, game_engine=None):
        self.port = port
        self.server = None
        self.game_engine = game_engine
        self.logger = logging.getLogger("GrpcServer")
        self._setup_logging()
        
    def _setup_logging(self):
        """Configuration du logger"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def start(self):
        """Démarrer le serveur gRPC"""
        self.logger.info(f"Starting gRPC server on port {self.port}")
        
        try:
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
            
            # Dans une implémentation réelle, on enregistrerait les services gRPC
            # game_service_pb2_grpc.add_GameServiceServicer_to_server(
            #     GameServicer(self.game_engine), self.server)
            
            # Pour l'exemple, nous simulons simplement le démarrage du serveur
            self.logger.info("gRPC services registered")
            
            self.server.add_insecure_port(f'[::]:{self.port}')
            self.server.start()
            self.logger.info(f"gRPC server started on port {self.port}")
            
            # Garde le serveur en vie
            try:
                while True:
                    time.sleep(86400)  # Un jour
            except KeyboardInterrupt:
                self.stop()
        except Exception as e:
            self.logger.error(f"Error starting gRPC server: {e}")
    
    def stop(self):
        """Arrêter le serveur gRPC"""
        if self.server:
            self.logger.info("Stopping gRPC server...")
            self.server.stop(0)
            self.logger.info("gRPC server stopped")

# Pour le test individuel
if __name__ == "__main__":
    # Dans une situation réelle, nous utiliserions un singleton du moteur de jeu
    # from game_engine_module.game_engine import GameEngine
    # game_engine = GameEngine.get_instance()ooo
    
    # Pour l'exemple, nous simulons simplement le moteur de jeu
    game_engine = None
    
    # Créer et démarrer le serveur gRPC
    server = GrpcServer(port=5002, game_engine=game_engine)
    
    # Démarrer dans un thread séparé pour pouvoir arrêter proprement
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        print("gRPC server running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()