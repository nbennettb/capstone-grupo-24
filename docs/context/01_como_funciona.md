# Cómo funciona el proyecto

## El problema

RED (Santiago) asigna a cada operador sus recorridos y horarios: 64.502 viajes en un día laboral, que hay que cumplir
tal cual. Nuestra tarea es decidir **cuántos buses eléctricos se necesitan y qué hace cada uno** (qué viajes, cuándo
vuelve al patio y cuándo carga), al menor costo total:

- bus: 250 USD/día;
- km sin pasajeros: 0,5 USD;
- espera: 0,03 USD/min;
- energía: tarifa por hora;
- evento de carga: 5 USD.

Lo que lo hace difícil es la batería: 315 kWh útiles no alcanzan para muchas jornadas, y los 700 puestos de carga de los
5 electroterminales (4 si se cuentan Los Espinos y Santa Rosa como uno) se llenan de noche. Es un **E-VSP** (Electric
Vehicle Scheduling Problem). Para que se pueda resolver se descompone por tipo de decisión: primero la flota, después la
carga.

## El pipeline

```
Etapa 0 Preproceso         64.502 expediciones, distancias de traslado (euclidiana x 1,3 a 20 km/h)
   |
Etapa 1 Rutas -> electroterminal    cada ruta sale, vuelve y carga en uno (el mas cercano a sus paraderos)
   |
Etapa 2 VSP sin batería    flujo de costo minimo en red espacio-tiempo: las jornadas (que bus hace que viajes)
   |          E0: cada ruta con sus buses      E1: interlining dentro del electroterminal
   |
   +--> CASO BASE (no es una etapa): jornadas + carga reactiva + ciclo al 100% con buses de reserva
   |
Etapa 3 Cortes y re-encadenamiento   corta cada jornada donde la bateria no alcanza y re-encadena los tramos
   |                                 por el patio, con recarga completa entre tramos -> ventanas de carga
Etapa 4 Programacion de la carga     cuando carga cada bus, con los puestos y la tarifa (MILP agregado)
```

Cada etapa se corre **una vez** y deja archivos. La siguiente los lee; no vuelve a correr las anteriores.

| Etapa | Script | Produce |
|---|---|---|
| 0 | `3-preprocesamiento_expediciones.py` | `data-processed/expediciones.csv` |
| 1 | `4-clustering_c1.py` (`5-`, `8-`: alternativas y comparación) | `data-processed/rutas_cluster_c1b.csv` |
| 2 | `6-vsp_asignacion_buses.py` (`7-`: comparación) | `data-processed/jornadas_{E0,E1}.csv` |
| Caso base | `10-caso_base_carga_reactiva.py` (`11-`: barrido de niveles) | `results/caso_base/`, `results/instancia_LR/caso_base/` |
| 3 | `12-etapa3_cortes_reencadenamiento.py` | `results/instancia_LR/etapa3/h<h>/` (tramos, cadenas, ventanas) |
| 4 | `13-etapa4_programacion_carga.py` | `results/instancia_LR/etapa4/h<h>_d<Δ>/` (programa de carga por orden de llegada y modelo agregado; con `--detallado`, el modelo detallado en `detallado/`) |
| KPIs y figuras | `14-kpis_instancia.py` | `results/instancia_LR/kpis/`, `results/instancia_LR/informe/` (figuras F0-F6 del informe), `resumen_para_analisis.md` |

Cómo correrlo: `docs/context/03_como_correr.md`. Por qué cada decisión: `docs/context/02_decisiones.md`.

## Caso base y escenarios de evaluación

**Caso base** (la línea base, bajo su propio título):

| Nombre | Qué es |
|---|---|
| Caso base | Jornadas por línea + carga reactiva: cada bus carga cuando lo necesita; si no alcanza, la jornada se parte; si no termina de cargar antes de salir al día siguiente, lo cubre un bus de reserva |
| Caso base con interlining | Lo mismo, con interlining en las jornadas. Aísla el efecto del interlining |

