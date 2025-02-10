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

def collect_bofip():
    """Collecte les documents du BOFIP"""
    try:
        # Liste des URLs à scraper
        urls = [
            "https://bofip.impots.gouv.fr/bofip/11669-PGP",  # Pacte Dutreil
            "https://bofip.impots.gouv.fr/bofip/3335-PGP",   # DMTG
            "https://bofip.impots.gouv.fr/bofip/2824-PGP",   # Location meublée
            "https://bofip.impots.gouv.fr/bofip/5713-PGP",   # Revenus fonciers
            "https://bofip.impots.gouv.fr/bofip/6218-PGP",   # Plus-values
        ]
        
        for url in urls:
            logger.info(f"Tentative d'accès à {url}")
            response = requests.get(url)
            
            if response.status_code == 200:
                logger.info(f"Accès réussi à {url}")
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraction du contenu principal
                content_div = soup.find('div', {'class': 'article_content'})
                if content_div:
                    title = soup.find('h1').text.strip() if soup.find('h1') else url
                    content = content_div.get_text(strip=True)
                    
                    # Génération du hash
                    doc_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                    # Vérification des doublons
                    existing = supabase.table('documents').select('id').eq('document_hash', doc_hash).execute()
                    
                    if not existing.data:
                        logger.info(f"Nouveau document trouvé: {title[:100]}...")
                        
                        # Classification avec Mistral
                        classification = classify_document(title, content)
                        if classification:
                            theme = supabase.table('fiscal_themes').select('id').eq('name', classification['theme']).execute()
                            category = supabase.table('document_categories').select('id').eq('name', classification['category']).execute()
                            
                            document = {
                                'title': title,
                                'content': content,
                                'theme_id': theme.data[0]['id'] if theme.data else None,
                                'category_id': category.data[0]['id'] if category.data else None,
                                'publication_date': datetime.now().date().isoformat(),
                                'source_url': url,
                                'document_hash': doc_hash
                            }
                            
                            supabase.table('documents').insert(document).execute()
                            logger.info(f"Document ajouté: {title[:100]}...")
                    else:
                        logger.info(f"Document déjà existant: {title[:100]}...")
            else:
                logger.error(f"Erreur d'accès à {url}: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Erreur lors de la collecte BOFIP: {str(e)}")

def classify_document(title, content):
    """Classifie le document avec Mistral AI"""
    try:
        logger.info(f"Classification du document: {title[:100]}...")
        prompt = f"""
        Analysez ce document fiscal/juridique et classifiez-le.
        
        TITRE: {title}
        CONTENU: {content[:500]}...
        
        1. Identifiez le thème principal parmi:
        - Pacte Dutreil
        - DMTG
        - Location meublée
        - Revenus fonciers
        - Plus-values particuliers
        - Plus-values immobilières
        - Plus-values professionnelles
        - BA
        
        2. Identifiez le type de document parmi:
        - Loi
        - Décret
        - Arrêté
        - Instruction fiscale
        - Réponse ministérielle
        - Jurisprudence
        
        Répondez uniquement au format JSON:
        {{"theme": "nom_du_theme", "category": "type_de_document"}}
        """
        
        chat_completion = client.chat.completions.create(
            model="mistral-medium",
            messages=[
                {"role": "system", "content": "Vous êtes un expert en classification de documents juridiques et fiscaux."},
                {"role": "user", "content": prompt}
            ]
        )
        
        result = json.loads(chat_completion.choices[0].message.content)
        logger.info(f"Classification obtenue: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Erreur de classification: {str(e)}")
        return None

def main():
    """Fonction principale"""
    logger.info("=== Début de la collecte ===")
    collect_bofip()
    logger.info("=== Fin de la collecte ===")

if __name__ == "__main__":
    main()
