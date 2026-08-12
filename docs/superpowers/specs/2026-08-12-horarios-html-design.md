# Diseño: generación de HTML con horarios por profesor

**Fecha:** 2026-08-12
**Estado:** Aprobado por el usuario, pendiente revisión final

## Resumen

Cuando se ejecuta `main.py <instancia.csv>`, además del CSV actual
(`output/<nombre>.csv`) se genera un único archivo HTML
(`output/<nombre>.html`) con una visualización del horario en formato
grilla semanal (días × bloques), una por cada profesor de la instancia.

El HTML es autocontenido (CSS embebido, JS vanilla, sin CDN, sin
dependencias externas), imprimible, e incluye un filtro por profesor en
JS puro para ocultar todas las grillas menos la seleccionada.

## Motivación

El `print.py` actual tiene `visualizar()` (texto en consola, grilla
`Sala × bloque`) y `guardar_csv()` (tabla plana). Falta una vista que
sea:

- **Compartible** (un solo archivo, se manda por correo).
- **Por profesor** (la vista `Sala × bloque` no responde la pregunta
  "¿qué tiene que dar Victor el lunes?").
- **Visual** (colores por curso, alerta de horarios penalizados).
- **Filtrable** (en instancias grandes con 10+ profesores, scrollear
  todo es tedioso).

## Decisiones de diseño (aprobadas)

| Decisión | Valor | Justificación |
|---|---|---|
| Visualización por profesor | Grilla semanal (5 días × 6 bloques) | Coherente con la visualización existente `Sala × bloque` que ya está en `print.py`. |
| Organización de archivos | Un solo `<nombre>.html` con TOC + anclas | Simple de compartir y mantener. |
| Interactividad | HTML + CSS + JS vanilla (filtro dropdown) | Sin dependencias. Funciona offline. |
| Contenido por celda | Curso + sala + alumnos (3 líneas) | Información completa para que el profe no tenga que cruzar con otra tabla. |
| Color de celda | Color fijo por curso (hash → paleta 12 colores) | Consistencia entre profes que comparten un curso. |
| Penalización horaria | ⚠ en celda + tooltip | Marca visual sin romper el color del curso. |
| Dónde vive el código | `guardar_html()` en `print.py` | Simétrico con `guardar_csv`. Cero archivos nuevos. |
| Generación | Siempre, sin flag CLI | El usuario pidió que se genere siempre. |

## Arquitectura

### Cambios en archivos existentes

**`print.py`** — agregar la función:

```python
def guardar_html(asignacion, datos, ruta):
    """Genera output/<nombre>.html con grilla semanal por profesor.

    Un solo archivo autocontenido (CSS embebido, JS vanilla).
    Retorna la cantidad de bytes escritos.
    """
    ...
```

Reutiliza directamente los dicts que ya usa `guardar_csv`:
`Salas`, `Cap`, `Alum`, `Profe`, `C_p`, `T`.

**`main.py`** — agregar después de `guardar_csv`:

```python
ruta_html = os.path.join(args.out_dir, f"{nombre}.html")
guardar_html(asignacion, datos, ruta_html)
print(f"HTML guardado en {ruta_html}")
```

### Archivos no tocados

`parser.py`, `costos.py`, `modelo.py`, `resolv.py`, `verificar.py`,
todos los CSVs de instancia.

## Estructura del HTML

