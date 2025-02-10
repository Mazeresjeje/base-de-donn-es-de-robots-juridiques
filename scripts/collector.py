from supabase import create_client
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import os
import json
import logging
from datetime import datetime, timedelta
import hashlib

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegalDataCollector:
    def __init__(self):
        self.supabase = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_KEY")
        )
        self.client = OpenAI(
            base_url="https://api.mistral.ai/v1",
            api_key=os.environ.get("MISTRAL_API_KEY")
        )
        
        # URLs des sources BOFIP par thème
        self.bofip_urls = {
            "Pacte Dutreil": [
                "https://bofip.impots.gouv.fr/bofip/11669-PGP",
                "https://bofip.impots.gouv.fr/bofip/6475-PGP"
            ],
            "DMTG": [
                "https://bofip.impots.gouv.fr/bofip/3335-PGP",
                "https://bofip.impots.gouv.fr/bofip/3359-PGP"
            ],
            "Location meublée": [
                "https://bofip.impots.gouv.fr/bofip/2824-PGP",
                "https://bofip.impots.gouv.fr/bofip/4105-PGP"
            ],
            "Revenus fonciers": [
                "https://bofip.impots.gouv.fr/bofip/5713-PGP",
                "https://bofip.impots.gouv.fr/bofip/5685-PGP"
            ]
        }
        
        # URLs des questions parlementaires par thème
        self.parliament_urls = {
            "assemblee": "https://questions.assemblee-nationale.fr/feed/questions.rss",
            "senat": "https://www.senat.fr/rss/questions.rss"
        }
        
        # URLs de jurisprudence par thème
        self.jurisprudence_urls = {
            "cassation": "https://www.courdecassation.fr/recherche-judilibre",
            "conseil_etat": "https://www.conseil-etat.fr/decisions-de-justice"
        }

    def collect_all(self):
        """Collecte les données de toutes les sources"""
        try:
            logger.info("Début de la collecte complète")
            
            # BOFIP
            self.collect_bofip()
            
            # Légifrance (nécessite une API key)
            self.collect_legifrance()
            
            # Questions parlementaires
            self.collect_parliament_questions()
            
            # Jurisprudence
            self.collect_jurisprudence()
            
            logger.info("Fin de la collecte complète")
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte : {str(e)}")

    def collect_bofip(self):
        """Collecte les documents du BOFIP"""
        try:
            for theme, urls in self.bofip_urls.items():
                for url in urls:
                    logger.info(f"Collecte BOFIP pour {theme} : {url}")
                    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extraction contenu
                        content = self.extract_content(soup)
                        if content:
                            self.save_document(
                                title=soup.find('h1').text.strip() if soup.find('h1') else url,
                                content=content,
                                source_url=url,
                                theme=theme,
                                doc_type='Instruction fiscale'
                            )
        except Exception as e:
            logger.error(f"Erreur BOFIP : {str(e)}")

    def collect_legifrance(self):
        """Collecte depuis Légifrance"""
        # Implémentation avec l'API Légifrance
        pass

    def collect_parliament_questions(self):
        """Collecte les questions parlementaires"""
        try:
            for source, url in self.parliament_urls.items():
                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')
                    
                    for item in items:
                        if self.is_relevant_question(item):
                            self.save_document(
                                title=item.title.text,
                                content=item.description.text,
                                source_url=item.link.text,
                                theme=self.determine_theme(item),
                                doc_type='Réponse ministérielle'
                            )
        except Exception as e:
            logger.error(f"Erreur questions parlementaires : {str(e)}")

    def collect_jurisprudence(self):
        """Collecte la jurisprudence"""
        # Implémentation pour chaque source de jurisprudence
        pass

    def extract_content(self, soup):
        """Extrait le contenu d'une page"""
        for selector in ['div.article_content', 'div.corps_texte', 'div#main-content']:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        return soup.get_text(strip=True)

    def determine_theme(self, item):
        """Détermine le thème d'un document"""
        try:
            chat_completion = self.client.chat.completions.create(
                model="mistral-medium",
                messages=[
                    {"role": "system", "content": "Vous êtes un expert en classification fiscale."},
                    {"role": "user", "content": f"Classez ce texte dans un des thèmes suivants : Pacte Dutreil, DMTG, Location meublée, Revenus fonciers, Plus-values. Texte : {item.title.text}\n\n{item.description.text[:500]}"}
                ]
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Erreur classification : {str(e)}")
            return None

    def save_document(self, title, content, source_url, theme, doc_type):
        """Sauvegarde un document dans Supabase"""
        try:
            # Génération du hash
            doc_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Vérification des doublons
            existing = self.supabase.table('documents').select('id').eq('document_hash', doc_hash).execute()
            
            if not existing.data:
                # Récupération des IDs
                theme_result = self.supabase.table('fiscal_themes').select('id').eq('name', theme).execute()
                category_result = self.supabase.table('document_categories').select('id').eq('name', doc_type).execute()
                
                if theme_result.data and category_result.data:
                    document = {
                        'title': title,
                        'content': content,
                        'theme_id': theme_result.data[0]['id'],
                        'category_id': category_result.data[0]['id'],
                        'publication_date': datetime.now().date().isoformat(),
                        'source_url': source_url,
                        'document_hash': doc_hash
                    }
                    
                    self.supabase.table('documents').insert(document).execute()
                    logger.info(f"Document ajouté : {title[:100]}...")
                    
        except Exception as e:
            logger.error(f"Erreur sauvegarde : {str(e)}")

def main():
    collector = LegalDataCollector()
    collector.collect_all()

if __name__ == "__main__":
    main()
