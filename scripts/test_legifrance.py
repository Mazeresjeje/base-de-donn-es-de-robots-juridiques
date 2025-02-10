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

def test_legifrance_connection():
    """Test la connexion à l'API Légifrance"""
    try:
        # Récupération des credentials
        client_id = os.environ.get("LEGIFRANCE_CLIENT_ID")
        client_secret = os.environ.get("LEGIFRANCE_CLIENT_SECRET")

        logger.info("Tentative d'obtention du token OAuth...")
        
        # Obtention du token
        token_url = "https://oauth.piste.gouv.fr/api/oauth/token"
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'openid'
        }
        
        token_response = requests.post(token_url, data=token_data)
        logger.info(f"Réponse du serveur OAuth: {token_response.status_code}")
        
        if token_response.status_code == 200:
            token = token_response.json()['access_token']
            logger.info("Token OAuth obtenu avec succès")
            
            # Headers pour l'API
            headers = {
                'Authorization': f'Bearer {token}',
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Requête de recherche basée sur la documentation
            search_payload = {
                "recherche": {
                    "champs": [
                        {
                            "typeChamp": "NUM",
                            "criteres": [
                                {
                                    "typeRecherche": "EXACTE",
                                    "valeur": "2019-290",
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
                    "sort": "PERTINENCE",
                    "typePagination": "DEFAUT"
                },
                "fond": "LODA_ETAT"
            }
            
            logger.info("Test d'une recherche sur Légifrance...")
            search_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app/search"
            logger.info(f"URL de recherche: {search_url}")
            logger.info(f"Payload: {json.dumps(search_payload, indent=2)}")
            
            search_response = requests.post(
                search_url,
                headers=headers,
                json=search_payload
            )
            
            logger.info(f"Statut de la recherche: {search_response.status_code}")
            logger.info(f"Détails de la réponse: {search_response.text}")
            
            if search_response.status_code == 200:
                results = search_response.json()
                logger.info("Recherche réussie!")
                logger.info(f"Nombre de résultats: {len(results.get('results', []))}")
                for result in results.get('results', []):
                    logger.info(f"Document trouvé: {result.get('title', 'Sans titre')}")
            else:
                logger.error(f"Erreur lors de la recherche: {search_response.text}")
        
        else:
            logger.error(f"Erreur d'authentification: {token_response.text}")
            
    except Exception as e:
        logger.error(f"Erreur lors du test: {str(e)}")

if __name__ == "__main__":
    test_legifrance_connection()
