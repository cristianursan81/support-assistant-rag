# 03 · Procesos de Escalado

## Principio Base

Un escalado bien gestionado no es un fallo del equipo — es el sistema
funcionando correctamente. El objetivo es resolver en el nivel adecuado,
en el tiempo correcto, con la información correcta.

**Regla de oro:** Escala el problema, nunca al cliente.

---

## Matriz de Severidad

| Prioridad | Definición | Ejemplo | SLA Respuesta | SLA Resolución |
|---|---|---|---|---|
| **P1 - Critical** | Sistema caído, impacto total en cliente | Producción inaccesible | 15 min | 4h |
| **P2 - High** | Funcionalidad crítica degradada | Fallo en módulo de pagos | 1h | 8h |
| **P3 - Medium** | Impacto parcial, workaround disponible | Informe no genera correctamente | 4h | 3 días |
| **P4 - Low** | Consulta, mejora, sin impacto operativo | ¿Cómo exporto a CSV? | 8h | 5 días |

---

## Tipos de Escalado

### 1. Escalado Funcional (Tier Escalation)
- **T1 → T2:** El agente no puede resolver técnicamente. Requiere acceso
  a sistemas backend o conocimiento especializado.
- **T2 → T3:** Problema requiere desarrollo, análisis de ingeniería o acceso
  a infraestructura.
- **Criterio de escalado:** No resolución en el 70% del SLA o complejidad técnica definida.

### 2. Escalado Jerárquico (Management Escalation)
- **Cuándo:** Cliente insatisfecho después de 2+ interacciones, amenaza de churn,
  cliente VIP/enterprise sin resolución, comunicación legal o contractual.
- **Quién decide:** El Team Lead, no el agente.
- **Proceso:** Team Lead notifica al Manager. Manager contacta al cliente en <2h.

### 3. Escalado de Urgencia (Proactive Escalation)
- El agente detecta que el impacto real es mayor que la prioridad asignada.
- **Ejemplo:** Cliente reporta P3 pero el análisis revela que afecta a 500 usuarios.
- **Acción:** Re-priorizar a P1/P2 sin esperar al cliente. Notificar proactivamente.

---

## Proceso Paso a Paso: Escalado Funcional T1 → T2

1. **Diagnóstico previo (obligatorio antes de escalar)**
   - El agente T1 debe documentar: qué pasos ejecutó, qué resultado obtuvo,
     qué información ya tiene del cliente.
   - Sin diagnóstico = escalado rechazado por T2.

2. **Transferencia de información**
   - Actualizar el ticket con: entorno, versión, logs relevantes, pasos reproducibles.
   - Etiquetar con prioridad correcta y tipo de problema.

3. **Notificación al cliente**
   - Antes de escalar, informar al cliente: "Estoy escalando tu caso a nuestro
     equipo técnico especializado. Te contactarán en [tiempo según SLA]."

4. **Handover interno**
   - Mencionar directamente al agente T2 en el ticket + Slack/Teams si es P1/P2.
   - Para P3/P4: asignación estándar en la cola.

5. **Seguimiento (ownership del T1)**
   - El agente T1 mantiene la relación con el cliente aunque T2 lleve el técnico.
   - Update al cliente cada 24h en P2, cada 48h en P3.

---

## Escalado para Clientes Premium / Enterprise

Los clientes con SLA premium tienen un circuito de escalado diferenciado:

- **CSM (Customer Success Manager) asignado:** Primera llamada de contacto en P1/P2.
- **Slack Connect / canal dedicado:** Comunicación directa sin pasar por tickets.
- **Escalado a Product/Engineering:** Acceso directo cuando el bug impacta en
  renovación o contrato.
- **Revisión Post-Incidente (PIR):** Documento formal de causa raíz + plan de acción
  entregado al cliente en 48–72h tras resolución de P1.

---

## Métricas de Escalado

| Métrica | Descripción | Target |
|---|---|---|
| Escalation Rate | % tickets escalados de T1 a T2+ | <20% |
| Wrong Escalation Rate | % escalados que T2 devuelve por falta de diagnóstico | <10% |
| Escalation Resolution Time | Tiempo desde escalado hasta resolución en T2 | <SLA definido |
| Management Escalation Rate | % escalados a management | <2% |

---

## Errores Frecuentes en Escalado

- **Escalar demasiado pronto:** El agente no intenta resolver por falta de confianza.
  → Solución: Umbral claro de cuándo escalar (70% SLA o criterio técnico).

- **Escalar sin información:** T2 recibe el ticket sin contexto suficiente.
  → Solución: Checklist de transferencia obligatorio antes de escalar.

- **Perder el ownership:** El agente T1 escala y "desaparece" del cliente.
  → Solución: T1 es siempre el punto de contacto con el cliente, T2 es back-end.

- **No actualizar al cliente durante el escalado:**
  → Solución: Template de actualización automática cada N horas según SLA.
