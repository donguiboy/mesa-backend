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
