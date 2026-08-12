"""
Visualiza la asignación como un horario en formato tabla y la exporta a CSV.
"""

import csv
import html as html_lib

from instancias.parser import bloque_a_horario, DIAS, HORAS


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
            fila += f"{(curso if curso else '-'):<18}"
        print(fila)

    print()
    print("Detalle por curso:")
    for c in sorted(asignacion.keys()):
        if not asignacion[c]:
            continue
        # Reunir todos los profesores del curso
        profs_del_curso = [
            Profe.get(p, f"Prof {p}")
            for p, cursos_p in datos['C_p'].items()
            if c in cursos_p
        ]
        prof_nombre = ' / '.join(profs_del_curso) if profs_del_curso else '?'
        for (b, r) in asignacion[c]:
            dia, horario = bloque_a_horario(b)
            print(f"  {c} ({Alum[c]} alumnos, prof. {prof_nombre}): "
                  f"{dia} {horario} -> {Salas[r]} (cap {Cap[r]})")


def guardar_csv(asignacion, datos, ruta):
    """Exporta la asignación a CSV (una fila por sesión).

    Columnas: curso, alumnos, profesor, sala, capacidad_sala, bloque, dia, horario
    """
    Salas = datos['Salas']
    Cap = datos['Cap']
    Alum = datos['Alum']
    Profe = datos['Profe']
    C_p = datos['C_p']

    # Mapa curso -> nombres de profesores (puede haber varios)
    curso_a_profe = {}
    for p, cursos_p in C_p.items():
        for c in cursos_p:
            curso_a_profe.setdefault(c, []).append(Profe.get(p, f"Prof {p}"))

    filas = []
    for c in sorted(asignacion.keys()):
        prof_nombre = ' / '.join(curso_a_profe.get(c, ['']))
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


# Paleta Okabe-Ito (colorblind-friendly, 12 colores)
PALETA = [
    '#E69F00', '#56B4E9', '#009E73', '#F0E442',
    '#0072B2', '#D55E00', '#CC79A7', '#999999',
    '#882255', '#44AA99', '#117733', '#AA4499',
]


def _color_idx(curso):
    """Índice determinista de color para un nombre de curso."""
    return hash(curso) % len(PALETA)


def _costo_total(asignacion, datos):
    """Suma el costo de todas las sesiones asignadas."""
    total = 0.0
    for c, sesiones in asignacion.items():
        for (t, r) in sesiones:
            key = (c, t, r)
            if key in datos['Costo']:
                total += datos['Costo'][key]
    return total


def _asignaciones_por_profe(asignacion, datos):
    """Invierte el dict: prof_id -> [(curso, bloque, sala)].

    Un curso con multiples profesores aparece en cada uno de sus profes
    (un prof no comparte aula con su co-profe, pero la sesion aparece en
    el horario de ambos).
    """
    C_p_inv = {}
    for p, cursos in datos['C_p'].items():
        for c in cursos:
            C_p_inv.setdefault(c, []).append(p)

    prof_asig = {p: [] for p in datos['P']}
    for c, sesiones in asignacion.items():
        for prof_id in C_p_inv.get(c, []):
            for (t, r) in sesiones:
                prof_asig[prof_id].append((c, t, r))
    return prof_asig


