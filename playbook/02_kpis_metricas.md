# 02 · KPIs y Métricas de Soporte

## Framework de Métricas: Los 4 Ejes

Un programa robusto de métricas en Customer Operations se estructura en
cuatro ejes: **Experiencia del cliente, Eficiencia operacional, Calidad
y Rendimiento del equipo.**

---

## 1. Métricas de Experiencia del Cliente

### CSAT (Customer Satisfaction Score)
- **Cálculo:** % de respuestas positivas / total respuestas × 100
- **Cuándo medir:** Post-resolución de ticket (encuesta automática)
- **Target recomendado:** >90% para soporte estándar, >93% para premium
- **Frequencia de revisión:** Semanal con tendencia mensual

### NPS (Net Promoter Score)
- **Cálculo:** % Promotores (9-10) − % Detractores (0-6)
- **Target:** >40 en B2B SaaS, >50 en enterprise
- **Cuándo usar:** Encuestas trimestrales, no por ticket individual

### CES (Customer Effort Score)
- **Mide:** El esfuerzo que pone el cliente para resolver su problema
- **Escala:** 1 (muy fácil) – 7 (muy difícil)
- **Target:** <3.0
- **Insight:** Alta correlación con churn. CES >5 = riesgo real de pérdida

---

## 2. Métricas de Eficiencia Operacional

### First Response Time (FRT)
- Tiempo desde la creación del ticket hasta la primera respuesta del agente
- **Target por canal:**
  - Email: <4h (business hours) / <1h (premium)
  - Chat en vivo: <2 min
  - Teléfono: <30 segundos para contestar

### Full Resolution Time (FRT/AHT)
- Tiempo total desde apertura hasta cierre del ticket
- **Benchmarks:**
  - Soporte técnico T1: <8h
  - Soporte técnico T2: <24h
  - Soporte técnico T3: <72h (SLA negociado)

### First Contact Resolution (FCR)
- % de tickets resueltos en el primer contacto sin necesidad de seguimiento
- **Target:** >75% (T1), >60% (global)
- **Fórmula:** Tickets resueltos en 1 contacto / Total tickets × 100

### Ticket Volume per Agent
- Volumen de tickets gestionados por agente por período
- Usar para capacity planning, no como métrica de rendimiento individual

---

## 3. Métricas de Calidad (QA)

### Quality Score (QS)
- Evaluación estructurada de tickets según rúbrica QA
- **Dimensiones típicas:**
  - Resolución correcta del problema (40%)
  - Comunicación y tono (20%)
  - Adherencia a proceso (20%)
  - Documentación del ticket (20%)
- **Target:** >85% QS promedio por agente

### Error Rate / DSAT Rate
- % de tickets con valoración negativa del cliente o error identificado en QA
- **Target:** <5%

---

## 4. Métricas de Rendimiento del Equipo

### Agent Utilization Rate
- % del tiempo del agente en trabajo productivo vs tiempo disponible
- **Target:** 70–80% (por encima genera burnout, por debajo ineficiencia)

### Attrition Rate
- % de abandono del equipo por período
- **Target en Customer Ops:** <20% anual (industria tiene ~30%)
- Alta attrition = problema de gestión, no de selección

### Adherencia al Turno (Schedule Adherence)
- % del tiempo que el agente está disponible según planificación
- **Target:** >92%

---

## Dashboard Recomendado

### Vista Semanal (Team Lead)
- CSAT + tendencia
- FRT por canal
- FCR rate
- Tickets abiertos por prioridad

### Vista Mensual (Ops Manager)
- NPS + CES
- Volumen total y distribución por categoría
- QA Score por agente y por equipo
- Attrition y headcount

### Vista Trimestral (Director)
- Tendencias de CSAT/NPS vs targets
- Comparativa regional
- Impacto de iniciativas (automatización, nuevos procesos)
- Cost per ticket y eficiencia

---

## Errores Comunes en Medición

1. **Medir demasiado:** Tener 20+ KPIs sin saber cuáles mover. Elegir 5–7 métricas core.
2. **Optimizar en silos:** Mejorar FCR bajando FRT dispara DSAT. Las métricas interactúan.
3. **Ignorar datos cualitativos:** Los comentarios de CSAT explican el número, no al revés.
4. **Medir lo fácil, no lo importante:** Velocidad es fácil de medir; calidad real, no.
