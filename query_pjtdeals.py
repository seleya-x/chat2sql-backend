#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example script to connect to pjtdeals database and run a SQL query
"""

import pandas as pd
from sql_connector import connect_to_mysql, read_sql_query_with_pandas, list_tables, execute_query

def main():
    # Database name
    database_name = "pjtdeals"
    
    # Connect to the database
    connection = connect_to_mysql()
    if not connection:
        print("Failed to connect to the database. Please check your connection parameters.")
        return
    
    try:
        # Select the database
        connection.select_db(database_name)
        print(f"Successfully connected to {database_name} database!")
        
        # List tables in the database
        print("\nTables in the database:")
        tables_query = "SHOW TABLES"
        with connection.cursor() as cursor:
            cursor.execute(tables_query)
            tables = cursor.fetchall()
            
        # Display table names
        table_names = [list(table.values())[0] for table in tables]
        for i, table in enumerate(table_names, 1):
            print(f"{i}. {table}")
        
        # Example query - let's get a sample from the deals table
        # You can replace 'deals' with any table that exists in your database
        print("\nEnter the number of the table you want to query (or press Enter to use 'deals'): ")
        table_choice = input()
        
        if table_choice and table_choice.isdigit() and 1 <= int(table_choice) <= len(table_names):
            table_name = table_names[int(table_choice) - 1]
        else:
            # Default to 'deals' if it exists, otherwise use the first table
            if 'deals' in table_names:
                table_name = 'deals'
            elif table_names:
                table_name = table_names[0]
            else:
                print("No tables found in the database.")
                return
        
        print(f"\nQuerying table: {table_name}")
        
        # Get column names first
        columns_query = f"SHOW COLUMNS FROM {table_name}"
        with connection.cursor() as cursor:
            cursor.execute(columns_query)
            columns = cursor.fetchall()
        
        print(f"\nColumns in {table_name}:")
        for col in columns:
            print(f"- {col['Field']} ({col['Type']})")
        
        # Run a sample query
        sample_query = f"""
        SELECT *
        FROM {table_name}
        LIMIT 5
        """
        
        print(f"\nRunning query: {sample_query}")
        results = read_sql_query_with_pandas(sample_query, database_name)
        
        if results is not None:
            # Process the results according to the memories
            # Replace "NO INFO", "Not Found", null, "nan", "None" values with blank strings
            results = results.fillna('')  # Replace NaN values with empty strings
            for col in results.columns:
                if results[col].dtype == 'object':  # Only process string columns
                    results[col] = results[col].replace(['NO INFO', 'Not Found', 'nan', 'None'], '')
            
            # Display the results
            print("\nQuery results (after cleaning):")
            print(results)
            
            # Save results to CSV
            csv_filename = f"{table_name}_sample.csv"
            results.to_csv(csv_filename, index=False)
            print(f"\nResults saved to {csv_filename}")
            
            # Basic data analysis
            print("\nDataFrame info:")
            print(results.info())
            
            # Custom query example
            print("\nWould you like to run a custom query? (y/n)")
            custom_choice = input().lower()
            
            if custom_choice == 'y':
                print("\nEnter your SQL query:")
                custom_query = input()
                
                if custom_query:
                    print(f"\nRunning custom query: {custom_query}")
                    custom_results = read_sql_query_with_pandas(custom_query, database_name)
                    
                    if custom_results is not None:
                        # Process the results according to the memories
                        custom_results = custom_results.fillna('')  # Replace NaN values with empty strings
                        for col in custom_results.columns:
                            if custom_results[col].dtype == 'object':  # Only process string columns
                                custom_results[col] = custom_results[col].replace(['NO INFO', 'Not Found', 'nan', 'None'], '')
                        
                        # Remove specified columns if they exist
                        if 'engagement_context' in custom_results.columns:
                            custom_results = custom_results.drop(columns=['engagement_context'])
                        if 'verification' in custom_results.columns:
                            custom_results = custom_results.drop(columns=['verification'])
                        
                        print("\nCustom query results (after cleaning):")
                        print(custom_results)
                        
                        # Save custom results to CSV
                        custom_csv = "custom_query_results.csv"
                        custom_results.to_csv(custom_csv, index=False)
                        print(f"\nCustom results saved to {custom_csv}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        connection.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
