
# Manual para entender

# dias y horas

DIAS = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie']
HORAS = ['8:15-9:35', '9:50-11:10', '11:25-12:45', '13:45-15:05', '15:20-16:40', '16:55-18:15']
BLOQUES_POR_DIA = len(HORAS)
SALAS = {1: "INF526", 2: "INF201"}



# Conjuntos
C = [1, 2, 3]                          # 3 cursos
T = list(range(1,5))                   # 4 bloques
R = [1, 2]                             # 2 salas
P = [1, 2]                             # 2 profesores


# Mapeo bloque → día, horario
def bloque_a_horario(t):
    idx_dia = (t - 1) // BLOQUES_POR_DIA
    idx_bloque = (t - 1) % BLOQUES_POR_DIA
    return DIAS[idx_dia], HORAS[idx_bloque]


# Parametros

D = {1: 1, 2: 1, 3: 1}                # 1 bloque por curso
Cap = {1: 30, 2: 25}                   # capacidades de salas
Alum = {1: 20, 2: 15, 3: 28}           # alumnos por curso

prof_de = {1: 1, 2: 1, 3: 2}           # cursos 1,2 → prof 1; curso 3 → prof 2

C_p = {1: [1, 2], 2: [3]}              # cursos del prof 1: [1,2]; del prof 2: [3]


# Costos (simplificado: solo penalización por capacidad)
Costo = {}
for c in C:
    for t in T:
        for r in R:
            dia, horario = bloque_a_horario(t)
            costo_base = 1.0
            # Penalización por capacidad
            if Cap[r] >= Alum[c]:
                desperdicio = (Cap[r] - Alum[c]) / Cap[r]
            else:
                desperdicio = 50.0
            # Penalización por horario extremo
            # Bloque 1 (8:15): penalizado (muy temprano)
            # Bloque 6 (16:55): penalizado (muy tarde)
            if horario in ['8:15-9:35', '16:55-18:15']:
                penal_horario = 0.5
            else:
                penal_horario = 0.0
            Costo[(c, t, r)] = costo_base + desperdicio + penal_horario
# Imprimir resumen
print("=" * 70)
print("INSTANCIA UCTP — horarios USACH")
print("=" * 70)
print(f"Cursos: {C}")
print(f"Salas: {R} ({[SALAS[r] for r in R]}, capacidades: {Cap})")
print(f"Profesores: {P}")
print(f"Alumnos por curso: {Alum}")
print()
print("Bloques disponibles:")
for t in T:
    dia, horario = bloque_a_horario(t)
    print(f"  Bloque {t:2d} = {dia} {horario}")
print()
print("Costos Costo[c,t,r]:")
print(f"{'curso':<6}{'bloque':<8}{'sala':<6}{'día':<6}{'horario':<18}{'costo':<8}")
for c in C:
    for t in T:
        for r in R:
            dia, horario = bloque_a_horario(t)
            print(f"{c:<6}{t:<8}{SALAS[r]:<6}{dia:<6}{horario:<18}{Costo[(c,t,r)]:.2f}")
    print("-" * 50)