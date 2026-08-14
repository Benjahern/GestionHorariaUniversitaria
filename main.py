"""
CLI para resolver UCTP desde un CSV de instancia.

Uso:
    python main.py instancias/ejemplo.csv [--time-limit N]

El CSV lista los CURSOS (una fila por curso, con sus salas permitidas). El
programa genera todas las combinaciones (curso, bloque, sala) factibles,
construye el modelo, lo resuelve, verifica la asignación y exporta:

- output/<nombre>.csv  (una fila por sesión)
- output/<nombre>.html (grilla semanal por profesor)

En ejecución normal imprime solo:
    ✓ Revise el HTML en output/<nombre>.html

Si la verificación falla, los errores van a stderr (no se silencia la
información crítica).
"""

import argparse
import contextlib
import io
import os
import sys
import time
import pulp

from instancias.parser import cargar
from resolv import resolver
from verificar import verificar
from print import guardar_csv, guardar_html


def _silenciar_stdout():
    """Redirige stdout a un buffer descartable. Para silenciar el output
    verboso de módulos externos (ej. resolv.py) sin perder stderr."""
    return contextlib.redirect_stdout(io.StringIO())


def main():
    p = argparse.ArgumentParser(
        description='Resuelve una instancia UCTP desde un CSV.'
    )
    p.add_argument(
        'instancia',
        help='Ruta al CSV con la instancia (ver instancias/ejemplo.csv).',
    )
    p.add_argument(
        '--time-limit', type=int, default=60,
        help='Tiempo máximo del solver en segundos (default: 60).',
    )
    p.add_argument(
        '--out-dir', default='output',
        help='Carpeta donde escribir el CSV y HTML (default: output).',
    )
    args = p.parse_args()

    # 1. Cargar datos
    try:
        datos = cargar(args.instancia)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error al leer la instancia: {e}", file=sys.stderr)
        return 1

    nombre = datos['nombre']

    # 2. Resolver (silencioso: solver output no es relevante en CLI)
    try:
        with _silenciar_stdout():
            start_time = time.time()
            prob, _, asignacion, _ = resolver(datos, time_limit=args.time_limit)
            end_time = time.time()
            tiempo_resolucion = end_time - start_time
            valor_objetivo = pulp.value(prob.objective)
            num_variables = len(prob.variables())
            num_restricciones = len(prob.constraints)
    except Exception as e:
        print(f"Error al resolver: {e}", file=sys.stderr)
        return 2

    # 3. Verificar
    cumple, errores = verificar(asignacion, datos)
    if not cumple:
        print(
            f"Verificación NO factible ({len(errores)} error(es)):",
            file=sys.stderr,
        )
        for e in errores:
            print(f"  - {e}", file=sys.stderr)

    # 4. Exportar CSV
    os.makedirs(args.out_dir, exist_ok=True)
    ruta_csv = os.path.join(args.out_dir, f"{nombre}.csv")
    guardar_csv(asignacion, datos, ruta_csv)

    # 5. Exportar HTML (grilla semanal por profesor)
    ruta_html = os.path.join(args.out_dir, f"{nombre}.html")
    guardar_html(asignacion, datos, ruta_html)

    # 6. Mensaje final (lo unico que ve el usuario en consola si todo OK)
    if cumple:
        print(f"✓ Revise el HTML en {ruta_html}")
        print(f"Tiempo de resolución: {tiempo_resolucion:.2f} segundos")
        print(f"Valor de la función objetivo (Costo total): {valor_objetivo}")
        print(f"Variables: {num_variables}")
        print(f"Restricciones: {num_restricciones}")
        return 0
    else:
        print(f"HTML guardado en {ruta_html}")
        print(f"Tiempo de resolución: {tiempo_resolucion:.2f} segundos")
        print(f"Valor de la función objetivo (Costo total): {valor_objetivo}")
        print(f"Variables: {num_variables}")
        print(f"Restricciones: {num_restricciones}")
        return 2


if __name__ == "__main__":
    sys.exit(main())