from flask import Flask, request, jsonify, render_template
import threading
import sys
import os

# Ajouter le chemin parent pour pouvoir importer les modules frères
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine_module.game_engine import GameEngine
from communication_module.grpc_server import GrpcServer
from communication_module.tcp_communication import TcpCommunication

class HttpServer:
    def __init__(self, host='127.0.0.1', port=5000, debug=False):
        self.app = Flask(__name__, 
                         static_folder='statics',
                         template_folder='templates')
        self.host = host
        self.port = port
        self.debug = debug
        self.game_engine = GameEngine.get_instance()
        self.tcp_comm = None
        self.grpc_server = None
        
        # Configuration des routes
        self._configure_routes()
        
    def _configure_routes(self):
        """Configure les routes de l'application Flask"""
        
        @self.app.route('/')
        def index():
            """Page d'accueil"""
            return render_template('index.html')
            
        @self.app.route('/games', methods=['GET'])
        def list_games():
            """Liste des parties disponibles"""
            open_games = self.game_engine.get_open_games()
            games_details = []
            
            for game_id in open_games:
                details = self.game_engine.get_game_details(game_id)
                if details:
                    games_details.append(details)
            
            return jsonify({"games": games_details})
            
        @self.app.route('/games', methods=['POST'])
        def create_game():
            """Création d'une nouvelle partie"""
            data = request.json
            
            # Vérification des données
            required_fields = ['title', 'rows', 'cols', 'max_time_per_turn', 
                              'num_turns', 'num_obstacles', 'max_players']
            
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            # Création de la partie
            game_id = self.game_engine.create_game(
                data['title'],
                int(data['rows']),
                int(data['cols']),
                int(data['max_time_per_turn']),
                int(data['num_turns']),
                int(data['num_obstacles']),
                int(data['max_players'])
            )
            
            return jsonify({"id_party": game_id}), 201
            
        @self.app.route('/games/<int:game_id>', methods=['GET'])
        def get_game(game_id):
            """Récupère les détails d'une partie"""
            details = self.game_engine.get_game_details(game_id)
            
            if details:
                return jsonify(details)
            else:
                return jsonify({"error": "Game not found"}), 404
                
        @self.app.route('/games/<int:game_id>/join', methods=['POST'])
        def join_game(game_id):
            """Rejoindre une partie"""
            data = request.json
            
            if 'player_name' not in data:
                return jsonify({"error": "Missing player_name"}), 400
                
            result, error = self.game_engine.add_player_to_game(game_id, data['player_name'])
            
            if error:
                return jsonify({"error": error}), 400
                
            return jsonify(result)
            
        @self.app.route('/games/<int:game_id>/start', methods=['POST'])
        def start_game(game_id):
            """Démarrer une partie"""
            success, error = self.game_engine.start_game(game_id)
            
            if error:
                return jsonify({"error": error}), 400
                
            return jsonify({"success": success})
            
        @self.app.route('/games/<int:game_id>/board', methods=['GET'])
        def get_board(game_id):
            """Récupérer l'état du plateau"""
            player_id = request.args.get('player_id', type=int)
            
            if player_id is None:
                return jsonify({"error": "Missing player_id parameter"}), 400
                
            result, error = self.game_engine.get_gameboard_status(game_id, player_id)
            
            if error:
                return jsonify({"error": error}), 400
                
            return jsonify(result)
            
        @self.app.route('/games/<int:game_id>/move', methods=['POST'])
        def make_move(game_id):
            """Effectuer un mouvement"""
            data = request.json
            
            if 'player_id' not in data or 'move' not in data:
                return jsonify({"error": "Missing player_id or move"}), 400
                
            result, error = self.game_engine.add_move(game_id, data['player_id'], data['move'])
            
            if error:
                return jsonify({"error": error}), 400
                
            return jsonify(result)
            
    def setup_communication(self, tcp_port=5001, grpc_port=5002):
        """Configure la communication avec le serveur TCP et gRPC"""
        # Initialisation du serveur TCP pour la communication avec le module d'administration
        self.tcp_comm = TcpCommunication(tcp_port)
        
        # Initialisation du serveur gRPC pour la communication avec le serveur TCP
        self.grpc_server = GrpcServer(grpc_port, self.game_engine)
        
    def start(self):
        """Démarrage du serveur HTTP"""
        # Démarrage des serveurs de communication dans des threads séparés
        if self.tcp_comm:
            tcp_thread = threading.Thread(target=self.tcp_comm.start)
            tcp_thread.daemon = True
            tcp_thread.start()
            
        if self.grpc_server:
            grpc_thread = threading.Thread(target=self.grpc_server.start)
            grpc_thread.daemon = True
            grpc_thread.start()
        
        # Démarrage du serveur Flask
        self.app.run(host=self.host, port=self.port, debug=self.debug)
        
    def stop(self):
        """Arrêt du serveur HTTP et des composants de communication"""
        if self.tcp_comm:
            self.tcp_comm.stop()
            
        if self.grpc_server:
            self.grpc_server.stop()
            
        # Le serveur Flask s'arrêtera automatiquement quand le processus se termine

# Point d'entrée pour démarrer le serveur
if __name__ == '__main__':
    server = HttpServer(debug=True)
    server.setup_communication()
    server.start()