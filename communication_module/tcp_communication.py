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

class TcpCommunication:
    """Gestion de la communication TCP entre les modules du système"""
    
    def __init__(self, port=5003, host='127.0.0.1'):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.clients = []
        self.lock = threading.Lock()
        self.logger = logging.getLogger("TcpCommunication")
        self._setup_logging()
        
    def _setup_logging(self):
        """Configuration du logger"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def start(self):
        """Démarrer le serveur TCP pour la communication inter-modules"""
        try:
            # Créer le socket serveur
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(5)
            self.sock.setblocking(False)
            self.running = True
            self.logger.info(f"TCP Communication server started on {self.host}:{self.port}")
            
            # Boucle principale pour accepter les connexions
            while self.running:
                # Utiliser select pour attendre les connexions sans bloquer
                readable, _, _ = select.select([self.sock], [], [], 1.0)
                
                if self.sock in readable:
                    client_sock, addr = self.sock.accept()
                    self.logger.info(f"New connection from {addr}")
                    
                    # Ajouter le client à la liste
                    with self.lock:
                        self.clients.append(client_sock)
                    
                    # Démarrer un thread pour gérer ce client
                    client_thread = threading.Thread(target=self._handle_client, args=(client_sock, addr))
                    client_thread.daemon = True
                    client_thread.start()
                    
        except Exception as e:
            self.logger.error(f"Error in TCP Communication server: {e}")
        finally:
            self.stop()
    
    def _handle_client(self, client_sock, addr):
        """Gérer les communications avec un module client"""
        buffer = ""
        client_sock.setblocking(False)
        
        try:
            while self.running:
                # Utiliser select pour attendre des données sans bloquer
                readable, _, exceptional = select.select([client_sock], [], [client_sock], 1.0)
                
                if client_sock in exceptional:
                    self.logger.info(f"Connection closed by client {addr}")
                    break
                
                if client_sock in readable:
                    data = client_sock.recv(4096)
                    if not data:
                        self.logger.info(f"Client disconnected: {addr}")
                        break
                    
                    # Ajouter les données au buffer
                    buffer += data.decode('utf-8')
                    
                    # Traiter les messages complets dans le buffer
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line:
                            self._process_message(client_sock, addr, line)
        except Exception as e:
            self.logger.error(f"Error handling client {addr}: {e}")
        finally:
            # Fermer la connexion et retirer le client de la liste
            try:
                client_sock.close()
            except:
                pass
            
            with self.lock:
                if client_sock in self.clients:
                    self.clients.remove(client_sock)
            
            self.logger.info(f"Connection closed with {addr}")
    
    def _process_message(self, client_sock, addr, message):
        """Traiter un message reçu d'un module client"""
        try:
            self.logger.info(f"Message received from {addr}: {message}")
            
            # Essayer de parser le message en JSON
            data = json.loads(message)
            
            # Traiter les différents types de messages
            if 'type' in data:
                if data['type'] == 'admin_command':
                    self._handle_admin_command(client_sock, data)
                elif data['type'] == 'status_update':
                    self._handle_status_update(data)
                else:
                    self.logger.warning(f"Unknown message type: {data['type']}")
            else:
                self.logger.warning("Message has no type field")
                
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON format: {message}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def _handle_admin_command(self, client_sock, data):
        """Traiter une commande d'administration"""
        try:
            command = data.get('command', '')
            params = data.get('params', {})
            
            self.logger.info(f"Admin command received: {command} with params {params}")
            
            # Simuler le traitement des différentes commandes d'administration
            response = {"status": "ok", "timestamp": datetime.now().isoformat()}
            
            if command == 'create_game':
                response["game_id"] = 123  # Simulé
            elif command == 'start_game':
                response["success"] = True
            elif command == 'stop_game':
                response["success"] = True
            elif command == 'get_status':
                response["status_info"] = {
                    "active_games": 5,
                    "connected_players": 23,
                    "uptime": "02:34:56"
                }
            else:
                response = {"status": "error", "message": f"Unknown command: {command}"}
            
            # Envoyer la réponse
            self._send_message(client_sock, response)
            
        except Exception as e:
            self.logger.error(f"Error handling admin command: {e}")
            self._send_message(client_sock, {"status": "error", "message": str(e)})
    
    def _handle_status_update(self, data):
        """Traiter une mise à jour de statut"""
        try:
            status_type = data.get('status_type', '')
            status_data = data.get('data', {})
            
            self.logger.info(f"Status update received: {status_type} with data {status_data}")
            
            # Ici, vous pourriez notifier d'autres modules ou loggers des mises à jour
            
        except Exception as e:
            self.logger.error(f"Error handling status update: {e}")
    
    def _send_message(self, client_sock, data):
        """Envoyer un message à un client"""
        try:
            message = json.dumps(data) + '\n'
            client_sock.sendall(message.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
    
    def broadcast(self, message):
        """Envoyer un message à tous les clients connectés"""
        with self.lock:
            for client in list(self.clients):
                try:
                    self._send_message(client, message)
                except:
                    # Si l'envoi échoue, le client sera retiré dans _handle_client
                    pass
    
    def send_notification(self, notification_type, notification_data):
        """Envoyer une notification à tous les clients"""
        message = {
            "type": "notification",
            "notification_type": notification_type,
            "data": notification_data,
            "timestamp": datetime.now().isoformat()
        }
        self.broadcast(message)
    
    def send_game_update(self, game_id, update_type, update_data):
        """Envoyer une mise à jour de jeu à tous les clients"""
        message = {
            "type": "game_update",
            "game_id": game_id,
            "update_type": update_type,
            "data": update_data,
            "timestamp": datetime.now().isoformat()
        }
        self.broadcast(message)
    
    def stop(self):
        """Arrêter le serveur TCP"""
        self.running = False
        
        # Fermer tous les clients
        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        # Fermer le socket serveur
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        
        self.logger.info("TCP Communication server stopped")
        
# Pour le test individuel
if __name__ == "__main__":
    # Créer et démarrer le serveur de communication TCP
    comm_server = TcpCommunication(port=5003)
    
    # Démarrer dans un thread séparé pour pouvoir envoyer des notifications
    server_thread = threading.Thread(target=comm_server.start)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        print("TCP Communication server running. Press Ctrl+C to stop.")
        
        # Simuler l'envoi d'une notification toutes les 10 secondes
        count = 0
        while True:
            time.sleep(10)
            count += 1
            comm_server.send_notification(
                "server_status", 
                {"message": f"Server running for {count*10} seconds", "health": "good"}
            )
    except KeyboardInterrupt:
        comm_server.stop()