_CSS = """
:root {
  --bg: #fafafa; --text: #222; --border: #ddd; --slot-bg: #f0f0f0;
}
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
               "Helvetica Neue", Arial, sans-serif;
  margin: 0; background: var(--bg); color: var(--text); line-height: 1.4;
}
header {
  background: white; padding: 1.5rem 2rem;
  border-bottom: 2px solid var(--border);
  position: sticky; top: 0; z-index: 10;
}
header h1 { margin: 0 0 0.5rem 0; font-size: 1.8rem; }
.meta { color: #666; font-size: 0.95rem; margin-bottom: 1rem; }
.controls select {
  padding: 0.4rem; font-size: 0.95rem;
  border: 1px solid var(--border); border-radius: 4px; background: white;
}
.banner {
  margin: 1rem 2rem; padding: 0.8rem 1rem; border-radius: 4px;
}
.banner.error { background: #fee; border-left: 4px solid #c33; color: #800; }
.banner.warn  { background: #ffeed4; border-left: 4px solid #e8a23a; color: #6a4400; }
.toc {
  background: white; padding: 1rem 2rem;
  border-bottom: 1px solid var(--border);
}
.toc h2 { margin: 0 0 0.5rem 0; font-size: 1.1rem; }
.toc ul { list-style: none; padding: 0; margin: 0; columns: 3; }
.toc li { margin: 0.2rem 0; }
.toc a { color: #0072B2; text-decoration: none; }
.toc a:hover { text-decoration: underline; }
main { padding: 1rem 2rem; max-width: 1200px; margin: 0 auto; }
section.profesor {
  background: white; padding: 1.5rem; margin-bottom: 2rem;
  border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
section.profesor h2 { margin-top: 0; }
section.profesor h2 small {
  color: #666; font-weight: normal; font-size: 0.85rem;
}
.empty { color: #888; font-style: italic; }
table.grilla {
  width: 100%; border-collapse: collapse; margin-top: 1rem;
}
table.grilla th, table.grilla td {
  border: 1px solid var(--border); padding: 0.4rem;
  vertical-align: top; min-height: 60px; text-align: center;
}
table.grilla thead th { background: #f5f5f5; font-weight: 600; }
table.grilla th.slot {
  background: #f5f5f5; font-weight: normal; font-size: 0.85rem;
  white-space: nowrap;
}
td.curso { position: relative; padding: 0.5rem; }
td.curso .curso { font-weight: 600; font-size: 0.95rem; display: block; }
td.curso .sala  { font-size: 0.8rem; opacity: 0.9; display: block; }
td.curso .alum  { font-size: 0.75rem; opacity: 0.85; display: block; }
td.curso .warn {
  position: absolute; top: 2px; right: 4px;
  font-size: 1rem; color: #d33; font-weight: bold;
}
td.vacio { background: var(--slot-bg); color: #999; }
@media (max-width: 600px) {
  header { padding: 1rem; }
  main { padding: 0.5rem; }
  section.profesor { padding: 1rem; }
  table.grilla { font-size: 0.85rem; }
  table.grilla th, table.grilla td { padding: 0.3rem; }
  .toc ul { columns: 1; }
}
@media print {
  .controls, .toc { display: none; }
  header { position: static; }
  section.profesor { break-inside: avoid; box-shadow: none; }
}
"""


