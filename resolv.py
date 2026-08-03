import pulp
from Modelos.modelo import crear_modelo
from instancias.prueba import C, T, R, P, D, Cap, Alum, C_p, Costo


def obtener_solver(time_limit=60):
    # Crear el solver CBC
    try:
        s = pulp.CPLEX_PY(msg=0, timeLimit=time_limit)
        if s.available():
            return s, "CPLEX"
    except Exception:
        pass
    return pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit), "CBC"

def solver():

    datos = {
        'C': C,
        'T': T,
        'R': R,
        'P': P,
        'D': D,
        'Cap': Cap,
        'Alum': Alum,
        'C_p': C_p,
        'Costo': Costo 
    }

    prob, x = crear_modelo(datos, "UCTP")

    solver, solver_name = obtener_solver(time_limit=60)
    print(f"Resolviendo con {solver_name}...")
    prob.solve(solver)

    # Mostrar resultados
    print(f"\nStatus: {pulp.LpStatus[prob.status]}")
    print(f"Objetivo (costo total): {pulp.value(prob.objective):.4f}")
    print(f"Variables: {len(prob.variables())}")
    print(f"Restricciones: {len(prob.constraints)}")

    #  Extraer la asignación
    print("\n=== ASIGNACIÓN ÓPTIMA ===")
    for c in C:
        for t in T:
            for r in R:
                if (c, t, r) in x and pulp.value(x[c, t, r]) > 0.5:
                    print(f"  Curso {c} → Bloque {t}, Sala {r}")

    return prob, x


if __name__ == "__main__":
    solver()