```
<head>
  <meta charset="utf-8">
  <title>Horario: <nombre></title>
  <style>
    /* Paleta de 12 colores, layout de grilla, responsive,
       print-friendly @media print */
  </style>
</head>
<body>
  <header>
    <h1>Horario: <nombre_instancia></h1>
    <div class="meta">
      N cursos · N salas · N profesores · costo total X
    </div>
    <div class="controls">
      <label for="filtro-prof">Filtrar:</label>
      <select id="filtro-prof">
        <option value="all">Todos los profesores</option>
        <option value="<prof_id>">Nombre Apellido</option>
        ...
      </select>
    </div>
  </header>

  <nav class="toc">
    <h2>Profesores</h2>
    <ul>
      <li><a href="#prof-<id>">Nombre Apellido</a></li>
      ...
    </ul>
  </nav>

  <main aria-live="polite">
    <section id="prof-<id>" class="profesor" data-prof-id="<id>">
      <h2>Nombre Apellido <small>(N cursos · M bloques/semana)</small></h2>
      <table class="grilla">
        <thead>
          <tr>
            <th></th>
            <th>Lun</th><th>Mar</th><th>Mie</th><th>Jue</th><th>Vie</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th>8:15-9:35</th>
            <td class="curso-Algoritmos penalizado" title="...">
              <span class="curso">Algoritmos</span>
              <span class="sala">EAO-101</span>
              <span class="alum">20 alumnos</span>
              <span class="warn" title="Bloque penalizado por horario">⚠</span>
            </td>
            <td class="vacio">-</td>
            ...
          </tr>
          ...
        </tbody>
      </table>
    </section>
    ...
  </main>

  <script>
    /* filtro dropdown */
  </script>
</body>
```

### Grilla por profesor

- **Filas:** 6 (una por bloque, etiqueta horaria a la izquierda).
- **Columnas:** 5 (`Lun`, `Mar`, `Mie`, `Jue`, `Vie`).
- **Celda llena:** fondo = color del curso, 3 líneas (curso / sala / alumnos) + ⚠ si penalizado.
- **Celda vacía:** fondo gris claro, contenido `-`.

### Color por curso

- Paleta fija de 12 colores colorblind-friendly (basada en Okabe-Ito).
- Asignación determinista: `color_idx = hash(nombre_curso) % 12`.
- Estable entre ejecuciones (no aleatoria).
- Si Victor y Maria enseñan Algoritmos, ambos lo ven del mismo color.

### Penalización horaria

- Bloques en `HORAS_PENALIZADAS = {'8:15-9:35', '16:55-18:15'}` (constante ya existente en `costos.py`).
- Celda recibe clase CSS `penalizado` + `<span class="warn">⚠</span>` en la esquina.
- Tooltip nativo: `title="Bloque penalizado por horario"`.

### CSS embebido

- Layout limpio tipo "calendario académico".
- Responsive básico: <600px reduce padding, mantiene grilla legible.
- `@media print`: oculta el dropdown, oculta la TOC.
- Contraste WCAG AA.

## JS (vanilla, ~30 líneas, sin dependencias)

```javascript
document.getElementById('filtro-prof').addEventListener('change', (e) => {
  const selected = e.target.value;
  document.querySelectorAll('section.profesor').forEach(sec => {
    sec.style.display = (selected === 'all' || sec.dataset.profId === selected)
      ? '' : 'none';
  });
});
```

- Sin resaltado al hover (la celda ya tiene `title` con info completa).
- Sin detección de solapamientos (el solver ya garantiza factibilidad).
- Sin export desde HTML (el CSV ya existe).
- Accesibilidad: `<label for>` + `aria-live="polite"` en `<main>`.

## Manejo de casos borde

| Caso | Comportamiento |
|---|---|
| Solver infactible (asignación vacía) | HTML se genera. Banner rojo: "⚠ Solver no encontró solución factible." Todas las celdas con `-`. |
| Curso parcialmente asignado | Celdas vacías en los bloques faltantes. Banner amarillo de aviso. |
| Profesor con 0 cursos | Sección muestra "— Sin cursos asignados —". Sigue en la TOC. |
| Nombre con `<`, `>`, `&`, comillas | `html.escape()` obligatorio antes de interpolar. |
| Nombre con caracteres no ASCII | `encoding='utf-8'` al escribir (consistente con `guardar_csv`). |
| Sala con capacidad o alumnos extremos | Sin wrapping raro. `word-break: break-word` en CSS. |
| Instancia con 1 o 50 profesores | Escala OK. TOC sticky en desktop. |
| Error de I/O al escribir el archivo | `OSError` se propaga. `main.py` no lo captura → traceback visible, exit code 1. |

## Datos leídos del dict (input)

`guardar_html` consume los mismos campos que `guardar_csv`:

```python
{
    'nombre': str,
    'T': list[int],                # bloques 1..30
    'C': list[str],                # cursos
    'Salas': dict[int, str],       # sala_id -> nombre
    'Cap': dict[int, int],         # sala_id -> capacidad
    'Alum': dict[str, int],        # curso -> alumnos
    'Profe': dict[int, str],       # prof_id -> nombre
    'C_p': dict[int, list[str]],   # prof_id -> [cursos]
}
```

