"""
Fórmula de costo y catálogo de salas para UCTP.

Centraliza:
- la fórmula `1.0 + desperdicio_capacidad + penal_horario_extremo`
- las salas disponibles (id -> {nombre, capacidad})
- el calendario semanal hardcoded

El parser usa SALAS para construir R/Cap/Salas en el dict de salida,
y pasa la restricción por curso a calcular_costos() para no enumerar
combinaciones imposibles en el modelo.
"""

DIAS = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie']
HORAS = ['8:15-9:35', '9:50-11:10', '11:25-12:45',
         '13:45-15:05', '15:20-16:40', '16:55-18:15']
SLOTS_POR_DIA = len(HORAS)
DIAS_HABILES = 5
TOTAL_BLOQUES = DIAS_HABILES * SLOTS_POR_DIA

# Penalización adicional cuando el bloque cae en un horario "extremo".
HORAS_PENALIZADAS = {'8:15-9:35', '16:55-18:15'}
PENAL_HORARIO = 0.5

COSTO_BASE = 1.0
DESPERDICIO_INFACTIBLE = 50.0


# Salas basadas en la infraestructura real de la USACH (DIINF + Edificio ED).
# Fuentes:
# - DIINF: 2 laboratorios de computacion (10 puestos c/u), 1 Lab TIC (20 puestos)
# - Edificio Innovacion Docente (ED): salas de 30, 60 y 100 estudiantes
# - EAO: salas genericas del complejo informatico
#
# Para agregar/quitar/editar una sala, modifique este dict.
SALAS = {
    1: {'nombre': 'INF-Lab1',  'capacidad': 10},   # Lab computacion DIINF
    2: {'nombre': 'INF-Lab2',  'capacidad': 10},   # Lab computacion DIINF
    3: {'nombre': 'INF-TIC',   'capacidad': 20},   # Lab TIC DIINF
    4: {'nombre': 'EAO-101',   'capacidad': 30},   # Sala EAO
    5: {'nombre': 'EAO-102',   'capacidad': 25},   # Sala EAO
    6: {'nombre': 'ED-301',    'capacidad': 30},   # Sala ED piso 3
    7: {'nombre': 'ED-302',    'capacidad': 30},   # Sala ED piso 3
    8: {'nombre': 'ED-401',    'capacidad': 60},   # Sala ED piso 4
    9: {'nombre': 'ED-501',    'capacidad': 60},   # Sala ED piso 5
    10: {'nombre': 'ED-601',   'capacidad': 100},  # Auditorio ED piso 6
}


def construir_datos_salas():
    """Devuelve (R, Cap, Salas) ordenados a partir de SALAS."""
    R = sorted(SALAS.keys())
    Cap = {r: SALAS[r]['capacidad'] for r in R}
    Salas = {r: SALAS[r]['nombre'] for r in R}
    return R, Cap, Salas


def horario_de_bloque(t):
    """Devuelve la etiqueta horaria del bloque t (1-indexed)."""
    idx = (t - 1) % SLOTS_POR_DIA
    return HORAS[idx]


def formula_costo(alumnos, capacidad, t):
    """Costo según la fórmula original:
        costo_base + desperdicio_capacidad + penal_horario_extremo
    """
    if capacidad >= alumnos:
        desperdicio = (capacidad - alumnos) / capacidad
    else:
        desperdicio = DESPERDICIO_INFACTIBLE

    penal = PENAL_HORARIO if horario_de_bloque(t) in HORAS_PENALIZADAS else 0.0
    return COSTO_BASE + desperdicio + penal


def calcular_costos(datos):
    """Rellena datos['Costo'] para todas las combinaciones factibles.

    Filtros aplicados:
    - capacidad de la sala >= alumnos del curso
    - sala en datos['Salas_disponibles'][c] si existe; si no, todas las salas.

    Sobrescribe datos['Costo']. Requiere que datos tenga al menos:
    C, T, R, Cap, Alum, y opcionalmente Salas_disponibles.
    """
    costo = {}
    salas_por_curso = datos.get('Salas_disponibles', {})
    for c in datos['C']:
        salas_de_este_curso = salas_por_curso.get(c, set(datos['R']))
        for t in datos['T']:
            for r in datos['R']:
                if r not in salas_de_este_curso:
                    continue
                if datos['Alum'][c] <= datos['Cap'][r]:
                    costo[(c, t, r)] = formula_costo(
                        datos['Alum'][c], datos['Cap'][r], t
                    )
    datos['Costo'] = costo
    return costo


if __name__ == "__main__":
    from instancias.parser import cargar
    datos = cargar('instancias/ejemplo.csv')
    print(f"Costo calculado: {len(datos['Costo'])} entradas")
    for k, v in list(datos['Costo'].items())[:8]:
        print(f"  {k}: {v:.4f}")
