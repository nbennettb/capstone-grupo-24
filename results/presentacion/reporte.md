# Graficos para la presentacion (Entrega 2)

Versiones simplificadas para las laminas (ver `docs/presentacion/plan_presentacion.md`). Cada grafico tiene su CSV en `tablas/`.

| Grafico | Lamina | Mensaje |
|---|---|---|
| `graficos/G1_demanda_y_tarifa.png` | 1 | Los buses se necesitan de dia; solo pueden cargar de noche, cuando la tarifa es mas baja |
| `graficos/G2_ida_vuelta.png` | 2 | 94,7% de las rutas cierra su ida y vuelta a < 500 m: se agrupan rutas |
| `graficos/G3_mapa_electroterminales.png` | 2 | Los Espinos y Santa Rosa a 1,1 km: un solo electroterminal de 270 puestos |
| `graficos/G4_diagrama_metodologia.png` | 3 | Cuatro etapas por tipo de decision, cada una con su validacion |
| `graficos/G5_patio_vs_puestos.png` | 8 | De noche los buses estan en el patio y los puestos se llenan |
| `graficos/G6_barrido.png` | 9 | 100% con reservas es el menor costo factible |
| `graficos/G7_reservas_milp.png` | 10 | El MILP reduce las reservas y queda cerca del piso (instancia reducida) |

## Archivos

- `tablas/G1_demanda_y_tarifa.csv`: maximo de expediciones en curso por hora (modulo 24 h).
- `tablas/G2_ida_vuelta.csv`: histograma de la distancia fin de ida - inicio de vuelta.
- `tablas/G3_distancias_electroterminales.csv`: distancia entre cada par de electroterminales.
- `tablas/G4_diagrama_metodologia.csv`: contenido de cada caja del diagrama.
- `tablas/G5_patio_vs_puestos.csv`: % y numero de buses en el patio y cargando, por hora (E1, 100%).
- `tablas/G6_barrido.csv`: costo por nivel de bateria (E1).
- `tablas/G7_reservas_milp.csv`: reservas, ganancia y brecha por tamano de instancia.