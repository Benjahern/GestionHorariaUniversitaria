"""Resuelve la instancia UCTP usando PuLP.

Usa CPLEX si está disponible, si no cae a CBC. Imprime status, objetivo
y la asignación óptima. La asignación se devuelve como dict para que
main.py pueda pasarla a verificar/visualizar/guardar.
"""

import pulp
from Modelos.modelo import crear_modelo


def obtener_solver(time_limit=60):
    """Devuelve (solver, nombre). CPLEX si está disponible, CBC en su lugar."""
    try:
        s = pulp.CPLEX_PY(msg=0, timeLimit=time_limit)
        if s.available():
            return s, "CPLEX"
    except Exception:
        pass
    return pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit), "CBC"


def resolver(datos, time_limit=60):
    """Resuelve el modelo. Devuelve (prob, x, asignacion).

    asignacion: dict {curso: [(bloque, sala), ...]}
    """
    nombre = datos.get('nombre', 'UCTP')

    prob, x = crear_modelo(datos, nombre)

    solver, solver_name = obtener_solver(time_limit=time_limit)
    print(f"Resolviendo '{nombre}' con {solver_name}...")
    prob.solve(solver)

    print(f"\nStatus: {pulp.LpStatus[prob.status]}")
    print(f"Objetivo (costo total): {pulp.value(prob.objective):.4f}")
    print(f"Variables: {len(prob.variables())}")
    print(f"Restricciones: {len(prob.constraints)}")

    # Extraer asignación agrupando por curso
    asignacion = {c: [] for c in datos['C']}
    print("\n=== ASIGNACIÓN ÓPTIMA ===")
    for c in datos['C']:
        for t in datos['T']:
            for r in datos['R']:
                if (c, t, r) in x and pulp.value(x[c, t, r]) > 0.5:
                    print(f"  {c} → Bloque {t}, Sala {r}")
                    asignacion[c].append((t, r))

    return prob, x, asignacion


if __name__ == "__main__":
    from instancias.parser import cargar
    datos = cargar('instancias/ejemplo.csv')
    resolver(datos)