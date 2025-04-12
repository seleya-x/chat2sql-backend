#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to set up database connection configuration
"""

import os
import sys
from dotenv import load_dotenv, set_key
import getpass
import pymysql

# Current directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(script_dir, '.env')

def prompt_for_config():
    """Prompt user for database configuration"""
    print("\n===== DATABASE CONFIGURATION SETUP =====")
    print("Please enter your database connection details:")
    
    db_host = input("Database Host (e.g., my-server.database.azure.com): ")
    db_user = input("Database Username: ")
    db_password = getpass.getpass("Database Password: ")
    db_port = input("Database Port [3306]: ") or "3306"
    db_ssl = input("Use SSL connection? [y/N]: ").lower()
    db_ssl = "true" if db_ssl == "y" else "false"
    
    return {
        "DB_HOST": db_host,
        "DB_USER": db_user,
        "DB_PASSWORD": db_password,
        "DB_PORT": db_port,
        "DB_SSL": db_ssl,
        "DB_SSL_VERIFY": "false"  # Default to not verify SSL cert
    }

def update_env_file(config):
    """Update the .env file with new configuration"""
    # Create .env file if it doesn't exist
    if not os.path.exists(env_file):
        open(env_file, 'a').close()
        print(f"Created new .env file at {env_file}")
    
    # Load existing environment
    load_dotenv(env_file)
    
    # Update or add each config value
    for key, value in config.items():
        set_key(env_file, key, value)
    
    print("Environment file updated successfully!")

def test_connection(host, user, password, port, use_ssl):
    """Test the database connection"""
    print("\nTesting database connection...")
    
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=int(port),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={"ssl": True} if use_ssl.lower() == "true" else None,
            ssl_verify_cert=False  # Don't verify server cert for ease of setup
        )
        
        print("✅ Connection successful!")
        
        # Try to list databases to verify permissions
        with connection.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            db_names = [db[list(db.keys())[0]] for db in databases]
            
            print(f"Available databases: {', '.join(db_names)}")
            
            if "pjtdeals" not in db_names:
                print("⚠️ Warning: 'pjtdeals' database not found. The application expects this database.")
                
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def interactive_setup():
    """Interactive setup process"""
    # Check if .env already exists and has database config
    load_dotenv(env_file)
    existing_host = os.getenv("DB_HOST")
    
    if existing_host and existing_host != "your-db-host.database.azure.com":
        print(f"Existing database configuration found: {existing_host}")
        update = input("Update database configuration? [y/N]: ").lower()
        if update != "y":
            print("Keeping existing configuration.")
            return
    
    # Get new configuration
    config = prompt_for_config()
    
    # Update .env file
    update_env_file(config)
    
    # Test connection
    test_result = test_connection(
        config["DB_HOST"], 
        config["DB_USER"], 
        config["DB_PASSWORD"], 
        config["DB_PORT"],
        config["DB_SSL"]
    )
    
    if test_result:
        print("\n==== NEXT STEPS ====")
        print("1. Restart your backend server for changes to take effect")
        print("2. Try executing a query in your application")
    else:
        print("\n==== TROUBLESHOOTING ====")
        print("1. Check your database credentials")
        print("2. Verify the database server is accessible from this machine")
        print("3. Check firewall rules on the database server")

if __name__ == "__main__":
    print("Database Connection Setup Utility")
    interactive_setup()
