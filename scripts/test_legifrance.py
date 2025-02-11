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
        
        # IDs connus des articles du CGI
        self.articles = {
            "787 B": "LEGIARTI000041471651",
            "787 C": "LEGIARTI000006305506"
        }

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

    def get_article(self, article_id):
        """Récupère le contenu d'un article via getArticle"""
        url = f"{self.base_url}/consult/getArticle"
        
        payload = {
            "id": article_id
        }

        logging.info(f"Récupération de l'article {article_id}...")
        logging.info(f"URL: {url}")
        logging.info(f"Headers: {self.get_headers()}")
        logging.info(f"Payload: {payload}")

        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        logging.info(f"Status code: {response.status_code}")
        logging.info(f"Réponse brute: {response.text}")

        if response.status_code == 200:
            result = response.json()
            logging.info(f"Réponse JSON: {result}")
            if result.get('article') is None:
                logging.warning("La réponse ne contient pas d'article")
            return result
        else:
            logging.error(f"Erreur lors de la récupération de l'article {article_id}: {response.text}")
            return None

    def test_collection(self):
        """Test de récupération des articles"""
        if not self.get_oauth_token():
            return

        # Test pour chaque article
        for article_name, article_id in self.articles.items():
            logging.info(f"\nTest pour l'article {article_name}")
            result = self.get_article(article_id)
            
            if result:
                logging.info(f"Résultat complet: {result}")
                article = result.get('article')
                if article:
                    logging.info(f"ID: {article.get('id', 'Non spécifié')}")
                    if 'texte' in article:
                        excerpt = article['texte'][:500] + "..." if len(article['texte']) > 500 else article['texte']
                        logging.info(f"Contenu: {excerpt}")
                else:
                    logging.info("Pas d'article dans la réponse")
            else:
                logging.info("Pas de résultat retourné")

if __name__ == "__main__":
    collector = ArticleCollector()
    collector.test_collection()
