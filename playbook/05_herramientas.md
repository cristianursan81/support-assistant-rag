# 05 · Herramientas de Customer Operations

## Principio

Las herramientas no hacen al equipo, pero el equipo sin las herramientas
correctas no escala. La elección del stack tecnológico debe seguir a los
procesos, nunca al revés.

**Regla de oro:** Primero define el proceso, luego elige la herramienta
que lo soporte. Implementar una herramienta sin proceso claro genera caos digitalizado.

---

## 1. Ticketing y Gestión de Soporte

### Zendesk
La plataforma más extendida en equipos de Customer Ops B2B/SaaS.

**Cuándo usarlo:**
- Equipos de 5–200 agentes
- Soporte multicanal (email, chat, teléfono, redes sociales)
- Necesidad de SLA policies automatizadas

**Configuraciones clave:**
- **Vistas por región:** Filtrar tickets por tag de región (EMEA, LATAM, APAC)
  para que cada equipo solo vea su cola.
- **SLA Policies:** Configurar por prioridad y tier de cliente (ver cap. 04)
- **Triggers y Automatizaciones:** 
  - Auto-asignación por idioma detectado
  - Notificación al Team Lead si ticket P1 sin respuesta en 10 min
  - Encuesta CSAT automática 24h después del cierre
- **Macros:** Respuestas predefinidas para las T10 consultas más frecuentes
- **Tags:** Sistema de etiquetado por categoría, región, tier, producto

**Integraciones recomendadas:**
- Slack: Notificaciones de P1/P2 en canal `#ops-alerts`
- Jira: Escalado automático de bugs a Engineering
- Salesforce/HubSpot: Sincronización de datos de cliente

### ServiceNow
Más robusto y complejo que Zendesk. Orientado a enterprise e ITSM.

**Cuándo usarlo:**
- Organizaciones enterprise con procesos ITIL
- Necesidad de CMDB (gestión de activos) integrada
- Equipos de 100+ agentes con flujos de aprobación complejos

**Diferencias clave vs Zendesk:**
- Mayor coste de implementación y mantenimiento
- Más potente para flujos de trabajo complejos
- Mejor para integraciones con sistemas corporativos (SAP, Oracle)
- Curva de aprendizaje más alta para agentes

---

## 2. Gestión de Proyectos y Bugs

### Jira (Atlassian)
Estándar de facto para la gestión de bugs y proyectos técnicos.

**Uso en Customer Ops:**
- Escalado de bugs desde Zendesk/ServiceNow a Engineering
- Tracking de issues reportados por clientes
- Proyectos internos de mejora de procesos

**Flujo de escalado recomendado:**
1. Agente identifica bug reproducible en Zendesk
2. Crea issue en Jira con template estándar:
   - Descripción del problema
   - Pasos para reproducir
   - Entorno (versión, OS, navegador)
   - Impacto en clientes (nº afectados, tier)
   - Link al ticket de Zendesk
3. Jira notifica automáticamente al Engineering Lead
4. Engineering actualiza estado → Zendesk se actualiza vía integración

**Configuración clave:**
- Board de "Customer-Reported Issues" separado del backlog de producto
- SLA de respuesta de Engineering por prioridad de bug
- Campos obligatorios: impacto en cliente + ticket origen

### Confluence (Atlassian)
Base de conocimiento y documentación interna del equipo.

**Estructura recomendada:**
```
Customer Operations/
├── Playbooks y Procesos/
├── Base de Conocimiento (FAQs internas)/
├── Onboarding de Agentes/
├── Templates y Macros/
├── Reuniones y Decisiones/
└── Métricas y Dashboards/
```

---

## 3. CRM y Gestión de Clientes

### Salesforce
El CRM más completo del mercado. Indispensable en empresas enterprise.

**Uso en Customer Ops:**
- Vista 360° del cliente: historial de tickets, contratos, renovaciones
- Alertas de churn: campos de health score y señales de riesgo
- Gestión de escalados comerciales
- Coordinación con Sales y Customer Success

**Campos críticos para soporte:**
- Tier del cliente (Platinum/Gold/Silver)
- CSM asignado
- Fecha de renovación
- NPS histórico
- Número de tickets en los últimos 90 días
- Health score actual

