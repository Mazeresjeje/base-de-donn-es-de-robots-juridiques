import os
import requests
import json
import logging
from datetime import datetime
import hashlib
from typing import Dict, List, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegifranceCollector:
    def __init__(self):
        self.client_id = os.environ.get("LEGIFRANCE_CLIENT_ID")
        self.client_secret = os.environ.get("LEGIFRANCE_CLIENT_SECRET")
        self.token = None
        self.base_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
        
        # Mots-clés par thème
        self.theme_keywords = {
            "Pacte Dutreil": [
                "transmission d'entreprise",
                "pacte dutreil",
                "engagement collectif de conservation",
                "dutreil transmission",
                "787 B"
            ],
            "DMTG": [
                "droits de mutation à titre gratuit",
                "succession",
                "donation",
                "transmission de patrimoine"
            ],
            "Location meublée": [
                "location meublée",
                "LMNP",
                "loueur en meublé",
                "location touristique"
            ],
            "Revenus fonciers": [
                "revenus fonciers",
                "location nue",
                "propriétaire bailleur",
                "déficit foncier"
            ]
        }

    def get_token(self) -> bool:
        """Obtient un token OAuth"""
        try:
            token_url = "https://oauth.piste.gouv.fr/api/oauth/token"
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
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

    def search_documents(self, keywords: List[str], doc_type: str = None) -> List[Dict]:
        """Recherche des documents basés sur des mots-clés"""
        if not self.token and not self.get_token():
            return []

        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }

            # Construction des critères de recherche
            search_criteria = []
            for keyword in keywords:
                search_criteria.append({
                    "typeRecherche": "EXACTE",
                    "valeur": keyword,
                    "operateur": "OU"
                })

            # Payload de recherche
            payload = {
                "recherche": {
                    "champs": [
                        {
                            "typeChamp": "TEXTE",
                            "criteres": search_criteria,
                            "operateur": "OU"
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
                    "sort": "PERTINENCE"
                },
                "fond": "LODA_ETAT" if doc_type == "loi" else "JURI_ALL"
            }

            # Ajout du filtre de type de document si spécifié
            if doc_type:
                payload["recherche"]["filtres"].append({
                    "facette": "TEXT_NATURE",
                    "valeur": doc_type.upper()
                })

            response = requests.post(
                f"{self.base_url}/search",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                results = response.json()
                logger.info(f"Nombre de résultats trouvés: {len(results.get('results', []))}")
                return results.get('results', [])
            else:
                logger.error(f"Erreur lors de la recherche: {response.text}")
                return []

        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            return []

    def get_document_content(self, doc_id: str) -> Optional[str]:
        """Récupère le contenu complet d'un document"""
        if not self.token and not self.get_token():
            return None

        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }

            payload = {
                "id": doc_id
            }

            response = requests.post(
                f"{self.base_url}/consult/getArticle",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erreur lors de la récupération du contenu: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contenu: {str(e)}")
            return None

    def collect_all(self):
        """Collecte tous les documents pour tous les thèmes"""
        document_types = ["loi", "decret", "arrete", "circulaire"]
        
        for theme, keywords in self.theme_keywords.items():
            logger.info(f"Collecte pour le thème: {theme}")
            
            for doc_type in document_types:
                logger.info(f"Recherche de documents de type: {doc_type}")
                documents = self.search_documents(keywords, doc_type)
                
                for doc in documents:
                    logger.info(f"Document trouvé: {doc.get('title', 'Sans titre')}")
                    content = self.get_document_content(doc.get('id'))
                    if content:
                        logger.info(f"Contenu récupéré : {len(str(content))} caractères")
                        # TODO: Sauvegarder dans Supabase
                        
                logger.info(f"Fin de la collecte pour {doc_type} dans {theme}")

def main():
    collector = LegifranceCollector()
    collector.collect_all()

if __name__ == "__main__":
    main()