**Escenarios de evaluación** (nuestra propuesta):

| Nombre | Qué cambia respecto del anterior | Qué aísla |
|---|---|---|
| Propuesta con carga por orden de llegada | La Etapa 3 en lugar de la carga reactiva | La Etapa 3 |
| Propuesta completa | La Etapa 4 en lugar de la carga por orden de llegada. En la tabla principal y las figuras es el modelo detallado con bloques de 15 min; el modelo agregado aparece en la validación y las sensibilidades | La Etapa 4 |

Cada escalón cambia una sola cosa. Los KPIs usan las mismas definiciones en todos: costo total desglosado (y el costo
total con espera nocturna), N de buses, % km vacíos, costo medio de la energía, buses extra por batería, reservas por tipo, uso de los
puestos y tiempo de cómputo.

**Diferencia entre la Etapa 3 y el caso base:**

| | Caso base (reactiva) | Etapa 3 |
|---|---|---|
| Cuándo decide | Viaje a viaje | Con la jornada completa a la vista |
| Si la batería no alcanza | Parte la jornada y el bus queda parado el resto del día | Corta donde menos cuesta |
| Después de cargar | El bus queda parado | El bus vuelve a servicio con otro tramo |

## Equivalencias entre siglas internas y nombres

Las siglas solo quedan en el código, las opciones de línea de comandos y los nombres de archivo. Todo lo que lee una
persona (figuras, tablas, CSV de resultados, reportes y estos documentos) usa los nombres.

| Sigla interna | Nombre |
|---|---|
| `E0` | Caso base |
| `E1` | Caso base con interlining |
| `E2-FIFO` | Propuesta con carga por orden de llegada |
| `E2` | Propuesta completa (si hace falta: modelo agregado o modelo detallado) |
| `LB` | Cota inferior de flota (no es operacional) |
| `E0_sep`, `E1_sep` | ... con terminales separados (evidencia para unir Los Espinos y Santa Rosa) |
| `C1` / `C1b`, `C2` | Asignación por cercanía; asignación con capacidad (Etapa 1) |
| `VSP` (en etiquetas) | Jornadas sin batería (Etapa 2) |
| `FIFO` | orden de llegada |
| reservas intermedias / nocturnas | reservas diurnas / reservas nocturnas |
| `h` | holgura de recarga (min), Etapa 3 |
| `Δ`, `Delta` | largo del bloque (min), Etapa 4 |
| `P1` ... `P6` | tramo horario con sus horas (por ejemplo, 00-08 h) |
| costo total comparable / original | costo total / costo total con espera nocturna |
| `LR` | La Reina |

## Por qué la instancia es el terminal La Reina

Después de la Etapa 1, cada electroterminal es un **subproblema independiente**: sus rutas solo se encadenan entre sí,
sus buses salen, vuelven y cargan ahí, y sus puestos no se comparten. Un terminal completo es entonces un problema real
y completo: sus viajes, sus buses y sus 100 puestos, sin escalar puestos ni muestrear jornadas. El caso base filtrado a
La Reina reproduce exactamente la corrida de la red completa filtrada (Caso base 1.333 → 1.726 buses y 319 reservas; Caso base con interlining 1.203 →
1.638 y 315), y esa igualdad lo prueba.

La Reina es el **terminal congestionado más chico**: la energía que necesita es el 80% de su capacidad de 24 h y el caso
base necesita 315 buses de reserva. Así, la Etapa 3 tiene jornadas que partir y la Etapa 4 tiene que decidir entre tarifa
y reservas. Vespucio Norte se descarta: sin congestión (3 reservas), la Etapa 4 se reduciría a cargar en la hora más
barata. **La red completa (los 4 terminales) queda para la entrega final**: es el mismo código, terminal por terminal
(`--terminal`).