def guardar_html(asignacion, datos, ruta):
    """Genera output/<nombre>.html con grilla semanal por profesor.

    Un solo archivo autocontenido (CSS embebido, JS vanilla, sin CDN).
    Retorna la cantidad de bytes escritos.
    """
    nombre = datos['nombre']
    Salas = datos['Salas']
    Cap = datos['Cap']
    Alum = datos['Alum']
    Profe = datos['Profe']
    T = datos['T']
    R = datos['R']
    T_set = set(T)
    slots_por_dia = len(HORAS)

    # --- Diagnosticos (banners) ---
    total_sesiones = sum(len(s) for s in asignacion.values())
    banners = []
    if total_sesiones == 0:
        banners.append(
            '<div class="banner error">'
            '⚠ Solver no encontró solución factible.'
            '</div>'
        )
    cursos_incompletos = [
        c for c in datos['C']
        if len(asignacion.get(c, [])) != datos['D'].get(c, 0)
    ]
    if cursos_incompletos and total_sesiones > 0:
        banners.append(
            f'<div class="banner warn">'
            f'⚠ Cursos con asignación parcial: '
            f'{html_lib.escape(", ".join(cursos_incompletos))}'
            f'</div>'
        )

    # --- Costo total ---
    costo = _costo_total(asignacion, datos)

    # --- Invertir por profesor ---
    prof_asig = _asignaciones_por_profe(asignacion, datos)

    # --- Color por curso (mapa estable) ---
    color_curso = {c: PALETA[_color_idx(c)] for c in datos['C']}

    # --- Bloques penalizados ---
    from instancias.costos import HORAS_PENALIZADAS
    penalizado = {slot_idx for slot_idx, h in enumerate(HORAS)
                  if h in HORAS_PENALIZADAS}

    # --- Construir HTML ---
    e = html_lib.escape
    out = []
    out.append('<!DOCTYPE html>')
    out.append('<html lang="es">')
    out.append('<head>')
    out.append('<meta charset="utf-8">')
    out.append(f'<title>Horario: {e(nombre)}</title>')
    out.append('<style>')
    out.append(_CSS)
    out.append('</style>')
    out.append('</head>')
    out.append('<body>')

    # Header
    out.append('<header>')
    out.append(f'<h1>Horario: {e(nombre)}</h1>')
    out.append('<div class="meta">')
    out.append(
        f'{len(datos["C"])} cursos · {len(R)} salas · '
        f'{len(datos["P"])} profesores · costo total {custo_str(costo)}'
    )
    out.append('</div>')
    out.append('<div class="controls">')
    out.append('<label for="filtro-prof">Filtrar:</label>')
    out.append('<select id="filtro-prof">')
    out.append('<option value="all">Todos los profesores</option>')
    for p in datos['P']:
        out.append(f'<option value="{p}">{e(Profe[p])}</option>')
    out.append('</select>')
    out.append('</div>')
    out.append('</header>')

    # Banners
    out.extend(banners)

    # TOC
    out.append('<nav class="toc">')
    out.append('<h2>Profesores</h2>')
    out.append('<ul>')
    for p in datos['P']:
        out.append(f'<li><a href="#prof-{p}">{e(Profe[p])}</a></li>')
    out.append('</ul>')
    out.append('</nav>')

    # Sections (una por profe)
    out.append('<main aria-live="polite">')
    for p in datos['P']:
        sesiones_p = prof_asig[p]
        n_cursos = len({c for c, _, _ in sesiones_p})
        n_bloques = len(sesiones_p)
        out.append(
            f'<section id="prof-{p}" class="profesor" '
            f'data-prof-id="{p}">'
        )
        out.append(
            f'<h2>{e(Profe[p])} '
            f'<small>({n_cursos} cursos · {n_bloques} bloques/semana)'
            f'</small></h2>'
        )

        if not sesiones_p:
            out.append('<p class="empty">— Sin cursos asignados —</p>')
            out.append('</section>')
            continue

        # grilla[(t)] = (curso, sala) o None
        grilla = {}
        for (c, t, r) in sesiones_p:
            # Si el mismo (t) tiene multiples cursos (no debería pasar
            # porque R(4) lo prohibe, pero por si acaso) gana el primero.
            grilla.setdefault(t, (c, r))

        out.append('<table class="grilla">')
        out.append('<thead><tr><th></th>')
        for d in DIAS:
            out.append(f'<th>{e(d)}</th>')
        out.append('</tr></thead>')
        out.append('<tbody>')

        for slot_idx, horario in enumerate(HORAS):
            out.append('<tr>')
            out.append(f'<th class="slot">{e(horario)}</th>')
            for day_idx in range(len(DIAS)):
                t = day_idx * slots_por_dia + slot_idx + 1
                if t not in T_set or t not in grilla:
                    out.append('<td class="vacio">-</td>')
                else:
                    c, r = grilla[t]
                    bg = color_curso.get(c, '#cccccc')
                    clases = ['curso']
                    if slot_idx in penalizado:
                        clases.append('penalizado')
                    title = (
                        f'{e(c)} · {e(Salas[r])} · '
                        f'{Alum[c]} alumnos · bloque {t}'
                    )
                    if slot_idx in penalizado:
                        title += ' · BLOQUE PENALIZADO'
                    out.append(
                        f'<td class="{" ".join(clases)}" '
                        f'style="background:{bg};color:#fff" '
                        f'title="{title}">'
                    )
                    out.append(f'<span class="curso">{e(c)}</span>')
                    out.append(
                        f'<span class="sala">{e(Salas[r])} '
                        f'(cap {Cap[r]})</span>'
                    )
                    out.append(
                        f'<span class="alum">{Alum[c]} alumnos</span>'
                    )
                    if slot_idx in penalizado:
                        out.append(
                            '<span class="warn" '
                            'title="Bloque penalizado por horario">'
                            '⚠</span>'
                        )
                    out.append('</td>')
            out.append('</tr>')
        out.append('</tbody>')
        out.append('</table>')
        out.append('</section>')

    out.append('</main>')

    # JS
    out.append('<script>')
    out.append("document.getElementById('filtro-prof')")
    out.append(".addEventListener('change', function(e) {")
    out.append("  var sel = e.target.value;")
    out.append("  document.querySelectorAll('section.profesor')")
    out.append(".forEach(function(s) {")
    out.append("    s.style.display =")
    out.append("      (sel === 'all' || s.dataset.profId === sel)")
    out.append("        ? '' : 'none';")
    out.append("  });")
    out.append("});")
    out.append('</script>')

    out.append('</body>')
    out.append('</html>')

    html_str = '\n'.join(out)
    with open(ruta, 'w', encoding='utf-8') as f:
        n = f.write(html_str)
    return n


def custo_str(costo):
    """Formatea el costo total con 2 decimales."""
    return f'{costo:.2f}'


if __name__ == "__main__":
    from instancias.parser import cargar
    from resolv import resolver

    datos = cargar('instancias/ejemplo.csv')
    _, _, asignacion, _ = resolver(datos)
    visualizar(asignacion, datos)
    guardar_csv(asignacion, datos, 'output/ejemplo.csv')
    print("\nCSV guardado en output/ejemplo.csv")