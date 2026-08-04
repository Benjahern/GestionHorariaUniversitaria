"""
Parser de instancias UCTP desde CSV.

Lee un CSV donde cada fila es un CURSO (no una combinación factible).
Columnas:
    curso, bloques, alumnos, profesor_id, nombre_profesor, salas_disponibles

`sala_disponibles` es opcional (lista de IDs separados por coma, e.g. "1,2").
Si está vacía, el curso puede usar cualquier sala conocida. Las salas en sí
(id, nombre, capacidad) vienen de `instancias.costos.SALAS`.

Devuelve el mismo dict que el modelo espera, con `Costo` ya calculado.

`bloque_a_horario` vive aquí como fuente única — los módulos verificar/print
lo importan desde acá para evitar duplicación (bug histórico del código viejo).
"""

import csv
from pathlib import Path

from instancias.costos import SALAS, calcular_costos, construir_datos_salas

DIAS = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie']
HORAS = ['8:15-9:35', '9:50-11:10', '11:25-12:45',
         '13:45-15:05', '15:20-16:40', '16:55-18:15']
DIAS_HABILES = 5
SLOTS_POR_DIA = len(HORAS)
TOTAL_BLOQUES = DIAS_HABILES * SLOTS_POR_DIA

COLUMNAS_REQUERIDAS = {
    'curso', 'bloques', 'alumnos', 'profesor_id', 'nombre_profesor',
}
COLUMNAS_OPCIONALES = {'salas_disponibles'}


def bloque_a_horario(t):
    """Convierte bloque (1-indexed, rango 1..30) a (día, horario)."""
    if t < 1 or t > TOTAL_BLOQUES:
        raise ValueError(
            f"Bloque {t} fuera de rango 1..{TOTAL_BLOQUES}"
        )
    idx_dia = (t - 1) // SLOTS_POR_DIA
    idx_bloque = (t - 1) % SLOTS_POR_DIA
    return DIAS[idx_dia], HORAS[idx_bloque]


def _parsear_salas_disponibles(texto, salas_validas):
    """Convierte '1,2' en {1, 2}. Vacío/None -> todas las salas."""
    if texto is None or texto.strip() == '':
        return set(salas_validas)
    resultado = set()
    for tok in texto.split(','):
        tok = tok.strip()
        if not tok:
            continue
        try:
            sala_id = int(tok)
        except ValueError:
            raise ValueError(f"sala_id inválido '{tok}' (debe ser entero)")
        if sala_id not in salas_validas:
            raise ValueError(
                f"sala {sala_id} no existe en el catálogo "
                f"{sorted(salas_validas)}"
            )
        resultado.add(sala_id)
    return resultado


