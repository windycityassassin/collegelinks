"""
Generate sample college data for testing and development.
"""
from typing import Dict, Any
import random
from datetime import datetime, timedelta
from pathlib import Path
import json

def generate_sample_location() -> Dict[str, Any]:
    """Generate sample location data"""
    return {
        "address": "123 College Road, Example Area",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400001",
        "latitude": 19.0760 + random.uniform(-0.1, 0.1),
        "longitude": 72.8777 + random.uniform(-0.1, 0.1),
        "district": "Mumbai City",
        "landmark": "Near Central Railway Station"
    }

def generate_sample_contact() -> Dict[str, Any]:
    """Generate sample contact information"""
    return {
        "website": "https://example-college.edu.in",
        "email": "info@example-college.edu.in",
        "phone": ["+91-22-12345678", "+91-22-87654321"],
        "fax": "+91-22-11223344",
        "social_media": {
            "facebook": "https://facebook.com/example-college",
            "twitter": "https://twitter.com/example-college"
        }
    }

def generate_sample_accreditation() -> Dict[str, Any]:
    """Generate sample accreditation data"""
    return {
        "naac_grade": random.choice(["A++", "A+", "A", "B++", "B+"]),
        "naac_score": round(random.uniform(3.0, 4.0), 2),
        "naac_valid_until": (datetime.now() + timedelta(days=365*3)).strftime("%Y-%m-%d"),
        "nirf_rank": random.randint(1, 200),
        "nba_accredited": random.choice([True, False]),
        "other_accreditations": ["ISO 9001:2015", "ABET"]
    }

def generate_sample_infrastructure() -> Dict[str, Any]:
    """Generate sample infrastructure details"""
    return {
        "campus_size_acres": round(random.uniform(10, 100), 2),
        "has_hostel": True,
        "hostel_capacity": {
            "boys": random.randint(500, 2000),
            "girls": random.randint(500, 2000)
        },
        "library": True,
        "sports_facilities": ["Cricket Ground", "Basketball Court", "Gymnasium"],
        "laboratories": ["Computer Lab", "Physics Lab", "Chemistry Lab"],
        "wifi_enabled": True,
        "classrooms": random.randint(50, 200),
        "auditorium": True,
        "cafeteria": True,
        "medical_facility": True
    }

def generate_sample_course() -> Dict[str, Any]:
    """Generate sample course information"""
    courses = [
        ("B.Tech", "Computer Science and Engineering"),
        ("B.Tech", "Electronics and Communication"),
        ("B.Tech", "Mechanical Engineering"),
        ("M.Tech", "Data Science"),
        ("MBA", "Business Administration")
    ]
    degree, specialization = random.choice(courses)
    
    return {
        "name": f"{degree} in {specialization}",
        "code": f"{degree.replace('.', '')}{random.randint(100, 999)}",
        "degree": degree,
        "duration_years": 4.0 if degree == "B.Tech" else 2.0,
        "department": specialization.split()[0],
        "specialization": specialization,
        "seats": random.randint(60, 180),
        "course_type": "UG" if degree.startswith("B") else "PG",
        "description": f"Premier {degree} program in {specialization}",
        "syllabus_url": f"https://example-college.edu.in/syllabus/{degree.lower()}-{specialization.lower().replace(' ', '-')}",
        "career_prospects": [
            "Software Engineer",
            "Data Scientist",
            "Research and Development",
            "Higher Studies"
        ]
    }

def generate_sample_department() -> Dict[str, Any]:
    """Generate sample department information"""
    departments = [
        "Computer Science",
        "Electronics",
        "Mechanical",
        "Civil",
        "Chemical"
    ]
    dept = random.choice(departments)
    
    return {
        "name": f"{dept} Engineering",
        "established_year": random.randint(1990, 2010),
        "head_of_dept": f"Dr. Example Professor",
        "courses_offered": [f"B.Tech in {dept}", f"M.Tech in {dept}"],
        "faculty_count": random.randint(20, 50),
        "research_areas": [
            "Artificial Intelligence",
            "Machine Learning",
            "IoT",
            "Robotics"
        ],
        "achievements": [
            "Best Department Award 2022",
            "Research Excellence Award"
        ]
    }

