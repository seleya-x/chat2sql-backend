#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to run SQL queries on the pjtdeals database and return results as a DataFrame
"""

import pandas as pd
from sql_connector import read_sql_query_with_pandas

def run_query(query, database="pjtdeals"):
    """
    Run a SQL query and return the results as a DataFrame with data cleaning applied
    
    Args:
        query (str): SQL query to execute
        database (str): Database name, defaults to "pjtdeals"
        
    Returns:
        pandas.DataFrame: Query results as a DataFrame
    """
    # Execute the query
    df = read_sql_query_with_pandas(query, database)
    
    if df is not None:
        # Apply data cleaning based on the project requirements
        
        # 1. Replace NaN values with empty strings
        df = df.fillna('')
        
        # 2. Replace "NO INFO", "Not Found", null, "nan", "None" with empty strings
        for col in df.columns:
            if df[col].dtype == 'object':  # Only process string columns
                df[col] = df[col].replace(['NO INFO', 'Not Found', 'nan', 'None'], '')
        
        # 3. Remove specified columns if they exist
        if 'engagement_context' in df.columns:
            df = df.drop(columns=['engagement_context'])
        if 'verification' in df.columns:
            df = df.drop(columns=['verification'])
        
        return df
    
    return None

if __name__ == "__main__":
    print("SQL Query Runner")
    print("----------------")
    print("Enter your SQL query below (press Enter twice to submit):")
    
    # Collect multi-line input
    lines = []
    while True:
        line = input()
        if line:
            lines.append(line)
        else:
            break
    
    query = '\n'.join(lines)
    
    if query:
        print("\nExecuting query...")
        result = run_query(query)
        
        if result is not None:
            print("\nQuery results:")
            print(result)
            
            # Save to CSV
            csv_filename = "query_results.csv"
            result.to_csv(csv_filename, index=False)
            print(f"\nResults saved to {csv_filename}")
        else:
            print("\nQuery execution failed or returned no results.")
    else:
        print("No query provided. Exiting.")
