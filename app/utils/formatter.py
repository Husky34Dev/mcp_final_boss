def format_datos_abonado(data: dict) -> str:
    return (
        "### Datos del abonado\n"
        f"- **Nombre:** {data.get('nombre', '-') }\n"
        f"- **DNI:** {data.get('dni', '-') }\n"
        f"- **Dirección:** {data.get('direccion', '-') }\n"
        f"- **Correo electrónico:** {data.get('correo', '-') }\n"
        f"- **Teléfono:** {data.get('telefono', '-') }\n"
        f"- **Póliza:** {data.get('poliza', '-') }"
    )

def format_facturas(data: dict) -> str:
    facturas = data.get('facturas', [])
    if not facturas:
        return "No se encontraron facturas para este abonado."
    if len(facturas) == 1:
        f = facturas[0]
        return (
            "### Factura\n"
            f"- **Fecha:** {f.get('fecha', '-')}\n"
            f"- **Estado:** {f.get('estado', '-')}\n"
            f"- **Importe:** {f.get('importe', 0):.2f} €"
        )
    # Si hay varias facturas, tabla y total pendiente
    total_pendiente = sum(f.get('importe', 0) for f in facturas if f.get('estado', '').lower() == 'pendiente')
    tabla = (
        "### Facturas\n"
        "| Fecha | Estado | Importe |\n"
        "|:------|:--------|--------:|\n"
    )
    for f in facturas:
        tabla += f"| {f.get('fecha','-')} | {f.get('estado','-')} | {f.get('importe',0):.2f} € |\n"
    tabla += f"\n**Total pendiente:** {total_pendiente:.2f} €"
    return tabla

def format_incidencias(data: dict) -> str:
    incidencias = data.get("incidencias", [])
    if not incidencias:
        return "### Incidencias\nNo se encontraron incidencias."
        
    # Contadores de estado
    estados = {"Abierto": 0, "En Proceso": 0, "Resuelto": 0}
    for inc in incidencias:
        estado = inc.get('estado', 'Desconocido')
        if estado in estados:
            estados[estado] += 1
            
    # Resumen
    resumen = (
        "### Incidencias\n"
        f"**Resumen:**\n"
        f"- Total: {len(incidencias)} incidencia(s)\n"
        f"- Abiertas: {estados['Abierto']}\n"
        f"- En proceso: {estados['En Proceso']}\n"
        f"- Resueltas: {estados['Resuelto']}\n\n"
        "#### Detalles\n"
        "| Ubicación | Descripción | Estado |\n"
        "|:----------|:------------|:-------|\n"
    )
    
    # Ordenar incidencias: primero abiertas, luego en proceso, finalmente resueltas
    orden_estados = {"Abierto": 0, "En Proceso": 1, "Resuelto": 2}
    incidencias_ordenadas = sorted(
        incidencias,
        key=lambda x: orden_estados.get(x.get('estado', 'Desconocido'), 99)
    )
    
    for inc in incidencias_ordenadas:
        tabla = f"| {inc.get('ubicacion', '-')} | {inc.get('descripcion', '-')} | {inc.get('estado', '-')} |\n"
        resumen += tabla
        
    return resumen

