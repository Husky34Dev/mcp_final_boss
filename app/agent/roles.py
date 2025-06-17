# app/agent/roles.py

ROLES_TOOLS = {
    # Acceso total a todas las herramientas
    "admin": [
        "datos_abonado", "facturas_pendientes", "todas_las_facturas", "deuda_total",
        "crear_incidencia", "incidencias_por_dni", "incidencias_por_ubicacion",
        "direccion_abonado", "estado_pagos", "ultimo_pago"
    ],
    # Solo facturación y consulta de abonado
    "facturacion": [
        "facturas_pendientes", "todas_las_facturas", "deuda_total", "datos_abonado"
    ],
    # Solo incidencias
    "incidencias": [
        "crear_incidencia", "incidencias_por_dni", "incidencias_por_ubicacion"
    ],
    # Soporte: datos básicos de abonado y estado de pagos
    "soporte": [
        "datos_abonado", "direccion_abonado", "estado_pagos", "ultimo_pago"
    ],
}
