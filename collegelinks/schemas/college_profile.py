from pydantic import BaseModel, Field
from typing import Optional, List, Dict

class CollegeProfile(BaseModel):
    """Schema for college profile data"""
    college_id: str = Field(..., description="Unique identifier for the college")
    name: str = Field(..., description="Name of the college")
    address: str = Field(..., description="Full address of the college")
    city: Optional[str] = Field(None, description="City where the college is located")
    state: Optional[str] = Field(None, description="State where the college is located")
    pincode: Optional[str] = Field(None, description="PIN code of the college location")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    courses: Optional[List[str]] = Field(default_factory=list, description="List of courses offered")
    facilities: Optional[List[str]] = Field(default_factory=list, description="List of available facilities")
    website: Optional[str] = Field(None, description="College website URL")
    contact: Optional[Dict[str, str]] = Field(default_factory=dict, description="Contact information")
    established_year: Optional[int] = Field(None, description="Year the college was established")
    accreditation: Optional[Dict[str, str]] = Field(default_factory=dict, description="Accreditation details")
    
    class Config:
        allow_population_by_field_name = True
