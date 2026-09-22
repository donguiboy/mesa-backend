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

   Los valores por defecto ya coinciden con el `docker-compose.yml`, así que no hace falta tocar nada para desarrollo local.

5. Levantá Postgres:

   ```powershell
   docker compose up -d
   ```

6. Corré la API:

   ```powershell
   uvicorn app.main:app --reload
   ```

7. Probá que responde en [http://localhost:8000/health](http://localhost:8000/health).

## Estructura

```
app/
  main.py          # instancia de FastAPI y registro de routers
  routers/         # endpoints agrupados por dominio
  models/          # modelos de SQLAlchemy
```

## Notas

- Nunca commitear el archivo `.env` (ya está en `.gitignore`).
- Este repo es solo el backend. El frontend vive en un repositorio aparte.
