import pymysql
import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_mysql():
    """
    Establish a connection to the Azure MySQL database
    """
    # Database connection parameters from environment variables
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port = int(os.getenv("DB_PORT", 3306))  # Default MySQL port if not specified
    
    # Create connection with SSL enabled
    try:
        # Get SSL configuration from environment variables
        use_ssl = os.getenv("DB_SSL", "true").lower() == "true"
        verify_ssl = os.getenv("DB_SSL_VERIFY", "false").lower() == "true"
        
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            ssl={"ssl": use_ssl} if use_ssl else None,  # Enable SSL based on env var
            ssl_verify_cert=verify_ssl  # Verify server's certificate based on env var
        )
        print("Connection to MySQL database successful!")
        return connection
    except Exception as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def execute_query(query, database=None):
    """
    Execute a SQL query and return the results as a pandas DataFrame
    
    Args:
        query (str): SQL query to execute
        database (str, optional): Database name to use. If None, uses the current database.
        
    Returns:
        pandas.DataFrame: Query results as a DataFrame
    """
    connection = connect_to_mysql()
    if not connection:
        return None
    
    try:
        if database:
            connection.select_db(database)
        
        # Execute the query and fetch results
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
        # Convert results to DataFrame
        df = pd.DataFrame(results)
        return df
    
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        connection.close()

def get_sqlalchemy_engine(database=None):
    """
    Create and return a SQLAlchemy engine for more complex pandas operations
    
    Args:
        database (str, optional): Database name to use
        
    Returns:
        sqlalchemy.engine.Engine: SQLAlchemy engine
    """
    # Database connection parameters from environment variables
    host = os.getenv("DB_HOST")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    port = int(os.getenv("DB_PORT", 3306))
    
    # Create connection string with URL encoding for special characters in password
    from urllib.parse import quote_plus
    encoded_password = quote_plus(password)
    conn_str = f"mysql+pymysql://{user}:{encoded_password}@{host}:{port}"
    if database:
        conn_str += f"/{database}"
    
    try:
        # Get SSL configuration from environment variables
        use_ssl = os.getenv("DB_SSL", "true").lower() == "true"
        verify_ssl = os.getenv("DB_SSL_VERIFY", "false").lower() == "true"
        
        # Add SSL configuration for secure connection based on environment variables
        connect_args = {}
        if use_ssl:
            connect_args["ssl"] = {"ssl": True}
            connect_args["ssl_verify_cert"] = verify_ssl
        engine = create_engine(conn_str, connect_args=connect_args)
        return engine
    except Exception as e:
        print(f"Error creating SQLAlchemy engine: {e}")
        return None

def list_databases():
    """
    List all available databases in the MySQL server
    
    Returns:
        pandas.DataFrame: DataFrame containing database names
    """
    query = "SHOW DATABASES"
    return execute_query(query)

def list_tables(database):
    """
    List all tables in the specified database
    
    Args:
        database (str): Database name
        
    Returns:
        pandas.DataFrame: DataFrame containing table names
    """
    connection = connect_to_mysql()
    if not connection:
        return None
    
    try:
        connection.select_db(database)
        query = "SHOW TABLES"
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
        
        # Convert results to DataFrame
        df = pd.DataFrame(results)
        return df
    
    except Exception as e:
        print(f"Error listing tables: {e}")
        return None
    finally:
        connection.close()

def read_sql_query_with_pandas(query, database):
    """
    Execute a SQL query using pandas read_sql_query function
    
    Args:
        query (str): SQL query to execute
        database (str): Database name
        
    Returns:
        pandas.DataFrame: Query results as a DataFrame
    """
    # Try to connect directly with pymysql first for better error handling
    connection = connect_to_mysql()
    if not connection:
        print("Failed to connect to MySQL database")
        return None
    
    try:
        # Select the database
        connection.select_db(database)
        print(f"Connected to database: {database}")
        
        # Try executing the query directly with pymysql
        with connection.cursor() as cursor:
            print("Executing query with pymysql...")
            cursor.execute(query)
            results = cursor.fetchall()
            print(f"Query executed successfully, fetched {len(results)} rows")
            
            # Convert results to DataFrame
            df = pd.DataFrame(results)
            return df
    except Exception as e:
        print(f"Error executing query with pymysql: {e}")
        print("Trying with SQLAlchemy as fallback...")
        
        # Try with SQLAlchemy as fallback
        try:
            engine = get_sqlalchemy_engine(database)
            if not engine:
                print("Failed to create SQLAlchemy engine")
                return None
                
            df = pd.read_sql_query(query, engine)
            return df
        except Exception as e:
            print(f"Error executing query with SQLAlchemy: {e}")
            return None
    finally:
        connection.close()

# Example usage
if __name__ == "__main__":
    # List all databases
    print("Available databases:")
    dbs = list_databases()
    if dbs is not None:
        print(dbs)
    
    # Example: Choose a database and list its tables
    # Replace 'your_database_name' with an actual database name
    database_name = input("Enter database name to explore: ")
    if database_name:
        print(f"Tables in {database_name}:")
        tables = list_tables(database_name)
        if tables is not None:
            print(tables)
        
        # Example: Run a query
        query = input("Enter SQL query (or press Enter to skip): ")
        if query:
            print("Query results:")
            results = read_sql_query_with_pandas(query, database_name)
            if results is not None:
                print(results.head())
                print(f"Total rows: {len(results)}")
