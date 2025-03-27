import socket
import threading
import json
import logging
import select
import sys
import os
import time
from datetime import datetime

# Ajouter le chemin parent pour pouvoir importer les modules frères
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .config import ConfigManager, GameConfig
from communication_module.tcp_communication import TcpCommunication
from game_engine_module.game_engine import GameEngine

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AdminServer:
    """Serveur d'administration pour le jeu Les Loups"""
    
    def __init__(self, host='127.0.0.1', port=5004):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.clients = []
        self.lock = threading.Lock()
        self.logger = logging.getLogger("AdminServer")
        
        # Gestionnaire de configuration
        self.config_manager = ConfigManager()
        
        # Moteur de jeu
        self.game_engine = GameEngine.get_instance()
        
        # Communication TCP avec les autres modules
        self.tcp_comm = TcpCommunication(port=5003)
        
    def start(self):
        """Démarrer le serveur d'administration"""
        try:
            # Créer le socket serveur
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            self.sock.setblocking(False)
            self.running = True
            self.logger.info(f"Serveur d'administration démarré sur {self.host}:{self.port}")
            
            # Démarrer la communication TCP dans un thread séparé
            tcp_thread = threading.Thread(target=self.tcp_comm.start)
            tcp_thread.daemon = True
            tcp_thread.start()
            
            # Boucle principale pour accepter les connexions
            while self.running:
                # Utiliser select pour attendre les connexions sans bloquer
                readable, _, _ = select.select([self.sock], [], [], 1.0)
                
                if self.sock in readable:
                    client_sock, addr = self.sock.accept()
                    self.logger.info(f"Nouvelle connexion de {addr}")
                    
                    # Ajouter le client à la liste
                    with self.lock:
                        self.clients.append(client_sock)
                    
                    # Démarrer un thread pour gérer ce client
                    client_thread = threading.Thread(target=self._handle_client, args=(client_sock, addr))
                    client_thread.daemon = True
                    client_thread.start()
                    
        except Exception as e:
            self.logger.error(f"Erreur serveur administration: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Arrêter le serveur d'administration"""
        self.running = False
        
        # Arrêter la communication TCP
        self.tcp_comm.stop()
        
        # Fermer tous les sockets clients
        with self.lock:
            for client_sock in self.clients:
                try:
                    client_sock.close()
                except:
                    pass
            self.clients.clear()
        
        # Fermer le socket serveur
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
                
        self.logger.info("Serveur d'administration arrêté")
    
    def _handle_client(self, client_sock, addr):
        """Gérer les communications avec un client administrateur"""
        buffer = ""
        client_sock.setblocking(False)
        
        try:
            while self.running:
                # Utiliser select pour attendre des données sans bloquer
                readable, _, exceptional = select.select([client_sock], [], [client_sock], 1.0)
                
                if client_sock in exceptional:
                    self.logger.info(f"Connexion fermée par le client {addr}")
                    break
                
                if client_sock in readable:
                    data = client_sock.recv(4096)
                    if not data:
                        self.logger.info(f"Client déconnecté: {addr}")
                        break
                    
                    # Ajouter les données au buffer
                    buffer += data.decode('utf-8')
                    
                    # Traiter les messages complets dans le buffer
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line:
                            self._process_message(client_sock, addr, line)
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du client {addr}: {e}")
        finally:
            # Fermer la connexion et retirer le client de la liste
            try:
                client_sock.close()
            except:
                pass
            
            with self.lock:
                if client_sock in self.clients:
                    self.clients.remove(client_sock)
            
            self.logger.info(f"Connexion fermée avec {addr}")
    
    def _process_message(self, client_sock, addr, message):
        """Traiter un message reçu d'un client administrateur"""
        try:
            self.logger.info(f"Message reçu de {addr}: {message}")
            
            # Essayer de parser le message en JSON
            data = json.loads(message)
            
            # Vérifier si le message contient un champ 'command'
            if 'command' not in data:
                self._send_error(client_sock, "Champ 'command' manquant")
                return
                
            # Récupérer la commande
            command = data['command']
            params = data.get('params', {})
            
            # Traiter les différentes commandes
            if command == "list_configs":
                self._handle_list_configs(client_sock)
            elif command == "get_config":
                self._handle_get_config(client_sock, params)
            elif command == "create_config":
                self._handle_create_config(client_sock, params)
            elif command == "save_config":
                self._handle_save_config(client_sock, params)
            elif command == "delete_config":
                self._handle_delete_config(client_sock, params)
            elif command == "create_game":
                self._handle_create_game(client_sock, params)
            elif command == "list_games":
                self._handle_list_games(client_sock)
            elif command == "get_game":
                self._handle_get_game(client_sock, params)
            elif command == "start_game":
                self._handle_start_game(client_sock, params)
            elif command == "get_stats":
                self._handle_get_stats(client_sock)
            else:
                self._send_error(client_sock, f"Commande inconnue: {command}")
                
        except json.JSONDecodeError:
            self._send_error(client_sock, "Format JSON invalide")
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du message: {e}")
            self._send_error(client_sock, f"Erreur serveur: {str(e)}")
    
    def _send_response(self, client_sock, response_data):
        """Envoyer une réponse à un client"""
        try:
            # Créer un message JSON
            response = {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "data": response_data
            }
            
            # Envoyer la réponse
            message = json.dumps(response) + '\n'
            client_sock.sendall(message.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de la réponse: {e}")
    
    def _send_error(self, client_sock, error_message):
        """Envoyer un message d'erreur à un client"""
        try:
            # Créer un message JSON d'erreur
            response = {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "message": error_message
            }
            
            # Envoyer la réponse
            message = json.dumps(response) + '\n'
            client_sock.sendall(message.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi du message d'erreur: {e}")
    
    def _handle_list_configs(self, client_sock):
        """Traiter une commande de liste des configurations"""
        configs = self.config_manager.list_configs()
        self._send_response(client_sock, {"configs": configs})
    
    def _handle_get_config(self, client_sock, params):
        """Traiter une commande de récupération d'une configuration"""
        if 'name' not in params:
            self._send_error(client_sock, "Paramètre 'name' manquant")
            return
            
        name = params['name']
        config, error = self.config_manager.load_config(name)
        
        if error:
            self._send_error(client_sock, error)
        else:
            self._send_response(client_sock, {"config": config.to_dict()})
    
    def _handle_create_config(self, client_sock, params):
        """Traiter une commande de création d'une configuration"""
        if 'config' not in params:
            self._send_error(client_sock, "Paramètre 'config' manquant")
            return
            
        config_data = params['config']
        config, error = self.config_manager.create_config(config_data)
        
        if error:
            self._send_error(client_sock, error)
        else:
            self._send_response(client_sock, {"config": config.to_dict()})
    
    def _handle_save_config(self, client_sock, params):
        """Traiter une commande d'enregistrement d'une configuration"""
        if 'name' not in params:
            self._send_error(client_sock, "Paramètre 'name' manquant")
            return
            
        if 'config' not in params:
            self._send_error(client_sock, "Paramètre 'config' manquant")
            return
            
        name = params['name']
        config_data = params['config']
        
        # Créer l'objet de configuration
        config, error = self.config_manager.create_config(config_data)
        
        if error:
            self._send_error(client_sock, error)
            return
            
        # Enregistrer la configuration
        success = self.config_manager.save_config(name, config)
        
        if success:
            self._send_response(client_sock, {"saved": name})
        else:
            self._send_error(client_sock, "Impossible d'enregistrer la configuration")
    
    def _handle_delete_config(self, client_sock, params):
        """Traiter une commande de suppression d'une configuration"""
        if 'name' not in params:
            self._send_error(client_sock, "Paramètre 'name' manquant")
            return
            
        name = params['name']
        success, message = self.config_manager.delete_config(name)
        
        if success:
            self._send_response(client_sock, {"deleted": name})
        else:
            self._send_error(client_sock, message)
    
    def _handle_create_game(self, client_sock, params):
        """Traiter une commande de création d'une partie"""
        if 'config_name' in params:
            # Créer une partie à partir d'une configuration existante
            config_name = params['config_name']
            config, error = self.config_manager.load_config(config_name)
            
            if error:
                self._send_error(client_sock, error)
                return
                
            # Créer la partie
            game_id = self.game_engine.create_game(
                config.title,
                config.rows,
                config.cols,
                config.max_time_per_turn,
                config.num_turns,
                config.num_obstacles,
                config.max_players
            )
            
            self._send_response(client_sock, {
                "game_id": game_id,
                "config": config.to_dict()
            })
            
        elif 'config' in params:
            # Créer une partie à partir d'une configuration fournie
            config_data = params['config']
            config, error = self.config_manager.create_config(config_data)
            
            if error:
                self._send_error(client_sock, error)
                return
                
            # Créer la partie
            game_id = self.game_engine.create_game(
                config.title,
                config.rows,
                config.cols,
                config.max_time_per_turn,
                config.num_turns,
                config.num_obstacles,
                config.max_players
            )
            
            self._send_response(client_sock, {
                "game_id": game_id,
                "config": config.to_dict()
            })
            
        else:
            self._send_error(client_sock, "Paramètre 'config_name' ou 'config' manquant")
    
    def _handle_list_games(self, client_sock):
        """Traiter une commande de liste des parties"""
        open_games = self.game_engine.get_open_games()
        games_details = []
        
        for game_id in open_games:
            details = self.game_engine.get_game_details(game_id)
            if details:
                games_details.append(details)
        
        self._send_response(client_sock, {"games": games_details})
    
    def _handle_get_game(self, client_sock, params):
        """Traiter une commande de récupération d'une partie"""
        if 'game_id' not in params:
            self._send_error(client_sock, "Paramètre 'game_id' manquant")
            return
            
        try:
            game_id = int(params['game_id'])
        except ValueError:
            self._send_error(client_sock, "'game_id' doit être un entier")
            return
            
        details = self.game_engine.get_game_details(game_id)
        
        if details:
            self._send_response(client_sock, {"game": details})
        else:
            self._send_error(client_sock, f"Partie {game_id} introuvable")
    
    def _handle_start_game(self, client_sock, params):
        """Traiter une commande de démarrage d'une partie"""
        if 'game_id' not in params:
            self._send_error(client_sock, "Paramètre 'game_id' manquant")
            return
            
        try:
            game_id = int(params['game_id'])
        except ValueError:
            self._send_error(client_sock, "'game_id' doit être un entier")
            return
            
        success, error = self.game_engine.start_game(game_id)
        
        if success:
            # Notifier les autres modules que la partie a démarré
            self.tcp_comm.send_game_update(
                game_id, 
                "game_started", 
                {"game_id": game_id}
            )
            
            self._send_response(client_sock, {"game_id": game_id, "started": True})
        else:
            self._send_error(client_sock, error or f"Impossible de démarrer la partie {game_id}")
    
    def _handle_get_stats(self, client_sock):
        """Traiter une commande de récupération des statistiques"""
        # Collecter les statistiques
        stats = {
            "server_uptime": self._get_uptime(),
            "active_games": len(self.game_engine.games),
            "open_games": len(self.game_engine.get_open_games()),
            "connected_players": self._count_connected_players()
        }
        
        self._send_response(client_sock, {"stats": stats})
    
    def _get_uptime(self):
        """Obtenir le temps d'activité du serveur"""
        # Dans une implémentation réelle, on stockerait l'heure de démarrage
        return "00:00:00"
    
    def _count_connected_players(self):
        """Compter le nombre de joueurs connectés"""
        count = 0
        for game in self.game_engine.games.values():
            count += sum(1 for p in game.board.players.values() if p.is_alive)
        return count


# Point d'entrée pour démarrer le serveur
if __name__ == "__main__":
    server = AdminServer()
    server.start()