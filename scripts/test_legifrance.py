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
        self.cgi_id = "LEGITEXT000006069577"  # Identifiant du CGI

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

    def get_article_content(self, article_num):
        """Récupère le contenu d'un article spécifique du CGI"""
        url = f"{self.base_url}/consult/legi"
        
        payload = {
            "textId": self.cgi_id,
            "sectionId": f"LEGIARTI000{article_num}"
        }

        logging.info(f"Tentative de récupération de l'article {article_num}...")
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code == 200:
            logging.info(f"Article {article_num} récupéré avec succès")
            return response.json()
        else:
            logging.error(f"Erreur lors de la récupération de l'article {article_num}: {response.text}")
            return None

    def get_section_content(self, section_id):
        """Récupère le contenu d'une section du CGI"""
        url = f"{self.base_url}/consult/legi"
        
        payload = {
            "textId": self.cgi_id,
            "sectionId": section_id
        }

        logging.info(f"Tentative de récupération de la section {section_id}...")
        response = requests.post(
            url,
            headers=self.get_headers(),
            json=payload
        )

        if response.status_code == 200:
            logging.info(f"Section {section_id} récupérée avec succès")
            return response.json()
        else:
            logging.error(f"Erreur lors de la récupération de la section {section_id}: {response.text}")
            return None

    def test_collection(self):
        """Test de récupération de l'article 787 B"""
        if not self.get_oauth_token():
            return

        # Test avec l'article 787 B
        logging.info("Test de récupération de l'article 787 B...")
        article_content = self.get_article_content("787B")
        
        if article_content:
            logging.info("Contenu de l'article 787 B:")
            logging.info(article_content)
            
            # Si nous avons le contenu, affichons les métadonnées importantes
            if 'title' in article_content:
                logging.info(f"Titre: {article_content['title']}")
            if 'text' in article_content:
                excerpt = article_content['text'][:500] + "..." if len(article_content['text']) > 500 else article_content['text']
                logging.info(f"Extrait du texte: {excerpt}")

if __name__ == "__main__":
    collector = CGICollector()
    collector.test_collection()
