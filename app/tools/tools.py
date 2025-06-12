import httpx
import jsonref
from config import OPENAPI_URL
from app.utils.utils import clean_schema

def fetch_tools():
    r = httpx.get(OPENAPI_URL)
    r.raise_for_status()
    spec = jsonref.JsonRef.replace_refs(r.json())

    tools = []
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if "operationId" not in op:
                continue
            schema = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
            tools.append({
                "name": op["operationId"],
                "description": op.get("description", f"Herramienta para {op['operationId']}"),
                "input_schema": clean_schema(schema),
                "endpoint": path
            })
    return tools
