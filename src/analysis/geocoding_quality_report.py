"""
Generate quality report for geocoded colleges data
"""
import pandas as pd
import json
from pathlib import Path

def analyze_geocoding_quality(df):
    """Analyze geocoding quality and generate report"""
    total_records = len(df)
    
    # Basic stats
    stats = {
        "total_records": total_records,
        "geocoded_records": df[df['latitude'].notna()].shape[0],
        "records_with_pincode": df[df['postal_code'].notna()].shape[0],
        "quality_scores": {
            "high_confidence": df[df['latitude'].notna() & (df['latitude'] != 0)].shape[0],
            "medium_confidence": df[df['latitude'].notna() & (df['latitude'] != 0)].shape[0],
            "low_confidence": df[df['latitude'].isna() | (df['latitude'] == 0)].shape[0]
        }
    }
    
    # State-wise distribution
    state_dist = df['state'].value_counts().to_dict()
    stats["state_distribution"] = state_dist
    
    # Institution type distribution
    inst_type_dist = df['institution_type'].value_counts().to_dict()
    stats["institution_type_distribution"] = inst_type_dist
    
    # Quality by institution type
    quality_by_type = {}
    for inst_type in df['institution_type'].unique():
        type_df = df[df['institution_type'] == inst_type]
        quality_by_type[inst_type] = {
            "total": type_df.shape[0],
            "geocoded": type_df[type_df['latitude'].notna() & (type_df['latitude'] != 0)].shape[0],
            "with_pincode": type_df[type_df['postal_code'].notna()].shape[0]
        }
    stats["quality_by_institution_type"] = quality_by_type
    
    # Missing data analysis
    missing_data = {
        "missing_pincode": df[df['postal_code'].isna()].shape[0],
        "missing_state": df[df['state'].isna()].shape[0],
        "missing_address": df[df['address'].isna()].shape[0],
        "missing_coordinates": df[df['latitude'].isna() | df['longitude'].isna()].shape[0]
    }
    stats["missing_data"] = missing_data
    
    return stats

def identify_unfound_colleges(df):
    """Identify colleges that weren't found or have low confidence scores"""
    unfound = df[
        (df['latitude'].isna()) | 
        (df['longitude'].isna()) |
        (df['latitude'] == 0) |
        (df['longitude'] == 0)
    ][['name', 'address', 'state', 'postal_code']]
    return unfound

def main():
    # Read data
    data_path = Path(__file__).parent.parent.parent / 'data/processed/geocoded_colleges.csv'
    df = pd.read_csv(data_path)
    
    # Generate quality report
    quality_stats = analyze_geocoding_quality(df)
    
    # Save quality report
    report_path = Path(__file__).parent.parent.parent / 'docs/geocoding_quality_report.json'
    with open(report_path, 'w') as f:
        json.dump(quality_stats, f, indent=2)
    
    # Generate unfound colleges report
    unfound_colleges = identify_unfound_colleges(df)
    unfound_path = Path(__file__).parent.parent.parent / 'docs/unfound_colleges.csv'
    unfound_colleges.to_csv(unfound_path, index=False)
    
    print(f"Reports generated:\n1. {report_path}\n2. {unfound_path}")

if __name__ == "__main__":
    main()
