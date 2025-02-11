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

    def search_jorf(self, keyword):
        """Recherche dans le JORF"""
        url = f"{self.base_url}/list/jorf"
        
        payload = {
            "text": keyword,
            "pubDateStart": "2010-01-01",
            "pubDateEnd": datetime.now().strftime("%Y-%m-%d"),
            "nature": "LOI",
            "etat": "VIGUEUR",
            "pageSize": 10,
            "pageNumber": 1
        }

        logging.info(f"Recherche du terme '{keyword}' dans le JORF...")
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code == 200:
            logging.info(f"Recherche JORF réussie")
            return response.json()
        else:
            logging.error(f"Erreur lors de la recherche JORF: {response.text}")
            return None

    def get_jorf_text(self, jorf_id):
        """Récupère le texte d'un document JORF"""
        url = f"{self.base_url}/consult/jorf"
        
        payload = {
            "id": jorf_id
        }

        logging.info(f"Récupération du texte JORF {jorf_id}...")
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code == 200:
            logging.info(f"Texte JORF récupéré avec succès")
            return response.json()
        else:
            logging.error(f"Erreur lors de la récupération du texte JORF: {response.text}")
            return None

    def test_collection(self):
        """Test de récupération d'articles sur le Pacte Dutreil"""
        if not self.get_oauth_token():
            return

        keywords = ["Pacte Dutreil", "787 B", "transmission d'entreprise"]
        
        for keyword in keywords:
            search_results = self.search_jorf(keyword)
            
            if search_results and 'results' in search_results:
                logging.info(f"\nRésultats pour '{keyword}':")
                for result in search_results['results']:
                    logging.info("\nDocument trouvé:")
                    if 'title' in result:
                        logging.info(f"Titre: {result['title']}")
                    if 'numeroJORF' in result:
                        logging.info(f"Numéro JORF: {result['numeroJORF']}")
                    
                    # Récupérer le contenu complet
                    if 'id' in result:
                        content = self.get_jorf_text(result['id'])
                        if content:
                            logging.info("Contenu récupéré avec succès")
                            if 'articles' in content:
                                for article in content['articles']:
                                    logging.info(f"\nArticle {article.get('num', 'sans numéro')}:")
                                    if 'content' in article:
                                        excerpt = article['content'][:500] + "..." if len(article['content']) > 500 else article['content']
                                        logging.info(excerpt)

if __name__ == "__main__":
    collector = CGICollector()
    collector.test_collection()
