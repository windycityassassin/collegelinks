import pandas as pd
import numpy as np
from pathlib import Path

class DataQualityChecker:
    def __init__(self, file_path='docs/cleaned_colleges.csv'):
        self.df = pd.read_csv(file_path)
        print(f"Loaded {len(self.df)} records for quality check")

    def check_completeness(self):
        """Check for missing values in each column"""
        print("\n1. COMPLETENESS CHECK")
        print("-" * 50)
        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df) * 100).round(2)
        
        print("Missing values by column:")
        for col in self.df.columns:
            print(f"{col}: {missing[col]} missing ({missing_pct[col]}%)")

    def check_consistency(self):
        """Check for consistency in state names and postal codes"""
        print("\n2. CONSISTENCY CHECK")
        print("-" * 50)
        
        # State names consistency
        print("\nState names frequency:")
        print(self.df['state'].value_counts().head(10))
        
        # Postal code format
        if 'postal_code' in self.df.columns:
            # Convert to string first
            postal_codes = self.df['postal_code'].astype(str)
            valid_postal = postal_codes.str.match(r'^\d{6}$').sum()
            total_postal = self.df['postal_code'].notna().sum()
            print(f"\nPostal code format check:")
            print(f"Valid 6-digit codes: {valid_postal} out of {total_postal} ({(valid_postal/total_postal*100):.2f}% valid)")

    def check_uniqueness(self):
        """Check for potential duplicates"""
        print("\n3. UNIQUENESS CHECK")
        print("-" * 50)
        
        # Check for exact duplicates
        exact_dupes = self.df.duplicated().sum()
        print(f"Exact duplicates: {exact_dupes}")
        
        # Check for potential duplicates based on name similarity
        name_dupes = self.df.groupby(['state', 'name']).size()
        dupes = name_dupes[name_dupes > 1]
        print(f"\nPotential name duplicates by state:")
        if len(dupes) > 0:
            print(dupes)
        else:
            print("No duplicate names found within states")

    def check_validity(self):
        """Check data validity"""
        print("\n4. VALIDITY CHECK")
        print("-" * 50)
        
        # Institution types
        print("\nInstitution types:")
        print(self.df['institution_type'].value_counts())
        
        # Address length statistics
        address_lengths = self.df['address'].str.len()
        print("\nAddress length statistics:")
        print(f"Min length: {address_lengths.min()}")
        print(f"Max length: {address_lengths.max()}")
        print(f"Mean length: {address_lengths.mean():.2f}")
        
        # Check for suspicious patterns
        short_addresses = self.df[address_lengths < 20]
        if len(short_addresses) > 0:
            print(f"\nWarning: Found {len(short_addresses)} addresses shorter than 20 characters:")
            print(short_addresses[['name', 'address']].head())

    def check_distribution(self):
        """Check data distribution"""
        print("\n5. DISTRIBUTION CHECK")
        print("-" * 50)
        
        # Distribution by state
        state_dist = self.df['state'].value_counts()
        print("\nTop 10 states by number of institutions:")
        print(state_dist.head(10))
        
        # Distribution by institution type and state
        print("\nInstitutions by type and state (top 5 states):")
        type_state_dist = pd.crosstab(self.df['state'], self.df['institution_type'])
        print(type_state_dist.head())

    def suggest_improvements(self):
        """Suggest potential improvements"""
        print("\n6. SUGGESTED IMPROVEMENTS")
        print("-" * 50)
        
        improvements = []
        
        # Check for missing values
        if self.df.isnull().any().any():
            improvements.append("- Handle missing values in the dataset")
        
        # Check postal codes
        if 'postal_code' in self.df.columns:
            invalid_postal = ~self.df['postal_code'].str.match(r'^\d{6}$', na=False)
            if invalid_postal.any():
                improvements.append("- Standardize postal code format")
        
        # Check state names
        state_counts = self.df['state'].value_counts()
        if len(state_counts) > 29:  # India has 28 states and 8 union territories
            improvements.append("- Standardize state names (possible variations present)")
        
        # Check address quality
        if (self.df['address'].str.len() < 20).any():
            improvements.append("- Review and enhance short addresses")
        
        print("\nSuggested improvements:")
        for imp in improvements:
            print(imp)

    def run_all_checks(self):
        """Run all quality checks"""
        self.check_completeness()
        self.check_consistency()
        self.check_uniqueness()
        self.check_validity()
        self.check_distribution()
        self.suggest_improvements()

if __name__ == "__main__":
    checker = DataQualityChecker()
    checker.run_all_checks()
