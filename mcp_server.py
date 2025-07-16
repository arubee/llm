from mcp.server.fastmcp import FastMCP
import uvicorn
from fastapi import FastAPI, HTTPException, Header
import json
from anthropic import Anthropic
from datetime import datetime
import os
from file_to_db import query_companies_table, SqlQuery

MODEL = "claude-3-5-sonnet-20240620"
# Read API key from environment variable
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set.")

anthropic = Anthropic(api_key=anthropic_api_key)

# Create instances
mcp = FastMCP("companies")
app = FastAPI()
app.router.redirect_slashes = False

@app.get("/api/companies/search", response_model=dict)
async def search_companies_with_llm(
    query: str,
    limit: int = 5,  # Default limit set to 5
    api_key: str = Header(None, alias="X-API-Key")
):
    """Receives a natural language query and uses an LLM to generate and run SQL.
    
    Args:
        query: The natural language query to search for companies
        limit: Maximum number of results to return (default: 5)
        api_key: API key for authentication
    """
    print(f"Received search request with query: {query}")
    
    try:
        # Verify API key
        if api_key != anthropic_api_key:
            print("Invalid API key provided")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )

        # Add the limit to the query if not already specified
        if 'limit' not in query.lower() and 'top ' not in query.lower():
            query = f"{query} (limit to {limit} results)"
            
        # Call the new text-to-sql tool
        data = {"natural_language_query": query}
        print(f"Calling generate_and_run_sql_query with: {data}")
        
        result = await mcp.call_tool("generate_and_run_sql_query", data)
        print(f"Query result: {result}")
        
        if not result or (isinstance(result, dict) and not result.get('result')):
            print("No results found for the query")
            return {"result": [], "status": "success", "message": "No results found"}
            
        return {"result": result, "status": "success"}
        
    except Exception as e:
        print(f"Error in search_companies_with_llm: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

def get_db_schema_for_prompt():
    """Fetches the database schema and formats it for an LLM prompt."""
    try:
        schema_df = query_companies_table(sql=SqlQuery.SCHEMA.value)
        if not schema_df.empty:
            # Format the schema into a simple string for the prompt
            return "\n".join([f"- {row['name']} ({row['type']})" for _, row in schema_df.iterrows()])
        return "Could not retrieve schema."
    except Exception as e:
        print(f"Error fetching schema: {e}")
        return "Error fetching schema."


@mcp.tool()
async def generate_and_run_sql_query(natural_language_query: str):
    """
    Takes a natural language query, converts it to SQL using an LLM,
    executes the SQL against the company database, and returns the result.
    """
    print(f"\n=== Processing query: {natural_language_query} ===")
    
    try:
        schema_info = get_db_schema_for_prompt()
        print("Fetched database schema")

        system_prompt = f"""
        You are an expert SQL writer. Your task is to convert a user's natural language question into a valid SQLite query.
        You must only respond with the SQL query and nothing else. Do not add any explanation or markdown formatting.
        
        Important: Always include these key columns in your SELECT statements:
        - CompanyName
        - CompanyNumber
        - CompanyStatus
        - CompanyCategory
        - RegAddressPostCode
        - RegAddressCounty
        - RegAddressPostTown
        - AccountsAccountCategory
        - AccountsNextDueDate

        if SICCode is queried or job , also return the following columns:
        - SICCodeSicText_1
        - SICCodeSicText_2
        - SICCodeSicText_3
        - SICCodeSicText_4

        The database table is named 'companies' and has the following columns:
        {schema_info}

        Here are some examples of valid values in the database:
        - CompanyStatus can be 'Active', 'Liquidation', 'Voluntary', 'Dissolved', 'Admin', etc.
        - AccountsAccountCategory can be 'MICRO ENTITY', 'SMALL', 'DORMANT', etc.
        - CompanyCategory common values: 'Private Limited Company', 'Private Limited by Shares', 'Private Unlimited Company', 'Public Limited Company', 'Limited Liability Partnership', 'Charitable Company', 'Investment Company'
        - For location-based queries, search in these fields:
            - RegAddressCounty
            - RegAddressPostTown
            - RegAddressAddressLine1
            - RegAddressAddressLine2
        - Example for Suffolk: 
          WHERE UPPER(RegAddressCounty) LIKE '%SUFFOLK%' 
             OR UPPER(RegAddressPostTown) LIKE '%SUFFOLK%'
             OR UPPER(RegAddressAddressLine1) LIKE '%SUFFOLK%'
             OR UPPER(RegAddressAddressLine2) LIKE '%SUFFOLK%'
        - For queries involving strings, use UPPER() and LIKE '%...%' for case-insensitive matching.
        - For queries involving dates, use SQLite date functions for date comparisons.
        - AccountsNextDueDate is stored as text in 'YYYY-MM-DD' format.
        - Always handle NULL values with: AccountsNextDueDate IS NOT NULL AND AccountsNextDueDate != ''
        - To find records within a date range, use: 
          date(trim(AccountsNextDueDate)) BETWEEN date('now') AND date('now', '+1 month')
        - Example: 
          SELECT * FROM companies 
          WHERE AccountsNextDueDate IS NOT NULL 
            AND AccountsNextDueDate != ''
            AND date(trim(AccountsNextDueDate)) BETWEEN date('now') AND date('now', '+1 month')

        When searching for company types:
        1. For private limited companies, use: UPPER(CompanyCategory) LIKE '%PRIVATE%' 
        2. For public limited companies, use: UPPER(CompanyCategory) LIKE '%PUBLIC%' OR UPPER(CompanyCategory) = 'PLC' OR UPPER(CompanyCategory) = 'PUBLIC LIMITED COMPANY'
        3. For specific categories, match the full category name exactly (e.g., 'Public Limited Company')
        4. Always include the exact filter in the WHERE clause that matches the requested company type
        
        For date-based queries:
        - Use SQLite date functions for date comparisons
        - AccountsNextDueDate is stored as text in 'YYYY-MM-DD' format
        - To find records within a date range, use: date(column_name) BETWEEN date('now') AND date('now', '+1 month')
        - Example: SELECT * FROM companies WHERE date(AccountsNextDueDate) BETWEEN date('now') AND date('now', '+1 month')
        
        Only use SIC codes if the query specifically asks about business activities or industries.
        
        Always include ORDER BY and LIMIT clauses to ensure the query returns a manageable number of results.
        Default to LIMIT 20 if no specific limit is mentioned in the query.

        Based on this schema, convert the following user question into a SQLite query.
        """

        print("Sending request to Anthropic API...")
        response = anthropic.messages.create(
            model=MODEL,
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": natural_language_query}
            ]
        )
        
        # Extract the generated SQL query
        generated_sql = response.content[0].text.strip()
        print(f"\n=== Generated SQL ===\n{generated_sql}\n")
        
        # Basic validation of the generated SQL
        if not generated_sql.upper().startswith('SELECT'):
            error_msg = f"Generated query is not a SELECT statement: {generated_sql}"
            print(f"Error: {error_msg}")
            return {"error": error_msg}

        print("Executing SQL query...")
        print(f"SQL Query: {generated_sql}")
        
        # Debug: Check date range in the database
        debug_query = """
        SELECT 
            MIN(date(AccountsNextDueDate)) as min_date,
            MAX(date(AccountsNextDueDate)) as max_date,
            COUNT(*) as total_companies,
            COUNT(AccountsNextDueDate) as companies_with_due_date
        FROM companies
        WHERE AccountsNextDueDate IS NOT NULL 
          AND AccountsNextDueDate != ''
        """
        print("\n=== Running debug query ===")
        debug_df = query_companies_table(sql=debug_query, return_json=False)
        print(f"Date range in database: {debug_df.to_dict('records')}")
        
        result_df = query_companies_table(sql=generated_sql, return_json=False)
        print(f"\nMain query returned {len(result_df)} rows")
        
        if not result_df.empty:
            result = result_df.to_dict('records')
            print(f"First result: {result[0] if result else 'No results'}")
            return result
        else:
            print("No results found")
            return [{"message": "No results found for your query."}]
            
    except Exception as e:
        error_msg = f"Error in generate_and_run_sql_query: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()