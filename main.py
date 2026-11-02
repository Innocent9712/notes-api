import os

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

app = FastAPI(title="Notes API", version="1.0.0")


class Note(BaseModel):
    title: str
    body: str = ""


@app.get("/health")
def health():
    try:
        r.ping()
    except redis.RedisError:
        raise HTTPException(status_code=503, detail="redis unavailable")
    return {"status": "ok", "redis": "up"}


@app.get("/hits")
def hits():
    return {"hits": r.incr("hits")}


@app.post("/notes", status_code=201)
def create_note(note: Note):
    note_id = r.incr("note:id")
    r.hset(f"note:{note_id}", mapping=note.model_dump())
    r.sadd("notes", note_id)
    return {"id": note_id, **note.model_dump()}


@app.get("/notes")
def list_notes():
    ids = sorted(r.smembers("notes"), key=int)
    return [{"id": int(i), **r.hgetall(f"note:{i}")} for i in ids]


@app.get("/notes/{note_id}")
def get_note(note_id: int):
    data = r.hgetall(f"note:{note_id}")
    if not data:
        raise HTTPException(status_code=404, detail="note not found")
    return {"id": note_id, **data}
