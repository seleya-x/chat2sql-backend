#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to run a specific SQL query and display the results
"""

import os
import pandas as pd
from sql_connector import read_sql_query_with_pandas
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_dataframe(df):
    """
    Apply data cleaning rules based on project requirements
    
    Args:
        df (pandas.DataFrame): DataFrame to clean
        
    Returns:
        pandas.DataFrame: Cleaned DataFrame
    """
    if df is None:
        return None
    
    # Store original column order
    original_columns = list(df.columns)
        
    # 1. Replace NaN values with empty strings
    df = df.fillna('')
    
    # 2. Replace "NO INFO", "Not Found", null, "nan", "None" with empty strings
    for col in df.columns:
        if df[col].dtype == 'object':  # Only process string columns
            df[col] = df[col].replace(['NO INFO', 'Not Found', 'nan', 'None'], '')
    
    # 3. Remove specified columns if they exist
    columns_to_remove = []
    if 'engagement_context' in df.columns:
        columns_to_remove.append('engagement_context')
    if 'verification' in df.columns:
        columns_to_remove.append('verification')
    
    if columns_to_remove:
        df = df.drop(columns=columns_to_remove)
        # Update original_columns list to remove dropped columns
        original_columns = [col for col in original_columns if col not in columns_to_remove]
    
    # 4. For deal deduplication project: Remove rows where columns 5 through 13 are all blank
    if len(df.columns) >= 13:
        # Get columns 5 through 13 (0-indexed, so 4 to 12)
        cols_to_check = df.columns[4:13] if len(df.columns) > 13 else df.columns[4:]
        
        # Check if all values in these columns are blank, nan, null, or None
        blank_mask = df[cols_to_check].apply(lambda row: all(val == '' for val in row), axis=1)
        df = df[~blank_mask]
    
    # 5. For deal deduplication project: Fill blank "engagement_role" values with "company"
    if 'engagement_role' in df.columns:
        df['engagement_role'] = df['engagement_role'].replace('', 'company')
    
    # Ensure the DataFrame columns are in the original order
    remaining_columns = [col for col in original_columns if col in df.columns]
    df = df[remaining_columns]
    
    return df

def main():
    # Get the SQL query file path from environment variables
    sql_query_file = os.getenv('SQL_QUERY_FILE', 'sql_query.txt')  # Default to sql_query.txt if env var not set
    
    # Read the SQL query from the file
    try:
        with open(sql_query_file, 'r') as file:
            query = file.read().strip()
        print(f"Successfully read SQL query from {sql_query_file}")
    except Exception as e:
        print(f"Error reading SQL query file: {e}")
        return
    
    # Database name
    database = "pjtdeals"
    
    print(f"\nExecuting query:\n{query}")
    
    # Run the query
    df = read_sql_query_with_pandas(query, database)
    
    # Clean the data
    df = clean_dataframe(df)
    
    if df is not None:
        print("\nQuery results:")
        print(df)
        
        # Save to CSV - Use environment variable for results file path
        csv_filename = os.getenv('RESULTS_CSV_FILE', 'deal_extract_docs_results.csv')
        df.to_csv(csv_filename, index=False)
        print(f"\nResults saved to {csv_filename}")
    else:
        print("\nQuery execution failed or returned no results.")

if __name__ == "__main__":
    main()
