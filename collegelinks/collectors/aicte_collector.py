"""
AICTE Data Collector

This module handles data collection from the AICTE dashboard and APIs.
It includes functionality for fetching institution details, course information,
and other relevant data from AICTE sources.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import pandas as pd
from datetime import datetime
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AICTEInstitution(BaseModel):
    """Model for AICTE institution data"""
    institution_id: str = Field(..., description="AICTE permanent institution ID")
    name: str = Field(..., description="Institution name")
    state: str = Field(..., description="State where institution is located")
    district: str = Field(..., description="District where institution is located")
    institution_type: str = Field(..., description="Type of institution")
    approved_intake: int = Field(..., description="Total approved intake")
    website: Optional[str] = Field(None, description="Institution website")
    email: Optional[str] = Field(None, description="Institution email")
    phone: Optional[str] = Field(None, description="Institution phone")
    address: Optional[str] = Field(None, description="Institution address")
    last_updated: datetime = Field(default_factory=datetime.now)

class AICTECourse(BaseModel):
    """Model for AICTE approved course data"""
    course_id: str = Field(..., description="Course ID")
    institution_id: str = Field(..., description="Institution ID")
    program: str = Field(..., description="Program name (e.g., B.Tech, M.Tech)")
    level: str = Field(..., description="Education level")
    intake: int = Field(..., description="Approved intake")
    nri_quota: Optional[int] = Field(None, description="NRI quota seats")
    duration: str = Field(..., description="Course duration")
    last_updated: datetime = Field(default_factory=datetime.now)

class AICTEDataCollector:
    """Collector for AICTE data"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the collector with data directory"""
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw" / "aicte"
        self.processed_dir = self.data_dir / "processed" / "aicte"
        
        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Base URLs for AICTE data
        self.base_url = "https://facilities.aicte-india.org/api/institutes"
        self.course_url = "https://facilities.aicte-india.org/api/courses"
        
        # Headers for requests
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://facilities.aicte-india.org/dashboard/"
        }
    
    async def fetch_data(self, url: str, params: Dict = None) -> Dict:
        """Fetch data from AICTE API with rate limiting and retries"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for attempt in range(3):  # 3 retries
                try:
                    # First get the session token
                    async with session.get("https://facilities.aicte-india.org/dashboard/") as init_response:
                        if init_response.status != 200:
                            logger.error(f"Failed to initialize session: {init_response.status}")
                            continue

                    # Add form data
                    form_data = {
                        'year': '2023-24',
                        'status': 'active'
                    }
                    if params:
                        form_data.update(params)

                    # Make the actual request
                    async with session.post(url, data=form_data) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Too many requests
                            wait_time = int(response.headers.get('Retry-After', 60))
                            logger.warning(f"Rate limited. Waiting {wait_time} seconds")
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"Error {response.status}: {await response.text()}")
                            await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
                except Exception as e:
                    logger.error(f"Error fetching data: {str(e)}")
                    await asyncio.sleep(5 * (attempt + 1))
            return None

    async def fetch_institutions(self, state: Optional[str] = None) -> List[AICTEInstitution]:
        """Fetch institution data from AICTE"""
        params = {"state": state} if state else {}
        data = await self.fetch_data(self.base_url, params)
        
        if not data:
            logger.error("Failed to fetch institution data")
            return []
        
        institutions = []
        for item in data:
            try:
                institution = AICTEInstitution(
                    institution_id=item['permanent_id'],
                    name=item['name'],
                    state=item['state'],
                    district=item['district'],
                    institution_type=item['type'],
                    approved_intake=int(item.get('total_intake', 0)),
                    website=item.get('website'),
                    email=item.get('email'),
                    phone=item.get('phone'),
                    address=item.get('address')
                )
                institutions.append(institution)
            except Exception as e:
                logger.error(f"Error processing institution: {str(e)}")
        
        return institutions

    async def fetch_courses(self, institution_id: str) -> List[AICTECourse]:
        """Fetch course data for an institution"""
        params = {"institution_id": institution_id}
        data = await self.fetch_data(self.course_url, params)
        
        if not data:
            logger.error(f"Failed to fetch course data for institution {institution_id}")
            return []
        
        courses = []
        for item in data:
            try:
                course = AICTECourse(
                    course_id=item['course_id'],
                    institution_id=institution_id,
                    program=item['program'],
                    level=item['level'],
                    intake=int(item.get('intake', 0)),
                    nri_quota=int(item.get('nri_quota', 0)),
                    duration=item['duration']
                )
                courses.append(course)
            except Exception as e:
                logger.error(f"Error processing course: {str(e)}")
        
        return courses

    async def collect_all_data(self):
        """Collect all institution and course data"""
        # Fetch all institutions
        institutions = await self.fetch_institutions()
        logger.info(f"Fetched {len(institutions)} institutions")
        
        # Save raw institution data
        institution_file = self.raw_dir / "institutions.json"
        with open(institution_file, 'w') as f:
            json.dump([inst.dict() for inst in institutions], f, indent=2, default=str)
        
        # Fetch courses for each institution
        all_courses = []
        for inst in institutions:
            courses = await self.fetch_courses(inst.institution_id)
            all_courses.extend(courses)
            logger.info(f"Fetched {len(courses)} courses for {inst.name}")
            await asyncio.sleep(1)  # Rate limiting
        
        # Save raw course data
        course_file = self.raw_dir / "courses.json"
        with open(course_file, 'w') as f:
            json.dump([course.dict() for course in all_courses], f, indent=2, default=str)
        
        # Create processed CSV files
        inst_df = pd.DataFrame([inst.dict() for inst in institutions])
        course_df = pd.DataFrame([course.dict() for course in all_courses])
        
        inst_df.to_csv(self.processed_dir / "institutions.csv", index=False)
        course_df.to_csv(self.processed_dir / "courses.csv", index=False)
        
        return {
            "institutions": len(institutions),
            "courses": len(all_courses)
        }

async def main():
    """Main function to run the collector"""
    collector = AICTEDataCollector()
    stats = await collector.collect_all_data()
    logger.info(f"Collection completed. Stats: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
