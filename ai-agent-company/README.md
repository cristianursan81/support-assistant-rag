# 🤖 GestorIA

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI 0.135+](https://img.shields.io/badge/FastAPI-0.135%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Gradio 6.9+](https://img.shields.io/badge/Gradio-6.9%2B-orange?logo=gradio)](https://gradio.app)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)](https://docker.com)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Automatización de atención al cliente con IA para gestorías y PYMEs españolas.**
> Customer service AI automation for Spanish SMEs — WhatsApp + email, 5-minute setup.

---

## ✨ Highlights

- 🧠 **RAG + Agentes Claude** — respuestas contextuales en <15 segundos vía Claude Haiku/Sonnet
- 💬 **WhatsApp & Email** — integración Twilio lista para producción
- 📊 **Dashboard Gradio** — panel de operador multi-tenant sin código adicional
- ⚡ **FastAPI REST** — webhooks, auth JWT, API REST completa en `:8000`
- 🐳 **Docker 1-comando** — despliega en un VPS de €3.29/mes (Hetzner CX11)
- 🏢 **Multi-tenant** — aísla datos por workspace, soporta N clientes en la misma instancia
- 📅 **Reservas automáticas** — plantillas para restaurante, clínica y tienda

---

## ¿Qué es GestorIA? / What is GestorIA?

**ES** — GestorIA es una plataforma SaaS lista para producción que permite a restaurantes, clínicas y tiendas desplegar un equipo de agentes IA en minutos. Atiende clientes por WhatsApp y email las 24 horas, gestiona reservas y citas, y proporciona un panel de control en tiempo real.

**EN** — GestorIA is a production-ready multi-tenant SaaS that lets Spanish SMEs deploy an AI agent team in under 5 minutes. Agents answer customer messages on WhatsApp and email 24/7, handle bookings, and report to operators via a Gradio dashboard — all powered by Anthropic Claude.

---

## 📸 Demo / Screenshots

| Dashboard | Gestión de Tickets | Configuración |
|---|---|---|
| <img src="screenshots/dashboard.png" alt="Dashboard" width="280"> | <img src="screenshots/tickets.png" alt="Tickets" width="280"> | <img src="screenshots/setup.png" alt="Setup" width="280"> |

> 📷 *Screenshots coming soon — contributions welcome!*

---

## 📋 Requisitos / Prerequisites

| Herramienta | Versión mínima |
|---|---|
| Python | 3.11+ |
| Docker + Compose | 24+ / v2+ |
| Cuenta Anthropic | API key activa |
| Cuenta Twilio | Para WhatsApp (opcional en dev) |

---

## 🚀 Instalación local / Local Setup

```bash
# 1. Clonar
git clone https://github.com/cristianursan81/GestorIA.git
cd GestorIA

# 2. Entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Variables de entorno
cp .env.example .env
nano .env                        # Añade ANTHROPIC_API_KEY como mínimo

# 5. Arrancar (ambos servicios)
python run.py
#   ✅ FastAPI  → http://localhost:8000
#   ✅ Dashboard → http://localhost:7861
```

---

## 🐳 Docker (recomendado / recommended)

```bash
# 1. Preparar .env
cp .env.example .env && nano .env

# 2. Build + arranque
docker compose up -d

# 3. Logs en tiempo real
docker compose logs -f gestor

# 4. Parar
docker compose down
```

> El contenedor expone `:8000` (FastAPI) y `:7861` (Gradio).
> Para HTTPS usa Caddy o Nginx como reverse proxy delante.

### Producción pura (Gunicorn solamente)

```bash
# Elimina el override de command en docker-compose.yml para usar el CMD del Dockerfile:
#   gunicorn -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000 src.api:app
docker compose up -d

# El dashboard Gradio se lanza en un contenedor/proceso separado:
docker exec gestor-gestor-1 python run.py dashboard
```

---

## ⚙️ Variables de entorno / Environment Variables

| Variable | Requerida | Ejemplo | Descripción |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | `sk-ant-...` | Clave API de Anthropic |
| `DATABASE_URL` | ✅ | `sqlite:///./gestoria.db` | SQLite (dev) o PostgreSQL (prod) |
| `JWT_SECRET` | ✅ | *(cadena aleatoria 48+ chars)* | `openssl rand -base64 48` |
| `BASE_URL` | ✅ | `https://tudominio.com` | URL pública para webhooks Twilio |
| `TWILIO_ACCOUNT_SID` | ⚠️ | `ACxxx...` | SID de cuenta Twilio |
| `TWILIO_AUTH_TOKEN` | ⚠️ | `...` | Token de autenticación Twilio |
| `TWILIO_WHATSAPP_NUMBER` | ⚠️ | `+34600000000` | Número WhatsApp Twilio |
| `SMTP_HOST` | ⚠️ | `smtp.gmail.com` | Servidor SMTP para emails |
| `SMTP_PORT` | ⚠️ | `587` | Puerto SMTP (TLS) |
| `SMTP_USER` | ⚠️ | `empresa@gmail.com` | Usuario SMTP |
| `SMTP_PASSWORD` | ⚠️ | `app-password` | Contraseña / App Password |
| `ALLOWED_ORIGINS` | — | `https://tudominio.com` | CORS origins (coma-separados) |
| `LOG_LEVEL` | — | `info` | `debug\|info\|warning\|error` |
| `ENVIRONMENT` | — | `production` | `development\|staging\|production` |
| `SLOWAPI_RATE_LIMIT` | — | `100/minute` | Límite de tasa global (próximamente) |

> ⚠️ = requerida para canal correspondiente (WhatsApp o email). No necesaria en dev si no usas ese canal.

---

## 🏗️ Arquitectura / Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Internet                          │
│   WhatsApp (Twilio) ──┐     Email (SMTP/Mailgun) ──┐    │
└───────────────────────┼─────────────────────────────┼───┘
                        ▼                             ▼
             ┌─────────────────────┐
             │   FastAPI :8000     │  ← Webhooks, REST API, Auth JWT
             │   (Gunicorn prod)   │
             └────────┬────────────┘
                      │
          ┌───────────▼───────────┐
          │   Agent Agentic Loop  │  ← Claude Haiku (cliente) / Sonnet (orquestador)
          │   Tool Use (11 tools) │
          └───────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │   SQLite / PostgreSQL │  ← Multi-tenant: Workspace, Agent, Ticket…
          └───────────────────────┘
                      │
          ┌───────────▼───────────┐
          │   Gradio :7861        │  ← Panel operador (empresas, agentes, tickets)
          └───────────────────────┘
```

**Flujo de un mensaje WhatsApp:**
1. Twilio → `POST /api/webhook/whatsapp`
2. FastAPI crea/continúa `Ticket` + `Conversation`
3. Thread daemon lanza `run_agent_on_ticket()` (no bloquea Twilio <5 s)
4. Claude Haiku ejecuta herramientas (reservas, info negocio, respuesta WA)
5. Respuesta enviada al cliente vía `send_whatsapp()`

---

## 🛠️ Comandos útiles / Useful Commands Cheatsheet

```bash
# ── Desarrollo ────────────────────────────────────────────────────────────────
python run.py                   # API + Dashboard
python run.py api               # Solo FastAPI
python run.py dashboard         # Solo Gradio

# ── Docker ────────────────────────────────────────────────────────────────────
docker compose up -d            # Arrancar en background
docker compose down             # Parar y eliminar contenedores
docker compose build --no-cache # Rebuild imagen desde cero
docker compose logs -f gestor   # Logs en tiempo real
docker compose ps               # Estado (incluye healthcheck)
docker exec -it $(docker compose ps -q gestor) bash  # Shell en contenedor

# ── Base de datos ─────────────────────────────────────────────────────────────
# SQLite — inspeccionar
sqlite3 gestoria.db ".tables"
sqlite3 gestoria.db "SELECT * FROM workspaces;"

# Alembic — migraciones (cuando se active)
alembic init alembic
alembic revision --autogenerate -m "add column X"
alembic upgrade head

# ── API — ejemplos curl ───────────────────────────────────────────────────────
# Registro
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@gestor.ia","password":"test1234","full_name":"Demo","workspace_name":"Mi Restaurante","industry":"restaurante"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@gestor.ia","password":"test1234"}'

