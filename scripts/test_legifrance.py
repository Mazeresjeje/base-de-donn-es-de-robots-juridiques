import os
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ArticleCollector:
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
            'Content-Type': 'application/json'
        }

    def search_jorf(self, article_num):
        """Recherche dans le JORF"""
        url = f"{self.base_url}/consult/jorf"
        
        payload = {
            "recherche": {
                "texte": f"Article {article_num}",
                "nature": "LOI",
                "pubDate": datetime.now().strftime("%Y-%m-%d"),
                "page": 1,
                "pageSize": 10
            }
        }

        logging.info(f"Recherche de l'article {article_num} dans le JORF...")
        logging.info(f"Payload: {payload}")
        
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        logging.info(f"Status code: {response.status_code}")
        try:
            result = response.json()
            logging.info(f"Structure de la réponse: {list(result.keys()) if isinstance(result, dict) else 'Non dictionnaire'}")
            return result
        except Exception as e:
            logging.error(f"Erreur lors du parsing de la réponse: {e}")
            logging.error(f"Réponse brute: {response.text}")
            return None

    def get_article_content(self, jorf_id):
        """Récupère le contenu d'un article du JORF"""
        url = f"{self.base_url}/consult/jorfArticle"
        
        payload = {
            "id": jorf_id
        }

        logging.info(f"Récupération du contenu de l'article {jorf_id}...")
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        logging.info(f"Status code: {response.status_code}")
        try:
            result = response.json()
            logging.info(f"Structure de la réponse: {list(result.keys()) if isinstance(result, dict) else 'Non dictionnaire'}")
            return result
        except Exception as e:
            logging.error(f"Erreur lors du parsing de la réponse: {e}")
            logging.error(f"Réponse brute: {response.text}")
            return None

    def test_collection(self):
        """Test de récupération de l'article 787 B"""
        if not self.get_oauth_token():
            return

        logging.info("\nRecherche de l'article 787 B...")
        search_result = self.search_jorf("787 B")
        
        if search_result:
            logging.info(f"Résultat de la recherche: {search_result}")
            if isinstance(search_result, dict) and 'articles' in search_result:
                for article in search_result['articles']:
                    if 'id' in article:
                        content = self.get_article_content(article['id'])
                        if content:
                            logging.info(f"Contenu de l'article: {content}")

if __name__ == "__main__":
    collector = ArticleCollector()
    collector.test_collection()
