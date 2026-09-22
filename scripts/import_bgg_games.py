"""Importa el catálogo de juegos desde el dataset de BGG (top 500 por
popularidad, ver app/seed_data/bgg_games.json). Idempotente: hace upsert
por bgg_id, así que correrlo de nuevo actualiza datos sin duplicar filas.

Uso (desde la raíz del repo, con el venv activado):
    python scripts/import_bgg_games.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.game import Game  # noqa: E402

DATA_PATH = Path(__file__).resolve().parent.parent / "app" / "seed_data" / "bgg_games.json"


def main() -> None:
    games_data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    with SessionLocal() as db:
        existing = {g.bgg_id: g for g in db.scalars(select(Game).where(Game.bgg_id.is_not(None)))}

        created = 0
        updated = 0
        for entry in games_data:
            bgg_id = entry["id"]
            game = existing.get(bgg_id)
            if game is None:
                game = Game(bgg_id=bgg_id)
                db.add(game)
                created += 1
            else:
                updated += 1

            game.name = entry["name"]
            game.description = entry.get("description")
            game.players = entry.get("players")
            game.duration = entry.get("duration")
            game.complexity = entry.get("complexity")
            game.category = entry.get("category")
            game.categories = entry.get("categories") or None
            game.mechanics = entry.get("mechanics") or None
            game.themes = entry.get("themes") or None
            game.tags = entry.get("tags") or None
            game.image = entry.get("image")
            game.rating = entry.get("rating")
            game.year_published = entry.get("yearPublished")
            game.min_age = entry.get("minAge")
            game.gradient = entry.get("gradient")
            game.emoji = entry.get("emoji")

        db.commit()

    print(f"Listo: {created} creados, {updated} actualizados ({len(games_data)} en el dataset).")


if __name__ == "__main__":
    main()
