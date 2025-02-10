import os
import requests
import json
import logging
from datetime import datetime

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

    def get_text_content(self, text_id):
        """Récupère le contenu d'un texte"""
        if not self.token and not self.get_token():
            return None

        headers = {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

        try:
            # D'abord, essayons avec JORF
            payload = {
                "id": text_id,
                "nature": "ARTICLE"
            }
            
            response = requests.post(
                f"{self.base_url}/consult/jorf",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
                
            # Si ça ne marche pas, essayons avec JADE
            payload = {
                "id": text_id
            }
            
            response = requests.post(
                f"{self.base_url}/consult/jade",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
                
            logger.error(f"Erreur {response.status_code}: {response.text}")
            return None

        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
            return None

    def search_documents(self, theme, nature="ARRETE"):
        """Recherche des documents"""
        if not self.token and not self.get_token():
            return []

        headers = {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

        search_payload = {
            "recherche": {
                "champs": [
                    {
                        "typeChamp": "TEXTE",
                        "criteres": [
                            {
                                "typeRecherche": "EXACTE",
                                "valeur": theme,
                                "operateur": "ET"
                            }
                        ],
                        "operateur": "ET"
                    }
                ],
                "filtres": [
                    {
                        "facette": "NATURE_TEXTE",
                        "valeurs": [nature]
                    },
                    {
                        "facette": "ETAT_JURIDIQUE",
                        "valeurs": ["VIGUEUR"]
                    }
                ],
                "pageNumber": 1,
                "pageSize": 10,
                "sort": "PERTINENCE",
                "typePagination": "ARTICLE"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/search/jorf",
                headers=headers,
                json=search_payload
            )

            if response.status_code == 200:
                results = response.json()
                logger.info(f"Trouvé {len(results.get('results', []))} documents")
                return results.get('results', [])
            else:
                logger.error(f"Erreur de recherche: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
            return []

def main():
    collector = LegifranceCollector()
    
    themes = ["Pacte Dutreil", "DMTG", "Location meublée", "Revenus fonciers"]
    natures = ["LOI", "DECRET", "ARRETE", "CIRCULAIRE"]
    
    for theme in themes:
        logger.info(f"\nTraitement du thème: {theme}")
        for nature in natures:
            logger.info(f"\nRecherche de documents de type: {nature}")
            documents = collector.search_documents(theme, nature)
            
            for doc in documents:
                if 'title' in doc:
                    logger.info(f"\nTitre: {doc['title']}")
                    if 'id' in doc:
                        content = collector.get_text_content(doc['id'])
                        if content:
                            logger.info(f"Contenu récupéré ({len(str(content))} caractères)")
                        else:
                            logger.warning("Impossible de récupérer le contenu")

if __name__ == "__main__":
    main()
