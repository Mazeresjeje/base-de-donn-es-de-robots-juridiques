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

    def search_cgi_article(self):
        logging.info("Recherche de l'article 787 B dans le CGI...")
        
        search_payload = {
            "recherche": {
                "champs": [
                    {
                        "typeChamp": "NUM_ARTICLE",
                        "criteres": [
                            {
                                "typeRecherche": "EXACTE",
                                "valeur": "787 B",
                                "operateur": "ET"
                            }
                        ],
                        "operateur": "ET"
                    }
                ],
                "filtres": [
                    {
                        "facette": "CODE",
                        "valeur": "CGIAN2"
                    },
                    {
                        "facette": "DATE_VERSION",
                        "singleDate": int(datetime.now().timestamp() * 1000)
                    }
                ],
                "pageNumber": 1,
                "pageSize": 1,
                "operateur": "ET",
                "sort": "PERTINENCE",
                "typePagination": "ARTICLE"
            },
            "fond": "CODE_DATE"
        }

        response = requests.post(
            f"{self.base_url}/search",
            headers=self.get_headers(),
            json=search_payload
        )

        if response.status_code != 200:
            logging.error(f"Erreur lors de la recherche: {response.text}")
            return None

        results = response.json()
        logging.info(f"Résultats de la recherche: {results}")
        return results

    def get_article_content(self, article_id):
        logging.info(f"Récupération du contenu de l'article {article_id}...")
        
        payload = {
            "id": article_id
        }

        response = requests.post(
            f"{self.base_url}/consult/getArticle",
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code != 200:
            logging.error(f"Erreur lors de la récupération du contenu: {response.text}")
            return None

        content = response.json()
        logging.info(f"Contenu récupéré avec succès")
        return content

    def collect(self):
        if not self.get_oauth_token():
            return

        # Recherche de l'article
        search_results = self.search_cgi_article()
        if not search_results:
            logging.error("Aucun résultat trouvé")
            return

        # Pour chaque résultat trouvé
        if 'results' in search_results:
            for result in search_results['results']:
                logging.info(f"Article trouvé")
                
                # Récupération des détails de l'article
                if 'id' in result:
                    article_content = self.get_article_content(result['id'])
                    if article_content:
                        logging.info(f"Contenu de l'article:")
                        logging.info(article_content)

if __name__ == "__main__":
    collector = CGICollector()
    collector.collect()
