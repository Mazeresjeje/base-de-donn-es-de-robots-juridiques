import os
import requests
import json
import logging
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegifranceCollector:
    def __init__(self):
        self.token = None
        self.base_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        
    def get_token(self):
        """Obtient un token OAuth"""
        try:
            token_url = "https://oauth.piste.gouv.fr/api/oauth/token"
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': os.environ.get("LEGIFRANCE_CLIENT_ID"),
                'client_secret': os.environ.get("LEGIFRANCE_CLIENT_SECRET"),
                'scope': 'openid'
            }
            
            response = requests.post(token_url, data=token_data)
            if response.status_code == 200:
                self.token = response.json()['access_token']
                logger.info("Token OAuth obtenu avec succès")
                return True
            else:
                logger.error(f"Erreur d'authentification: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention du token: {str(e)}")
            return False

    def get_headers(self):
        """Retourne les headers pour les requêtes API"""
        return {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def query_jorfsimple(self, theme):
        """Recherche dans JORFSIMPLE avec des paramètres simplifiés"""
        try:
            logger.info(f"Recherche de documents pour le thème: {theme}")
            
            payload = {
                "textCons": theme,
                "nature": "ALL",
                "offset": 0,
                "limit": 10,
                "order": "DESC"
            }
            
            response = requests.post(
                f"{self.base_url}/consult/simple",
                headers=self.get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                results = response.json()
                logger.info(f"Résultats trouvés: {len(results)}")
                return results
            else:
                logger.error(f"Erreur de recherche: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            return []

    def get_text_details(self, id_text):
        """Récupère les détails d'un texte"""
        try:
            payload = {
                "textId": id_text
            }
            
            response = requests.post(
                f"{self.base_url}/consult/jorfsimple",
                headers=self.get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erreur lors de la récupération du texte: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du texte: {str(e)}")
            return None

    def process_theme(self, theme):
        """Traite un thème spécifique"""
        if not self.token and not self.get_token():
            return

        logger.info(f"\nTraitement du thème: {theme}")
        
        # Recherche des documents
        results = self.query_jorfsimple(theme)
        
        for result in results:
            logger.info("-" * 50)
            logger.info(f"Titre: {result.get('title', 'Sans titre')}")
            
            if 'id' in result:
                content = self.get_text_details(result['id'])
                if content:
                    logger.info(f"""
                    Document récupéré :
                    - Date: {content.get('datePubli', 'Date inconnue')}
                    - Nature: {content.get('nature', 'Nature inconnue')}
                    - Taille du contenu: {len(str(content.get('text', '')))} caractères
                    """)
                else:
                    logger.warning(f"Impossible de récupérer le contenu pour l'ID: {result['id']}")

def main():
    collector = LegifranceCollector()
    themes = [
        "Pacte Dutreil",
        "droits de mutation à titre gratuit",
        "location meublée",
        "revenus fonciers"
    ]
    
    for theme in themes:
        collector.process_theme(theme)

if __name__ == "__main__":
    main()
