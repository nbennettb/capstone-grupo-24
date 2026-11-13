# Etapa 3 - Cortes y re-encadenamiento, Los Espinos + Santa Rosa (jornadas Caso base con interlining, holgura 0 min)

## Diagnostico de flota

| paso                             |   buses | que_mide                                                            |
|:---------------------------------|--------:|:--------------------------------------------------------------------|
| (i) Jornadas sin bateria                          |    3204 | Punto de partida: una jornada = un bus                              |
| (ii) Reuso del patio sin bateria |    3157 | Jornadas enteras re-encadenadas por el patio, sin tiempo de recarga |
| (iii) Solo cortes                |    4623 | Cada tramo un bus                                                   |
| (iv) Cortes + re-encadenamiento  |    3280 | La Etapa 3 completa (recarga completa + holgura 0 min)              |

## Cifras

- Tramos: 4,623 (1,413 de 3,204 jornadas se cortan); km extra por los cortes: 19,164.3 km.
- Energia: 989.35 MWh en los tramos (VSP: 962.52 MWh).
- Ventanas de carga: 1,343 diurnas y 3,280 nocturnas. Holgura mediana de las diurnas: 136 min; de las nocturnas: 345 min.
- Ventanas nocturnas que no alcanzan la recarga completa ni con puesto libre: 194; de ellas 151 son cadenas de mas de 24 h (el flujo, como el VSP, es de un dia y no ciclico). La Etapa 4 las cubre con un bus de reserva, la misma regla del caso base.

## Validaciones (todas pasaron)
- Reconstruccion de las jornadas = VSP (kWh por jornada).
- Cobertura exacta de cada expedicion del terminal.
- Cada tramo factible al revisarlo paso a paso (SOC >= minimo y puede volver al patio).
- Solucion del flujo entera; cadenas factibles en tiempo.
- Flota del flujo = numero de cadenas = maximo de intervalos [salida, listo) superpuestos.
- Balance de energia: tramos = VSP + km extra; ventanas = tramos.

## Tiempo y memoria
- Corte: 0.94 s | flujo: 0.23 s | total: 2.5 s | pico de memoria: 192 MB.

## Archivos
- `tablas/tramos.csv`: un tramo por fila (bus, jornada del VSP, expediciones, km, kWh, salida, llegada y listo).
- `tablas/cadenas.csv`: los tramos de cada bus en orden.
- `tablas/ventanas.csv`: ventanas de carga (llegada, hora limite, kWh, holgura) = entrada de la Etapa 4.
- `tablas/diagnostico_flota.csv`, `tablas/resumen.csv`.
- `graficos/gantt_cadenas.png` (+ .csv): cadenas con mas tramos.
- `graficos/llegadas_patio_por_hora.png` (+ .csv): llegadas al patio por hora.