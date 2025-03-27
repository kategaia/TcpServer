import socket
import threading
import json
import sys
import os
import select
import time
import logging

# Ajouter le chemin parent pour pouvoir importer les modules frères
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_engine_module.game_engine import GameEngine
from .client_handler import ClientHandler
from .protocol import Protocol

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TcpServer:
    """Serveur TCP pour gérer les connexions des clients au jeu Les Loups"""
    
    def __init__(self, host='127.0.0.1', port=5001):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.clients = {}  # socket -> ClientHandler
        self.game_engine = GameEngine.get_instance()
        self.lock = threading.Lock()
        self.logger = logging.getLogger("TcpServer")
        
        # Enregistrer les callbacks pour les événements du jeu
        self.game_engine.register_turn_end_callback(self.on_turn_end)
        self.game_engine.register_game_end_callback(self.on_game_end)
    
    def start(self):
        """Démarrer le serveur TCP"""
        try:
            # Créer le socket serveur
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            self.sock.setblocking(False)
            self.running = True
            self.logger.info(f"Serveur TCP démarré sur {self.host}:{self.port}")
            
            # Boucle principale pour accepter les connexions
            while self.running:
                # Utilisation de select pour attendre des événements sans bloquer
                readable, _, _ = select.select([self.sock], [], [], 1.0)
                
                if self.sock in readable:
                    client_sock, addr = self.sock.accept()
                    self.logger.info(f"Nouvelle connexion de {addr}")
                    
                    # Créer un gestionnaire pour ce client
                    client_handler = ClientHandler(client_sock, addr, self)
                    
                    # Ajouter le client à la liste des clients
                    with self.lock:
                        self.clients[client_sock] = client_handler
                    
                    # Démarrer le thread pour gérer ce client
                    client_thread = threading.Thread(target=client_handler.handle)
                    client_thread.daemon = True
                    client_thread.start()
                    
        except Exception as e:
            self.logger.error(f"Erreur serveur TCP: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Arrêter le serveur TCP"""
        self.running = False
        
        # Fermer tous les sockets clients
        with self.lock:
            for client_sock in list(self.clients.keys()):
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
                
        self.logger.info("Serveur TCP arrêté")
    
    def remove_client(self, client_sock):
        """Supprimer un client de la liste des clients"""
        with self.lock:
            if client_sock in self.clients:
                del self.clients[client_sock]
                
    def on_turn_end(self, game_id, turn_number, move_results):
        """Callback appelé quand un tour se termine"""
        self.logger.info(f"Fin du tour {turn_number} pour la partie {game_id}")
        
        # Notifier tous les clients connectés à cette partie
        notification = {
            "notification": "turn_end",
            "id_party": game_id,
            "round": turn_number,
            "move_results": move_results
        }
        
        self.notify_game_clients(game_id, notification)
    
    def on_game_end(self, game_id, winner):
        """Callback appelé quand une partie se termine"""
        self.logger.info(f"Fin de la partie {game_id}, gagnant: {winner}")
        
        # Notifier tous les clients connectés à cette partie
        notification = {
            "notification": "game_end",
            "id_party": game_id,
            "winner": winner
        }
        
        self.notify_game_clients(game_id, notification)
    
    def notify_game_clients(self, game_id, notification):
        """Notifier tous les clients connectés à une partie spécifique"""
        with self.lock:
            for client_handler in self.clients.values():
                if client_handler.is_in_game(game_id):
                    client_handler.send_notification(notification)

# Point d'entrée pour démarrer le serveur
if __name__ == "__main__":
    server = TcpServer()
    server.start()