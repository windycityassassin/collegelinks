"""
Data processing module for CareerSaathi Geocoding Platform
"""

from .data_loader import CollegeDataLoader
from .indian_address_parser import IndianAddressParser

__all__ = ['CollegeDataLoader', 'IndianAddressParser']
