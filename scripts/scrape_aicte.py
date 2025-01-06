"""
Script to run AICTE website scraper
"""
import logging
from pathlib import Path
import sys

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from collegelinks.scrapers.aicte_scraper import AICTEScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the scraper"""
    try:
        scraper = AICTEScraper()
        logger.info("Starting AICTE website scraping...")
        stats = scraper.scrape_all_data()
        logger.info(f"Scraping completed successfully. Stats: {stats}")
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        raise

if __name__ == "__main__":
    main()
