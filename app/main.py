from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, games, health, matches, tables, users

app = FastAPI(title="Meeple API")

app.add_middleware(
    CORSMiddleware,
    # vite dev salta de puerto si el anterior está ocupado (8080, 8081, ...);
    # el regex evita tener que ir agregando cada puerto nuevo a mano.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(games.router)
app.include_router(tables.router)
app.include_router(matches.router)
