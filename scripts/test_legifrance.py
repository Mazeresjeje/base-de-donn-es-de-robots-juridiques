import os
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LegifranceMinimal:
    def __init__(self):
        self.token = None
        self.base_url = "https://api.piste.gouv.fr/dila/legifrance-beta/lf-engine-app"  # Utilisation de l'API beta
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
        return {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_minimal_search(self):
        """Test avec la requête la plus simple possible"""
        if not self.get_oauth_token():
            return

        # Test 1: Requête simple sur le Code Général des Impôts
        endpoint = f"{self.base_url}/consult/code"
        payload = {
            "code": "CGIAN1"
        }

        logging.info("Test 1: Requête simple sur le CGI")
        logging.info(f"Endpoint: {endpoint}")
        logging.info(f"Payload: {payload}")

        response = requests.get(
            endpoint,
            headers=self.get_headers(),
            params=payload
        )

        logging.info(f"Status code: {response.status_code}")
        if response.status_code == 200:
            logging.info("Requête réussie!")
            logging.info(f"Réponse: {response.json()}")
        else:
            logging.error(f"Erreur: {response.text}")

        # Test 2: Version alternative avec recherche simple
        search_endpoint = f"{self.base_url}/search"
        search_payload = {
            "query": "787 B",
            "filter": {
                "textType": ["CODE"],
                "publicationDate": {
                    "start": "2010-01-01",
                    "end": datetime.now().strftime("%Y-%m-%d")
                }
            }
        }

        logging.info("\nTest 2: Recherche simple")
        logging.info(f"Endpoint: {search_endpoint}")
        logging.info(f"Payload: {search_payload}")

        response = requests.post(
            search_endpoint,
            headers=self.get_headers(),
            json=search_payload
        )

        logging.info(f"Status code: {response.status_code}")
        if response.status_code == 200:
            logging.info("Requête réussie!")
            logging.info(f"Réponse: {response.json()}")
        else:
            logging.error(f"Erreur: {response.text}")

if __name__ == "__main__":
    client = LegifranceMinimal()
    client.test_minimal_search()
