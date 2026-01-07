"""FastAPI pour exposer les séances stockées dans Supabase."""
import os
from datetime import date
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def build_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Configurer SUPABASE_URL et SUPABASE_KEY dans l'environnement")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


try:
    supabase: Client | None = build_supabase_client()
    supabase_init_error: Exception | None = None
except Exception as exc:  # pragma: no cover - init errors are surfaced via the API
    supabase = None
    supabase_init_error = exc


class Cinema(BaseModel):
    id: int
    name: str
    address: str | None = None
    url: str | None = None


class Movie(BaseModel):
    id: int
    title: str


class Showtime(BaseModel):
    id: int
    showtime_date: date
    time: str
    details: str | None = None
    cinema: Cinema
    movie: Movie


app = FastAPI(title="Allocinoche API", version="0.1.0")


def require_supabase() -> Client:
    if supabase_init_error:
        raise HTTPException(status_code=500, detail=f"Supabase init failed: {supabase_init_error}")
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not available")
    return supabase


async def fetch_showtimes(
    day: date | None,
    cinema_id: int | None,
    client: Client,
) -> List[Showtime]:
    """Récupère les séances avec jointure cinéma/film, filtrées sur un jour et/ou un cinéma."""
    query = client.table("showtimes").select(
        "id, showtime_date, time, details, cinemas ( id, name, address, url ), movies ( id, title )"
    )
    if day:
        query = query.eq("showtime_date", day.isoformat())
    if cinema_id:
        query = query.eq("cinema_id", cinema_id)
    query = query.order("showtime_date").order("time")

    response = await run_in_threadpool(query.execute)
    if getattr(response, "error", None):
        raise HTTPException(status_code=502, detail=f"Supabase error: {response.error}")

    rows = response.data or []
    return [
        Showtime(
            id=row["id"],
            showtime_date=date.fromisoformat(row["showtime_date"]),
            time=row["time"],
            details=row.get("details"),
            cinema=Cinema(**row.get("cinemas", {})),
            movie=Movie(**row.get("movies", {})),
        )
        for row in rows
    ]


@app.get("/health")
async def health() -> dict:
    if supabase_init_error:
        raise HTTPException(status_code=500, detail=f"Supabase init failed: {supabase_init_error}")
    return {"status": "ok"}


@app.get("/showtimes", response_model=List[Showtime])
async def list_showtimes(
    day: date | None = Query(None, description="Jour au format YYYY-MM-DD"),
    cinema_id: int | None = Query(None, description="Identifiant du cinéma"),
) -> List[Showtime]:
    client = require_supabase()
    showtimes = await fetch_showtimes(day, cinema_id, client)
    if (day or cinema_id) and not showtimes:
        raise HTTPException(status_code=404, detail="Aucune séance trouvée")
    return showtimes
