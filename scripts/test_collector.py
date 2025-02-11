import os
import logging
import requests
import hashlib
import json
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LegifranceCollector:
    def __init__(self):
        self.token = None
        self.base_url = "https://api.piste.gouv.fr/dila/legifrance"
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
        response = requests.post(self.oauth_url, data=data)
        if response.status_code == 200:
            self.token = response.json()['access_token']
            return True
        return False

    def get_headers(self):
        """Génération des headers pour les requêtes"""
        return {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def search_articles(self, theme, doc_type):
        """Recherche d'articles selon le thème et le type"""
        # Construction de la requête selon la documentation
        search_payload = {
            "recherche": {
                "champs": [
                    {
                        "typeChamp": "TEXTE",
                        "criteres": [
                            {
                                "typeRecherche": "TOUS_LES_MOTS",
                                "valeur": theme,
                                "operateur": "ET"
                            }
                        ],
                        "operateur": "ET"
                    }
                ],
                "filtres": [
                    {
                        "facette": "DATE_VERSION",
                        "singleDate": int(datetime.now().timestamp() * 1000)
                    },
                    {
                        "facette": "TEXT_LEGAL_STATUS",
                        "valeur": "VIGUEUR"
                    }
                ],
                "pageNumber": 1,
                "pageSize": 20,
                "operateur": "ET",
                "sort": "PERTINENCE",
                "typePagination": "DEFAUT"
            },
            "fond": self.get_fond_type(doc_type)
        }

        response = requests.post(
            f"{self.base_url}/lf-engine-app/search",
            headers=self.get_headers(),
            json=search_payload
        )

        if response.status_code != 200:
            logging.error(f"Erreur lors de la recherche: {response.text}")
            return []

        results = response.json()
        return results.get('results', [])

    def get_fond_type(self, doc_type):
        """Détermine le type de fond selon le document"""
        type_mapping = {
            'loi': 'LODA_ETAT',
            'decret': 'JORF',
            'arrete': 'JORF',
            'circulaire': 'CIRC'
        }
        return type_mapping.get(doc_type, 'LODA_ETAT')

    def get_document_content(self, doc_id):
        """Récupère le contenu d'un document"""
        payload = {"id": doc_id}
        response = requests.post(
            f"{self.base_url}/lf-engine-app/consult/legiPart",
            headers=self.get_headers(),
            json=payload
        )
        if response.status_code == 200:
            return response.json()
        return None

    def collect_for_theme(self, theme, doc_types=None):
        """Collecte les documents pour un thème donné"""
        if doc_types is None:
            doc_types = ['loi', 'decret', 'arrete', 'circulaire']

        if not self.get_oauth_token():
            logging.error("Impossible d'obtenir le token OAuth")
            return

        for doc_type in doc_types:
            logging.info(f"Recherche de documents de type: {doc_type}")
            results = self.search_articles(theme, doc_type)
            
            for result in results:
                try:
                    doc_id = result['titles'][0]['id']
                    content = self.get_document_content(doc_id)
                    if content:
                        logging.info(f"Document trouvé et récupéré: {doc_id}")
                except Exception as e:
                    logging.error(f"Erreur lors du traitement du document: {str(e)}")

def main():
    collector = LegifranceCollector()
    themes = [
        "Pacte Dutreil",
        "DMTG",
        "Location meublée",
        "Revenus fonciers"
    ]
    
    for theme in themes:
        logging.info(f"Collecte pour le thème: {theme}")
        collector.collect_for_theme(theme)

if __name__ == "__main__":
    main()