Y el argumento `asignacion: dict[str, list[tuple[int, int]]]`
(misma forma que recibe `guardar_csv`).

## Datos escritos al HTML (output)

Un archivo UTF-8 con extensión `.html` que contiene:

- Header con nombre de la instancia + meta.
- TOC con anclas a cada profesor.
- Una `<section>` por profesor con su grilla.
- CSS y JS embebidos.

## Estrategia de prueba

El proyecto no tiene test suite, no se agrega una para esta feature
(sería inconsistente). En su lugar:

1. **Manual — visual:** correr
   `python main.py instancias/inst_10_full.csv` (la más grande, 14
   cursos / 14 profesores) y abrir el HTML en el navegador. Verificar:
   - Todas las grillas se ven.
   - Colores distinguibles entre cursos.
   - ⚠ aparece en bloques penalizados.
   - Filtro JS funciona.
   - Imprimir desde el navegador da un resultado limpio.

2. **Manual — smoke:** correr las 10 instancias (`inst_01` → `inst_10`)
   y verificar que el HTML se genere sin error y se abra correctamente.

3. **Sanity check automatizado** (opcional, archivo
   `tests/test_html.py` standalone sin pytest):

   ```python
   import os
   from instancias.parser import cargar
   from resolv import resolver
   from print import guardar_html

   datos = cargar('instancias/ejemplo.csv')
   _, _, asignacion, _ = resolver(datos)

   ruta = '/tmp/test_horario.html'
   guardar_html(asignacion, datos, ruta)

   with open(ruta, 'r', encoding='utf-8') as f:
       html = f.read()

   assert '<html' in html
   for nombre in datos['Profe'].values():
       assert nombre in html, f"Falta profesor {nombre}"
   for curso in datos['C']:
       assert curso in html, f"Falta curso {curso}"
   assert html.count('<script') == 1, "Debería haber exactamente un <script>"

   # XSS escaping
   datos['C'] = ['<script>alert(1)</script>']
   datos['Alum']['<script>alert(1)</script>'] = 10
   datos['D']['<script>alert(1)</script>'] = 1
   guardar_html({'<script>alert(1)</script>': []}, datos, ruta)
   with open(ruta, 'r', encoding='utf-8') as f:
       html = f.read()
   assert '<script>alert(1)</script>' not in html
   assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html
   ```

   Se ejecuta con `python tests/test_html.py`. Pasa o falla con exit
   code explícito.

## Riesgos y trade-offs

| Riesgo | Mitigación |
|---|---|
| Paleta de 12 colores insuficiente para 13+ cursos | Dos cursos pueden colisionar (mismo color). Es aceptable visualmente — el nombre del curso en la celda sigue distinguiéndolos. Si el usuario pide más, se sube a 16 o 20. |
| HTML pesado en instancias grandes | Para `inst_10_full` (14 cursos) el HTML pesa ~30-50 KB. Despreciable. |
| JS desactivado en el navegador del usuario | El HTML sigue siendo 100% funcional sin JS (todas las grillas visibles). El filtro es un enhancement, no un requirement. |
| Cambios futuros en la estructura de `datos` | Si `parser.py` cambia, `guardar_html` se rompe igual que `guardar_csv`. Mismo riesgo, mismo contrato. |
| Locale (fecha, números) | Sin números grandes ni formateo regional sensible. Strings literales. |

## Lo que NO hace (fuera de alcance)

- Exportar a PDF directamente (se imprime desde el navegador).
- Vista por sala (ya existe la grilla `Sala × bloque` en consola).
- Vista por curso individual (se puede derivar mentalmente del filtro).
- Detección de conflictos en el HTML (verificar.py ya lo hace upstream).
- Modificación del CSV existente (es read-only después de generado).

## Próximos pasos

Una vez aprobado este spec:

1. Invocar la skill `superpowers:writing-plans` para descomponer en
   tareas de implementación ordenadas.
2. Implementar siguiendo el plan.
3. Correr las pruebas manuales y el sanity check.
4. Commit.