"""
Веб-приложение: форма ввода + генерация методического материала.

Запуск из корня проекта:  python -m app.main
Открыть:                   http://localhost:8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import llm
from .prompts import SYSTEM_PROMPT, build_user_prompt

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="AI-ассистент методиста", version="1.0")


class GenRequest(BaseModel):
    topic: str
    grade: str = "7"
    material_type: str = "lesson"


@app.get("/api/status")
async def status():
    # Дашборд показывает бейдж: реальный Claude или демо-режим.
    return {"live": llm.is_live(), "model": llm.MODEL if llm.is_live() else None}


@app.post("/api/generate")
async def generate(req: GenRequest):
    topic = req.topic.strip()
    if not topic:
        return JSONResponse({"error": "Укажите тему материала."}, status_code=400)

    user_prompt = build_user_prompt(topic, req.grade, req.material_type)
    try:
        text = llm.generate(SYSTEM_PROMPT, user_prompt)
    except Exception as exc:  # не роняем UI на ошибке провайдера
        # детали — только в лог сервера, клиенту общее сообщение (без утечки внутренностей)
        print(f"[generate] ошибка: {exc!r}")
        return JSONResponse(
            {"error": "Не удалось сгенерировать материал. Попробуйте ещё раз позже."},
            status_code=502,
        )

    return {"markdown": text, "live": llm.is_live()}


app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    print("\n  Открой:  http://localhost:8000")
    print("  Режим:  ", "Claude" if llm.is_live() else "демо (нет ANTHROPIC_API_KEY)", "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
