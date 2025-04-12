#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to test the database connection and query execution
"""

import os
import pandas as pd
from sql_connector import connect_to_mysql, read_sql_query_with_pandas
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test the database connection and print detailed information"""
    print("====== TESTING DATABASE CONNECTION ======")
    
    # Print environment information (without exposing passwords)
    db_host = os.getenv("DB_HOST", "Not set")
    db_user = os.getenv("DB_USER", "Not set")
    db_port = os.getenv("DB_PORT", "Not set")
    db_ssl = os.getenv("DB_SSL", "Not set")
    
    print(f"Host: {db_host}")
    print(f"User: {db_user}")
    print(f"Port: {db_port}")
    print(f"SSL: {db_ssl}")
    
    # Try to connect
    connection = connect_to_mysql()
    if connection:
        print("✅ Database connection SUCCESSFUL")
        connection.close()
        return True
    else:
        print("❌ Database connection FAILED")
        return False

def test_simple_query():
    """Test a very simple query to verify the connection works"""
    print("\n====== TESTING SIMPLE QUERY ======")
    
    database = "pjtdeals"  # Database from run_specific_query.py
    query = "SHOW TABLES"  # Very simple query that should work on any database
    
    print(f"Database: {database}")
    print(f"Query: {query}")
    
    try:
        result = read_sql_query_with_pandas(query, database)
        
        if result is not None and not result.empty:
            print("✅ Simple query SUCCESSFUL")
            print(f"Result (first 5 rows):\n{result.head()}")
            return True
        else:
            print("❌ Simple query FAILED - Empty result")
            return False
    except Exception as e:
        print(f"❌ Simple query FAILED with error: {e}")
        return False

def test_file_query():
    """Test running the query from sql_query.txt"""
    print("\n====== TESTING QUERY FROM FILE ======")
    
    database = "pjtdeals"
    query_file = "sql_query.txt"
    
    # Read query from file
    try:
        with open(query_file, 'r') as f:
            query = f.read().strip()
        
        print(f"Read query from {query_file} ({len(query)} characters)")
        print("Query preview (first 100 chars):", query[:100] + "..." if len(query) > 100 else query)
        
        # Execute the query
        print("\nExecuting query...")
        result = read_sql_query_with_pandas(query, database)
        
        if result is not None and not result.empty:
            print("✅ File query execution SUCCESSFUL")
            print(f"Result shape: {result.shape[0]} rows, {result.shape[1]} columns")
            print(f"Columns: {', '.join(result.columns.tolist())}")
            return True
        else:
            print("❌ File query execution FAILED - Empty result")
            return False
    except Exception as e:
        print(f"❌ File query execution FAILED with error: {e}")
        return False

if __name__ == "__main__":
    print("⚠️ Database Connection Diagnostic Tool ⚠️\n")
    
    # Test database connection
    connection_ok = test_connection()
    
    # Test simple query (only if connection worked)
    if connection_ok:
        simple_query_ok = test_simple_query()
    else:
        print("\n⚠️ Skipping simple query test due to failed connection")
        simple_query_ok = False
    
    # Test file query (only if simple query worked)
    if simple_query_ok:
        file_query_ok = test_file_query()
    else:
        print("\n⚠️ Skipping file query test due to failed simple query")
        file_query_ok = False
    
    # Summary
    print("\n====== SUMMARY ======")
    print(f"Connection: {'✅ PASSED' if connection_ok else '❌ FAILED'}")
    print(f"Simple Query: {'✅ PASSED' if simple_query_ok else '❌ FAILED'}")
    print(f"File Query: {'✅ PASSED' if file_query_ok else '❌ FAILED'}")
    
    if not (connection_ok and simple_query_ok and file_query_ok):
        print("\n⚠️ TROUBLESHOOTING SUGGESTIONS:")
        if not connection_ok:
            print("- Check your database credentials in .env file")
            print("- Verify the database server is running")
            print("- Check network connectivity to the database server")
        elif not simple_query_ok:
            print("- Verify the user has permissions to execute queries")
            print("- Check if the database schema exists")
        elif not file_query_ok:
            print("- Validate the SQL syntax in sql_query.txt")
            print("- Check for encoding issues in the SQL file")
        
    print("\nDiagnostics complete!")