# Setup workspace (usa el token del login)
curl -X POST http://localhost:8000/api/workspace/setup \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"industry":"restaurante","business_info":{"name":"El Rincón","address":"C/ Mayor 1"}}'

# Health check
curl http://localhost:8000/health
```

---

## 🗺️ Roadmap

- [x] Agentic loop con Claude Haiku + Sonnet
- [x] Webhook WhatsApp (Twilio)
- [x] Dashboard Gradio multi-tenant
- [x] Auth JWT + registro de clientes
- [x] Plantillas: restaurante, clínica, tienda
- [x] Docker multi-stage + Gunicorn
- [x] Healthcheck + logging estructurado
- [ ] Migraciones con Alembic
- [ ] Rate limiting global con SlowAPI
- [ ] PostgreSQL async (asyncpg) para producción
- [ ] Tests automáticos (pytest + httpx)
- [ ] Panel de facturación / Stripe
- [ ] Soporte multi-idioma (catalán, euskera…)
- [ ] RAG sobre documentos propios del negocio (PDF → pgvector)
- [ ] App móvil operador (React Native)

---

## 🤝 Contribuyendo / Contributing

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del repositorio
2. Crea una rama: `git checkout -b feature/mi-mejora`
3. Haz commit con mensaje descriptivo: `git commit -m "feat: añadir soporte Telegram"`
4. Push: `git push origin feature/mi-mejora`
5. Abre un Pull Request describiendo el cambio

**Áreas prioritarias:** tests, documentación, plantillas nuevas (peluquería, hotel…), integraciones (Stripe, Calendly).

---

## ⚠️ Limitaciones y Seguridad actuales / Current Limitations & Security

| Aspecto | Estado actual | Recomendación producción |
|---|---|---|
| Base de datos | SQLite (mono-instancia) | Migrar a PostgreSQL |
| Rate limiting | Auth endpoints (10/5min) | Activar SlowAPI global |
| Validación Twilio | Comprueba si `TWILIO_AUTH_TOKEN` está definido | Siempre activo en prod |
| CORS | Configurable vía `ALLOWED_ORIGINS` | Nunca usar `*` en prod |
| Secretos | `.env` local | Vault / AWS Secrets Manager |
| Backups | Manual (volumen Docker) | Cron + S3/Backblaze |
| HTTPS | No incluido | Caddy / Nginx reverse proxy |
| Multi-instancia | No soportado (SQLite) | PostgreSQL + sticky sessions |

> 🔒 **Nunca** hagas commit de tu fichero `.env`. Está en `.gitignore` por defecto.

---

## 📄 Licencia / License

MIT © 2026 [cristianursan81](https://github.com/cristianursan81)

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions: [...]
```

---

<div align="center">

**[⬆ volver arriba / back to top](#-gestoría)**

Hecho con ❤️ para las PYMEs españolas · Built for Spanish SMEs

*Keywords: RAG gestoría IA, FastAPI Gradio España, asistente IA WhatsApp pymes, automatización atención cliente IA*

</div>
