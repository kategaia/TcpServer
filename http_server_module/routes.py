from flask import Blueprint, request, jsonify, render_template
import sys
import os

# Ajouter le chemin parent pour pouvoir importer les modules frères
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from game_engine_module.game_engine import GameEngine

# Créer un Blueprint pour les routes
routes_bp = Blueprint('routes', __name__)
game_engine = GameEngine.get_instance()

@routes_bp.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@routes_bp.route('/games', methods=['GET'])
def list_games():
    """Liste des parties disponibles"""
    open_games = game_engine.get_open_games()
    games_details = []
    
    for game_id in open_games:
        details = game_engine.get_game_details(game_id)
        if details:
            games_details.append(details)
    
    return jsonify({"games": games_details})

@routes_bp.route('/games', methods=['POST'])
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
    game_id = game_engine.create_game(
        data['title'],
        int(data['rows']),
        int(data['cols']),
        int(data['max_time_per_turn']),
        int(data['num_turns']),
        int(data['num_obstacles']),
        int(data['max_players'])
    )
    
    return jsonify({"id_party": game_id}), 201

@routes_bp.route('/games/<int:game_id>', methods=['GET'])
def get_game(game_id):
    """Récupère les détails d'une partie"""
    details = game_engine.get_game_details(game_id)
    
    if details:
        return jsonify(details)
    else:
        return jsonify({"error": "Game not found"}), 404

@routes_bp.route('/games/<int:game_id>/join', methods=['POST'])
def join_game(game_id):
    """Rejoindre une partie"""
    data = request.json
    
    if 'player_name' not in data:
        return jsonify({"error": "Missing player_name"}), 400
        
    result, error = game_engine.add_player_to_game(game_id, data['player_name'])
    
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify(result)

@routes_bp.route('/games/<int:game_id>/start', methods=['POST'])
def start_game(game_id):
    """Démarrer une partie"""
    success, error = game_engine.start_game(game_id)
    
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify({"success": success})

@routes_bp.route('/games/<int:game_id>/board', methods=['GET'])
def get_board(game_id):
    """Récupérer l'état du plateau"""
    player_id = request.args.get('player_id', type=int)
    
    if player_id is None:
        return jsonify({"error": "Missing player_id parameter"}), 400
        
    result, error = game_engine.get_gameboard_status(game_id, player_id)
    
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify(result)

@routes_bp.route('/games/<int:game_id>/move', methods=['POST'])
def make_move(game_id):
    """Effectuer un mouvement"""
    data = request.json
    
    if 'player_id' not in data or 'move' not in data:
        return jsonify({"error": "Missing player_id or move"}), 400
        
    result, error = game_engine.add_move(game_id, data['player_id'], data['move'])
    
    if error:
        return jsonify({"error": error}), 400
        
    return jsonify(result)

@routes_bp.route('/api/documentation', methods=['GET'])
def api_docs():
    """Documentation de l'API"""
    return render_template('api_docs.html')

@routes_bp.route('/game/<int:game_id>/play', methods=['GET'])
def play_game(game_id):
    """Interface de jeu pour une partie spécifique"""
    player_id = request.args.get('player_id', type=int)
    
    if player_id is None:
        return render_template('error.html', message="ID du joueur requis"), 400
    
    game_details = game_engine.get_game_details(game_id)
    if not game_details:
        return render_template('error.html', message="Partie introuvable"), 404
        
    return render_template('play_game.html', 
                          game=game_details, 
                          player_id=player_id)

def register_routes(app):
    """Enregistre les routes dans l'application Flask"""
    app.register_blueprint(routes_bp)