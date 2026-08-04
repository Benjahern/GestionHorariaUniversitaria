"""
Verifica que la asignación cumple TODAS las restricciones del UCTP.

Las constantes del modelo (Cap, Alum, C_p, etc.) vienen del dict `datos`,
así que esta función no toca código de la instancia.
"""

from instancias.parser import bloque_a_horario


def verificar(asignacion, datos):
    """Valida una asignación contra las 4 restricciones del modelo.

    Parámetros:
        asignacion: dict {curso: [(bloque, sala), ...]}
        datos: dict producido por instancias.parser.cargar

    Retorna:
        tupla (cumple, errores)
    """
    C = datos['C']
    T = datos['T']
    R = datos['R']
    D = datos['D']
    Cap = datos['Cap']
    Alum = datos['Alum']
    C_p = datos['C_p']

    errores = []

    # R(3): cada curso debe cubrir exactamente D[c] bloques
    for c in C:
        if c not in asignacion:
            errores.append(f"R(3): curso {c} sin asignación")
        elif len(asignacion[c]) != D[c]:
            errores.append(
                f"R(3): curso {c} tiene {len(asignacion[c])} bloques, "
                f"esperaba {D[c]}"
            )

    # R(4): una sola clase por sala y bloque
    for t in T:
        for r in R:
            cursos_en = []
            for c in C:
                if c in asignacion:
                    for (b, s) in asignacion[c]:
                        if b == t and s == r:
                            cursos_en.append(c)
            if len(cursos_en) > 1:
                errores.append(
                    f"R(4): sala {r} bloque {t} tiene {len(cursos_en)} "
                    f"cursos: {cursos_en}"
                )

    # R(5): capacidad de la sala
    for c in C:
        if c in asignacion:
            for (b, r) in asignacion[c]:
                if Cap[r] < Alum[c]:
                    errores.append(
                        f"R(5): curso {c} ({Alum[c]} alumnos) en sala {r} "
                        f"(cap {Cap[r]})"
                    )

    # R(6): profesor no se solapa
    for p in C_p:
        for t in T:
            cursos_prof = []
            for c in C_p[p]:
                if c in asignacion:
                    for (b, s) in asignacion[c]:
                        if b == t:
                            cursos_prof.append(c)
            if len(cursos_prof) > 1:
                errores.append(
                    f"R(6): profesor {p} tiene {len(cursos_prof)} cursos "
                    f"simultáneos en bloque {t}: {cursos_prof}"
                )

    return len(errores) == 0, errores


if __name__ == "__main__":
    from instancias.parser import cargar
    from resolv import resolver

    datos = cargar('instancias/ejemplo.csv')
    _, _, asignacion, _ = resolver(datos)

    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE LA ASIGNACIÓN")
    print("=" * 60)
    print("\nAsignación:")
    for c, sesiones in sorted(asignacion.items()):
        for (b, r) in sesiones:
            dia, horario = bloque_a_horario(b)
            print(f"  {c} -> Bloque {b} ({dia} {horario}), Sala {r}")

    cumple, errores = verificar(asignacion, datos)
    print(f"\nResultado: {'OK FACTIBLE' if cumple else 'X NO FACTIBLE'}")
    if errores:
        print(f"\nErrores ({len(errores)}):")
        for e in errores:
            print(f"  - {e}")
    else:
        print("\nOK Todas las restricciones se cumplen correctamente.")