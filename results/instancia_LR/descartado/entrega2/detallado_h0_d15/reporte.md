# Etapa 4 - Modelo detallado, La Reina (holgura 0 min, largo del bloque 15 min, 100 puestos)

- Detallado: 109,040.58 USD = energia + reservas 100,665.58 + eventos 8,375.00; 217 reservas; limite de tiempo; brecha 0.658% (cota valida (LP del agregado + un evento por ventana)); 3,605 s.
- Agregado (misma carpeta): energia + reservas 100,905.49 USD; con sus eventos contados despues: 130,235.49 USD; 218 reservas.
- Propuesta con carga por orden de llegada: 173,204.72 USD con eventos; el detallado la supera.
- Realizacion por minuto del detallado: 32 minutos sobre los puestos (maximo 115.00).

## Fases

|   holgura_min |   delta_min | modelo                                 | estado           |   objetivo_usd |   cota_usd |   brecha | fuente_brecha                                         |   segundos |   variables |   binarias |   restricciones |   cota_gurobi_usd |   brecha_gurobi |   cota_valida_usd |   segundos_fase2 | inicio_fase2             |   supera_fifo |   desempate_usd |   eventos_usd |
|--------------:|------------:|:---------------------------------------|:-----------------|---------------:|-----------:|---------:|:------------------------------------------------------|-----------:|------------:|-----------:|----------------:|------------------:|----------------:|------------------:|-----------------:|:-------------------------|--------------:|----------------:|--------------:|
|             0 |          15 | Modelo detallado, fase 1 (reservas fijas) | limite de tiempo |         110653 |     105825 | 0.043684 | Gurobi, con las reservas fijas                        |    1506.46 |      482122 |     160720 |          478938 |               nan |      nan        |               nan |           nan    | nan                      |           nan |        nan      |           nan |
|             0 |          15 | Modelo detallado (MILP)                    | limite de tiempo |         109041 |     108329 | 0.006581 | cota valida (LP del agregado + un evento por ventana) |    3605.12 |      482122 |     160720 |          478938 |            105379 |        0.033631 |            108329 |          2098.66 | la solucion de la fase 1 |             1 |          5.9506 |          8375 |

## Archivos
- `programa_E2_detallado.csv`, `resumen.csv`, `modelo.csv`, `ocupacion_minutos.csv`, `ocupacion_bloques.csv`, `energia_por_tarifa.csv`, `ocupacion_24h.png` (+ .csv), `gurobi_fase1.log`, `gurobi_fase2.log`.