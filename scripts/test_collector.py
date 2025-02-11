import os
import requests
import json
import logging
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegifranceCollector:
    def __init__(self):
        self.token = None
        self.base_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        
    def get_token(self):
        """Obtient un token OAuth"""
        try:
            token_url = "https://oauth.piste.gouv.fr/api/oauth/token"
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': os.environ.get("LEGIFRANCE_CLIENT_ID"),
                'client_secret': os.environ.get("LEGIFRANCE_CLIENT_SECRET"),
                'scope': 'openid'
            }
            
            response = requests.post(token_url, data=token_data)
            if response.status_code == 200:
                self.token = response.json()['access_token']
                logger.info("Token OAuth obtenu avec succès")
                return True
            else:
                logger.error(f"Erreur d'authentification: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention du token: {str(e)}")
            return False

    def get_headers(self):
        """Retourne les headers pour les requêtes API"""
        return {
            'Authorization': f'Bearer {self.token}',
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def get_text_content(self, jorf_id):
        """Récupère le contenu d'un texte du JORF"""
        try:
            payload = {
                "id": jorf_id
            }
            
            response = requests.post(
                f"{self.base_url}/consult/jorf",
                headers=self.get_headers(),
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            logger.error(f"Erreur {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
            return None

    def search_jorf(self, theme, start_date=None, end_date=None):
        """Recherche dans le Journal Officiel"""
        if not self.token and not self.get_token():
            return []

        if not start_date:
            start_date = datetime.now() - timedelta(days=365*2)  # 2 ans en arrière
        if not end_date:
            end_date = datetime.now()

        payload = {
            "recherche": {
                "champs": [
                    {
                        "typeChamp": "ALL",
                        "criteres": [
                            {
                                "typeRecherche": "EXACTE",
                                "valeur": theme
                            }
                        ]
                    }
                ],
                "datePeriode": {
                    "startDate": start_date.strftime("%Y-%m-%d"),
                    "endDate": end_date.strftime("%Y-%m-%d")
                },
                "pageNumber": 1,
                "pageSize": 10,
                "sort": "DATE_PUBLI"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/search/jorf",
                headers=self.get_headers(),
                json=payload
            )

            if response.status_code == 200:
                results = response.json()
                logger.info(f"Trouvé {len(results.get('results', []))} documents")
                return results.get('results', [])
            else:
                logger.error(f"Erreur de recherche: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
            return []

    def process_theme(self, theme):
        """Traite un thème spécifique"""
        logger.info(f"\nTraitement du thème: {theme}")
        
        # Recherche dans le JORF
        documents = self.search_jorf(theme)
        
        for doc in documents:
            logger.info(f"\nDocument trouvé dans le JORF:")
            
            # Extraire les métadonnées
            title = doc.get('titre', 'Sans titre')
            date = doc.get('date', 'Date inconnue')
            numero = doc.get('numero', 'Numéro inconnu')
            
            logger.info(f"Titre: {title}")
            logger.info(f"Date: {date}")
            logger.info(f"Numéro: {numero}")
            
            # Récupérer le contenu complet
            if 'id' in doc:
                content = self.get_text_content(doc['id'])
                if content:
                    logger.info(f"Contenu récupéré ({len(str(content))} caractères)")
                    # TODO: Sauvegarder dans Supabase
                else:
                    logger.warning("Impossible de récupérer le contenu")

def main():
    collector = LegifranceCollector()
    
    themes = [
        "Pacte Dutreil",
        "droits de mutation à titre gratuit",
        "location meublée",
        "revenus fonciers"
    ]
    
    for theme in themes:
        collector.process_theme(theme)

if __name__ == "__main__":
    main()
