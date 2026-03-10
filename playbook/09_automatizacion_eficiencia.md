# 09 · Automatización y Eficiencia en Customer Ops

## Principio

Automatizar no es eliminar agentes — es eliminar el trabajo repetitivo
para que los agentes puedan centrarse en lo que realmente importa:
resolver problemas complejos y construir relaciones con clientes.

**Regla de oro:** Automatiza primero lo que más se repite y menos
valor aporta. Nunca automatices lo que requiere empatía real.

---

## Framework de Automatización: Los 3 Niveles

### Nivel 1 — Automatización de Tareas Repetitivas
Eliminar trabajo manual sin valor añadido.

**Ejemplos:**
- Asignación automática de tickets por idioma, región o categoría
- Respuestas automáticas de confirmación de recepción
- Cierre automático de tickets sin respuesta del cliente (7 días)
- Actualización automática de campos (tier de cliente, prioridad)
- Notificaciones de SLA breach

### Nivel 2 — Automatización de Flujos de Trabajo
Orquestar secuencias de acciones sin intervención humana.

**Ejemplos:**
- Flujo de escalado T1 → T2 con notificación automática
- Envío automático de encuesta CSAT post-cierre
- Re-apertura automática si el cliente responde tras cierre
- Flujo de onboarding de nuevo cliente (emails secuenciales)
- Alertas de churn basadas en comportamiento del cliente

### Nivel 3 — Automatización Inteligente (IA)
Usar inteligencia artificial para resolver o clasificar tickets.

**Ejemplos:**
- Clasificación automática de tickets por categoría y prioridad
- Sugerencia de respuesta al agente basada en tickets similares
- Detección de sentimiento negativo para priorización
- Chatbot para resolución de consultas frecuentes (T4/P4)
- Resumen automático de tickets largos para escalado

---

## Automatizaciones Prioritarias en Zendesk

### Las 10 Automatizaciones de Mayor Impacto

**1. Auto-asignación por idioma**
```
Trigger: Ticket creado
Condición: Idioma detectado = ES / PT / FR / DE / JP
Acción: Asignar a grupo región correspondiente
```

**2. SLA Warning al 80%**
```
Trigger: Tiempo de ticket = 80% del SLA
Acción: Notificar al agente asignado + Team Lead vía Slack
```

**3. Escalado automático por inactividad**
```
Trigger: Ticket P1/P2 sin respuesta en 2h
Acción: Reasignar al Team Lead + notificación urgente
```

**4. CSAT automático post-cierre**
```
Trigger: Ticket cerrado
Condición: Canal = email
Acción: Enviar encuesta CSAT 2h después del cierre
```

**5. Re-apertura inteligente**
```
Trigger: Cliente responde a ticket cerrado
Condición: Hace <7 días del cierre
Acción: Re-abrir ticket y asignar al agente original
```

**6. Prioridad VIP automática**
```
Trigger: Ticket creado
Condición: Organización tiene tag "platinum"
Acción: Prioridad = Urgente + Asignar a cola VIP
```

**7. Clasificación por palabras clave**
```
Trigger: Ticket creado
Condición: Asunto contiene "factura" / "pago" / "contrato"
Acción: Tag = billing + Asignar a grupo billing
```

**8. Aviso de renovación próxima**
```
Trigger: Fecha de renovación en Salesforce < 30 días
Acción: Notificar al CSM + Tag "renewal-risk" en tickets del cliente
```

**9. Cierre por inactividad del cliente**
```
Trigger: Ticket en estado "Pendiente cliente" > 7 días sin respuesta
Acción: Email automático de aviso + cierre en 48h si no responde
```

**10. Resumen diario de cola**
```
Trigger: Cada día a las 08:00 hora local de cada región
Acción: Post automático en #ops-handover con tickets abiertos P1/P2
```

---

## Chatbots y IA Conversacional

### Cuándo tiene sentido un chatbot

Un chatbot aporta valor cuando:
- El 30%+ del volumen son consultas FAQ repetitivas
- Tienes base de conocimiento bien mantenida
- Los clientes aceptan el autoservicio (B2C más que B2B enterprise)
- El equipo tiene capacidad de mantener el bot actualizado

