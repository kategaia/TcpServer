import json
import socket
import logging
import threading
import select
from .protocol import Protocol

class ClientHandler:
    """Gestionnaire pour chaque connexion client TCP"""
    
    def __init__(self, client_socket, client_address, server):
        self.client_socket = client_socket
        self.client_address = client_address
        self.server = server
        self.protocol = Protocol()
        self.running = False
        self.player_id = None
        self.game_id = None
        self.buffer = ""
        self.lock = threading.Lock()
        self.logger = logging.getLogger(f"ClientHandler-{client_address}")
    
    def handle(self):
        """Gérer la connexion client"""
        self.running = True
        self.client_socket.setblocking(False)
        
        try:
            while self.running:
                # Utiliser select pour attendre des données sans bloquer
                readable, _, exceptional = select.select([self.client_socket], [], [self.client_socket], 1.0)
                
                if self.client_socket in exceptional:
                    self.logger.info(f"Connexion fermée par le client {self.client_address}")
                    break
                
                if self.client_socket in readable:
                    data = self.client_socket.recv(4096)
                    if not data:
                        self.logger.info(f"Client déconnecté: {self.client_address}")
                        break
                    
                    # Ajouter les données au buffer
                    self.buffer += data.decode('utf-8')
                    
                    # Traiter les messages complets dans le buffer
                    self._process_buffer()
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du client {self.client_address}: {e}")
        finally:
            self.close()
    
    def _process_buffer(self):
        """Traiter les messages JSON complets dans le buffer"""
        while '\n' in self.buffer:
            # Extraire le premier message complet
            line, self.buffer = self.buffer.split('\n', 1)
            
            # Traiter le message
            if line:
                self._handle_message(line)
    
    def _handle_message(self, message):
        """Traiter un message JSON du client"""
        try:
            # Utiliser le protocole pour traiter le message
            response = self.protocol.handle_message(message)
            
            # Envoyer la réponse au client
            self.send_message(response)
            
            # Extraire les informations de jeu et de joueur si disponibles
            self._update_game_info(message, response)
            
        except Exception as e:
            self.logger.error(f"Erreur lors du traitement du message: {e}")
            error_response = json.dumps({
                "status": "KO",
                "response": {
                    "error": "Erreur interne du serveur"
                }
            })
            self.send_message(error_response)
    
    def _update_game_info(self, message, response):
        """Mettre à jour les informations de jeu et de joueur"""
        try:
            message_json = json.loads(message)
            response_json = json.loads(response)
            
            # Si l'action était "subscribe" et la réponse est OK
            if message_json.get('action') == 'subscribe' and response_json.get('status') == 'OK':
                # Récupérer l'ID de la partie
                for param in message_json.get('parameters', []):
                    if 'id_party' in param:
                        self.game_id = int(param['id_party'])
                        break
                
                # Récupérer l'ID du joueur
                if 'response' in response_json and 'id_player' in response_json['response']:
                    self.player_id = response_json['response']['id_player']
            
            # Si l'action concernait une partie spécifique
            elif 'parameters' in message_json:
                for param in message_json.get('parameters', []):
                    if 'id_party' in param:
                        self.game_id = int(param['id_party'])
                        break
                    
                    if 'id_player' in param:
                        self.player_id = int(param['id_player'])
                        break
        except:
            pass
    
    def send_message(self, message):
        """Envoyer un message au client"""
        try:
            with self.lock:
                if not message.endswith('\n'):
                    message += '\n'
                self.client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi du message: {e}")
            self.close()
    
    def send_notification(self, notification):
        """Envoyer une notification au client"""
        try:
            notification_str = json.dumps(notification)
            self.send_message(notification_str)
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de la notification: {e}")
    
    def is_in_game(self, game_id):
        """Vérifier si le client est dans une partie spécifique"""
        return self.game_id == game_id
    
    def close(self):
        """Fermer la connexion client"""
        self.running = False
        
        try:
            self.client_socket.close()
        except:
            pass
        
        self.server.remove_client(self.client_socket)
        self.logger.info(f"Connexion fermée avec {self.client_address}")