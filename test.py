import sys
import os

# Ajouter le chemin du dossier TcpServeur au PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), "TcpServeur"))

from game_engine_module.game_engine import GameEngine
import time

def test_game_engine():
    print("===== Test du module game_engine_module =====")
    
    # Récupérer l'instance du moteur de jeu
    game_engine = GameEngine.get_instance()
    
    # 1. Créer une partie
    print("\n1. Création d'une partie...")
    game_id = game_engine.create_game(
        title="Test Game",
        rows=5,
        cols=5,
        max_time_per_turn=10,  # 10 secondes par tour pour accélérer le test
        num_turns=5,
        num_obstacles=3,
        max_players=4
    )
    print(f"Partie créée avec l'ID: {game_id}")
    
    # 2. Récupérer les détails de la partie
    print("\n2. Récupération des détails de la partie...")
    game_details = game_engine.get_game_details(game_id)
    print(f"Détails de la partie: {game_details}")
    
    # 3. Ajouter des joueurs
    print("\n3. Ajout de joueurs à la partie...")
    player1, error1 = game_engine.add_player_to_game(game_id, "Joueur1")
    player2, error2 = game_engine.add_player_to_game(game_id, "Joueur2")
    
    if error1:
        print(f"Erreur lors de l'ajout du joueur 1: {error1}")
    else:
        print(f"Joueur 1 ajouté: ID={player1['id_player']}, Rôle={player1['role']}")
    
    if error2:
        print(f"Erreur lors de l'ajout du joueur 2: {error2}")
    else:
        print(f"Joueur 2 ajouté: ID={player2['id_player']}, Rôle={player2['role']}")
    
    # 4. Démarrer la partie
    print("\n4. Démarrage de la partie...")
    success, error = game_engine.start_game(game_id)
    
    if error:
        print(f"Erreur lors du démarrage de la partie: {error}")
    else:
        print(f"La partie a démarré avec succès: {success}")
    
    # 5. Récupérer l'état du plateau
    print("\n5. Récupération de l'état du plateau...")
    board_state, error = game_engine.get_gameboard_status(game_id, player1['id_player'])
    
    if error:
        print(f"Erreur lors de la récupération de l'état du plateau: {error}")
    else:
        print(f"État du plateau: {board_state}")
    
    # 6. Effectuer un déplacement pour le joueur 1
    print("\n6. Déplacement du joueur 1...")
    move_result, error = game_engine.add_move(game_id, player1['id_player'], "01")  # Déplacement vers la droite
    
    if error:
        print(f"Erreur lors du déplacement du joueur 1: {error}")
    else:
        print(f"Résultat du déplacement: {move_result}")
    
    # 7. Attendre la fin du tour
    print("\n7. Attente de la fin du tour (10 secondes maximum)...")
    for i in range(10):
        time.sleep(1)
        print(f"Attente... {i+1}/10 secondes écoulées")
        
        # Vérifier si le tour est terminé
        game_state = game_engine.games[game_id]
        if game_state.current_turn > 1 or not game_state.started:
            print("Le tour est terminé !")
            break
    
    # 8. Vérifier l'état final
    print("\n8. Vérification de l'état final...")
    game_details = game_engine.get_game_details(game_id)
    print(f"Détails de la partie: {game_details}")
    
    # 9. Afficher les mouvements résolus
    print("\n9. Affichage des joueurs et leurs positions...")
    game_state = game_engine.games[game_id]
    for player_id, player in game_state.board.players.items():
        print(f"Joueur {player.id_player} ({player.role}): Position={player.position}, Vivant={player.is_alive}")
    
    print("\n===== Test terminé =====")

if __name__ == "__main__":
    test_game_engine()