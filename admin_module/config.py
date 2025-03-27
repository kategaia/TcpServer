import os
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Union

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class GameConfig:
    """Configuration d'une partie de jeu"""
    title: str
    rows: int
    cols: int
    max_time_per_turn: int
    num_turns: int
    num_obstacles: int
    max_players: int
    
    # Paramètres calculés
    max_wolves: Optional[int] = None
    max_villagers: Optional[int] = None
    
    def __post_init__(self):
        """Calcule automatiquement les quotas de rôles si non définis"""
        if self.max_wolves is None:
            # Par défaut, environ 1/3 de loups et 2/3 de villageois
            self.max_wolves = max(1, self.max_players // 3)
        
        if self.max_villagers is None:
            self.max_villagers = max(1, self.max_players - self.max_wolves)
            
    def validate(self) -> Tuple[bool, str]:
        """
        Valide la configuration de la partie
        Retourne un tuple (valide, message d'erreur)
        """
        if self.rows <= 0:
            return False, "Le nombre de lignes doit être positif"
            
        if self.cols <= 0:
            return False, "Le nombre de colonnes doit être positif"
            
        if self.max_time_per_turn <= 0:
            return False, "Le temps maximum par tour doit être positif"
            
        if self.num_turns <= 0:
            return False, "Le nombre de tours doit être positif"
            
        if self.num_obstacles < 0:
            return False, "Le nombre d'obstacles ne peut pas être négatif"
            
        if self.max_players <= 1:
            return False, "Il faut au moins 2 joueurs"
            
        if self.max_wolves <= 0:
            return False, "Il faut au moins 1 loup"
            
        if self.max_villagers <= 0:
            return False, "Il faut au moins 1 villageois"
            
        if self.max_wolves + self.max_villagers != self.max_players:
            return False, "Le nombre total de loups et de villageois doit égaler le nombre maximum de joueurs"
            
        # Vérifier que le nombre d'obstacles n'est pas trop grand par rapport à la taille du plateau
        total_cells = self.rows * self.cols
        if self.num_obstacles >= total_cells - self.max_players:
            return False, "Trop d'obstacles pour la taille du plateau"
            
        return True, ""
    
    def to_dict(self) -> Dict:
        """Convertit l'objet en dictionnaire"""
        return asdict(self)


class ConfigManager:
    """Gestionnaire de configuration pour le module d'administration"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = config_dir
        self.logger = logging.getLogger("ConfigManager")
        
        # Créer le répertoire de configuration s'il n'existe pas
        os.makedirs(config_dir, exist_ok=True)
        
        # Templates de configuration prédéfinis
        self.templates = {
            "small": GameConfig(
                title="Petite partie",
                rows=5,
                cols=5,
                max_time_per_turn=30,
                num_turns=20,
                num_obstacles=3,
                max_players=4
            ),
            "medium": GameConfig(
                title="Partie moyenne",
                rows=8,
                cols=8,
                max_time_per_turn=45,
                num_turns=30,
                num_obstacles=8,
                max_players=8
            ),
            "large": GameConfig(
                title="Grande partie",
                rows=12,
                cols=12,
                max_time_per_turn=60,
                num_turns=40,
                num_obstacles=15,
                max_players=16
            )
        }
        
    def create_config(self, config_data: Dict) -> Tuple[Optional[GameConfig], str]:
        """
        Crée une nouvelle configuration à partir des données fournies
        Retourne un tuple (configuration, message d'erreur)
        """
        try:
            game_config = GameConfig(
                title=config_data.get('title', 'Nouvelle partie'),
                rows=int(config_data.get('rows', 8)),
                cols=int(config_data.get('cols', 8)),
                max_time_per_turn=int(config_data.get('max_time_per_turn', 30)),
                num_turns=int(config_data.get('num_turns', 20)),
                num_obstacles=int(config_data.get('num_obstacles', 5)),
                max_players=int(config_data.get('max_players', 8)),
                max_wolves=int(config_data.get('max_wolves')) if 'max_wolves' in config_data else None,
                max_villagers=int(config_data.get('max_villagers')) if 'max_villagers' in config_data else None
            )
            
            # Valider la configuration
            valid, message = game_config.validate()
            if not valid:
                return None, message
                
            return game_config, ""
            
        except (ValueError, TypeError) as e:
            self.logger.error(f"Erreur lors de la création de la configuration: {e}")
            return None, f"Données de configuration invalides: {str(e)}"
    
    def save_config(self, config_name: str, game_config: GameConfig) -> bool:
        """
        Enregistre une configuration dans un fichier
        Retourne True si l'opération a réussi, False sinon
        """
        try:
            # Valider la configuration
            valid, message = game_config.validate()
            if not valid:
                self.logger.error(f"Impossible d'enregistrer la configuration: {message}")
                return False
                
            # Créer le chemin du fichier
            config_path = os.path.join(self.config_dir, f"{config_name}.json")
            
            # Enregistrer la configuration dans un fichier JSON
            with open(config_path, 'w') as f:
                json.dump(game_config.to_dict(), f, indent=2)
                
            self.logger.info(f"Configuration '{config_name}' enregistrée avec succès")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'enregistrement de la configuration: {e}")
            return False
    
    def load_config(self, config_name: str) -> Tuple[Optional[GameConfig], str]:
        """
        Charge une configuration à partir d'un fichier
        Retourne un tuple (configuration, message d'erreur)
        """
        try:
            # Si le nom est un template prédéfini
            if config_name in self.templates:
                return self.templates[config_name], ""
            
            # Sinon, essayer de charger depuis un fichier
            config_path = os.path.join(self.config_dir, f"{config_name}.json")
            
            # Vérifier si le fichier existe
            if not os.path.exists(config_path):
                return None, f"Configuration '{config_name}' introuvable"
                
            # Charger la configuration depuis le fichier JSON
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                
            # Créer l'objet de configuration
            game_config = GameConfig(**config_data)
            
            # Valider la configuration
            valid, message = game_config.validate()
            if not valid:
                return None, f"Configuration invalide: {message}"
                
            return game_config, ""
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return None, f"Erreur lors du chargement de la configuration: {str(e)}"
    
    def list_configs(self) -> List[str]:
        """
        Liste toutes les configurations disponibles (templates et fichiers)
        Retourne une liste de noms de configuration
        """
        try:
            # Récupérer les templates prédéfinis
            config_names = list(self.templates.keys())
            
            # Récupérer les fichiers de configuration
            if os.path.exists(self.config_dir):
                for filename in os.listdir(self.config_dir):
                    if filename.endswith('.json'):
                        config_name = filename[:-5]  # Enlever l'extension '.json'
                        if config_name not in config_names:
                            config_names.append(config_name)
                            
            return config_names
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la liste des configurations: {e}")
            return []
    
    def delete_config(self, config_name: str) -> Tuple[bool, str]:
        """
        Supprime une configuration
        Retourne un tuple (succès, message)
        """
        try:
            # Vérifier si c'est un template prédéfini
            if config_name in self.templates:
                return False, "Impossible de supprimer un template prédéfini"
            
            # Vérifier si le fichier existe
            config_path = os.path.join(self.config_dir, f"{config_name}.json")
            if not os.path.exists(config_path):
                return False, f"Configuration '{config_name}' introuvable"
                
            # Supprimer le fichier
            os.remove(config_path)
            self.logger.info(f"Configuration '{config_name}' supprimée avec succès")
            return True, ""
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression de la configuration: {e}")
            return False, f"Erreur lors de la suppression de la configuration: {str(e)}"