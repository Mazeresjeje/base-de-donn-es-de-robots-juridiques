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

    def search_jorf_content(self, theme):
        """Recherche dans le JORF"""
        try:
            date_end = datetime.now()
            date_start = date_end - timedelta(days=365*2)  # 2 ans en arrière

            payload = {
                "theseParConcept": {
                    "operateur": "ET",
                    "listeConcepts": [
                        {
                            "typeConcept": "THEMATIQUE",
                            "motsCles": [theme]
                        }
                    ]
                },
                "pageNumber": 1,
                "pageSize": 10,
                "dateDebut": int(date_start.timestamp() * 1000),
                "dateFin": int(date_end.timestamp() * 1000)
            }

            response = requests.post(
                f"{self.base_url}/list/jorf",
                headers=self.get_headers(),
                json=payload
            )

            if response.status_code == 200:
                results = response.json()
                logger.info(f"Nombre de résultats JORF: {len(results.get('list', []))}")
                return results.get('list', [])
            else:
                logger.error(f"Erreur recherche JORF: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Erreur lors de la recherche JORF: {str(e)}")
            return []

    def get_jorf_text(self, jorftext):
        """Récupère le texte complet d'un JORF"""
        try:
            payload = {
                "id": jorftext,
                "origineJo": True
            }

            response = requests.post(
                f"{self.base_url}/consult/jorftext",
                headers=self.get_headers(),
                json=payload
            )

            if response.status_code == 200:
                document = response.json()
                logger.info(f"Document JORF récupéré: {document.get('titre', 'Sans titre')}")
                return document
            else:
                logger.error(f"Erreur récupération JORF: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Erreur lors de la récupération JORF: {str(e)}")
            return None

    def process_theme(self, theme):
        """Traite un thème spécifique"""
        if not self.token and not self.get_token():
            return

        logger.info(f"\nTraitement du thème: {theme}")
        results = self.search_jorf_content(theme)
        
        for result in results:
            jorf_id = result.get('id')
            if jorf_id:
                document = self.get_jorf_text(jorf_id)
                if document:
                    # Extrait les informations utiles
                    title = document.get('titre', 'Sans titre')
                    date_publi = document.get('datePubli')
                    contenu = document.get('texte', '')
                    
                    logger.info(f"""
                    Document trouvé:
                    Titre: {title}
                    Date: {date_publi}
                    Taille du contenu: {len(contenu)} caractères
                    """)

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
