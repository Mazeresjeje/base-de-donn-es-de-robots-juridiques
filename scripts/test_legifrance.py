import os
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CGIArticleCollector:
    def __init__(self):
        self.token = None
        self.base_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        self.oauth_url = "https://oauth.piste.gouv.fr/api/oauth/token"
        self.client_id = os.environ.get('LEGIFRANCE_CLIENT_ID')
        self.client_secret = os.environ.get('LEGIFRANCE_CLIENT_SECRET')
        
        # Informations sur le CGI
        self.code_id = "LEGITEXT000006069577"

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
            'Content-Type': 'application/json'
        }

    def get_code_article(self, article_num):
        """Récupère un article du CGI"""
        url = f"{self.base_url}/consult/code/article"
        
        payload = {
            "code": "CGIAN1",
            "article": article_num,
            "date": int(datetime.now().timestamp() * 1000),
            "textId": self.code_id
        }

        logging.info(f"Récupération de l'article {article_num} du CGI...")
        logging.info(f"URL: {url}")
        logging.info(f"Payload: {payload}")
        
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        logging.info(f"Status code: {response.status_code}")
        try:
            result = response.json()
            logging.info(f"Réponse brute: {result}")
            if isinstance(result, dict):
                logging.info(f"Structure de la réponse: {list(result.keys())}")
            return result
        except Exception as e:
            logging.error(f"Erreur lors du parsing de la réponse: {e}")
            return None

    def get_article_from_code(self, article_num):
        """Récupère un article via l'endpoint /codes"""
        url = f"{self.base_url}/consult/codes"
        
        payload = {
            "date": int(datetime.now().timestamp() * 1000),
            "sctId": self.code_id,
            "textId": article_num
        }

        logging.info(f"\nTentative alternative via /codes...")
        logging.info(f"URL: {url}")
        logging.info(f"Payload: {payload}")
        
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        logging.info(f"Status code: {response.status_code}")
        try:
            result = response.json()
            logging.info(f"Réponse brute: {result}")
            return result
        except Exception as e:
            logging.error(f"Erreur lors du parsing de la réponse: {e}")
            return None

    def test_collection(self):
        """Test de récupération de l'article 787 B"""
        if not self.get_oauth_token():
            return

        # Test avec l'article 787 B
        article_num = "787 B"
        logging.info(f"\nTest pour l'article {article_num}")
        
        # Première tentative via /consult/code/article
        result = self.get_code_article(article_num)
        if not result or 'error' in result:
            # Deuxième tentative via /consult/codes
            result = self.get_article_from_code(article_num)

if __name__ == "__main__":
    collector = CGIArticleCollector()
    collector.test_collection()
