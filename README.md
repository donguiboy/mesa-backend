# mesa-backend

Backend de Meeple hecho con FastAPI, SQLAlchemy/Alembic y Postgres.

## Requisitos

- Python 3.13
- Docker + Docker Compose (para la base de datos)

## Setup

1. Cloná el repo y entrá a la carpeta.

2. Creá y activá el entorno virtual:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. Instalá las dependencias:

   ```powershell
   pip install -r requirements.txt
   ```

4. Copiá el archivo de variables de entorno:

   ```powershell
   copy .env.example .env
   ```

   Los valores por defecto ya coinciden con el `docker-compose.yml`, así que no hace falta tocar nada para desarrollo local, salvo `SECRET_KEY` (usada para firmar los JWT de auth). Generá una propia:

   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Si ya tenés un Postgres corriendo en el puerto 5432 (por ejemplo un servicio nativo de Windows), cambiá `POSTGRES_PORT` en `.env` y el puerto en `DATABASE_URL` a algo libre como `5433`.

5. Levantá Postgres:

   ```powershell
   docker compose up -d
   ```

6. Aplicá las migraciones:

   ```powershell
   alembic upgrade head
   ```

7. Corré la API:

   ```powershell
   uvicorn app.main:app --reload
   ```

8. Probá que responde en [http://localhost:8000/health](http://localhost:8000/health).

## Auth

- `POST /auth/register` — `{ email, username, name, password }` → crea el usuario.
- `POST /auth/login` — `{ email, password }` → `{ access_token, token_type }`.
- `GET /users/me` — requiere header `Authorization: Bearer <access_token>`.

## Juegos y mesas

- `GET /games` / `POST /games` — catálogo de juegos, con datos de BGG (descripción, mecánicas, imagen, rating, etc.) para los importados con `scripts/import_bgg_games.py`; `POST /games` crea uno ad-hoc solo con `name`.
- `POST /tables` — crea una mesa (el creador queda como host confirmado); acepta `participant_ids` para invitar de una.
- `GET /tables` — lista las mesas donde participás (host o invitado).
- `GET /tables/{id}` — detalle de una mesa (solo si sos participante).
- `POST /tables/{id}/invite` — el host invita más participantes.
- `POST /tables/{id}/respond` — `{ confirm }`: el invitado confirma o rechaza.
- `POST /tables/{id}/propose` — `{ game_ids }`: un participante confirmado propone juegos (mientras la mesa está `proposing`).
- `POST /tables/{id}/start-voting` — el host cierra propuestas y abre votación.
- `POST /tables/{id}/vote` — `{ game_ids }`: un participante confirmado vota (mientras la mesa está `voting`; respeta `planned_games_count` si está seteado).
- `POST /tables/{id}/resolve` — `{ result_game_ids, result_was_tie }`: el host cierra la mesa con el resultado.
- `POST /tables/{id}/cancel` — el host cancela la mesa (si no está resuelta o ya cancelada).

Estados de una mesa: `proposing → voting → resolved`, o `cancelled` en cualquier momento antes de resolverse.

### Catálogo de BGG

`app/seed_data/bgg_games.json` tiene los 500 juegos más poseídos en BoardGameGeek (mismo dataset que usa el frontend en `bgg-seed-data.ts`, extraído una sola vez — no se vuelve a generar automáticamente). Para cargarlos:

```powershell
python scripts/import_bgg_games.py
```

Es idempotente: hace upsert por `bgg_id`, así que correrlo de nuevo actualiza los datos existentes en vez de duplicarlos.

## Partidas

- `POST /matches` — registra una partida jugada. Requiere `game_id`, `participant_ids` (el usuario logueado tiene que ser uno de ellos) y exactamente un resultado: `winner_id`, o `is_tie` + `tied_ids`, o `is_group_win` + `group_win_ids`. `table_id` es opcional: si se manda, la mesa debe estar `resolved`, no tener ya una partida registrada, y los participantes deben pertenecer a ella — al crearse la partida, la mesa queda linkeada vía `logged_match_id`.
- `GET /matches` — lista las partidas en las que participaste.
- `GET /matches/{id}` — detalle de una partida (solo si fuiste participante).

## Tests

```powershell
pip install -r requirements-dev.txt
createdb -U meeple -h localhost -p 5433 meeple_test   # una sola vez
pytest
```

Los tests corren contra `TEST_DATABASE_URL` (ver `.env.example`), nunca contra la base de desarrollo: cada test se ejecuta dentro de una transacción que se revierte al terminar.

## Estructura

```
app/
  main.py          # instancia de FastAPI y registro de routers
  core/            # configuración (env vars) y seguridad (hashing, JWT)
  db/              # engine y sesión de SQLAlchemy
  deps.py          # dependencias compartidas (ej. get_current_user)
  models/          # modelos de SQLAlchemy
  schemas/         # esquemas de Pydantic (request/response)
  routers/         # endpoints agrupados por dominio
alembic/           # migraciones de base de datos
tests/             # tests de pytest (ver sección "Tests")
```

Para agregar un modelo nuevo: creá el modelo en `app/models/`, importalo en `app/models/__init__.py` y corré `alembic revision --autogenerate -m "..."` seguido de `alembic upgrade head`.

## Notas

- Nunca commitear el archivo `.env` (ya está en `.gitignore`).
- Este repo es solo el backend. El frontend vive en un repositorio aparte.
