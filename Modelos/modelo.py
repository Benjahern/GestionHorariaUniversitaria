import pulp

def crear_modelo(datos, nombre):


    # Extraemos conjuntos y parámetros
    C = datos['C']
    T = datos['T']
    R = datos['R']
    P = datos['P']
    D = datos['D']
    Cap = datos['Cap']
    Alum = datos['Alum']
    C_p = datos['C_p']
    Costo = datos['Costo']


    # Problema de optimización
    prob = pulp.LpProblem(nombre, pulp.LpMinimize)

    #  Crear las variables de decisión x[c,t,r]
    x = {}
    for c in C:
        for t in T:
            for r in R:
                nombre_var = f"x_{c}_{t}_{r}"
                if Alum[c] <= Cap[r]:
                    # Hay capacidad: variable libre
                    x[c, t, r] = pulp.LpVariable(nombre_var, cat='Binary')
                else:
                    # No cabe: variable forzada a 0
                    x[c, t, r] = pulp.LpVariable(
                        nombre_var, lowBound=0, upBound=0, cat='Binary'
                    )

    # Función objetivo: minimizar costo total
    prob += pulp.lpSum(
        Costo[(c, t, r)] * x[c, t, r]
        for c in C for t in T for r in R
    ), "Costo_Total"

    # Restricciones

    # Cada curso debe cubrir exactamente D_c bloques
    for c in C:
        prob += pulp.lpSum(x[c, t, r] for t in T for r in R) == D[c], f"Dem_{c}"

    #  Una sola clase por sala y bloque
    for t in T:
        for r in R:
            prob += pulp.lpSum(x[c, t, r] for c in C) <= 1, f"Sala_{t}_{r}"

    #  Profesor no se solapa
    for p in P:
        for t in T:
            prob += pulp.lpSum(
                x[c, t, r] for c in C_p[p] for r in R
            ) <= 1, f"Prof_{p}_{t}"


    return prob, x