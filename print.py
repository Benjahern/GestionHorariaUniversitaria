"""
Visualiza la asignación como un horario en formato tabla y la exporta a CSV.
"""

import csv

from instancias.parser import bloque_a_horario


def visualizar(asignacion, datos):
    """Muestra el horario en formato de tabla (sala × bloque).

    Las columnas son exactamente los bloques en datos['T'], en orden numérico.
    """
    Salas = datos['Salas']
    Cap = datos['Cap']
    Alum = datos['Alum']
    Profe = datos['Profe']
    R = datos['R']
    T = datos['T']

    print("HORARIO SEMANAL")

    # Una columna por bloque en T (preserva el orden numérico)
    header = f"{'Sala':<12}"
    for t in T:
        dia, horario = bloque_a_horario(t)
        col = f"{dia[:3]} B{t}({horario[:5]})"
        header += f"{col:<18}"
    print(header)
    print("-" * len(header))

    # Grilla: grilla[(t, r)] = curso
    grilla = {}
    for c, sesiones in asignacion.items():
        for (b, r) in sesiones:
            grilla[(b, r)] = c

    for r in R:
        fila = f"{Salas[r]:<12}"
        for t in T:
            curso = grilla.get((t, r))
            fila += f"{(curso if curso else '—'):<18}"
        print(fila)

    print()
    print("Detalle por curso:")
    for c in sorted(asignacion.keys()):
        if not asignacion[c]:
            continue
        prof_id = next(
            (p for p, cursos in datos['C_p'].items() if c in cursos), None
        )
        prof_nombre = Profe.get(prof_id, "?") if prof_id is not None else "?"
        for (b, r) in asignacion[c]:
            dia, horario = bloque_a_horario(b)
            print(f"  {c} ({Alum[c]} alumnos, prof. {prof_nombre}): "
                  f"{dia} {horario} → {Salas[r]} (cap {Cap[r]})")


def guardar_csv(asignacion, datos, ruta):
    """Exporta la asignación a CSV (una fila por sesión).

    Columnas: curso, alumnos, profesor, sala, capacidad_sala, bloque, dia, horario
    """
    Salas = datos['Salas']
    Cap = datos['Cap']
    Alum = datos['Alum']
    Profe = datos['Profe']
    C_p = datos['C_p']

    # Mapa curso -> nombre del profesor
    curso_a_profe = {}
    for p, cursos in C_p.items():
        for c in cursos:
            curso_a_profe[c] = Profe.get(p, f"Prof {p}")

    filas = []
    for c in sorted(asignacion.keys()):
        prof_nombre = curso_a_profe.get(c, "")
        for (b, r) in asignacion[c]:
            dia, horario = bloque_a_horario(b)
            filas.append({
                'curso': c,
                'alumnos': Alum[c],
                'profesor': prof_nombre,
                'sala': Salas[r],
                'capacidad_sala': Cap[r],
                'bloque': b,
                'dia': dia,
                'horario': horario,
            })

    with open(ruta, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'curso', 'alumnos', 'profesor', 'sala',
            'capacidad_sala', 'bloque', 'dia', 'horario',
        ])
        writer.writeheader()
        writer.writerows(filas)


if __name__ == "__main__":
    from instancias.parser import cargar
    from resolv import resolver

    datos = cargar('instancias/ejemplo.csv')
    _, _, asignacion = resolver(datos)
    visualizar(asignacion, datos)
    guardar_csv(asignacion, datos, 'output/ejemplo.csv')
    print("\nCSV guardado en output/ejemplo.csv")