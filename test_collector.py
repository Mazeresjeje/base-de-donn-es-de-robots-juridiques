import os
import requests
import json
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_collect_dutreil():
    """Test de collecte des documents sur le Pacte Dutreil"""
    try:
        # 1. Obtention du token
        logger.info("Tentative d'obtention du token OAuth...")
        token_url = "https://oauth.piste.gouv.fr/api/oauth/token"
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': os.environ.get("LEGIFRANCE_CLIENT_ID"),
            'client_secret': os.environ.get("LEGIFRANCE_CLIENT_SECRET"),
            'scope': 'openid'
        }
        
        token_response = requests.post(token_url, data=token_data)
        logger.info(f"Réponse du serveur OAuth: {token_response.status_code}")
        
        if token_response.status_code == 200:
            token = token_response.json()['access_token']
            logger.info("Token OAuth obtenu avec succès")
            
            # 2. Recherche de documents
            headers = {
                'Authorization': f'Bearer {token}',
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Payload pour le Pacte Dutreil
            search_payload = {
                "recherche": {
                    "champs": [
                        {
                            "typeChamp": "TEXTE",
                            "criteres": [
                                {
                                    "typeRecherche": "EXACTE",
                                    "valeur": "pacte dutreil",
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
                    "pageSize": 10,
                    "operateur": "ET",
                    "sort": "PERTINENCE"
                },
                "fond": "LODA_DATE"
            }
            
            logger.info("Recherche de documents sur le Pacte Dutreil...")
            search_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app/search"
            search_response = requests.post(
                search_url,
                headers=headers,
                json=search_payload
            )
            
            logger.info(f"Statut de la recherche: {search_response.status_code}")
            
            if search_response.status_code == 200:
                results = search_response.json()
                logger.info("Recherche réussie!")
                logger.info(f"Nombre de résultats: {len(results.get('results', []))}")
                
                # Affichage des résultats
                for result in results.get('results', []):
                    titles = result.get('titles', [])
                    if titles:
                        logger.info(f"\nDocument trouvé:")
                        logger.info(f"Titre: {titles[0].get('title', 'Sans titre')}")
                        logger.info(f"ID: {titles[0].get('id', 'Pas d\'ID')}")
                        logger.info(f"Statut: {titles[0].get('legalStatus', 'Statut inconnu')}")
                        logger.info("-" * 50)
            else:
                logger.error(f"Erreur lors de la recherche: {search_response.text}")
        
        else:
            logger.error(f"Erreur d'authentification: {token_response.text}")
            
    except Exception as e:
        logger.error(f"Erreur lors du test: {str(e)}")

if __name__ == "__main__":
    test_collect_dutreil()
