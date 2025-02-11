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

    def search_article(self, article_num):
        """Recherche un article pour obtenir son identifiant complet"""
        url = f"{self.base_url}/search"
        
        payload = {
            "recherche": {
                "champs": [
                    {
                        "typeChamp": "NUM_ARTICLE",
                        "criteres": [
                            {
                                "typeRecherche": "EXACTE",
                                "valeur": str(article_num),
                                "operateur": "ET"
                            }
                        ],
                        "operateur": "ET"
                    }
                ],
                "filtres": [
                    {
                        "facette": "CODE",
                        "valeur": "CGIAN1"
                    },
                    {
                        "facette": "ETAT_JURIDIQUE",
                        "valeur": "VIGUEUR"
                    }
                ],
                "pageNumber": 1,
                "pageSize": 1,
                "operateur": "ET",
                "sort": "PERTINENCE"
            }
        }

        logging.info(f"Recherche de l'article {article_num}...")
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code == 200:
            logging.info(f"Recherche réussie pour l'article {article_num}")
            results = response.json()
            logging.info(f"Résultats de la recherche: {results}")
            return results
        else:
            logging.error(f"Erreur lors de la recherche de l'article {article_num}: {response.text}")
            return None

    def get_article_content(self, article_id):
        """Récupère le contenu d'un article à partir de son ID complet"""
        url = f"{self.base_url}/consult/legi"
        
        payload = {
            "textId": self.cgi_id,
            "articleId": article_id
        }

        logging.info(f"Tentative de récupération de l'article {article_id}...")
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

        # D'abord rechercher l'identifiant complet
        search_results = self.search_article("787 B")
        
        if search_results and 'results' in search_results and search_results['results']:
            article_id = search_results['results'][0].get('id')
            logging.info(f"Identifiant trouvé pour l'article 787 B: {article_id}")
            
            # Maintenant récupérer le contenu avec l'ID complet
            article_content = self.get_article_content(article_id)
            
            if article_content:
                logging.info("Contenu de l'article 787 B:")
                logging.info(article_content)

if __name__ == "__main__":
    collector = CGICollector()
    collector.test_collection()
