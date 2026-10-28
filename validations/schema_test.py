
"""Check a request shape without a server (run from the project folder):  uv run python backend/try_schemas.py"""
from pydantic import ValidationError

from backend.api.schema import QueryRequest

ok = QueryRequest(query="What are the payment terms?")  (1)
print("valid  :", ok)
print("as dict:", ok.model_dump())  (2)

try:
    QueryRequest(retriever_type="similarity")  (3)
except ValidationError as err:
    first = err.errors()[0]  (4)
    print("invalid:", first["type"], first["loc"], "-", first["msg"])


    #---------------------------------------------------------------------------
# Root Folder: ProcurePilotAI

# How to run the file
# cmd.exe:
    # set PYTHONPATH=backend
    # uv run python -m validations.schema_test

#Or on one line: 
    # set "PYTHONPATH=backend" && uv run python -m validations.schema_test

#PowerShell:
    #$env:PYTHONPATH = "backend"; uv run python -m validations.agent_test

#---------------------------------------------------------------------------