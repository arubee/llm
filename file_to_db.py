

import pandas as pd
import sqlite3
import os
import argparse
from enum import Enum
from typing import Union

DB_PATH = "companydata/companydata.db"

def csv_to_sqlite(csv_path, table_name, chunksize=50000):
    """
    Reads a large CSV file in chunks and loads it into a SQLite database table.

    Args:
        csv_path (str): The path to the input CSV file.
        table_name (str): The name of the table to create/replace.
        chunksize (int): The number of rows to read per chunk.
    """
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return False

    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    
    print(f"Reading CSV from {csv_path} in chunks...")
    try:
        chunk_iter = pd.read_csv(csv_path, chunksize=chunksize, low_memory=False, on_bad_lines='warn')

        first_chunk = True
        for i, chunk in enumerate(chunk_iter):
            print(f"Processing chunk {i+1}...")
            if_exists_param = 'replace' if first_chunk else 'append'
            
            # Clean column names to be valid SQL identifiers
            clean_columns = {}
            for col in chunk.columns:
                clean_col = ''.join(e for e in col if e.isalnum() or e == '_')
                clean_columns[col] = clean_col
            chunk.rename(columns=clean_columns, inplace=True)
            
            chunk.to_sql(table_name, conn, if_exists=if_exists_param, index=False)
            first_chunk = False
        
        print(f"\nSuccessfully loaded data into '{table_name}' table in {DB_PATH}")

    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        print("Closing database connection.")
        conn.close()
    return True


def query_companies_table(sql: str, return_json: bool = True) -> Union[pd.DataFrame, str]:
    """
    Execute a SQL query against the companies database and return results as JSON or DataFrame.
    
    This function provides a safe way to execute read-only queries against the companies table.
    It includes basic SQL injection protection by only allowing SELECT queries.
    
    Args:
        sql (str): The SQL SELECT query to execute. Should be a read-only query.
        return_json (bool, optional): If True, returns results as JSON string. If False, returns DataFrame.
                                    Defaults to True.
        
    Returns:
        Union[str, pd.DataFrame]: Query results as JSON string if return_json is True, 
                                otherwise as pandas DataFrame. Returns empty JSON object or 
                                DataFrame on error.
        
    Raises:
        ValueError: If the query is not a SELECT statement.
        sqlite3.Error: For database-related errors.
    """
    # Basic SQL injection protection - only allow SELECT queries
    if not sql.strip().upper().startswith('SELECT'):
        raise ValueError("Only SELECT queries are allowed for security reasons.")
    
    # Add default LIMIT 10 if not specified
    sql_upper = sql.upper()
    if 'LIMIT' not in sql_upper and ';' not in sql_upper:
        sql = f"{sql.rstrip()} LIMIT 10"
    
    print(f"Connecting to database at {DB_PATH}...")
    conn = None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Set a timeout for the database connection
        conn.execute('PRAGMA busy_timeout = 30000')  # 30 seconds
        
        # Execute the query and return results
        df = pd.read_sql_query(sql, conn)
        
        # Convert to JSON if requested
        if return_json:
            # Convert DataFrame to JSON records (list of dicts)
            return df.to_json(orient='records', date_format='iso')
        return df
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Unexpected error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            try:
                conn.close()
                print("Database connection closed.")
            except Exception as e:
                print(f"Error closing connection: {e}")


def create_indexes(db_path=None):
    """
    Creates indexes on the companies table to improve query performance.
    
    Args:
        db_path (str, optional): Path to the SQLite database. Uses DB_PATH if not provided.
    """
    db_to_use = db_path if db_path else DB_PATH
    print(f"Connecting to database at {db_to_use} to create indexes...")
    conn = sqlite3.connect(db_to_use)
    cursor = conn.cursor()

    indexes_to_create = {
        'idx_company_status': 'CREATE INDEX IF NOT EXISTS idx_company_status ON companies (CompanyStatus);',
        'idx_accounts_category': 'CREATE INDEX IF NOT EXISTS idx_accounts_category ON companies (AccountsAccountCategory);',
        'idx_reg_address_county': 'CREATE INDEX IF NOT EXISTS idx_reg_address_county ON companies (UPPER(RegAddressCounty));',
        'idx_accounts_due_date': 'CREATE INDEX IF NOT EXISTS idx_accounts_due_date ON companies (AccountsNextDueDate);',
        'idx_sic_code_1': 'CREATE INDEX IF NOT EXISTS idx_sic_code_1 ON companies (SICCodeSicText_1);',
        'idx_sic_code_2': 'CREATE INDEX IF NOT EXISTS idx_sic_code_2 ON companies (SICCodeSicText_2);',
        'idx_sic_code_3': 'CREATE INDEX IF NOT EXISTS idx_sic_code_3 ON companies (SICCodeSicText_3);',
        'idx_sic_code_4': 'CREATE INDEX IF NOT EXISTS idx_sic_code_4 ON companies (SICCodeSicText_4);'
    }

    try:
        for name, sql in indexes_to_create.items():
            print(f"Creating index {name}...")
            cursor.execute(sql)
        conn.commit()
        print("Indexes created successfully.")

    except Exception as e:
        print(f"An error occurred while creating indexes: {e}")
    finally:
        print("Closing database connection.")
        conn.close()