def cargar(path):
    """Lee el CSV y devuelve el dict de datos para el modelo.

    El CSV es "raw input": una fila por curso. El programa genera todas
    las combinaciones (curso, bloque, sala) factibles vía `calcular_costos`.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    nombre = p.stem

    with open(p, 'r', encoding='utf-8', newline='') as f:
        filas = list(csv.DictReader(f))

    if not filas:
        raise ValueError(f"CSV vacío: {path}")

    columnas = {k for k in filas[0].keys() if k is not None}
    faltantes = COLUMNAS_REQUERIDAS - columnas
    if faltantes:
        raise ValueError(
            f"Faltan columnas en el CSV: {sorted(faltantes)}\n"
            f"Columnas encontradas: {sorted(columnas)}"
        )
    desconocidas = columnas - COLUMNAS_REQUERIDAS - COLUMNAS_OPCIONALES
    if desconocidas:
        # Warning light, no error — útil si el usuario agrega columnas extra.
        # Pero por consistencia del modelo, las ignoramos.
        pass

    R, Cap, Salas = construir_datos_salas()

    cursos = {}                    # curso -> {alumnos, bloques}
    profesores = {}                # id -> nombre
    salas_por_curso = {}           # curso -> set(sala_id)
    profesores_por_curso = {}      # curso -> list[(prof_id, nombre_prof)]

    for i, fila in enumerate(filas, start=2):
        try:
            curso = fila['curso'].strip()
            bloques = int(fila['bloques'])
            alumnos = int(fila['alumnos'])
            prof_id = int(fila['profesor_id'])
            nombre_prof = fila['nombre_profesor'].strip()
            salas_str = fila.get('salas_disponibles')
        except (ValueError, TypeError) as e:
            raise ValueError(f"Fila {i}: dato mal formado — {e}") from e
        except KeyError as e:
            raise ValueError(f"Fila {i}: columna faltante — {e}") from e

        if not curso:
            raise ValueError(f"Fila {i}: 'curso' vacío")
        if bloques < 1:
            raise ValueError(f"Fila {i}: 'bloques' debe ser >= 1")

        salas_set = _parsear_salas_disponibles(salas_str, R)

        # Validar que al menos una sala admite el curso
        if not any(alumnos <= Cap[r] for r in salas_set):
            raise ValueError(
                f"Fila {i}: ninguna sala disponible admite '{curso}' "
                f"con {alumnos} alumnos. Disponibles: {sorted(salas_set)}, "
                f"capacidades: {{r: Cap[r] for r in salas_set}}"
            )

        if curso in cursos:
            # En filas duplicadas del mismo curso solo validamos consistencia
            # en alumnos, bloques y salas_disponibles. profesor_id y
            # nombre_profesor pueden cambiar (es la forma de declarar varios
            # profesores para un mismo curso).
            prev = cursos[curso]
            if prev['alumnos'] != alumnos:
                raise ValueError(
                    f"Fila {i}: curso '{curso}' tiene 'alumnos' inconsistente "
                    f"({prev['alumnos']} vs {alumnos})."
                )
            if prev['bloques'] != bloques:
                raise ValueError(
                    f"Fila {i}: curso '{curso}' tiene 'bloques' inconsistente "
                    f"({prev['bloques']} vs {bloques})."
                )
            if salas_por_curso[curso] != salas_set:
                raise ValueError(
                    f"Fila {i}: 'salas_disponibles' inconsistente para "
                    f"'{curso}' ({salas_por_curso[curso]} vs {salas_set})"
                )
            if any(p == prof_id for p, _ in profesores_por_curso[curso]):
                raise ValueError(
                    f"Fila {i}: profesor_id {prof_id} repetido para '{curso}'. "
                    f"Cada fila de un mismo curso debe tener un profesor_id "
                    f"distinto."
                )
            profesores_por_curso[curso].append((prof_id, nombre_prof))
        else:
            cursos[curso] = {
                'alumnos': alumnos,
                'bloques': bloques,
            }
            salas_por_curso[curso] = salas_set
            profesores_por_curso[curso] = [(prof_id, nombre_prof)]
            if prof_id in profesores and profesores[prof_id] != nombre_prof:
                raise ValueError(
                    f"Fila {i}: profesor_id {prof_id} ya existe con nombre "
                    f"'{profesores[prof_id]}', no puede ser '{nombre_prof}'."
                )
            profesores[prof_id] = nombre_prof

    C = sorted(cursos.keys())
    P = sorted(profesores.keys())
    # T default = todos los bloques del calendario. Si el usuario quiere
    # restringirlo por instancia, puede agregarse luego sin cambiar este formato.
    T = list(range(1, TOTAL_BLOQUES + 1))

    # C_p: profesor -> cursos. Un curso con multiples profesores aparece en
    # cada uno de sus profesores (la restriccion "prof sin solapamiento" se
    # aplica a cada profesor por separado).
    C_p = {p: [] for p in P}
    for c, profs in profesores_por_curso.items():
        for prof_id, _ in profs:
            C_p[prof_id].append(c)

    datos = {
        'nombre': nombre,
        'C': C,
        'T': T,
        'R': R,
        'P': P,
        'D': {c: cursos[c]['bloques'] for c in C},
        'Cap': Cap,
        'Alum': {c: cursos[c]['alumnos'] for c in C},
        'C_p': C_p,
        'Salas': Salas,
        'Profe': profesores,
        'Salas_disponibles': salas_por_curso,
    }

    calcular_costos(datos)

    # Validar que cada curso tiene suficientes combinaciones factibles
    for c, info in cursos.items():
        factibles = sum(1 for (cc, _, _) in datos['Costo'] if cc == c)
        if factibles < info['bloques']:
            raise ValueError(
                f"Curso '{c}' requiere {info['bloques']} bloques pero solo "
                f"hay {factibles} combinaciones factibles. "
                f"Agrega más salas disponibles o relaja restricciones."
            )

    return datos


if __name__ == "__main__":
    import sys
    ruta = sys.argv[1] if len(sys.argv) > 1 else 'instancias/ejemplo.csv'
    d = cargar(ruta)
    print(f"Nombre: {d['nombre']}")
    print(f"Cursos ({len(d['C'])}): {d['C']}")
    print(f"Salas ({len(d['R'])}): {d['R']} -> {d['Salas']} (cap: {d['Cap']})")
    print(f"Profesores ({len(d['P'])}): {d['P']} -> {d['Profe']}")
    print(f"Alumnos: {d['Alum']}")
    print(f"Bloques por curso (D): {d['D']}")
    print(f"Cursos por profesor (C_p): {d['C_p']}")
    print(f"Salas por curso: {d['Salas_disponibles']}")
    print(f"Tamaño de T: {len(d['T'])}")
    print(f"Variables de costo: {len(d['Costo'])}")
