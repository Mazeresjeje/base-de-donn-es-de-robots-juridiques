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
        self.cgi_id = "LEGITEXT000006069577"

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

    def get_article_direct(self, article_id):
        """Récupère directement un article avec son ID complet"""
        url = f"{self.base_url}/consult/getArticle"
        
        payload = {
            "id": article_id
        }

        logging.info(f"Tentative de récupération directe de l'article {article_id}...")
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code == 200:
            logging.info(f"Article {article_id} récupéré avec succès")
            return response.json()
        else:
            logging.error(f"Erreur lors de la récupération de l'article {article_id}: {response.text}")
            return None

    def test_collection(self):
        """Test de récupération de l'article 787 B"""
        if not self.get_oauth_token():
            return

        # Utilisation directe de l'ID connu pour l'article 787 B
        article_787b_id = "LEGIARTI000027795329"
        logging.info(f"Test de récupération directe de l'article 787 B avec ID {article_787b_id}")
        
        article_content = self.get_article_direct(article_787b_id)
        
        if article_content:
            logging.info("Contenu de l'article 787 B:")
            logging.info(article_content)
            
            # Affichage des informations importantes
            if isinstance(article_content, dict):
                for key, value in article_content.items():
                    if isinstance(value, str):
                        excerpt = value[:200] + "..." if len(value) > 200 else value
                        logging.info(f"{key}: {excerpt}")

if __name__ == "__main__":
    collector = CGICollector()
    collector.test_collection()
