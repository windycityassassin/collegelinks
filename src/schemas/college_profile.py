"""
Schema definitions for college profiles and related data structures.
"""
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, HttpUrl, confloat

class Course(BaseModel):
    """Course information"""
    name: str
    duration: str
    seats: int
    fee_per_semester: float

class Library(BaseModel):
    """Library facilities"""
    name: str
    books: int
    digital_resources: bool
    study_spaces: bool

class Hostel(BaseModel):
    """Hostel facilities"""
    boys: bool
    girls: bool
    total_capacity: int

class Facilities(BaseModel):
    """Campus facilities"""
    library: Library
    hostel: Hostel
    sports: List[str]
    labs: Optional[List[str]] = None

class Contact(BaseModel):
    """Contact information"""
    website: HttpUrl
    email: str
    phone: str

class Accreditation(BaseModel):
    """Accreditation details"""
    naac_grade: Optional[str] = None
    nirf_rank: Optional[int] = None

class PlacementStats(BaseModel):
    """Placement statistics"""
    year: int
    companies_visited: int
    highest_package: int
    average_package: int
    placement_percentage: float

class Placements(BaseModel):
    """Placement information"""
    statistics: PlacementStats
    top_recruiters: List[str]

class Research(BaseModel):
    """Research information"""
    research_centers: int
    patents_filed: int
    publications: int
    funding: str

class ImportantDates(BaseModel):
    """Important admission dates"""
    application_start: str
    application_end: str
    academic_year_start: str

class Admissions(BaseModel):
    """Admission information"""
    entrance_exams: List[str]
    admission_process: str
    important_dates: ImportantDates

class Media(BaseModel):
    """Media information"""
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    virtual_tour: Optional[str] = None

class CollegeProfile(BaseModel):
    """Complete college profile"""
    id: str
    name: str
    type: str
    established: int
    latitude: Optional[confloat(ge=-90, le=90)] = None
    longitude: Optional[confloat(ge=-180, le=180)] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    accreditation: Accreditation
    contact: Contact
    courses: Dict[str, List[Course]]
    facilities: Facilities
    placements: Optional[Placements] = None
    research: Optional[Research] = None
    admissions: Admissions
    media: Optional[Media] = None

    class Config:
        populate_by_name = True
