from fastapi import FastAPI

from app.routers import auth, health, users

app = FastAPI(title="Meeple API")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
