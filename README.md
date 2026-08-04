# GestionHorariaUniversitaria

Resuelve el **Problema de Horarios Universitarios (UCTP)** para USACH usando PuLP (CPLEX/CBC como motor de resolución). Los datos de la instancia viven en un CSV editable desde Excel.

## Uso rápido

```bash
pip install pulp
python main.py instancias/ejemplo.csv
```

El programa:
1. Lee el CSV con la instancia.
2. Construye el modelo ILP.
3. Lo resuelve con CPLEX (si está disponible) o CBC.
4. Verifica que la asignación cumple todas las restricciones.
5. Imprime el horario en formato tabla.
6. Exporta la asignación a `output/<nombre>.csv` (abrible en Excel).

## Crear tu propia instancia

Copia `instancias/ejemplo.csv`, ábrelo en Excel y edítalo. **Una fila por curso** — el programa genera solo las combinaciones `(curso, bloque, sala)` factibles (capacidad y salas disponibles).

### Columnas

| Columna | Significado |
|---|---|
| `curso` | nombre del curso (identificador único) |
| `bloques` | bloques semanales que ocupa el curso |
| `alumnos` | alumnos inscritos |
| `profesor_id` | ID del profesor |
| `nombre_profesor` | nombre del profesor |
| `salas_disponibles` | IDs de salas separados por coma (vacío = todas) |

### Casos comunes

- **Agregar un curso:** añade una fila nueva.
- **Restringir las salas de un curso:** escribe los IDs en `salas_disponibles`, ej. `"1,2"`. Déjalo vacío para que use cualquiera.
- **Agregar una sala nueva:** edita la constante `SALAS` en `instancias/costos.py` (id, nombre, capacidad). Después úsala en `salas_disponibles` si quieres restringir cursos a ella.
- **Cambiar el horario** (días, bloques, penalizaciones): edita las constantes en `instancias/parser.py` y `instancias/costos.py`.

Luego corre `python main.py instancias/mi_instancia.csv` y el horario se exporta a `output/mi_instancia.csv`.

### Restricciones que el modelo respeta

- Cada curso se dicta exactamente en los bloques que indica su columna `bloques`.
- Una sola clase por sala y bloque.
- La capacidad de la sala debe alcanzar para los alumnos del curso.
- Un profesor no puede tener dos cursos al mismo tiempo.

Si el CSV pide algo que viola estas restricciones (ej. curso con más alumnos que la sala), el parser lo rechaza con un mensaje claro antes de resolver.

## Estructura del proyecto

```
.
├── main.py                 # CLI: python main.py instancia.csv
├── resolv.py               # resuelve el modelo
├── verificar.py            # valida la asignación
├── print.py                # visualiza + exporta CSV
├── instancias/
│   ├── parser.py           # carga el CSV, valida, expone bloque_a_horario
│   ├── costos.py           # fórmula de costo (1.0 + desperdicio + penal_horario)
│   └── ejemplo.csv         # instancia de ejemplo
├── Modelos/
│   └── modelo.py           # construye el ILP en PuLP
└── output/                 # CSV generados
```

## ¿Por qué PuLP?

Librería de modelado de Programación Lineal Entera. Como motor de resolución usa **CBC** (open source) o **CPLEX** (comercial, si está disponible).

## Detalles avanzados

- Si quieres regenerar la columna `costo` desde la fórmula en vez de escribirla a mano, edita las constantes en `instancias/costos.py` y ejecuta `python instancias/costos.py`.
- Si necesitas cambiar el horizonte (más o menos días/bloques), modifica `DIAS`, `HORAS` y `SLOTS_POR_DIA` en `instancias/parser.py`.
- El solver tiene un time limit de 60s por defecto. Cámbialo con `--time-limit N`.