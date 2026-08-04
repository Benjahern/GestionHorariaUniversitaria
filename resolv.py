"""Resuelve la instancia UCTP usando PuLP.

Usa CPLEX si está disponible, si no cae a CBC. Imprime status, objetivo
y la asignación óptima. La asignación se devuelve como dict para que
main.py pueda pasarla a verificar/visualizar/guardar.
"""

import os
import time
import platform

import pulp
from Modelos.modelo import crear_modelo

# Rutas por defecto del ejecutable academico segun Sistema Operativo
if os.environ.get("CPLEX_BIN_PATH"):
    CPLEX_PATH = os.environ.get("CPLEX_BIN_PATH")
elif platform.system() == "Windows":
    CPLEX_PATH = r"C:\Program Files\IBM\ILOG\CPLEX_Studio222\cplex\bin\x64_win64\cplex.exe"
elif platform.system() == "Linux":
    # Ruta comun en Linux (ej. CachyOS, Ubuntu, etc.)
    CPLEX_PATH = "/opt/ibm/ILOG/CPLEX_Studio222/cplex/bin/x86-64_linux/cplex"
else:
    # MacOS como fallback
    CPLEX_PATH = "/Applications/CPLEX_Studio222/cplex/bin/x86-64_osx/cplex"


def obtener_solver(time_limit=60):
    """Devuelve (solver, nombre).

    Prioridad: CPLEX_PY > CPLEX_CMD > CBC.
    """
    # 1. API Python
    try:
        s = pulp.CPLEX_PY(msg=0, timeLimit=time_limit)
        if s.available():
            return s, "CPLEX (API)"
    except Exception:
        pass

    # 2. Ejecutable local
    if os.path.isfile(CPLEX_PATH):
        try:
            s = pulp.CPLEX_CMD(path=CPLEX_PATH, msg=0, timeLimit=time_limit)
            if s.available():
                return s, "CPLEX (CMD)"
        except Exception:
            pass

    # 3. Fallback
    return pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit), "CBC"


def resolver(datos, time_limit=60):
    """Resuelve el modelo. Devuelve (prob, x, asignacion).

    asignacion: dict {curso: [(bloque, sala), ...]}
    """
    nombre = datos.get('nombre', 'UCTP')

    prob, x = crear_modelo(datos, nombre)

    solver, solver_name = obtener_solver(time_limit=time_limit)
    print(f"Resolviendo '{nombre}' con {solver_name}...")
    t0 = time.perf_counter()
    prob.solve(solver)
    t_solve = time.perf_counter() - t0

    print(f"\nStatus: {pulp.LpStatus[prob.status]}")
    print(f"Objetivo (costo total): {pulp.value(prob.objective):.4f}")
    print(f"Tiempo de resolucion: {t_solve:.4f} s")
    print(f"Variables: {len(prob.variables())}")
    print(f"Restricciones: {len(prob.constraints)}")

    # Extraer asignación agrupando por curso
    asignacion = {c: [] for c in datos['C']}
    print("\n=== ASIGNACION OPTIMA ===")
    for c in datos['C']:
        for t in datos['T']:
            for r in datos['R']:
                if (c, t, r) in x and pulp.value(x[c, t, r]) > 0.5:
                    print(f"  {c} -> Bloque {t}, Sala {r}")
                    asignacion[c].append((t, r))

    return prob, x, asignacion, t_solve


if __name__ == "__main__":
    from instancias.parser import cargar
    datos = cargar('instancias/ejemplo.csv')
    resolver(datos)