**Integración con Zendesk:**
- Al abrir un ticket, el agente ve automáticamente el tier y CSM del cliente
- Los tickets se sincronizan en el registro de Salesforce
- Alertas automáticas al CSM cuando cliente Platinum abre P1/P2

### HubSpot
Alternativa a Salesforce para empresas mid-market.

**Ventajas vs Salesforce:**
- Más fácil de implementar y mantener
- Mejor UX para equipos pequeños
- Precio más accesible
- Service Hub integrado para ticketing básico

---

## 4. Comunicación Interna

### Slack
Estándar para equipos de tech y SaaS. Esencial para operaciones en tiempo real.

**Estructura de canales recomendada:**
```
#ops-general          → Comunicación general del equipo
#ops-alerts           → Alertas automáticas P1/P2 (solo bots)
#ops-handover-emea    → Handover diario EMEA
#ops-handover-latam   → Handover diario LATAM
#ops-handover-apac    → Handover diario APAC
#ops-escalations      → Escalados activos cross-región
#ops-qa               → Revisiones de calidad y calibraciones
#product-bugs         → Coordinación con Engineering
```

**Automatizaciones clave:**
- Bot de SLA breach: alerta cuando ticket supera 80% del tiempo
- Bot de P1: notifica a Team Lead + Manager inmediatamente
- Bot de CSAT: reporte semanal automático en `#ops-general`

### Microsoft Teams
Alternativa a Slack en empresas con ecosistema Microsoft (Office 365).

**Ventajas en entornos enterprise:**
- Integración nativa con SharePoint, Outlook, Azure
- Mejor para videollamadas y reuniones formales
- Cumplimiento y seguridad empresarial

---

## 5. Workforce Management

### Assembled
Herramienta especializada en planning y scheduling para equipos de soporte.

**Funcionalidades clave:**
- Forecasting de volumen de tickets por hora/día
- Scheduling automático respetando zonas horarias
- Real-time adherence: ve si los agentes están en su puesto
- Integración con Zendesk para datos históricos

### When I Work
Alternativa más simple y económica para equipos pequeños.

**Ideal para:**
- Equipos de 10–50 agentes
- Gestión de turnos rotativos
- Solicitudes de vacaciones y cambios de turno

---

## 6. Análisis y Business Intelligence

### Tableau / Looker / PowerBI
Para dashboards avanzados de Customer Ops más allá de los reportes nativos.

**Dashboards prioritarios:**
- CSAT y NPS histórico por región y agente
- SLA compliance por tier de cliente
- Volumen de tickets por categoría y tendencia
- Performance individual de agentes (QA + productividad)
- Cost per ticket y ROI de automatizaciones

---

## Matriz de Herramientas por Tamaño de Equipo

| Tamaño | Ticketing | CRM | Comunicación | Docs | WFM |
|---|---|---|---|---|---|
| Startup (1–10) | Zendesk Lite | HubSpot Free | Slack | Notion | Manual |
| Scale-up (10–50) | Zendesk Growth | HubSpot / SF Essentials | Slack | Confluence | When I Work |
| Mid-market (50–150) | Zendesk Suite | Salesforce | Slack | Confluence | Assembled |
| Enterprise (150+) | ServiceNow | Salesforce Enterprise | Teams | Confluence/SharePoint | Assembled / NICE |

---

## Errores Comunes con Herramientas

**Error 1: Implementar demasiadas herramientas a la vez**
→ El equipo no adopta ninguna bien. Máximo 1 herramienta nueva por trimestre.

**Error 2: No configurar las integraciones entre herramientas**
→ Los agentes trabajan en silos. Zendesk ↔ Jira ↔ Salesforce deben estar conectados.

**Error 3: No entrenar al equipo en las herramientas**
→ El 80% del valor de Zendesk viene del 20% de funcionalidades más usadas.
Formación práctica obligatoria, no solo documentación.

**Error 4: Usar las herramientas como sustituto del proceso**
→ Automatizar un proceso roto solo genera errores más rápido.
Primero arregla el proceso, luego automatiza.
