from fastapi import FastAPI, Body
from fastapi_mcp import FastApiMCP
import sqlite3

app = FastAPI()
DB_PATH = "demo.db"

def run_query(query, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

# === EXISTENTES Y CORREGIDOS ===

@app.post("/existe_abonado", operation_id="existe_abonado")
async def existe_abonado(dni: str = Body(..., embed=True)):
    result = run_query("SELECT 1 FROM abonados WHERE dni = ?", (dni,))
    return {"existe": bool(result)}

@app.post("/direccion_abonado", operation_id="direccion_abonado")
async def direccion_abonado(dni: str = Body(..., embed=True)):
    result = run_query("SELECT direccion FROM abonados WHERE dni = ?", (dni,))
    return {"direccion": result[0][0] if result else None}

@app.post("/estado_pagos", operation_id="estado_pagos")
async def estado_pagos(dni: str = Body(..., embed=True)):
    result = run_query("SELECT estado FROM facturas WHERE dni_abonado = ?", (dni,))
    return {"estados": [r[0] for r in result]}

@app.post("/ultimo_pago", operation_id="ultimo_pago")
async def ultimo_pago(dni: str = Body(..., embed=True)):
    result = run_query(
        "SELECT fecha, importe FROM facturas WHERE dni_abonado = ? AND estado = 'Pagado' ORDER BY fecha DESC LIMIT 1",
        (dni,)
    )
    return {"ultimo_pago": {"fecha": result[0][0], "importe": result[0][1]} if result else None}

@app.post("/deuda_total", operation_id="deuda_total")
async def deuda_total(dni: str = Body(..., embed=True)):
    result = run_query(
        "SELECT SUM(importe) FROM facturas WHERE dni_abonado = ? AND estado != 'pagado'",
        (dni,)
    )
    return {"deuda": result[0][0] if result[0][0] else 0}

@app.post("/facturas_pendientes", operation_id="facturas_pendientes")
async def facturas_pendientes(dni: str = Body(..., embed=True)):
    result = run_query(
        "SELECT fecha, importe FROM facturas WHERE dni_abonado = ? AND estado != 'pagado'",
        (dni,)
    )
    return {"facturas": [{"fecha": r[0], "importe": r[1]} for r in result]}

# === NUEVAS ===

@app.post("/todas_las_facturas", operation_id="todas_las_facturas")
async def todas_las_facturas(dni: str = Body(..., embed=True)):
    result = run_query(
        "SELECT fecha, estado, importe FROM facturas WHERE dni_abonado = ? ORDER BY fecha DESC",
        (dni,)
    )
    return {"facturas": [{"fecha": r[0], "estado": r[1], "importe": r[2]} for r in result]}

@app.post("/datos_abonado", operation_id="datos_abonado")
async def datos_abonado(dni: str = Body(None), poliza: str = Body(None)):
    if not dni and not poliza:
        return {"error": "Debe proporcionar un DNI o una póliza"}

    if dni:
        result = run_query(
            "SELECT nombre, dni, direccion, email, telefono, poliza FROM abonados WHERE dni = ?",
            (dni,)
        ) 
    else:
        result = run_query(
            "SELECT nombre, dni, direccion, email, telefono, poliza FROM abonados WHERE poliza = ?",
            (poliza,)
        )

    if result:
        nombre, dni, direccion, correo, telefono, poliza = result[0]
        return {
            "nombre": nombre,
            "dni": dni,
            "direccion": direccion,
            "correo": correo,
            "telefono": telefono,
            "poliza": poliza
        }
    else:
        return {"error": "Abonado no encontrado"}

# Montar FastAPI-MCP
mcp = FastApiMCP(app)
mcp.mount()
