"""
Validation utilities for college data schemas.
"""
from typing import Dict, List, Any, Tuple
from pathlib import Path
import json
from pydantic import ValidationError
from .college_profile import CollegeProfile

class SchemaValidator:
    """Validator class for college data"""
    
    @staticmethod
    def validate_college_profile(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate college profile data against the schema.
        
        Args:
            data: Dictionary containing college profile data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            CollegeProfile(**data)
            return True, []
        except ValidationError as e:
            errors = []
            for error in e.errors():
                location = " -> ".join(str(loc) for loc in error["loc"])
                message = error["msg"]
                errors.append(f"{location}: {message}")
            return False, errors

    @staticmethod
    def validate_college_profiles_file(file_path: Path) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate a JSON file containing multiple college profiles.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple of (is_valid, dict_of_errors_by_college)
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, {"file_error": [f"Invalid JSON: {str(e)}"]}
        
        if not isinstance(data, dict):
            return False, {"file_error": ["Root element must be a dictionary"]}
        
        all_valid = True
        errors_by_college = {}
        
        for college_id, college_data in data.items():
            is_valid, errors = SchemaValidator.validate_college_profile(college_data)
            if not is_valid:
                all_valid = False
                errors_by_college[college_id] = errors
        
        return all_valid, errors_by_college

    @staticmethod
    def generate_schema_documentation(output_path: Path) -> None:
        """
        Generate markdown documentation for the college profile schema.
        
        Args:
            output_path: Path where to save the documentation
        """
        schema = CollegeProfile.schema()
        
        def format_field(field: Dict[str, Any], indent: int = 0) -> str:
            """Format a single schema field as markdown"""
            indent_str = "  " * indent
            required = field.get("required", False)
            field_type = field.get("type", "any")
            description = field.get("description", "")
            
            md = f"{indent_str}- **{field['title']}**"
            if required:
                md += " (required)"
            md += f"\n{indent_str}  - Type: `{field_type}`"
            if description:
                md += f"\n{indent_str}  - Description: {description}"
            return md
        
        def format_properties(properties: Dict[str, Any], indent: int = 0) -> str:
            """Format all properties of a schema section"""
            return "\n".join(
                format_field({**prop, "title": name}, indent)
                for name, prop in properties.items()
            )
        
        # Generate documentation
        doc = f"""# College Profile Schema Documentation

## Overview
This document describes the schema for college profiles in the CareerSaathi platform.

## Schema Details

{format_properties(schema.get("properties", {}))}
"""
        
        # Save documentation
        with open(output_path, 'w') as f:
            f.write(doc)

def validate_file(file_path: Path) -> None:
    """
    Validate a college profiles file and print results.
    
    Args:
        file_path: Path to the JSON file to validate
    """
    print(f"Validating {file_path}...")
    is_valid, errors = SchemaValidator.validate_college_profiles_file(file_path)
    
    if is_valid:
        print("✅ File is valid!")
    else:
        print("❌ Validation failed!")
        for college_id, college_errors in errors.items():
            print(f"\nErrors in college {college_id}:")
            for error in college_errors:
                print(f"  - {error}")