class SqlQuery(Enum):
    LIST_TABLES = "SELECT name FROM sqlite_master WHERE type='table';"
    ACTIVE_COMPANIES = "SELECT CompanyName, CompanyNumber, CompanyStatus FROM companies WHERE CompanyStatus = 'Active' ORDER BY CompanyName LIMIT 20;"
    LIQUID_COMPANIES = "SELECT CompanyName, CompanyNumber, CompanyStatus FROM companies WHERE CompanyStatus = 'Liquidation' LIMIT 20;"
    MICRO_ENTITY = "SELECT CompanyName, CompanyNumber, AccountsAccountCategory FROM companies WHERE AccountsAccountCategory = 'MICRO ENTITY' LIMIT 20;"
    SCHEMA = "PRAGMA table_info(companies);"
    COMPANY_CAT = "SELECT DISTINCT CompanyCategory FROM companies;"
    ACCOUNTS_CAT = "SELECT DISTINCT AccountsAccountCategory FROM companies;"
    COUNTIES = "SELECT DISTINCT RegAddressCounty FROM companies;"
    COMPANIES_IN_SUFFOLK = "SELECT CompanyName, CompanyNumber, RegAddressCounty FROM companies WHERE UPPER(RegAddressCounty) LIKE '%SUFFOLK%' LIMIT 20;"
    ACCOUNTS_DUE_NEXT_MONTH = "SELECT CompanyName, CompanyNumber, AccountsNextDueDate FROM companies WHERE date(AccountsNextDueDate) BETWEEN date('now') AND date('now', '+1 month') ORDER BY AccountsNextDueDate LIMIT 20;"
    PLUMBING_HEAT_AC_COMPANIES = "SELECT CompanyName, CompanyNumber, SICCodeSicText_1 FROM companies WHERE SICCodeSicText_1 LIKE '%43220%' OR SICCodeSicText_2 LIKE '%43220%' OR SICCodeSicText_3 LIKE '%43220%' OR SICCodeSicText_4 LIKE '%43220%' LIMIT 20;"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A tool to import company data to SQLite and query it.')
    parser.add_argument('action', choices=['import', 'query', 'index'], help='The action to perform: import, query, or index.')
    parser.add_argument('--query_name', type=str, choices=[q.name for q in SqlQuery], help='The name of the query to execute.')
    parser.add_argument('--csv_path', type=str, help='Path to the CSV file for import.')
    parser.add_argument('--db_path', type=str, default='companydata/companydata.db', help='Path to the SQLite database file.')

    args = parser.parse_args()

    if args.action == 'import':
        if not args.csv_path:
            print("Error: --csv_path is required for the import action.")
        else:
            TABLE_NAME = 'companies'
            import_success = csv_to_sqlite(args.csv_path, TABLE_NAME)  # Removed db_path as it's a global
            if import_success:
                create_indexes(args.db_path)
    
    elif args.action == 'query':
        if not args.query_name:
            print("Error: Please specify a query to run with --query_name")
            print(f"Available queries: {[q.name for q in SqlQuery]}")
        else:
            sql_to_run = SqlQuery[args.query_name].value
            print(f"Executing query '{args.query_name}': {sql_to_run}")
            results_df = query_companies_table(args.db_path, sql_to_run)
            
            if not results_df.empty:
                print(f"\nQuery returned {len(results_df)} results:")
                print(results_df.to_string())
            else:
                print(f"\nQuery returned no results.")

    elif args.action == 'index':
        print(f"Creating indexes on the database at {args.db_path}...")
        create_indexes(args.db_path)
