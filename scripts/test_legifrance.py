import os
import requests
import json
import logging

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
        token_url = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
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
            
            # Test d'une requête simple sur Légifrance
            headers = {
                'Authorization': f'Bearer {token}',
                'accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Recherche simple sur le Pacte Dutreil
            search_payload = {
                "recherche": {
                    "champs": [
                        {
                            "typeChamp": "TITLE",
                            "criteres": [
                                {
                                    "typeRecherche": "EXACTE",
                                    "valeur": "Pacte Dutreil",
                                    "operateur": "ET"
                                }
                            ]
                        }
                    ],
                    "pageNumber": 1,
                    "pageSize": 10
                },
                "fond": "LODA_DATE"
            }
            
            logger.info("Test d'une recherche sur Légifrance...")
            search_response = requests.post(
                "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app/search",
                headers=headers,
                json=search_payload
            )
            
            logger.info(f"Statut de la recherche: {search_response.status_code}")
            
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
