# 06 · Gestión de Crisis

## Principio

Una crisis no se improvisa — se gestiona con un protocolo preestablecido.
La diferencia entre un equipo que controla la crisis y uno que la sufre
está en la preparación previa, no en la reacción del momento.

**Definición de crisis en Customer Ops:** Cualquier evento que afecta
simultáneamente a múltiples clientes, compromete la confianza en el servicio
o supera la capacidad de respuesta normal del equipo.

---

## Clasificación de Crisis

### Nivel 1 — Incidente Mayor (Major Incident)
- **Definición:** Caída total o parcial del servicio que afecta a >10% de clientes activos
- **Ejemplos:** Outage de producción, fallo de base de datos, brecha de seguridad
- **Activación:** Automática cuando se detecta P1 con impacto masivo
- **Duración típica:** 1–8 horas

### Nivel 2 — Crisis de Comunicación
- **Definición:** Evento que genera volumen masivo de contactos o daño reputacional
- **Ejemplos:** Noticia negativa viral, email masivo con error, cambio de precios conflictivo
- **Activación:** Manual por el Manager o Director
- **Duración típica:** 24–72 horas

### Nivel 3 — Crisis Operacional
- **Definición:** El equipo no puede operar con normalidad
- **Ejemplos:** Caída de herramientas (Zendesk, Slack), baja masiva de agentes, desastre natural en una región
- **Activación:** Manual por el Team Lead
- **Duración típica:** 2–24 horas

---

## Protocolo de Gestión de Crisis (War Room)

### Fase 1: Detección y Activación (0–15 min)

1. **Detección:** Alerta automática (monitorización) o reporte manual de agente/cliente
2. **Evaluación rápida:** ¿Cuántos clientes afectados? ¿Qué funcionalidad? ¿Sigue activo?
3. **Activación del protocolo:**
   - Notificar al Incident Manager (rol rotativo en el equipo)
   - Abrir canal de crisis en Slack: `#incident-YYYYMMDD`
   - Notificar a Engineering/Product si es incidente técnico
4. **Asignar roles inmediatamente:**
   - **Incident Manager:** Coordina y toma decisiones
   - **Communications Lead:** Gestiona comunicación con clientes
   - **Technical Lead:** Investiga causa raíz
   - **Support Lead:** Gestiona la cola de tickets entrantes

### Fase 2: Contención y Comunicación (15–60 min)

**Comunicación interna:**
- Update en `#incident-YYYYMMDD` cada 15 minutos
- Formato estándar: `[HH:MM] Estado: [activo/contenido/resuelto] | Afectados: [N] | Próximo paso: [acción]`
- Notificar a Management si impacto >20 clientes Platinum/Gold

**Comunicación externa (clientes):**
- Primera comunicación en <30 min desde detección
- Canal: Email + Status Page + Slack Connect (clientes Platinum)
- Tono: Transparente, sin tecnicismos, con próximo update prometido

**Template de primera comunicación:**
> Asunto: [Servicio] — Estamos investigando un problema activo
>
> Estimado/a [Nombre],
> Somos conscientes de que algunos clientes están experimentando
> [descripción breve del problema]. Nuestro equipo técnico está
> trabajando activamente en la resolución.
> Estado actual: Investigando causa raíz.
> Próximo update: [hora concreta, máximo 1h].
> Pedimos disculpas por las molestias ocasionadas.

### Fase 3: Resolución y Cierre (variable)

1. **Confirmación de resolución:** Engineering confirma fix desplegado
2. **Verificación en producción:** Support Lead verifica que clientes pueden operar
3. **Comunicación de resolución:** Email a todos los afectados con:
   - Confirmación de resolución
   - Resumen del impacto (tiempo de inactividad)
   - Causa raíz en lenguaje no técnico
   - Medidas preventivas para evitar recurrencia
4. **Cierre del canal de crisis:** Archivar `#incident-YYYYMMDD`
5. **Tickets:** Cerrar o actualizar todos los tickets relacionados

### Fase 4: Post-Mortem (24–72h después)

**Post-Incident Review (PIR) — documento obligatorio para Nivel 1:**
- Timeline detallado del incidente
- Causa raíz técnica
- Impacto cuantificado (clientes afectados, tiempo, revenue en riesgo)
- Qué salió bien en la gestión
- Qué salió mal y por qué
- Acciones correctivas con responsable y fecha

**Distribución del PIR:**
- Interno: Todo el equipo de Ops + Engineering + Management
- Externo: Clientes Platinum y Gold afectados (versión resumida)

---

## Gestión de la Cola Durante una Crisis

Cuando el volumen de tickets se dispara:

1. **Triage inmediato:** Identificar tickets relacionados con el incidente
   y agruparlos con un tag `#incident-FECHA`
2. **Respuesta masiva:** Una sola respuesta template para todos los tickets
   del incidente — no responder uno a uno
3. **Priorización:** Los tickets NO relacionados con el incidente
   mantienen su SLA normal
4. **Refuerzo de equipo:** Activar agentes de otras regiones o turno
   si el volumen supera el 150% del normal
5. **Cierre masivo:** Al resolverse el incidente, cerrar todos los tickets
   agrupados con una respuesta de resolución

---

## Comunicación con Clientes VIP Durante Crisis

### Clientes Platinum
- Llamada proactiva del CSM en los primeros 30 minutos
- Updates cada 30 minutos por Slack Connect o teléfono
- PIR entregado en 48h
- Revisión de créditos de servicio si aplica según contrato

### Clientes Gold
- Email proactivo en los primeros 30 minutos
- Updates cada hora
- PIR resumido entregado en 72h

### Clientes Silver
- Status page como canal principal
- Email de resolución al cierre

---

## Métricas de Gestión de Crisis

| Métrica | Descripción | Target |
|---|---|---|
| MTTI (Mean Time to Identify) | Tiempo hasta detectar el incidente | <10 min |
| MTTC (Mean Time to Communicate) | Tiempo hasta primera comunicación al cliente | <30 min |
| MTTR (Mean Time to Resolve) | Tiempo hasta resolución completa | Según severidad |
| Customer Impact Rate | % clientes afectados sobre total | Minimizar |
| PIR Delivery Time | Tiempo hasta entrega del post-mortem | <72h para P1 |

---

## Errores Frecuentes en Gestión de Crisis

**Error 1: Esperar a tener toda la información antes de comunicar**
→ El silencio genera más alarma que la incertidumbre. Comunicar pronto
aunque sea solo para decir "estamos investigando".

**Error 2: No asignar roles claros desde el primer minuto**
→ Todo el mundo haciendo de todo = nadie haciendo nada bien.
El Incident Manager decide, los demás ejecutan.

**Error 3: Prometer tiempos de resolución que no se pueden cumplir**
→ Mejor "próximo update en 1h" que "resuelto en 30 min" y luego incumplir.

**Error 4: No hacer el post-mortem o hacerlo sin acción real**
→ El post-mortem sin acciones correctivas concretas es papel mojado.
Cada acción debe tener responsable y fecha de cierre.

**Error 5: No practicar la gestión de crisis**
→ Los simulacros anuales de crisis (tabletop exercises) reducen el MTTR
real en un 40%. Practicar antes de necesitarlo.
