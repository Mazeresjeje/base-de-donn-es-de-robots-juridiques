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
        
        # Liste des articles avec leurs versions
        self.articles = {
            "787 B": [
                "LEGIARTI000041471651",  # Version actuelle
                "LEGIARTI000038612430",  # Version précédente
                "LEGIARTI000027795329"   # Version antérieure
            ]
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

        logging.info(f"Tentative de récupération de l'article {article_id}...")
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        logging.info(f"Status code: {response.status_code}")
        
        try:
            result = response.json()
            logging.info(f"Structure de la réponse: {list(result.keys())}")
            return result
        except Exception as e:
            logging.error(f"Erreur lors du parsing de la réponse: {e}")
            logging.error(f"Réponse brute: {response.text}")
            return None

    def test_collection(self):
        """Test de récupération des articles"""
        if not self.get_oauth_token():
            return

        # Test pour chaque article et ses versions
        for article_name, versions in self.articles.items():
            logging.info(f"\nTest de l'article {article_name}")
            for version_id in versions:
                logging.info(f"\nTest de la version {version_id}")
                result = self.get_article(version_id)
                
                if result:
                    logging.info("Clés de la réponse :")
                    for key in result.keys():
                        logging.info(f"- {key}")
                    
                    article = result.get('article')
                    if article:
                        logging.info(f"ID article: {article.get('id', 'Non spécifié')}")
                        if 'texte' in article:
                            logging.info(f"Texte: {article['texte']}")
                        else:
                            logging.info("Pas de texte disponible")
                        
                        if 'etat' in article:
                            logging.info(f"État: {article['etat']}")
                        
                        if 'dateDebut' in article:
                            date_debut = datetime.fromtimestamp(article['dateDebut']/1000)
                            logging.info(f"Date de début: {date_debut}")
                    else:
                        logging.info("Pas de contenu d'article dans la réponse")

if __name__ == "__main__":
    collector = ArticleCollector()
    collector.test_collection()
