from fastapi import FastAPI

from app.routers import auth, games, health, tables, users

app = FastAPI(title="Meeple API")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(games.router)
app.include_router(tables.router)
