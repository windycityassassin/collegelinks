"""
Schema package for college data structures.
"""
from .college_profile import (
    CollegeProfile,
    Contact,
    Accreditation,
    Facilities,
    Library,
    Hostel,
    Course,
    PlacementStats,
    Placements,
    Research,
    ImportantDates,
    Admissions,
    Media
)
from .validators import SchemaValidator, validate_file

__all__ = [
    'CollegeProfile',
    'Contact',
    'Accreditation',
    'Facilities',
    'Library',
    'Hostel',
    'Course',
    'PlacementStats',
    'Placements',
    'Research',
    'ImportantDates',
    'Admissions',
    'Media',
    'SchemaValidator',
    'validate_file'
]
