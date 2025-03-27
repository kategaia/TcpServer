import json
import sys
import os
import logging

# Ajouter le chemin parent pour pouvoir importer les modules frères
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine_module.game_engine import GameEngine

class Protocol:
    """
    Protocole de communication pour le serveur TCP
    Gère l'interprétation des messages JSON et les réponses à envoyer
    """
    
    def __init__(self):
        self.game_engine = GameEngine.get_instance()
        self.logger = logging.getLogger("Protocol")
    
    def handle_message(self, message_str):
        """
        Traite un message JSON envoyé par le client
        Retourne une réponse JSON
        """
        try:
            message = json.loads(message_str)
            
            if 'action' not in message:
                return self._error_response("Champ 'action' manquant")
                
            action = message.get('action')
            parameters = message.get('parameters', [])
            
            # Conversion de la liste des paramètres en dictionnaire
            params_dict = {}
            for param in parameters:
                if isinstance(param, dict):
                    params_dict.update(param)
            
            # Traitement des différentes actions
            if action == "list":
                return self._handle_list()
            elif action == "subscribe":
                return self._handle_subscribe(params_dict)
            elif action == "party_status":
                return self._handle_party_status(params_dict)
            elif action == "gameboard_status":
                return self._handle_gameboard_status(params_dict)
            elif action == "move":
                return self._handle_move(params_dict)
            else:
                return self._error_response(f"Action inconnue: {action}")
                
        except json.JSONDecodeError:
            return self._error_response("Format JSON invalide")
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du message: {e}")
            return self._error_response(f"Erreur serveur: {str(e)}")
    
    def _success_response(self, response_data):
        """Crée une réponse de succès avec les données fournies"""
        response = {
            "status": "OK",
            "response": response_data
        }
        return json.dumps(response)
    
    def _error_response(self, error_message):
        """Crée une réponse d'erreur avec le message fourni"""
        response = {
            "status": "KO",
            "response": {
                "error": error_message
            }
        }
        return json.dumps(response)
    
    def _handle_list(self):
        """Traite une requête de liste des parties disponibles"""
        parties_ouvertes = self.game_engine.get_open_games()
        return self._success_response({
            "id_parties": parties_ouvertes
        })
    
    def _handle_subscribe(self, params):
        """Traite une demande d'inscription à une partie"""
        player_name = params.get("player")
        id_party = params.get("id_party")
        
        if not player_name:
            return self._error_response("Paramètre 'player' manquant")
        if not id_party:
            return self._error_response("Paramètre 'id_party' manquant")
            
        try:
            id_party = int(id_party)
        except ValueError:
            return self._error_response("'id_party' doit être un entier")
            
        result, error = self.game_engine.add_player_to_game(id_party, player_name)
        if error:
            return self._error_response(error)
            
        return self._success_response(result)
    
    def _handle_party_status(self, params):
        """Traite une demande de statut d'une partie"""
        id_party = params.get("id_party")
        id_player = params.get("id_player")
        
        if not id_party:
            return self._error_response("Paramètre 'id_party' manquant")
        if not id_player:
            return self._error_response("Paramètre 'id_player' manquant")
            
        try:
            id_party = int(id_party)
            id_player = int(id_player)
        except ValueError:
            return self._error_response("'id_party' et 'id_player' doivent être des entiers")
            
        result, error = self.game_engine.get_party_status(id_party, id_player)
        if error:
            return self._error_response(error)
            
        return self._success_response({"party": result})
    
    def _handle_gameboard_status(self, params):
        """Traite une demande de statut du plateau de jeu"""
        id_party = params.get("id_party")
        id_player = params.get("id_player")
        
        if not id_party:
            return self._error_response("Paramètre 'id_party' manquant")
        if not id_player:
            return self._error_response("Paramètre 'id_player' manquant")
            
        try:
            id_party = int(id_party)
            id_player = int(id_player)
        except ValueError:
            return self._error_response("'id_party' et 'id_player' doivent être des entiers")
            
        result, error = self.game_engine.get_gameboard_status(id_party, id_player)
        if error:
            return self._error_response(error)
            
        return self._success_response(result)
    
    def _handle_move(self, params):
        """Traite une demande de déplacement"""
        id_party = params.get("id_party")
        id_player = params.get("id_player")
        move = params.get("move")
        
        if not id_party:
            return self._error_response("Paramètre 'id_party' manquant")
        if not id_player:
            return self._error_response("Paramètre 'id_player' manquant")
        if not move:
            return self._error_response("Paramètre 'move' manquant")
            
        try:
            id_party = int(id_party)
            id_player = int(id_player)
        except ValueError:
            return self._error_response("'id_party' et 'id_player' doivent être des entiers")
            
        if len(move) != 2 or not all(c in "01-" for c in move):
            return self._error_response("Format de mouvement invalide. Doit être 2 caractères indiquant le vecteur déplacement")
            
        result, error = self.game_engine.add_move(id_party, id_player, move)
        if error:
            return self._error_response(error)
            
        return self._success_response(result)