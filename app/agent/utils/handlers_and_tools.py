import httpx
import jsonref
from app.config.config import OPENAPI_URL, API_BASE_URL
from app.utils.utils import clean_schema


def fetch_tools():
    """
    Descarga la especificación OpenAPI, expande referencias y construye la lista de herramientas
    en formato compatible con Groq (JSON schema).
    Cada herramienta incluye el endpoint y método HTTP para invocarla.
    """
    r = httpx.get(OPENAPI_URL)
    r.raise_for_status()
    spec = jsonref.JsonRef.replace_refs(r.json())
    print("Spec structure:", spec)  # Debug statement to print the structure of the spec object
    print("Raw JSON response:", r.json())  # Debug statement to print the raw JSON response
    print("Spec type:", type(spec))  # Debug statement to check the type of spec
    print("Spec content:", spec)  # Debug statement to inspect the content of spec

    tools = []
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            operation_id = op.get("operationId")
            if not operation_id:
                continue
            schema = (
                op.get("requestBody", {})
                  .get("content", {})
                  .get("application/json", {})
                  .get("schema", {})
            )
            parameters = clean_schema(schema)
            description = op.get("description")
            if not description:
                description = f"Esta herramienta realiza la operación '{operation_id}' en el endpoint '{path}' usando el método '{method.upper()}.'"
            tools.append({
                "type": "function",
                "function": {
                    "name": operation_id,
                    "description": description,
                    "parameters": parameters
                },
                "endpoint": path,
                "method": method.upper()
            })
    return tools


def call_api(endpoint: str, method: str, payload: dict):
    """
    Invoca el endpoint HTTP definido en la herramienta con el payload dado.
    """
    url = API_BASE_URL.rstrip('/') + endpoint
    response = httpx.request(method, url, json=payload)
    response.raise_for_status()
    return response.json()


def generate_handlers(tools: list):
    """
    Crea un diccionario {nombre_herramienta: función_python} que envuelve a call_api.
    """
    handlers = {}
    for tool in tools:
        name = tool["function"]["name"]
        endpoint = tool["endpoint"]
        method = tool["method"]
        def make_handler(ep, mtd):
            def handler(**kwargs):
                return call_api(ep, mtd, kwargs)
            return handler
        handlers[name] = make_handler(endpoint, method)
    return handlers