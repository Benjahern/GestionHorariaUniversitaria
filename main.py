"""
CLI para resolver UCTP desde un CSV de instancia.

Uso:
    python main.py instancias/ejemplo.csv [--time-limit N]

El CSV lista los CURSOS (una fila por curso, con sus salas permitidas). El
programa genera todas las combinaciones (curso, bloque, sala) factibles,
construye el modelo, lo resuelve, verifica la asignación contra las
restricciones, la imprime como tabla y la exporta a output/<nombre>.csv.
"""

import argparse
import os
import sys

from instancias.parser import cargar
from Modelos.modelo import crear_modelo
from resolv import resolver, obtener_solver
from verificar import verificar
from print import visualizar, guardar_csv


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
        help='Carpeta donde escribir el CSV de salida (default: output).',
    )
    args = p.parse_args()

    # 1. Cargar datos
    try:
        datos = cargar(args.instancia)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error al leer la instancia: {e}", file=sys.stderr)
        return 1

    nombre = datos['nombre']
    print("=" * 60)
    print(f"  {nombre}")
    print("=" * 60)
    print(f"Cursos: {datos['C']}")
    print(f"Salas: {datos['Salas']} (capacidades: {datos['Cap']})")
    print(f"Profesores: {datos['Profe']}")
    print(f"Variables de costo (combinaciones factibles): "
          f"{len(datos['Costo'])}")
    print()

    # 2. Resolver
    _, _, asignacion = resolver(datos, time_limit=args.time_limit)

    # 3. Verificar
    cumple, errores = verificar(asignacion, datos)
    print(f"\nVerificación: {'✓ FACTIBLE' if cumple else '✗ NO FACTIBLE'}")
    if errores:
        for e in errores:
            print(f"  - {e}")

    # 4. Visualizar
    print()
    visualizar(asignacion, datos)

    # 5. Exportar CSV
    os.makedirs(args.out_dir, exist_ok=True)
    ruta_csv = os.path.join(args.out_dir, f"{nombre}.csv")
    guardar_csv(asignacion, datos, ruta_csv)
    print(f"\nCSV guardado en {ruta_csv}")

    return 0 if cumple else 2


if __name__ == "__main__":
    sys.exit(main())