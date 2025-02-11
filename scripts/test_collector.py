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
        
        # Définition des articles à collecter
        self.article_ranges = [
            ["787 B"],
            ["787 C"],
            range(750, 809),  # 750 ter à 808
            range(14, 34),    # 14 à 33 quinquies
            range(150, 151),  # 150 A bis à 150 VH
            range(79, 91),    # 79 à 90
            range(14, 156)    # 14 à 155 B
        ]

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

    def search_cgi_article(self, article_num):
        """Recherche un article spécifique dans le CGI"""
        logging.info(f"Recherche de l'article {article_num} dans le CGI...")
        
        search_payload = {
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
                        "valeur": "CGIAN1"  # Code général des impôts
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
            f"{self.base_url}/consult/code",
            headers=self.get_headers(),
            json=search_payload
        )

        if response.status_code == 200:
            logging.info(f"Article {article_num} trouvé")
            result = response.json()
            return result
        else:
            logging.error(f"Erreur lors de la recherche de l'article {article_num}: {response.text}")
            return None

    def get_article_content(self, article_id):
        """Récupère le contenu d'un article par son ID"""
        payload = {
            "textId": article_id
        }

        response = requests.post(
            f"{self.base_url}/consult/getArticle",
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code == 200:
            logging.info(f"Contenu récupéré pour l'article {article_id}")
            return response.json()
        else:
            logging.error(f"Erreur lors de la récupération du contenu de l'article {article_id}: {response.text}")
            return None

    def collect(self):
        """Collecte tous les articles spécifiés"""
        if not self.get_oauth_token():
            return

        collected_articles = []
        
        # Traitement de chaque plage d'articles
        for article_range in self.article_ranges:
            if isinstance(article_range, list):
                # Pour les articles spécifiques comme "787 B"
                for article in article_range:
                    logging.info(f"Traitement de l'article {article}")
                    result = self.search_cgi_article(article)
                    if result:
                        collected_articles.append(result)
            else:
                # Pour les plages numériques
                for article_num in article_range:
                    logging.info(f"Traitement de l'article {article_num}")
                    result = self.search_cgi_article(article_num)
                    if result:
                        collected_articles.append(result)

        logging.info(f"Nombre total d'articles collectés: {len(collected_articles)}")
        return collected_articles

if __name__ == "__main__":
    collector = CGICollector()
    articles = collector.collect()
    for article in articles:
        logging.info(f"Article trouvé: {article}")
