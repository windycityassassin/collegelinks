"""
Scrapers for collecting institution data from UGC and AICTE websites
"""
import logging
import time
from typing import Dict, List
import os
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UGCScraper:
    """Scraper for UGC university data"""
    
    def __init__(self):
        self.base_url = "https://www.ugc.ac.in"
        self.api_url = "https://www.ugc.ac.in/api/get_central_universities"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
    
    def _get_universities_list(self) -> List[Dict]:
        """Get list of universities from UGC API"""
        try:
            # First try direct API call
            logger.info("Trying direct API call...")
            response = requests.get(
                self.api_url,
                headers=self.headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        return [{
                            'name': univ.get('name', ''),
                            'address': f"{univ.get('address', '')}, {univ.get('city', '')}, {univ.get('state', '')}",
                            'source': 'UGC'
                        } for univ in data if univ.get('name')]
                except:
                    pass
            
            # Fallback to scraping the HTML page
            logger.info("Falling back to HTML scraping...")
            response = requests.get(
                urljoin(self.base_url, 'oldpdf/consolidated_central_univ.pdf'),
                headers=self.headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                universities = []
                
                # Find all university entries
                for div in soup.find_all('div', class_='university-item'):
                    name = div.find('h3')
                    address = div.find('p', class_='address')
                    
                    if name and address:
                        universities.append({
                            'name': name.text.strip(),
                            'address': address.text.strip(),
                            'source': 'UGC'
                        })
                
                return universities
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting universities list: {e}")
            return []
    
    def scrape(self) -> List[Dict]:
        """Scrape university data"""
        try:
            logger.info("Getting universities list...")
            universities = self._get_universities_list()
            
            logger.info(f"Found {len(universities)} universities")
            return universities
            
        except Exception as e:
            logger.error(f"Error scraping UGC data: {e}")
            return []

class AICTEScraper:
    """Scraper for AICTE college data"""
    
    def __init__(self):
        self.base_url = "https://facilities.aicte-india.org"
        self.api_url = f"{self.base_url}/api/v2/institutes"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
    
    def _get_colleges_list(self) -> List[Dict]:
        """Get list of colleges from AICTE API"""
        try:
            # Try direct API call
            logger.info("Trying direct API call...")
            response = requests.get(
                self.api_url,
                headers=self.headers,
                params={
                    'page': 1,
                    'limit': 100,  # Limit to 100 for testing
                    'approved': 'true'
                },
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'data' in data:
                        return [{
                            'name': college.get('name', ''),
                            'address': f"{college.get('address', '')}, {college.get('city', '')}, {college.get('state', '')}",
                            'source': 'AICTE'
                        } for college in data['data'] if college.get('name')]
                except:
                    pass
            
            # Fallback to scraping the HTML page
            logger.info("Falling back to HTML scraping...")
            response = requests.get(
                urljoin(self.base_url, 'dashboard/pages/approved-institutes.html'),
                headers=self.headers,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                colleges = []
                
                # Find all college entries
                for tr in soup.find_all('tr')[1:101]:  # Skip header, limit to 100
                    cols = tr.find_all('td')
                    if len(cols) >= 3:
                        name = cols[1].text.strip()
                        address = cols[2].text.strip()
                        if name and address:
                            colleges.append({
                                'name': name,
                                'address': address,
                                'source': 'AICTE'
                            })
                
                return colleges
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting colleges list: {e}")
            return []
    
    def scrape(self) -> List[Dict]:
        """Scrape college data"""
        try:
            logger.info("Getting colleges list...")
            colleges = self._get_colleges_list()
            
            logger.info(f"Successfully scraped {len(colleges)} colleges")
            return colleges
            
        except Exception as e:
            logger.error(f"Error scraping AICTE data: {e}")
            return []

def main():
    # Create data directory if it doesn't exist
    os.makedirs("data/scraped", exist_ok=True)
    
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Scrape UGC universities
    logger.info("Starting UGC scraper...")
    ugc_scraper = UGCScraper()
    universities = ugc_scraper.scrape()
    
    # Save universities to CSV
    df = pd.DataFrame(universities)
    output_file = "data/scraped/ugc_universities.csv"
    df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(universities)} institutions to {output_file}")
    
    # Scrape AICTE colleges
    logger.info("\nStarting AICTE scraper...")
    aicte_scraper = AICTEScraper()
    colleges = aicte_scraper.scrape()
    
    # Save colleges to CSV
    df = pd.DataFrame(colleges)
    output_file = "data/scraped/aicte_colleges.csv"
    df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(colleges)} institutions to {output_file}")

if __name__ == "__main__":
    main()
