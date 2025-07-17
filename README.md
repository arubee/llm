# intro to mcp
[Refer to url](https://modelcontextprotocol.io/introduction)

# mcp documentation
[Refer to url](https://pypi.org/project/mcp/)

# python sdk for mcp
[Refer to url](https://github.com/modelcontextprotocol/python-sdk)


# uv for package manager
[Refer to url](https://docs.astral.sh/uv/)
```
uv init # create a new project
uv venv # create a virtual environment
source .venv/bin/activate # activate the virtual environment
deactivate # deactivate the virtual environment
```
# install libraries with uv
```
uv add <library_name>
uv remove <library_name>
uv update <library_name>
uv pip list # list installed libraries
```

#running download_file.py
```
python download_file.py <url>
```

#running file_to_db.py
```
python file_to_db.py import --csv_path <csv_path>
```

#running mcp_server.py with uvicorn
```
uvicorn mcp_server:app --reload
```
#Postman as client

1. Open visual studio code (command + space and type "Visual Studio Code")
2. In visual studio code, type command + shift + p and type postman
3. select Create new http request
4. copy the local host address with endpoint as below: http://127.0.0.1:8000/api/companies/search
5. Go to Params tab in postman. Add the below:
    - key: query
    - value: SELECT * FROM companies WHERE CompanyStatus = 'Active' LIMIT 20;
    Other queries for the values are:
    Find me all companies that are Micro Entities.
    Find me all companies that are Micro Entities and that are in Liquidation. 
    Find me all companies that are based in Suffolk.
    Find me all companies where their accounts are due within the next month.
    Find me all companies that are involved in Plumbing, heat and air-conditioning installation (SIC Code 43220)

6. Add Header:
    - key: accept
    - value: application/json
    -X-API-Key: <your_api_key> ## api key is in the environment variable ANTHROPIC_API_KEY. You can get it from the terminal by typing echo $ANTHROPIC_API_KEY
    


