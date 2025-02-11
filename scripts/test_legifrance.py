import os
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CGICollector:
    def __init__(self):
        self.token = None
        self.base_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        self.oauth_url = "https://oauth.piste.gouv.fr/api/oauth/token"
        self.client_id = os.environ.get('LEGIFRANCE_CLIENT_ID')
        self.client_secret = os.environ.get('LEGIFRANCE_CLIENT_SECRET')

    def get_oauth_token(self):
        """Obtention du token OAuth"""
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'openid'
        }
        logging.info("Tentative d'obtention du token OAuth...")
        response = requests.post(self.oauth_url, data=data)
        if response.status_code == 200:
            self.token = response.json()['access_token']
            logging.info("Token OAuth obtenu avec succès")
            return True
        logging.error(f"Erreur d'authentification: {response.text}")
        return False

    def get_headers(self):
        """Obtention des headers pour les requêtes"""
        return {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def search_text(self):
        """Recherche simple du texte"""
        url = f"{self.base_url}/search"
        
        payload = {
            "recherche": {
                "champs": [
                    {
                        "typeChamp": "TEXTE",
                        "criteres": [
                            {
                                "typeRecherche": "EXACTE",
                                "valeur": "transmission d'entreprise",
                                "operateur": "ET"
                            }
                        ]
                    }
                ],
                "filtres": [
                    {
                        "typeFiltre": "NATURE",
                        "values": ["LOI"]
                    },
                    {
                        "typeFiltre": "DATE_VERSION",
                        "dateSingle": int(datetime.now().timestamp() * 1000)
                    }
                ],
                "pageNumber": 1,
                "pageSize": 10,
                "sort": "PERTINENCE"
            }
        }

        logging.info("Lancement de la recherche...")
        logging.info(f"Payload: {payload}")
        
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code == 200:
            logging.info("Recherche réussie")
            result = response.json()
            logging.info(f"Résultats: {result}")
            return result
        else:
            logging.error(f"Erreur lors de la recherche: {response.status_code}")
            logging.error(f"Détails: {response.text}")
            return None

    def test_collection(self):
        """Test de la recherche"""
        if not self.get_oauth_token():
            return

        results = self.search_text()
        if results:
            if 'results' in results:
                for result in results['results']:
                    logging.info("\nDocument trouvé:")
                    if 'title' in result:
                        logging.info(f"Titre: {result['title']}")
                    if 'nature' in result:
                        logging.info(f"Nature: {result['nature']}")
                    if 'date' in result:
                        logging.info(f"Date: {result['date']}")

if __name__ == "__main__":
    collector = CGICollector()
    collector.test_collection()
