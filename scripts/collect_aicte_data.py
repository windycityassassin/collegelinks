"""
Script to collect data from AICTE
"""
import asyncio
import logging
from pathlib import Path
import sys

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from collegelinks.collectors.aicte_collector import AICTEDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to run data collection"""
    try:
        collector = AICTEDataCollector()
        logger.info("Starting AICTE data collection...")
        stats = await collector.collect_all_data()
        logger.info(f"Collection completed successfully. Stats: {stats}")
    except Exception as e:
        logger.error(f"Error during data collection: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
