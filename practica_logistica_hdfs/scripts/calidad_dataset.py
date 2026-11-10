#!/usr/bin/env python3
"""
calidad_dataset.py
Calcula hashes SHA-256 y sanea el dataset de telemetria logistica.
Todo se lee como texto (sin pandas) para no alterar ningun valor.
"""
import csv
import hashlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
ORIGINAL = DATOS / "telemetria_envios.csv"
LIMPIO = DATOS / "telemetria_limpia.csv"
RECHAZADOS = DATOS / "telemetria_rechazados.csv"
HASHES = DATOS / "hashes_sha256.txt"

HASH_REFERENCIA = "4471c18a0284b3aa5b32a0713e691e3c7fcadae402f105e901c7c57f49474911"
ESTADOS_VALIDOS = {"ENTREGADO", "EN_TRANSITO", "EN_REPARTO", "INCIDENCIA_REPARTO"}
TEMP_MIN, TEMP_MAX = -30.0, 40.0
CAMPOS_OBLIGATORIOS = ["temp_celsius", "peso_kg", "destino"]


def sha256_fichero(ruta):
    """SHA-256 de un fichero leyendo bytes, por bloques."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_filas(ruta):
    """Lee el CSV como texto puro: devuelve (columnas, lista de dicts)."""
    with open(ruta, "r", encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        columnas = lector.fieldnames
        filas = list(lector)
    return columnas, filas

def a_numero(texto):
    """Convierte texto a float; devuelve None si no es un numero valido."""
    try:
        return float(texto.strip())
    except (ValueError, AttributeError):
        return None


def clasificar(columnas, filas):
    """Separa filas validas y rechazadas (con motivo)."""
    validas, rechazadas = [], []
    vistas = set()
    for fila in filas:
        clave = tuple(fila[c] for c in columnas)
        motivos = []

        if clave in vistas:
            motivos.append("duplicado_exacto")
        else:
            vistas.add(clave)

        for campo in CAMPOS_OBLIGATORIOS:
            if fila[campo] is None or fila[campo].strip() == "":
                motivos.append("nulo_" + campo)

        peso = a_numero(fila["peso_kg"] or "")
        if peso is not None and peso <= 0:
            motivos.append("peso_no_positivo")

        temp = a_numero(fila["temp_celsius"] or "")
        if temp is not None and not (TEMP_MIN <= temp <= TEMP_MAX):
            motivos.append("temperatura_fuera_de_rango")

        if fila["estado_envio"].strip() not in ESTADOS_VALIDOS:
            motivos.append("estado_invalido")

        if motivos:
            rechazadas.append((fila, ";".join(motivos)))
        else:
            validas.append(fila)
    return validas, rechazadas

def escribir_csv(ruta, columnas, filas):
    """Escribe CSV en UTF-8 (sin BOM) con saltos LF."""
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f, lineterminator="\n")
        escritor.writerow(columnas)
        for fila in filas:
            escritor.writerow([fila[c] for c in columnas])


def escribir_rechazados(ruta, columnas, rechazadas):
    """Igual que escribir_csv, con una columna extra 'motivo_rechazo'."""
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f, lineterminator="\n")
        escritor.writerow(columnas + ["motivo_rechazo"])
        for fila, motivo in rechazadas:
            escritor.writerow([fila[c] for c in columnas] + [motivo])

def main():
    hash_original = sha256_fichero(ORIGINAL)
    print("SHA-256 original :", hash_original)
    print("SHA-256 referencia:", HASH_REFERENCIA)
    if hash_original == HASH_REFERENCIA:
        print("OK: el hash coincide con el de referencia.")
    else:
        print("AVISO: el hash NO coincide con el de referencia.")

    columnas, filas = leer_filas(ORIGINAL)
    print("Columnas:", len(columnas), columnas)
    print("Filas de datos:", len(filas))

    validas, rechazadas = clasificar(columnas, filas)
    print("Filas validas   :", len(validas))
    print("Filas rechazadas:", len(rechazadas))
    for fila, motivo in rechazadas:
        print("  ", fila["id_envio"], "->", motivo)

    escribir_csv(LIMPIO, columnas, validas)
    escribir_rechazados(RECHAZADOS, columnas, rechazadas)

    hash_limpio = sha256_fichero(LIMPIO)
    print("SHA-256 limpio   :", hash_limpio)

    with open(HASHES, "w", encoding="utf-8", newline="") as f:
        f.write("SHA-256 telemetria_envios.csv (original): " + hash_original + "\n")
        f.write("SHA-256 de referencia (enunciado)       : " + HASH_REFERENCIA + "\n")
        f.write("Coincide con la referencia              : " + str(hash_original == HASH_REFERENCIA) + "\n")
        f.write("SHA-256 telemetria_limpia.csv (nuevo)    : " + hash_limpio + "\n")
    print("Ficheros generados en:", DATOS)


if __name__ == "__main__":
    main()