def generate_sample_placement() -> Dict[str, Any]:
    """Generate sample placement statistics"""
    eligible = random.randint(100, 200)
    placed = random.randint(80, eligible)
    
    return {
        "year": datetime.now().year,
        "eligible_students": eligible,
        "placed_students": placed,
        "companies_visited": random.randint(50, 100),
        "highest_package": round(random.uniform(20, 50), 2),
        "average_package": round(random.uniform(8, 15), 2),
        "median_package": round(random.uniform(6, 12), 2),
        "sector_wise_placements": {
            "IT": random.randint(40, 80),
            "Manufacturing": random.randint(10, 30),
            "Finance": random.randint(10, 30)
        },
        "top_recruiters": [
            "Example Tech",
            "Sample Systems",
            "Test Industries"
        ]
    }

def generate_sample_college(college_id: str) -> Dict[str, Any]:
    """Generate a complete sample college profile"""
    return {
        "id": college_id,
        "name": f"Example Institute of Technology {college_id}",
        "short_name": f"EIT-{college_id}",
        "established_year": random.randint(1950, 2000),
        "institution_type": random.choice(["Private", "State", "Central", "Deemed"]),
        "approved_by": ["AICTE", "UGC"],
        "affiliated_to": "Example Technical University",
        
        "location": generate_sample_location(),
        "contact": generate_sample_contact(),
        "accreditation": generate_sample_accreditation(),
        "infrastructure": generate_sample_infrastructure(),
        "departments": [generate_sample_department() for _ in range(3)],
        "courses": [generate_sample_course() for _ in range(5)],
        "admissions": {
            "entrance_exams": ["JEE Main", "JEE Advanced", "GATE"],
            "admission_process": "Merit based on entrance exam rank",
            "important_dates": {
                "application_start": "2024-01-01",
                "application_end": "2024-03-31"
            },
            "eligibility_criteria": "Minimum 60% in PCM",
            "required_documents": [
                "10th Certificate",
                "12th Certificate",
                "Entrance Exam Score Card"
            ]
        },
        "fee_structure": {
            "currency": "INR",
            "program_fees": {
                "B.Tech": {
                    "tuition": 200000,
                    "hostel": 100000,
                    "other": 50000
                },
                "M.Tech": {
                    "tuition": 250000,
                    "hostel": 100000,
                    "other": 50000
                }
            },
            "scholarship_available": True,
            "scholarship_details": "Merit-based scholarships available"
        },
        "placement": [generate_sample_placement()],
        
        "about": "Example Institute of Technology is a premier institution...",
        "vision": "To be a globally recognized institution...",
        "mission": "To provide quality technical education...",
        "notable_alumni": [
            "Dr. Example Scientist",
            "Mr. Sample Entrepreneur"
        ],
        "research_centers": [
            "Center for AI and ML",
            "Center for IoT"
        ]
    }

def generate_sample_dataset(num_colleges: int = 10, output_file: Path = None) -> Dict[str, Any]:
    """
    Generate a sample dataset with multiple colleges.
    
    Args:
        num_colleges: Number of colleges to generate
        output_file: Optional path to save the generated data
        
    Returns:
        Dictionary containing college data
    """
    colleges = {}
    for i in range(num_colleges):
        college_id = f"{i+1:03d}"
        colleges[college_id] = generate_sample_college(college_id)
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(colleges, f, indent=2)
    
    return colleges

if __name__ == "__main__":
    # Generate sample data
    output_path = Path(__file__).parent.parent.parent / "data/processed/sample_colleges.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating sample college data...")
    colleges = generate_sample_dataset(num_colleges=20, output_file=output_path)
    print(f"Generated {len(colleges)} sample colleges at: {output_path}")
    
    # Validate the generated data
    from ..schemas.validators import validate_file
    validate_file(output_path)
