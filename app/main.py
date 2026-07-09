"""FastAPI backend for the text-to-SQL chat UI.

Serves the static frontend and exposes POST /api/ask, which wraps
text_to_sql.ask(). Run with: uvicorn main:app --reload --app-dir app
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from text_to_sql import ask

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Retail Lakehouse — Text-to-SQL")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class Question(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    sql: str
    columns: list[str]
    rows: list[list]


def _serialize(value):
    if value is None or isinstance(value, (int, float, str, bool)):
        return value
    return str(value)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/ask", response_model=AnswerResponse)
def ask_question(payload: Question):
    try:
        sql_text, columns, rows = ask(payload.question)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    return AnswerResponse(
        sql=sql_text,
        columns=columns,
        rows=[[_serialize(value) for value in row] for row in rows],
    )
