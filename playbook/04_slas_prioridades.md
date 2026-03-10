# 04 · SLAs y Gestión de Prioridades

## ¿Qué es un SLA?

Un **Service Level Agreement (SLA)** es el contrato de tiempo de respuesta
y resolución acordado con el cliente. Incumplir un SLA tiene consecuencias
comerciales (penalizaciones, créditos de servicio) y de confianza.

Distinguir:
- **SLA externo:** Comprometido con el cliente en contrato
- **SLA interno (OLA):** Target del equipo para cumplir el SLA externo con margen

**Regla:** El OLA interno siempre debe ser el 70–80% del SLA externo para tener
margen ante imprevistos.

---

## Estructura de SLAs por Tier de Cliente

### Tier Platinum (Enterprise / Top 20 clientes)
- FRT: 15 min (24/7)
- Resolución P1: 4h, P2: 8h, P3: 2 días, P4: 5 días
- Canal dedicado (Slack Connect o Zoom directo)
- CSM asignado
- Revisión QBR trimestral

### Tier Gold (Mid-market)
- FRT: 1h (horario laboral) / 4h (fuera de horario)
- Resolución P1: 8h, P2: 24h, P3: 3 días, P4: 7 días
- Email + portal de tickets

### Tier Silver (SME / Self-service)
- FRT: 4h (horario laboral)
- Resolución P1: 24h, P2: 3 días, P3: 7 días, P4: 14 días
- Portal de tickets + base de conocimiento

---

## Gestión de la Cola de Tickets

### Principio de Priorización

No es FIFO (First In, First Out). Es una combinación de:
1. **Severidad del problema** (P1 siempre antes que P4)
2. **Tiempo de espera** (un P3 con 48h es más urgente que un P3 con 2h)
3. **Tier del cliente** (Platinum siempre con prioridad dentro de la misma severidad)
4. **Riesgo de churn** (detectado vía señales: sentiment negativo, renovación próxima)

### Fórmula de Scoring de Prioridad

```
Score = (Peso_Severidad × 40) + (Tiempo_Espera_% × 30) + (Tier_Cliente × 20) + (Riesgo_Churn × 10)
```

Los sistemas modernos (Zendesk, ServiceNow) calculan esto automáticamente
con Business Rules o SLA Policies.

---

## Configuración de SLAs en Zendesk

### Pasos para configurar una SLA Policy:
1. Admin → Objects and rules → SLA Policies
2. Crear política por condiciones: `ticket.priority = urgent AND ticket.tags includes platinum`
3. Definir targets: First Reply Time + Resolution Time
4. Activar notificaciones de breach (80% del tiempo = warning, 100% = breach)

### Automatizaciones críticas:
- **Auto-escalado:** Si un ticket P2 lleva >6h sin respuesta → asignar al Team Lead
- **Breach alert:** Slack bot que notifica al manager cuando SLA >90%
- **Re-priorización automática:** Si cliente responde "urgente" o "crítico" → re-evaluar

---

## Gestión de Brechas de SLA (SLA Breach Management)

Cuando ocurre un breach:

1. **Notificación inmediata** al Team Lead (Slack alert automático)
2. **Root cause rápido:** ¿Por qué no se respondió a tiempo? (volumen, asignación, complejidad)
3. **Contacto proactivo al cliente** antes de que se queje: "Vemos que tu caso supera
   nuestro SLA comprometido. Te pedimos disculpas. Aquí está el estado actual..."
4. **Registro del breach:** Base de datos interna de breaches con causa y resolución
5. **Revisión semanal:** Tendencia de breaches por categoría y agente

### Template de Comunicación por Breach

> Hola [Nombre],
> Queremos informarte proactivamente de que tu solicitud (#TICKET) ha superado
> el tiempo de respuesta comprometido en nuestro SLA. Lamentamos el retraso.
> Estado actual: [descripción breve]. Próximo paso: [acción concreta] en [tiempo].
> Quedamos a tu disposición para cualquier consulta.

---

## Métricas de SLA

| Métrica | Descripción | Target |
|---|---|---|
| SLA Compliance Rate | % tickets dentro del SLA | >95% (Platinum), >90% (Gold) |
| SLA Breach Rate | % tickets que superan el SLA | <5% |
| Near-Miss Rate | % tickets entre 80–100% del SLA | <15% (señal de alerta temprana) |
| MTTR (Mean Time to Resolve) | Tiempo medio de resolución | Definido por tier/prioridad |
