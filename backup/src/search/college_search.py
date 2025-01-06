"""
Advanced search functionality for colleges with multiple filter options.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from pydantic import BaseModel
import pandas as pd
from ..schemas.college_profile import CollegeProfile

class SearchFilters(BaseModel):
    """Search filters for college search"""
    # Location filters
    state: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    max_distance_km: Optional[float] = None  # If user provides location
    
    # Academic filters
    courses: Optional[List[str]] = None
    degrees: Optional[List[str]] = None  # B.Tech, M.Tech, MBA etc.
    specializations: Optional[List[str]] = None
    
    # Fee filters
    max_tuition_fee: Optional[float] = None
    min_tuition_fee: Optional[float] = None
    
    # Ranking/Rating filters
    min_nirf_rank: Optional[int] = None
    max_nirf_rank: Optional[int] = None
    naac_grades: Optional[List[str]] = None  # A++, A+, A etc.
    min_naac_score: Optional[float] = None
    
    # Infrastructure filters
    required_facilities: Optional[List[str]] = None
    hostel_required: Optional[bool] = None
    
    # Type filters
    institution_types: Optional[List[str]] = None
    approvals: Optional[List[str]] = None

class CollegeSearchEngine:
    """Engine for advanced college search with multiple filters"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize search engine with data directory"""
        self.data_dir = Path(data_dir)
        self.colleges: Dict[str, CollegeProfile] = {}
        self.load_colleges()
    
    def load_colleges(self):
        """Load college data from processed directory"""
        college_file = self.data_dir / "processed" / "college_profiles.json"
        if college_file.exists():
            with open(college_file, 'r') as f:
                data = json.load(f)
                if "colleges" in data:
                    for college in data["colleges"]:
                        self.colleges[college["id"]] = CollegeProfile(**college)
                else:
                    raise ValueError("Invalid college data format: missing 'colleges' key")
        else:
            raise ValueError(f"College data file not found: {college_file}")
    
    def filter_by_type(self, college: CollegeProfile, filters: SearchFilters) -> bool:
        """Apply institution type and approval filters"""
        if filters.institution_types and college.type.lower() not in [t.lower() for t in filters.institution_types]:
            return False
        return True
    
    def filter_by_academics(self, college: CollegeProfile, filters: SearchFilters) -> bool:
        """Apply academic filters"""
        if filters.courses:
            all_courses = []
            for program_type, courses in college.courses.items():
                all_courses.extend([c.name.lower() for c in courses])
            if not any(course.lower() in all_courses for course in filters.courses):
                return False
        
        if filters.degrees:
            all_degrees = set()
            for program_type, courses in college.courses.items():
                for course in courses:
                    degree = course.name.split()[0].lower()
                    all_degrees.add(degree)
            if not any(degree.lower() in all_degrees for degree in filters.degrees):
                return False
        
        return True
    
    def filter_by_rankings(self, college: CollegeProfile, filters: SearchFilters) -> bool:
        """Apply ranking and accreditation filters"""
        if filters.min_nirf_rank and college.accreditation.nirf_rank:
            if college.accreditation.nirf_rank > filters.min_nirf_rank:
                return False
        
        if filters.max_nirf_rank and college.accreditation.nirf_rank:
            if college.accreditation.nirf_rank < filters.max_nirf_rank:
                return False
        
        if filters.naac_grades and college.accreditation.naac_grade:
            if college.accreditation.naac_grade not in filters.naac_grades:
                return False
        
        return True
    
    def filter_by_infrastructure(self, college: CollegeProfile, filters: SearchFilters) -> bool:
        """Apply infrastructure filters"""
        if filters.required_facilities:
            college_facilities = set(college.facilities.sports)
            if college.facilities.labs:
                college_facilities.update(college.facilities.labs)
            if not all(facility.lower() in [f.lower() for f in college_facilities] for facility in filters.required_facilities):
                return False
        
        if filters.hostel_required:
            if not (college.facilities.hostel.boys or college.facilities.hostel.girls):
                return False
        
        return True
    
    def search(self, filters: SearchFilters) -> List[CollegeProfile]:
        """
        Search colleges using provided filters
        
        Args:
            filters: SearchFilters object containing search criteria
            
        Returns:
            List of CollegeProfile objects matching the criteria
        """
        if not filters:
            return list(self.colleges.values())
        
        filtered_colleges = []
        for college in self.colleges.values():
            if all([
                self.filter_by_type(college, filters),
                self.filter_by_academics(college, filters),
                self.filter_by_rankings(college, filters),
                self.filter_by_infrastructure(college, filters),
            ]):
                filtered_colleges.append(college)
        
        return filtered_colleges
    
    def get_unique_values(self) -> Dict[str, List[str]]:
        """Get unique values for different filter fields to help in UI dropdowns"""
        unique_values = {
            'institution_types': set(),
            'courses': set(),
            'degrees': set(),
            'facilities': set(),
            'naac_grades': set()
        }
        
        for college in self.colleges.values():
            unique_values['institution_types'].add(college.type)
            
            for program_type, courses in college.courses.items():
                for course in courses:
                    unique_values['courses'].add(course.name)
                    unique_values['degrees'].add(course.name.split()[0])
            
            unique_values['facilities'].update(college.facilities.sports)
            if college.facilities.labs:
                unique_values['facilities'].update(college.facilities.labs)
            
            if college.accreditation.naac_grade:
                unique_values['naac_grades'].add(college.accreditation.naac_grade)
        
        return {k: sorted(list(v)) for k, v in unique_values.items()}