Un chatbot NO tiene sentido cuando:
- Los clientes siempre piden hablar con un humano
- Las consultas son mayoritariamente complejas y únicas
- No tienes recursos para mantener el contenido actualizado
- La experiencia de marca requiere toque humano (premium/luxury)

### Arquitectura recomendada

```
Cliente contacta
      ↓
Chatbot — ¿Consulta frecuente? 
      ↓ SÍ → Responde automáticamente → CSAT
      ↓ NO → Crea ticket con contexto → Agente humano
```

**Tasa de contención objetivo:** 20–35% del volumen total
(por encima puede indicar que el bot frustra a clientes que necesitan humanos)

### Herramientas de IA para soporte

- **Zendesk AI / Fin (Intercom):** Resolución automática con IA generativa
- **Ada / Tidio:** Chatbots configurables sin código
- **Forethought:** IA de triage y clasificación de tickets
- **Assembled AI:** Forecasting inteligente de volumen

---

## Métricas de Eficiencia Operacional

### Indicadores de Automatización

| Métrica | Descripción | Target |
|---|---|---|
| Automation Rate | % tickets con al menos una acción automática | >60% |
| Bot Containment Rate | % consultas resueltas por chatbot sin humano | 20–35% |
| Auto-assignment Accuracy | % tickets bien asignados automáticamente | >90% |
| Time Saved per Agent | Horas/semana liberadas por automatización | >5h |

### Indicadores de Eficiencia del Equipo

| Métrica | Descripción | Target |
|---|---|---|
| Tickets per Agent per Day | Productividad individual | Benchmark por tipo |
| Handle Time (AHT) | Tiempo medio de gestión por ticket | Reducción trimestral |
| Cost per Ticket | Coste operativo por ticket resuelto | Reducción anual >10% |
| Self-Service Rate | % problemas resueltos sin contactar soporte | >30% |

---

## Roadmap de Automatización: Cómo Priorizar

### Matriz de Priorización

```
         ALTO IMPACTO
              |
  Hacer ya   |   Planificar
(quick wins) |   (proyectos)
─────────────┼─────────────
  Descartar  |   Analizar
             |
         BAJO IMPACTO
    BAJO          ALTO
   ESFUERZO     ESFUERZO
```

**Proceso de priorización:**
1. Listar todas las tareas manuales repetitivas del equipo
2. Estimar tiempo total consumido por semana (toda la región)
3. Estimar esfuerzo de implementación (horas de configuración)
4. Priorizar por ratio impacto/esfuerzo
5. Implementar en sprints de 2 semanas, medir resultado

---

## Eficiencia sin Automatización: Quick Wins

No todo requiere automatización. Hay mejoras de eficiencia inmediatas:

**1. Macros y templates bien mantenidos**
→ Las 20 respuestas más frecuentes como macros en Zendesk.
Ahorra 3–5 min por ticket. Con 50 tickets/día = >2h ahorradas.

**2. Base de conocimiento actualizada**
→ Los agentes encuentran la solución en 1 min en lugar de 10.
Requiere mantenimiento semanal por el Team Lead.

**3. Atajos de teclado y snippets**
→ Herramientas como TextExpander o los snippets nativos del navegador
para insertar texto frecuente con 2-3 teclas.

**4. Flujos de trabajo documentados para los T10 problemas**
→ Un decision tree para los 10 problemas más frecuentes.
El agente sigue el árbol sin tener que pensar desde cero.

**5. Reuniones eficientes**
→ Stand-up diario de 15 min máximo. Sin reuniones sin agenda.
Cada reunión con output concreto documentado.

---

## Errores Comunes en Automatización

**Error 1: Automatizar antes de entender el proceso**
→ Primero mapea el proceso manualmente, luego automatiza.
Un proceso roto automatizado es un desastre a escala.

**Error 2: Olvidar mantener las automatizaciones**
→ Una automatización desactualizada crea más trabajo del que ahorra.
Revisar y auditar automatizaciones cada trimestre.

**Error 3: Automatizar la empatía**
→ Los clientes detectan cuando una respuesta es un bot.
En momentos de frustración, el toque humano es irreemplazable.

**Error 4: No medir el impacto de las automatizaciones**
→ Implementar una automatización sin antes definir cómo vas a medir
su impacto es desperdiciar el aprendizaje.

**Error 5: Implementar todo a la vez**
→ Una automatización por sprint. Si algo sale mal, sabes exactamente qué.
