# 08 · Quality Assurance (QA) en Soporte

## Principio

El QA no es una auditoría para castigar errores — es un sistema de mejora
continua. Su objetivo es identificar patrones, elevar el estándar del equipo
y proteger la experiencia del cliente.

**Regla de oro:** El QA mide la calidad del proceso, no la inteligencia
del agente. Un error sistemático es un fallo de proceso, no de persona.

---

## Framework de QA: Las 4 Dimensiones

Todo ticket evaluado se puntúa en 4 dimensiones:

### 1. Resolución del Problema (40%)
¿El agente resolvió correctamente el problema del cliente?

| Criterio | Puntuación |
|---|---|
| Problema resuelto completamente en el primer contacto | 100% |
| Problema resuelto pero requirió seguimiento evitable | 70% |
| Problema parcialmente resuelto, workaround dado | 50% |
| Escalado correcto con diagnóstico completo | 90% |
| Escalado incorrecto o sin diagnóstico | 20% |
| Problema no resuelto y sin escalado correcto | 0% |

### 2. Comunicación y Tono (20%)
¿El agente se comunicó de forma clara, empática y profesional?

**Criterios positivos:**
- Saludo y cierre personalizados
- Empatía genuina ante frustración del cliente
- Lenguaje claro sin tecnicismos innecesarios
- Respuesta adaptada al perfil del cliente (técnico vs no técnico)
- Proactividad: informa al cliente antes de que pregunte

**Criterios negativos (penalizan):**
- Tono defensivo o distante
- Respuesta genérica que no aborda el problema específico
- Errores ortográficos o gramaticales graves
- Promesas incumplidas sin seguimiento

### 3. Adherencia a Proceso (20%)
¿El agente siguió los procesos establecidos?

- Uso correcto de prioridades y SLA
- Escalado siguiendo la matriz definida
- Actualización correcta del ticket (campos, tags, categoría)
- Seguimiento en los plazos comprometidos
- Uso de templates y macros cuando aplica

### 4. Documentación del Ticket (20%)
¿El ticket queda correctamente documentado para el equipo?

- Descripción clara del problema en las notas internas
- Pasos de diagnóstico documentados
- Información del entorno registrada (versión, OS, etc.)
- Próximo paso o estado actual claro para cualquier agente que tome el ticket

---

## Proceso de Evaluación QA

### Selección de Tickets para Revisión

**Muestra mínima recomendada:**
- Agentes en onboarding (días 1–90): 5 tickets/semana
- Agentes senior: 2–3 tickets/semana
- Post-DSAT: 100% de tickets con valoración negativa
- Post-escalado: 20% de tickets escalados a T2+

**Selección estratégica:**
- Incluir siempre tickets de diferentes canales (email, chat, teléfono)
- Incluir tickets resueltos Y tickets escalados
- Incluir al menos 1 ticket complejo por agente por semana

### Rúbrica de Puntuación

```
Quality Score = (Resolución × 0.40) + (Comunicación × 0.20) 
              + (Proceso × 0.20) + (Documentación × 0.20)
```

**Escala:**
- 90–100%: Excelente — compartir como ejemplo de buena práctica
- 75–89%: Bueno — cumple estándar, pequeñas mejoras
- 60–74%: Necesita mejora — coaching individual
- <60%: Crítico — plan de acción inmediato

### Calibración de QA

**Problema:** Sin calibración, dos evaluadores dan puntuaciones diferentes
al mismo ticket. Esto destruye la credibilidad del programa.

**Solución: Sesiones de calibración mensuales**
1. Seleccionar 3–5 tickets representativos
2. Cada evaluador puntúa de forma independiente
3. Comparar resultados y discutir discrepancias
4. Actualizar la rúbrica si hay ambigüedad sistemática
5. Documentar los criterios acordados

**Target de consistencia:** Diferencia máxima de 10 puntos entre
evaluadores en el mismo ticket.

---

## Feedback al Agente

### Principios del Feedback de QA

1. **Específico, no genérico:** "En la línea 3 de tu respuesta, el tono
   fue defensivo porque..." mejor que "tu comunicación puede mejorar".

2. **Balanceado:** Siempre reconocer lo que salió bien antes de lo que
   debe mejorar. Ratio recomendado: 2 positivos por cada crítica.

3. **Accionable:** El agente debe saber exactamente qué hacer diferente
   la próxima vez.

4. **Oportuno:** El feedback pierde valor con el tiempo. Máximo 48–72h
   desde la evaluación del ticket.

### Sesión de Feedback 1:1

**Estructura (30 minutos):**
1. El agente autoevalúa el ticket antes de la sesión (5 min)
2. Comparar autoevaluación con evaluación del QA (10 min)
3. Discutir 1–2 áreas de mejora concretas (10 min)
4. Acordar próximos pasos y objetivo para la semana siguiente (5 min)

**Por qué la autoevaluación primero:**
- El agente que identifica su propio error aprende más que el que lo recibe
- Reduce la defensividad en la conversación
- Desarrolla el criterio propio del agente a largo plazo

---

## QA a Nivel de Equipo

### Tendencias que requieren acción inmediata

- **QA Score del equipo cae >5 puntos en 2 semanas consecutivas**
  → Revisar si hay cambio de proceso, herramienta o volumen inusual

- **Error sistemático en la misma dimensión en >30% del equipo**
  → El problema es de formación o proceso, no individual

- **DSAT correlacionado con agente específico**
  → Intervención individual urgente antes de que impacte el CSAT global

### Reporting de QA

**Vista semanal (Team Lead):**
- QA Score promedio del equipo
- Top 3 errores más frecuentes esta semana
- Agentes por debajo del target (<75%)

**Vista mensual (Ops Manager):**
- Tendencia de QA Score por agente y equipo
- Correlación QA Score vs CSAT
- Impacto de formaciones en QA Score
- Comparativa entre regiones

---

## QA para Equipos Internacionales

**Desafío:** Los criterios de calidad pueden interpretarse diferente
en distintas culturas y contextos lingüísticos.

**Soluciones:**
- Rúbrica traducida y adaptada por región (no solo traducida)
- Evaluadores de QA nativos del idioma que evalúan
- Calibraciones cross-región trimestrales (ver cap. 01)
- Ejemplos de tickets de referencia en cada idioma

---

## Métricas de QA

| Métrica | Descripción | Target |
|---|---|---|
| QA Score promedio | Puntuación media del equipo | >85% |
| DSAT Rate | % tickets con valoración negativa | <5% |
| QA Coverage | % tickets evaluados sobre total | >10% |
| Calibration Score | Consistencia entre evaluadores | <10 puntos de diferencia |
| Improvement Rate | % agentes que mejoran QA mes a mes | >70% |

---

## Errores Comunes en QA

**Error 1: Usar el QA solo para detectar errores, no para reconocer excelencia**
→ Compartir ejemplos de tickets excelentes tiene más impacto en la cultura
que solo señalar los malos.

**Error 2: QA sin calibración**
→ Si dos evaluadores dan puntuaciones radicalmente diferentes,
los agentes pierden confianza en el sistema.

**Error 3: Evaluar solo velocidad, no calidad real**
→ Un ticket cerrado en 5 minutos con DSAT vale menos que uno cerrado
en 30 minutos con CSAT positivo.

**Error 4: No cerrar el loop con formación**
→ Si el QA identifica sistemáticamente el mismo error y no se hace
una sesión de formación, el programa pierde sentido.
