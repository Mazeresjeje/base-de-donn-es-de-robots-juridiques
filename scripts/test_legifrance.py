import os
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HybridCollector:
    def __init__(self):
        self.token = None
        self.base_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        self.oauth_url = "https://oauth.piste.gouv.fr/api/oauth/token"
        self.client_id = os.environ.get('LEGIFRANCE_CLIENT_ID')
        self.client_secret = os.environ.get('LEGIFRANCE_CLIENT_SECRET')
        
        # URLs pour le scraping
        self.legifrance_web = "https://www.legifrance.gouv.fr"
        self.cgi_base = f"{self.legifrance_web}/codes/id/LEGITEXT000006069577"

        # Headers pour le scraping
        self.scraping_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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

    def find_article_id(self, article_num):
        """Recherche l'identifiant LEGIARTI d'un article via web scraping"""
        logging.info(f"Recherche de l'ID pour l'article {article_num}...")
        
        # Construction de l'URL de recherche
        search_url = f"{self.legifrance_web}/search/code"
        params = {
            'query': f'article {article_num}',
            'searchField': 'ALL',
            'tab_selection': 'code_article',
            'searchProximity': 'true',
            'idSectionTA': 'LEGISCTA000006084232',  # Section CGI
            'typeRecherche': 'date'
        }
        
        try:
            response = requests.get(search_url, params=params, headers=self.scraping_headers)
            logging.info(f"Status code scraping: {response.status_code}")
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Recherche des liens d'articles
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if 'LEGIARTI' in href:
                        legiarti_id = href.split('LEGIARTI')[-1].split('/')[0]
                        if legiarti_id:
                            logging.info(f"ID LEGIARTI trouvé: LEGIARTI{legiarti_id}")
                            return f"LEGIARTI{legiarti_id}"
            
            logging.warning(f"Aucun ID trouvé pour l'article {article_num}")
            return None
                    
        except Exception as e:
            logging.error(f"Erreur lors du scraping: {e}")
            return None

    def get_article_content(self, article_id):
        """Récupère le contenu d'un article via l'API avec son ID LEGIARTI"""
        url = f"{self.base_url}/consult/getArticle"
        
        payload = {
            "id": article_id
        }

        logging.info(f"Récupération du contenu via API pour {article_id}...")
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code == 200:
            result = response.json()
            article = result.get('article')
            if article and 'texte' in article:
                logging.info("Contenu récupéré avec succès")
                return article
            else:
                logging.warning("Article trouvé mais pas de contenu")
                return None
        else:
            logging.error(f"Erreur API: {response.status_code}")
            logging.error(f"Détails: {response.text}")
            return None

    def test_collection(self):
        """Test de récupération hybride"""
        if not self.get_oauth_token():
            return

        articles_to_test = ["787 B", "810", "787 C"]
        for article_num in articles_to_test:
            logging.info(f"\nTest pour l'article {article_num}")
            
            # Étape 1 : Recherche de l'ID via scraping
            article_id = self.find_article_id(article_num)
            if not article_id:
                logging.error(f"Impossible de trouver l'ID pour l'article {article_num}")
                continue
            
            # Étape 2 : Récupération du contenu via API
            time.sleep(1)  # Pause pour éviter de surcharger les serveurs
            content = self.get_article_content(article_id)
            if content:
                logging.info(f"Article {article_num} :")
                logging.info(f"ID: {content.get('id')}")
                logging.info(f"Type: {content.get('type')}")
                logging.info(f"Texte: {content.get('texte')}")
            else:
                logging.error(f"Échec de la récupération du contenu pour l'article {article_num}")

if __name__ == "__main__":
    collector = HybridCollector()
    collector.test_collection()
