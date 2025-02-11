import os
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LegifranceExample:
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
        return {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def search_article(self):
        """Recherche selon l'exemple officiel de la documentation"""
        search_url = f"{self.base_url}/consult/lawArticle"
        
        payload = {
            "id": "LEGIARTI000027795329"  # ID connu de l'article 787 B
        }

        logging.info("Tentative de recherche d'article...")
        logging.info(f"URL: {search_url}")
        logging.info(f"Payload: {payload}")

        response = requests.post(
            search_url,
            headers=self.get_headers(),
            json=payload
        )

        logging.info(f"Status code: {response.status_code}")
        if response.status_code == 200:
            logging.info("Requête réussie!")
            result = response.json()
            logging.info(f"Réponse: {result}")
            return result
        else:
            logging.error(f"Erreur: {response.text}")
            return None

    def search_code_article(self):
        """Alternative avec recherche dans le code"""
        url = f"{self.base_url}/consult/code/article"
        
        payload = {
            "code": "CGIAN1",
            "numeroArticle": "787B"
        }

        logging.info("\nTentative de recherche dans le code...")
        logging.info(f"URL: {url}")
        logging.info(f"Payload: {payload}")

        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        logging.info(f"Status code: {response.status_code}")
        if response.status_code == 200:
            logging.info("Requête réussie!")
            result = response.json()
            logging.info(f"Réponse: {result}")
            return result
        else:
            logging.error(f"Erreur: {response.text}")
            return None

if __name__ == "__main__":
    client = LegifranceExample()
    if client.get_oauth_token():
        client.search_article()
        client.search_code_article()
