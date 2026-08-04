import pulp


def crear_modelo(datos, nombre):
    """Construye el problema ILP para UCTP.

    Las variables x[c,t,r] se crean SOLO para combinaciones con costo
    presente en datos['Costo']. Si una combinación (c,t,r) no aparece en
    Costo, el modelo no puede asignarla — equivale a declararla infactible
    en la entrada (más estricto que boundarla a 0).
    """

    C = datos['C']
    T = datos['T']
    R = datos['R']
    P = datos['P']
    D = datos['D']
    Costo = datos['Costo']
    C_p = datos['C_p']

    prob = pulp.LpProblem(nombre, pulp.LpMinimize)

    # Variables de decisión: una por combinación con costo definido
    x = {}
    for (c, t, r) in Costo:
        nombre_var = f"x_{c}_{t}_{r}"
        x[c, t, r] = pulp.LpVariable(nombre_var, cat='Binary')

    # Función objetivo: minimizar costo total
    prob += pulp.lpSum(
        Costo[(c, t, r)] * x[c, t, r] for (c, t, r) in Costo
    ), "Costo_Total"

    # R(3): cada curso cubre exactamente D[c] bloques
    for c in C:
        prob += pulp.lpSum(
            x.get((c, t, r), 0) for t in T for r in R
        ) == D[c], f"Dem_{c}"

    # R(4): una sola clase por (sala, bloque)
    for t in T:
        for r in R:
            prob += pulp.lpSum(
                x.get((c, t, r), 0) for c in C
            ) <= 1, f"Sala_{t}_{r}"

    # R(6): profesor no se solapa en un mismo bloque
    for p in P:
        for t in T:
            prob += pulp.lpSum(
                x.get((c, t, r), 0) for c in C_p[p] for r in R
            ) <= 1, f"Prof_{p}_{t}"

    return prob, x