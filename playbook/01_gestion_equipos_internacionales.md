# 01 · Gestión de Equipos Internacionales (EMEA, LATAM, APAC)

## Estructura Organizativa

Los equipos internacionales de Customer Operations requieren una estructura
adaptada a la complejidad de husos horarios, idiomas y culturas. La clave es
definir claramente los **nodos de gestión regional** sin perder visibilidad
global desde operaciones centrales.

Modelo recomendado:
- **Head of Customer Ops** (global) → visibilidad de KPIs consolidados
- **Regional Team Leads** por zona (EMEA / LATAM / APAC)
- **Tier Leads** dentro de cada región (T1, T2, T3)

## Gestión de Zonas Horarias

### Principio de Follow-the-Sun
Los equipos en EMEA, LATAM y APAC pueden cubrir 24h/7d sin turnos nocturnos
si se diseña el handover correctamente.

**Horario de solapamiento (overlap):**
- EMEA ↔ APAC: 08:00–10:00 CET / 15:00–17:00 SGT
- EMEA ↔ LATAM: 13:00–17:00 CET / 08:00–12:00 BRT
- LATAM ↔ APAC: Solo viable con equipos en Oceanía o SE Asia

### Protocolo de Handover Diario
1. Actualización del **Handover Doc** 30 min antes del fin del turno
2. Formato estándar: Tickets abiertos críticos + estado + próximo paso
3. Canal dedicado en Slack/Teams: `#ops-handover-[región]`
4. Sync call de 15 min entre Team Leads saliente y entrante (solo para P1/P2)

## Comunicación Multicultural

- **EMEA (Europa/Oriente Medio/África):** Comunicación directa, alta expectativa
  de respuesta rápida y escalado formal. Clientes enterprise con SLAs estrictos.
- **LATAM:** Relación más cálida y personal. Valorar el contexto antes de ir
  directo al problema. Idioma: español/portugués. Mayor tolerancia al seguimiento.
- **APAC:** Alta formalidad en mercados como Japón/Corea. Respeto jerárquico.
  Mercados como Australia/India tienen perfiles más anglosajones/directos.

## KPIs de Gestión Internacional

| KPI | Definición | Target |
|---|---|---|
| Regional CSAT | Satisfacción por región | >90% |
| Cross-region escalation rate | % tickets escalados entre regiones | <5% |
| Handover quality score | Evaluación del handover doc | >4/5 |
| Language resolution rate | % resuelto en idioma nativo | >95% |

## Herramientas Recomendadas

- **Gestión de tickets:** Zendesk o ServiceNow con vistas por región
- **Comunicación interna:** Slack (canales por región + global) o Teams
- **Scheduling:** When I Work o Assembled para rotación de turnos multi-zona
- **Documentación:** Confluence con estructura por región + idioma

## Desafíos Comunes y Soluciones

**Problema: Falta de consistencia en calidad entre regiones**
→ Solución: Calibraciones mensuales cross-region. Un mismo ticket se evalúa
por QA de 2 regiones distintas y se comparan criterios.

**Problema: Silos de comunicación entre regiones**
→ Solución: Buddy system entre Team Leads de regiones distintas. Rotación
trimestral de shadowing remoto.

**Problema: Escalados inconsistentes**
→ Solución: Matriz de escalado unificada con criterios claros independientes
de la región. Revisión mensual de casos mal escalados.
