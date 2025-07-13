# Requirements:
Specifically, I’m looking for a proof of concept that demonstrates the ability for a LLM to interrogate a data-set through MCP. The data-set I’d like to work with is Companies House. 

In terms of outcomes, I’d like to look at:
- Download and store the Companies House data locally - https://download.companieshouse.gov.uk/en_output.html << can be one of the part files, not all of them).
- Use an LLM / Vibe Coding tool to review the Companies House data and extract a schema so the data can be stored locally in sqlite; use the Vibe Coding tool to accelerate development to create relevant tables from the schema and insert the data from the CSV files.Create an MCP server running locally (a simple Python server running in a command-line is suitable), with simple tests being executed from tools like Postman to demonstrate functionality calling and consuming endpoints; see https://modelcontextprotocol.io/introduction for more information about MCP.Update the MCP server to allow tooling* to connect and execute queries via the tools endpoint - example queries that I would like to see are below; lets let Arun explore what is possible. Calls into the tools endpoints would need to translate into SQL queries into sqlite. 
- tooling would ideally be an LLM (such as Anthropic Claude) that can query a public MCP server, however this would require the MCP server to be on the public internet, with its additional associated headaches. I therefore propose that we leverage a pseudo LLM (i.e. Postman) to demonstrate how an LLM would query the MCP server by calling the tools endpoint. Arun might even go so far as querying an LLM to determine what JSON payload it would pass given the MCP request/response schema for example and then issuing that JSON payload from Postman.

Fundamentally, I’m looking to issue some simple natural language queries to interrogate the CH data:
1. Find me all companies that are Micro Entities.
2. Find me all companies that are Micro Entities and that are in Liquidation. 
3. Find me all companies that are based in Suffolk.
4. Find me all companies where their accounts are due within the next month.
5. Find me all companies that are involved in Plumbing, heat and air-conditioning installation (SIC Code 43220)
I’m happy for Arun to use Vibe coding tools as needed to achieve this outcome.