# **ICS2122 – Taller de Investigación Operativa (Capstone)** 

# **Planificación de la operación de los buses eléctricos en la Red Metropolitana de Movilidad de Santiago** 

# **Contexto** 

La Red Metropolitana de Movilidad de Santiago constituye uno de los sistemas de transporte público más grandes de América Latina y cuenta con una de las flotas de buses eléctricos más extensas fuera de Asia. La operación diaria de esta red involucra miles de viajes programados, múltiples recorridos, terminales y electroterminales distribuidos en toda el área metropolitana. 

La incorporación masiva de buses eléctricos ha generado nuevas oportunidades para avanzar hacia sistemas de transporte más sostenibles, pero también ha introducido importantes desafíos operacionales y energéticos. A diferencia de los buses convencionales, los vehículos eléctricos poseen una autonomía limitada y requieren acceder periódicamente a infraestructura de carga para mantener la continuidad del servicio. 

La planificación de la operación diaria de una flota de buses eléctricos requiere coordinar decisiones de transporte y energía de manera simultánea. Cada vehículo debe ejecutar una secuencia de viajes programados respetando horarios, autonomía de batería y disponibilidad de infraestructura de carga. Además, los desplazamientos sin pasajeros entre terminales, electroterminales y puntos de inicio de servicio generan costos operacionales que deben ser considerados durante la planificación. 

Por otra parte, la capacidad de los electroterminales es limitada. Cada instalación dispone de un número finito de cargadores y de una capacidad eléctrica restringida, por lo que no todos los buses pueden ser cargados simultáneamente. Una planificación inadecuada puede provocar congestión en la infraestructura de carga, mayores tiempos de espera para los vehículos, incrementos en los costos energéticos y dificultades para mantener la continuidad operacional de la red. 

A lo largo de la jornada, cada viaje programado debe ser atendido por algún vehículo disponible, evitando duplicidades u omisiones. Sin embargo, la asignación de viajes no puede realizarse de manera arbitraria: un bus sólo podrá continuar con una actividad posterior si dispone de tiempo suficiente para finalizar su servicio actual, desplazarse hasta el nuevo punto de inicio y comenzar el siguiente viaje respetando los horarios programados. De esta forma, la secuencia de actividades asignadas a cada vehículo debe corresponder a una cadena operacional físicamente factible. 

Al mismo tiempo, la energía almacenada en las baterías impone restricciones que no existen en flotas convencionales. Cada vehículo consume energía a medida que opera, 

por lo que las decisiones de asignación deben asegurar que ningún bus quede sin capacidad suficiente para completar los servicios comprometidos. Cuando la energía disponible se aproxima a niveles críticos, el plan debe considerar oportunamente visitas a electroterminales para efectuar recargas antes de continuar operando. 

Estas recargas tampoco pueden programarse libremente. Los buses compiten por una infraestructura compartida cuya capacidad es limitada, por lo que múltiples vehículos pueden requerir acceso a los mismos cargadores en períodos similares del día. Como consecuencia, la planificación debe distribuir adecuadamente las actividades de carga para evitar sobreutilización de los electroterminales y garantizar que la demanda de energía se mantenga dentro de los límites operacionales de la infraestructura disponible. 

La localización geográfica de terminales, electroterminales y recorridos también juega un papel fundamental. Los buses deben desplazarse continuamente por la ciudad para iniciar servicios, finalizar operaciones o acceder a puntos de recarga. Estos movimientos sin pasajeros generan tiempos y costos adicionales que afectan la eficiencia global del sistema. Una solución atractiva desde el punto de vista energético puede resultar poco eficiente si obliga a realizar grandes desplazamientos vacíos. 

Finalmente, la operación debe desarrollarse utilizando una flota finita de vehículos. Las decisiones de programación influyen directamente en la cantidad de buses necesarios para cubrir la demanda diaria, en la utilización de la infraestructura de carga y en los costos totales de operación. Por esta razón, el problema involucra una fuerte interacción entre recursos de transporte, recursos energéticos y restricciones espacio-temporales de gran complejidad. 

# **Objetivo** 

El propósito del proyecto es estudiar cómo la planificación integrada de transporte y energía afecta el desempeño de sistemas de transporte público electrificados, y evaluar el valor de las herramientas de Investigación Operativa, optimización, simulación, analítica y ciencia de datos para diseñar planes de operación eficientes, escalables y sostenibles para la Red Metropolitana de Movilidad de Santiago. Los equipos podrán proponer distintas metodologías de solución, incluyendo modelos exactos, heurísticas, metaheurísticas, enfoques híbridos o estrategias de descomposición, siempre que sean capaces de generar planes operacionales factibles y justificar adecuadamente las decisiones de modelamiento adoptadas. 

