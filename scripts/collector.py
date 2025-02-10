from supabase import create_client
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import os
import json
import logging
from datetime import datetime
import hashlib

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variables d'environnement
logger.info("=== Démarrage du script de collecte ===")
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
mistral_key = os.environ.get("MISTRAL_API_KEY")

logger.info(f"SUPABASE_URL présente: {'Oui' if supabase_url else 'Non'}")
logger.info(f"SUPABASE_KEY présente: {'Oui' if supabase_key else 'Non'}")
logger.info(f"MISTRAL_API_KEY présente: {'Oui' if mistral_key else 'Non'}")

if not supabase_url or not supabase_key or not mistral_key:
    raise Exception("Variables d'environnement manquantes")

# Initialisation des clients
logger.info("Tentative de connexion à Supabase...")
supabase = create_client(supabase_url, supabase_key)
logger.info("Connexion Supabase établie")

logger.info("Tentative de connexion à Mistral...")
client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=mistral_key
)
logger.info("Connexion Mistral établie")

def extract_bofip_content(soup):
    """Extrait le contenu d'une page BOFIP"""
    try:
        # Essai de différents sélecteurs possibles
        content_selectors = [
            'div.article_content',
            'div#main-content',
            'div.corps_texte',
            'div.contenupage'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                logger.info(f"Contenu trouvé avec le sélecteur: {selector}")
                # Nettoyage du contenu
                for script in content_div.find_all('script'):
                    script.decompose()
                for style in content_div.find_all('style'):
                    style.decompose()
                
                text = content_div.get_text(separator=' ', strip=True)
                return text
        
        logger.warning("Aucun contenu trouvé avec les sélecteurs standards")
        # Plan B : prendre tout le texte du body
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        return None
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du contenu: {str(e)}")
        return None

def collect_bofip():
    """Collecte les documents du BOFIP"""
    try:
        # Structure avec les URLs et leurs thèmes associés
        urls = {
            "https://bofip.impots.gouv.fr/bofip/11669-PGP": "Pacte Dutreil",
            "https://bofip.impots.gouv.fr/bofip/3335-PGP": "DMTG",
            "https://bofip.impots.gouv.fr/bofip/2824-PGP": "Location meublée",
            "https://bofip.impots.gouv.fr/bofip/5713-PGP": "Revenus fonciers",
            "https://bofip.impots.gouv.fr/bofip/6218-PGP": "Plus-values particuliers"
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for url, theme in urls.items():
            logger.info(f"Tentative d'accès à {url}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Accès réussi à {url}")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraction du titre
                title = None
                title_tags = ['h1', 'title']
                for tag in title_tags:
                    title_elem = soup.find(tag)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        break
                
                if not title:
                    title = url
                logger.info(f"Titre trouvé: {title[:100]}")
                
                # Extraction du contenu
                content = extract_bofip_content(soup)
                if content:
                    logger.info(f"Contenu extrait: {len(content)} caractères")
                    
                    # Génération du hash
                    doc_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                    # Vérification des doublons
                    existing = supabase.table('documents').select('id').eq('document_hash', doc_hash).execute()
                    
                    if not existing.data:
                        logger.info(f"Nouveau document trouvé: {title[:100]}...")
                        
                        # Récupération des IDs
                        theme_result = supabase.table('fiscal_themes').select('id').eq('name', theme).execute()
                        
                        if theme_result.data:
                            theme_id = theme_result.data[0]['id']
                            
                            document = {
                                'title': title,
                                'content': content,
                                'theme_id': theme_id,
                                'category_id': 4,  # ID pour "Instruction fiscale"
                                'publication_date': datetime.now().date().isoformat(),
                                'source_url': url,
                                'document_hash': doc_hash
                            }
                            
                            logger.info("Tentative d'insertion dans Supabase...")
                            result = supabase.table('documents').insert(document).execute()
                            logger.info(f"Document ajouté avec succès: {title[:100]}...")
                        else:
                            logger.error(f"Thème non trouvé dans la base: {theme}")
                    else:
                        logger.info(f"Document déjà existant: {title[:100]}...")
                else:
                    logger.error(f"Impossible d'extraire le contenu de {url}")
            else:
                logger.error(f"Erreur d'accès à {url}: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Erreur lors de la collecte BOFIP: {str(e)}")

def main():
    """Fonction principale"""
    logger.info("=== Début de la collecte ===")
    collect_bofip()
    logger.info("=== Fin de la collecte ===")

if __name__ == "__main__":
    main()
