# Práctica Sesión 11: integridad del dato e ingesta en HDFS

Módulos 5075 y 5074. Telemetría logística: verificación con SHA-256, saneado del dataset e ingesta en HDFS (Hadoop 3.4.0 en Docker).

## Estructura del repositorio

```
datos/        dataset original, limpio, rechazados y hashes
scripts/      calidad_dataset.py (hashes + saneado, reproducible)
evidencias/   capturas de pantalla
docker-compose.yml
```

## 1. Hashes SHA-256 antes y después del saneado

| Fichero | SHA-256 |
|---|---|
| `telemetria_envios.csv` (original) | `4471c18a0284b3aa5b32a0713e691e3c7fcadae402f105e901c7c57f49474911` |
| Hash de referencia del enunciado | `4471c18a0284b3aa5b32a0713e691e3c7fcadae402f105e901c7c57f49474911` |
| `telemetria_limpia.csv` (tras el saneado) | `f7af6b30a4067ea69c553a47db90d133380a9127224bf0c1fce830ddca58afae` |

El hash del original **coincide** con el de referencia, lo que confirma que el fichero de partida no ha sido alterado. El hash del limpio es distinto, como debe ser: al eliminar filas cambia el contenido.

### Saneado aplicado

El script lee todo como texto (sin pandas, para no alterar ningún valor) y escribe UTF-8 sin BOM con saltos LF. De 300 filas quedan **292 limpias** y **8 rechazadas**:

| Regla | Filas rechazadas |
|---|---|
| Duplicado exacto (se conserva la primera aparición) | ENV-2026-1012, ENV-2026-1078 |
| Nulo en `temp_celsius` | ENV-2026-1015 |
| Nulo en `peso_kg` | ENV-2026-1067 |
| Nulo en `destino` | ENV-2026-1189 |
| Peso <= 0 (-45.50) | ENV-2026-1088 |
| Temperatura fuera de [-30, 40] (98.4) | ENV-2026-1142 |
| Estado fuera de {ENTREGADO, EN_TRANSITO, EN_REPARTO, INCIDENCIA_REPARTO} | ENV-2026-1210 |

Las filas rechazadas, con su motivo, quedan en `datos/telemetria_rechazados.csv`.

### Nota sobre la integridad del dato

Al empezar solo se disponía de `telemetria_envios.xlsx` (SHA-256 `9ae5d0a2ccad70cb5466bb4717563d7c71a42be13a5cde7b431ddffbe964e655`) y de un CSV exportado desde Excel (SHA-256 `317f5047ddc0407b36fe4b8af54b919e5a2f815555c5c1b0c176cff4e0df0181`). Ninguno coincidía con la referencia: Excel había convertido temperaturas en fechas, había perdido el punto decimal de las coordenadas (`36.64536` pasaba a `3.664.536`) y había cambiado los saltos de línea y la codificación. Ese es un ejemplo práctico de por qué se compara el hash antes de trabajar con un fichero. El CSV original se obtuvo después y su hash sí coincide.

### Reproducir

```
python scripts/calidad_dataset.py
```

Genera `telemetria_limpia.csv`, `telemetria_rechazados.csv` y `hashes_sha256.txt` en `datos/`, y avisa si el hash del original no coincide con el de referencia.
