"""
AICTE Website Scraper

This module handles scraping of the AICTE website (https://www.aicte-india.org)
to collect comprehensive data about institutions, courses, and related documents.
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pathlib import Path
import json
import pandas as pd
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICTEScraper:
    """Scraper for AICTE website"""
    
    def __init__(self, data_dir: str = "data", download_dir: str = "downloads"):
        """Initialize the scraper"""
        self.data_dir = Path(data_dir)
        self.download_dir = Path(download_dir)
        self.raw_dir = self.data_dir / "raw" / "aicte"
        self.processed_dir = self.data_dir / "processed" / "aicte"
        
        # Create necessary directories
        for dir_path in [self.raw_dir, self.processed_dir, self.download_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Base URLs
        self.base_url = "https://facilities.aicte-india.org"
        self.api_url = "https://facilities.aicte-india.org/api/v2"
        
        # Set download preferences
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option(
            'prefs', {
                'download.default_directory': str(self.download_dir.absolute()),
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True
            }
        )
        
        # Add additional options for better performance
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-features=NetworkService')
        self.options.add_argument('--window-size=1920x1080')
        self.options.add_argument('--disable-notifications')
        self.options.add_argument('--disable-popup-blocking')
        self.options.add_argument('--headless=new')  # Use new headless mode
        
        # Initialize session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': self.base_url,
            'Referer': f"{self.base_url}/dashboard",
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        self.timeout = 30  # Increase timeout to 30 seconds

    def setup_driver(self) -> webdriver.Chrome:
        """Set up and return a Chrome webdriver"""
        driver = webdriver.Chrome(options=self.options)
        driver.implicitly_wait(10)
        return driver

    def wait_for_element(self, driver: webdriver.Chrome, by: By, value: str, timeout: int = 10) -> Any:
        """Wait for an element to be present and return it"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {value}")
            return None

    def scrape_approved_institutes(self) -> List[Dict[str, Any]]:
        """Scrape the list of approved institutes using Selenium with explicit waits"""
        logger.info("Starting to fetch approved institutes...")
        
        try:
            driver = self.setup_driver()
            try:
                # Load the main dashboard first
                dashboard_url = "https://facilities.aicte-india.org/dashboard"
                logger.info(f"Loading dashboard: {dashboard_url}")
                driver.get(dashboard_url)
                
                # Wait for initial page load
                time.sleep(5)
                
                # Navigate to approved institutes
                approved_url = f"{dashboard_url}/pages/angulardashboard/approvedinstitute"
                logger.info(f"Loading approved institutes page: {approved_url}")
                driver.get(approved_url)
                
                # Wait for Angular to finish loading
                wait = WebDriverWait(driver, 20)
                try:
                    wait.until(lambda d: d.execute_script('return !!window.angular && !!angular.element(document.body).injector()'))
                except:
                    logger.warning("Timed out waiting for Angular")
                
                # Wait for any loading indicators to disappear
                try:
                    wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [role='progressbar']")))
                except:
                    logger.warning("Timed out waiting for loading indicator")
                
                # Try to find the data table
                try:
                    # Wait for table or grid to be present
                    table_locators = [
                        (By.CSS_SELECTOR, "table"),
                        (By.CSS_SELECTOR, "[role='grid']"),
                        (By.CSS_SELECTOR, ".ag-root"),  # ag-Grid
                        (By.CSS_SELECTOR, ".dx-datagrid"),  # DevExtreme
                        (By.CSS_SELECTOR, ".k-grid"),  # Kendo UI
                    ]
                    
                    for by, locator in table_locators:
                        try:
                            table = wait.until(EC.presence_of_element_located((by, locator)))
                            logger.info(f"Found table using locator: {locator}")
                            
                            # Wait for rows to be present
                            rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, f"{locator} tr, {locator} [role='row']")))
                            if rows:
                                logger.info(f"Found {len(rows)} rows")
                                
                                # Try to get headers
                                headers = []
                                header_cells = rows[0].find_elements(By.CSS_SELECTOR, "th, td, [role='columnheader']")
                                for cell in header_cells:
                                    try:
                                        header_text = cell.text.strip().lower()
                                        if header_text:
                                            headers.append(header_text)
                                    except:
                                        continue
                                
                                if headers:
                                    logger.info(f"Found headers: {headers}")
                                    
                                    # Extract data from rows
                                    institutes = []
                                    for row in rows[1:]:  # Skip header row
                                        try:
                                            cells = row.find_elements(By.CSS_SELECTOR, "td, [role='gridcell']")
                                            if cells:
                                                institute = {}
                                                for header, cell in zip(headers, cells):
                                                    try:
                                                        cell_text = cell.text.strip()
                                                        if cell_text:
                                                            institute[header] = cell_text
                                                    except:
                                                        continue
                                                if institute:
                                                    institutes.append(institute)
                                        except:
                                            continue
                                    
                                    if institutes:
                                        logger.info(f"Successfully extracted {len(institutes)} institutes")
                                        return institutes
                            
                            break  # Found a table, no need to check other locators
                            
                        except TimeoutException:
                            continue
                    
                except Exception as e:
                    logger.warning(f"Failed to find or process table: {str(e)}")
                
                # If we couldn't get data from the table, try JavaScript
                try:
                    # Try to get data from Angular scope
                    js_data = driver.execute_script("""
                        try {
                            var scope = angular.element(document.querySelector('[ng-controller]')).scope();
                            if (scope && scope.institutes) return scope.institutes;
                            if (scope && scope.data) return scope.data;
                            return null;
                        } catch (e) {
                            return null;
                        }
                    """)
                    
                    if js_data and isinstance(js_data, list):
                        logger.info(f"Successfully extracted {len(js_data)} institutes from JavaScript")
                        return js_data
                    
                except Exception as e:
                    logger.warning(f"Failed to get data from JavaScript: {str(e)}")
                
                logger.error("Could not find any institutes")
                return []
                
            finally:
                driver.quit()
            
        except Exception as e:
            logger.error(f"Error fetching institutes: {str(e)}")
            return []

    def scrape_institute_details(self, institute: Dict) -> Dict:
        """Scrape detailed information for a specific institute"""
        logger.info(f"Scraping details for: {institute['name']}")
        details = institute.copy()
        
        try:
            institute_url = f"{self.api_url}/institutes/{institute['institute_code']}"
            logger.info(f"Fetching institute details from {institute_url}")
            institute_response = self.session.get(institute_url, timeout=self.timeout)
            institute_response.raise_for_status()
            institute_details = institute_response.json()
            
            details.update({
                'address': institute_details.get('address', ''),
                'website': institute_details.get('website', ''),
                'email': institute_details.get('email', ''),
                'phone': institute_details.get('phone', ''),
                'courses': institute_details.get('courses', []),
                'facilities': institute_details.get('facilities', []),
                'faculty': institute_details.get('faculty', [])
            })
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping institute details: {str(e)}")
        
        return details

    def scrape_all_data(self):
        """Main function to scrape all AICTE data"""
        try:
            # Step 1: Get list of institutes
            institutes = self.scrape_approved_institutes()
            logger.info(f"Found {len(institutes)} institutes")
            
            # Step 2: Get detailed information for each institute
            detailed_data = []
            for institute in institutes:
                details = self.scrape_institute_details(institute)
                detailed_data.append(details)
                time.sleep(2)  # Rate limiting
            
            # Step 3: Save processed data
            with open(self.processed_dir / "detailed_institutes.json", 'w') as f:
                json.dump(detailed_data, f, indent=2)
            
            # Create CSV files for different aspects
            self.create_csv_files(detailed_data)
            
            return {
                "institutes": len(institutes),
                "detailed_data": len(detailed_data)
            }
            
        except Exception as e:
            logger.error(f"Error in scrape_all_data: {str(e)}")
            return None

    def create_csv_files(self, detailed_data: List[Dict]):
        """Create separate CSV files for different data aspects"""
        try:
            # Basic institute information
            institutes_df = pd.DataFrame([
                {k: v for k, v in d.items() if not isinstance(v, (list, dict))}
                for d in detailed_data
            ])
            institutes_df.to_csv(self.processed_dir / "institutes.csv", index=False)
            
            # Courses information
            courses = []
            for inst in detailed_data:
                for course in inst.get('courses', []):
                    course['institute_name'] = inst['name']
                    courses.append(course)
            pd.DataFrame(courses).to_csv(self.processed_dir / "courses.csv", index=False)
            
            # Faculty information
            faculty = []
            for inst in detailed_data:
                for member in inst.get('faculty', []):
                    member['institute_name'] = inst['name']
                    faculty.append(member)
            pd.DataFrame(faculty).to_csv(self.processed_dir / "faculty.csv", index=False)
            
            # Facilities information
            facilities = []
            for inst in detailed_data:
                facility = inst.get('facilities', [])
                facility['institute_name'] = inst['name']
                facilities.append(facility)
            pd.DataFrame(facilities).to_csv(self.processed_dir / "facilities.csv", index=False)
            
        except Exception as e:
            logger.error(f"Error creating CSV files: {str(e)}")

def main():
    """Main function to run the scraper"""
    scraper = AICTEScraper()
    stats = scraper.scrape_all_data()
    logger.info(f"Scraping completed. Stats: {stats}")

if __name__ == "__main__":
    main()
