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

def format_tool_response(tool_name: str, data: dict) -> str:
    if tool_name == "datos_abonado":
        return format_datos_abonado(data)
    elif tool_name == "todas_las_facturas":
        return format_facturas(data)
    # Por defecto, mostrar JSON
    import json
    return f"Respuesta de la herramienta {tool_name}:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
