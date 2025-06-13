import re
import json

def extract_dni(texto):
    match = re.search(r"\b\d{8}[A-Z]\b", texto, re.IGNORECASE)
    return match.group(0) if match else None

def clean_schema(schema):
    try:
        return json.loads(json.dumps(schema))
    except TypeError:
        if isinstance(schema, dict):
            return {k: clean_schema(v) for k, v in schema.items()}
        elif isinstance(schema, list):
            return [clean_schema(i) for i in schema]
        else:
            return str(schema)

def extract_nombre(texto):
    match = re.search(r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b", texto)
    return match.group(0) if match else None
