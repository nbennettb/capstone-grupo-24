# Cómo correr la propuesta en un electroterminal

Un solo comando corre todo en un electroterminal: caso base, Etapa 3, Etapa 4 (relajado y exacto), validación y KPIs.
Se corre desde la **raíz del repositorio**, la carpeta que contiene `scripts/`, `results/` y `data-processed/`.

## 1. Requisitos (una vez por computador)

1. **Python 3.11** con los paquetes:
   ```
   pip install pandas numpy scipy matplotlib tabulate gurobipy psutil
   ```
2. **Licencia académica de Gurobi, personal.** La que viene con `pip` no sirve, porque se limita a 2.000 variables y
   aquí hay millones.
   - Se pide en gurobi.com (Academic Named-User License).
   - Se activa con `grbgetkey <clave>`, conectado a la red UC o a la VPN.
   - Para comprobarla: `python -c "import gurobipy; gurobipy.Model()"` debe decir `Academic license`.
3. **El repositorio completo**, con `data-processed/` (jornadas de la Etapa 2) y `results/caso_base/` (caso base de la
   red completa, contra el que se compara el caso base de cada terminal).

## 2. Antes de correr La Reina (solo Nicolás, una vez)

Las corridas de la entrega 2 quedan guardadas en git y las carpetas viejas se apartan. Se hicieron con la Etapa 3
anterior, así que ya no son comparables, y las sensibilidades de holgura y largo del bloque no se van a usar. En
PowerShell, desde la raíz:
```
git add -A results/instancia_LR scripts docs/contexto_entrega_3
git commit -m "Etapa 4 exacta al minuto: codigo; resultados de La Reina de la entrega 2"
$d = "results/instancia_LR/descartado/entrega2"; New-Item -ItemType Directory -Force $d
Move-Item results/instancia_LR/etapa3/h30, results/instancia_LR/etapa3/h60 $d
Move-Item results/instancia_LR/etapa4/h0_d5, results/instancia_LR/etapa4/h0_d30 $d
Move-Item results/instancia_LR/etapa4/h30_d15, results/instancia_LR/etapa4/h60_d15 $d
Move-Item results/instancia_LR/etapa4/h0_d15/detallado "$d/detallado_h0_d15"
```

## 3. Comando

```
python scripts/correr_terminal.py --terminal 4      # La Reina
python scripts/correr_terminal.py --terminal 1      # Vespucio Norte
python scripts/correr_terminal.py --terminal 2      # El Conquistador
python scripts/correr_terminal.py --terminal 3      # Los Espinos + Santa Rosa
```

Si un paso falla, el script dice cuál y cómo retomar (por ejemplo `--desde 4`), sin repetir lo anterior.

## 4. Tiempos estimados

Son estimaciones a partir de una prueba mediana: 3 a 5 min y 1,1 a 1,7 GB para 1.025 ventanas. Se ajustan después
de la corrida de La Reina.

| Terminal | `--terminal` | Tiempo total | Memoria | Quién |
|---|---|---|---|---|
| La Reina | 4 | ~15 min | ~2,5 GB | Nicolás (primero, para confirmar que todo funciona) |
| Vespucio Norte | 1 | ~10 min | ~2 GB | cualquiera |
| El Conquistador | 2 | ~30 min | ~4 GB | cualquiera |
| Los Espinos + Santa Rosa | 3 | ~1 h | ~6 GB | idealmente un computador con 16 GB de RAM |

Lo que más demora es el paso 4 (plan exacto). Mientras corre no imprime nada; el avance de Gurobi queda en
`results/instancia_<siglas>/etapa4/h0_d15/exacto/gurobi.log`. El modelo exacto tiene un límite de 30 min. Si llega a
ese límite, igual entrega un plan factible y lo informa.

## 5. Qué debe aparecer en pantalla

- En el paso 3, la Etapa 3: `[OK] Cobertura exacta ...` y `[OK] Solucion entera ...`.
- En el paso 4, el plan exacto:
  - `[OK] Programa exacto: maximo N buses cargando a la vez (N puestos) ...`, con N igual a los puestos;
  - `Energia + reservas: ... cota inferior ...: brecha X%`;
  - `[OK] Mejor que la carga por orden de llegada`.
- En el paso 5, la validación: seis líneas `[OK]` y `PLAN DE CARGA FACTIBLE: TODAS LAS VALIDACIONES OK`.
- En el paso 6, los KPIs: `TODAS LAS VALIDACIONES OK` al final.

Si aparece `[AVISO]`, no es un error: es un resultado que se informa (por ejemplo, energía que no cabe en los
puestos). Si aparece `AssertionError` o `FALLA`, no hay que cambiar nada para que pase: se manda el log.

## 6. Qué devolver

Comprimir y enviar la carpeta del terminal: `results/instancia_<siglas>/` (`VN`, `EC`, `LESR` o `LR`). Adentro va
`correr_terminal.log`, con todo lo que se imprimió.

## 7. Si cambia el clustering (Etapa 1)

1. Correr el script de la Etapa 1 que deje el compañero.
2. Correr la Etapa 2 (`6-vsp_asignacion_buses.py`) para los escenarios E0 y E1.
3. Correr el caso base de la red completa (`10-caso_base_carga_reactiva.py --escenario E0` y `--escenario E1`, sin
   `--terminal`), que deja `results/caso_base/`.
4. Repetir la sección 3 para los cuatro terminales.

Los comandos exactos de los pasos 1 a 3 se agregan aquí cuando el compañero cierre el clustering.

## 8. Pruebas chicas (para revisar el código, no son resultados)

```
python scripts/12-etapa3_cortes_reencadenamiento.py --terminal 4 --rutas C09 C10
python scripts/13-etapa4_programacion_carga.py --prueba --puestos-prueba 3
python scripts/13-etapa4_programacion_carga.py --prueba --puestos-prueba 3 --exacto
python scripts/15-validar_plan_carga.py --prueba
```
Escriben en carpetas `*_prueba/` y tardan segundos.
