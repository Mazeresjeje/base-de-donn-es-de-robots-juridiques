import os
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_oauth_token():
    """Obtention du token OAuth"""
    oauth_url = "https://oauth.piste.gouv.fr/api/oauth/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': os.environ.get('LEGIFRANCE_CLIENT_ID'),
        'client_secret': os.environ.get('LEGIFRANCE_CLIENT_SECRET'),
        'scope': 'openid'
    }
    response = requests.post(oauth_url, data=data)
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def search_law(token, theme="Pacte Dutreil"):
    """Recherche une loi selon la méthode de l'exemple 4"""
    search_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app/search"
    headers = {
        'Authorization': f'Bearer {token}',
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    payload = {
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
            "pageSize": 1,
            "operateur": "ET",
            "sort": "PERTINENCE",
            "typePagination": "DEFAUT"
        },
        "fond": "LODA_ETAT"
    }
    
    response = requests.post(search_url, headers=headers, json=payload)
    if response.status_code != 200:
        logging.error(f"Erreur de recherche: {response.text}")
        return None
        
    return response.json()

def get_law_content(token, text_id):
    """Récupère le contenu d'une loi selon l'exemple 4"""
    content_url = "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app/consult/legiPart"
    headers = {
        'Authorization': f'Bearer {token}',
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "date": int(datetime.now().timestamp() * 1000),
        "textId": text_id
    }
    
    response = requests.post(content_url, headers=headers, json=payload)
    if response.status_code != 200:
        logging.error(f"Erreur de récupération: {response.text}")
        return None
        
    return response.json()

def main():
    logging.info("=== Démarrage du test Pacte Dutreil ===")
    
    # Obtention du token
    token = get_oauth_token()
    if not token:
        logging.error("Impossible d'obtenir le token OAuth")
        return
    logging.info("Token OAuth obtenu")
    
    # Recherche de la loi
    search_results = search_law(token)
    if not search_results:
        logging.error("Aucun résultat trouvé")
        return
    
    logging.info(f"Résultats de recherche: {search_results}")
    
    # Pour le premier résultat
    if 'results' in search_results and len(search_results['results']) > 0:
        result = search_results['results'][0]
        if 'titles' in result and len(result['titles']) > 0:
            text_id = result['titles'][0]['id']
            logging.info(f"Récupération du contenu pour {text_id}")
            
            content = get_law_content(token, text_id)
            if content:
                logging.info("Contenu récupéré avec succès")
                logging.info(f"Premier fragment du contenu: {str(content)[:500]}...")

if __name__ == "__main__":
    main()