def format_incidencias_por_dni(data: dict) -> str:
    dni = data.get("dni", "")  # Si tienes el DNI en la respuesta
    incidencias = data.get("incidencias", [])
    if not incidencias:
        return f"### Incidencias del usuario {dni}\nNo se encontraron incidencias activas."
        
    # Contadores de estado
    estados = {"Abierto": 0, "En Proceso": 0, "Resuelto": 0}
    for inc in incidencias:
        estado = inc.get('estado', 'Desconocido')
        if estado in estados:
            estados[estado] += 1
            
    # Resumen personalizado
    resumen = (
        f"### Incidencias del usuario {dni}\n\n"
        f"**Estado actual de sus incidencias:**\n"
        f"- Total: {len(incidencias)} incidencia(s)\n"
        f"- Abiertas: {estados['Abierto']}\n"
        f"- En proceso: {estados['En Proceso']}\n"
        f"- Resueltas: {estados['Resuelto']}\n\n"
    )
    
    if estados['Abierto'] > 0:
        resumen += "**Tiene incidencias abiertas pendientes de resolución**\n\n"
    
    resumen += (
        "#### Lista detallada de incidencias\n"
        "| Ubicación | Descripción | Estado |\n"
        "|:----------|:------------|:-------|\n"
    )
    
    # Ordenar incidencias: primero abiertas, luego en proceso, finalmente resueltas
    orden_estados = {"Abierto": 0, "En Proceso": 1, "Resuelto": 2}
    incidencias_ordenadas = sorted(
        incidencias,
        key=lambda x: orden_estados.get(x.get('estado', 'Desconocido'), 99)
    )
    
    for inc in incidencias_ordenadas:
        tabla = f"| {inc.get('ubicacion', '-')} | {inc.get('descripcion', '-')} | {inc.get('estado', '-')} |\n"
        resumen += tabla
        
    return resumen

def format_existe_abonado(data: dict) -> str:
    existe = data.get("existe", False)
    return "El abonado existe." if existe else "El abonado no existe."

def format_direccion_abonado(data: dict) -> str:
    direccion = data.get("direccion")
    return f"### Dirección del abonado\n- **Dirección:** {direccion}" if direccion else "No se encontró dirección para el abonado."

def format_estado_pagos(data: dict) -> str:
    estados = data.get("estados", [])
    if not estados:
        return "No se encontraron estados de pago para este abonado."
    return (
        "### Estados de pago\n" +
        "\n".join(f"- {estado}" for estado in estados)
    )

def format_ultimo_pago(data: dict) -> str:
    ultimo_pago = data.get("ultimo_pago")
    if not ultimo_pago:
        return "No se encontró un último pago para este abonado."
    return (
        "### Último pago\n" +
        f"- **Fecha:** {ultimo_pago.get('fecha', '-')}\n" +
        f"- **Importe:** {ultimo_pago.get('importe', 0):.2f} €"
    )

def format_deuda_total(data: dict) -> str:
    deuda = data.get("deuda", 0)
    return f"### Deuda total\n- **Deuda:** {deuda:.2f} €"

def format_crear_incidencia(data: dict) -> str:
    message = data.get("message")
    if message:
        return f"### Resultado de la creación de incidencia\n- **Mensaje:** {message}"
    return "No se pudo crear la incidencia."

def format_herramientas_disponibles(data: dict) -> str:
    herramientas = data.get("herramientas", [])
    if not herramientas:
        return "No se encontraron herramientas disponibles."
    return (
        "### Herramientas disponibles\n" +
        "\n".join(f"- {herramienta}" for herramienta in herramientas)
    )

# Define a dictionary mapping tool names to formatting functions
FORMATTERS = {
    "datos_abonado": format_datos_abonado,
    "todas_las_facturas": format_facturas,
    "facturas_pendientes": format_facturas,
    "incidencias_por_ubicacion": format_incidencias,
    "incidencias_por_dni": format_incidencias_por_dni,  # Nuevo formateador
    "existe_abonado": format_existe_abonado,
    "direccion_abonado": format_direccion_abonado,
    "estado_pagos": format_estado_pagos,
    "ultimo_pago": format_ultimo_pago,
    "deuda_total": format_deuda_total,
    "crear_incidencia": format_crear_incidencia,
    "incidencias": format_incidencias,
    "herramientas_disponibles": format_herramientas_disponibles,
}

def format_tool_response(tool_name: str, data: dict) -> str:
    # Lookup the formatter function in the dictionary
    formatter = FORMATTERS.get(tool_name, None)
    if formatter:
        return formatter(data)

    # Default
    import json
    return f"Respuesta de la herramienta {tool_name}:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
