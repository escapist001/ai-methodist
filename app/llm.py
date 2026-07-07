"""
Слой работы с языковой моделью.

Одна функция generate(): если задан ANTHROPIC_API_KEY — идём в Claude через
официальный SDK; если ключа нет — возвращаем демо-заглушку, чтобы приложение
работало и его можно было показать без ключа и без затрат.

Провайдер спрятан за одной функцией: заменить модель или провайдера можно здесь,
не трогая остальной код.
"""

import os
import re
import time

MODEL = "claude-opus-4-8"  # актуальная модель Claude на момент разработки

try:
    import anthropic
except ImportError:  # SDK может быть не установлен в демо-окружении
    anthropic = None


def is_live() -> bool:
    """Есть ли ключ и SDK для реальной генерации через Claude."""
    return bool(os.environ.get("ANTHROPIC_API_KEY")) and anthropic is not None


def generate(system: str, user: str) -> str:
    """Сгенерировать материал. Реальный Claude или демо-заглушка."""
    if not is_live():
        return _demo(user)

    client = anthropic.Anthropic()
    # Стримим ответ: у методических материалов большой max_tokens, а стриминг
    # спасает от таймаутов на длинных ответах. Итоговый текст собираем целиком.
    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        message = stream.get_final_message()

    return "".join(block.text for block in message.content if block.type == "text")


def stream_generate(system: str, user: str):
    """Потоковая генерация: отдаём материал кусками по мере готовности.

    Live — токены Claude по мере ответа модели (эффект набора текста и защита
    от таймаутов на длинных материалах). Demo — заглушку «печатаем» по словам.
    """
    if not is_live():
        yield from _demo_stream(user)
        return

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        for text in stream.text_stream:
            yield text


def _demo_stream(user: str):
    """«Печатаем» демо-заглушку по словам — чтобы эффект набора работал без ключа."""
    for token in re.findall(r"\S+\s*|\n", _demo(user)):
        yield token
        time.sleep(0.012)


def _demo(user: str) -> str:
    """Заглушка на случай отсутствия ключа — чтобы UI был живым."""
    return (
        "> ⚠️ **Демо-режим.** Ключ Claude не задан, показан пример-заглушка. "
        "Добавьте `ANTHROPIC_API_KEY` в `.env`, чтобы получать настоящую генерацию.\n\n"
        "# Конспект урока (пример)\n\n"
        f"*Запрос:* {user}\n\n"
        "## Планируемые результаты (ФГОС)\n"
        "- **Предметные:** ученик формулирует закон и применяет его к расчётной задаче.\n"
        "- **Метапредметные:** ставит цель опыта, анализирует данные, делает вывод.\n"
        "- **Личностные:** проявляет интерес к физическому объяснению явлений.\n\n"
        "## Цель урока\n"
        "Сформировать понимание изучаемого закона и умение применять его на практике.\n\n"
        "## Ход урока\n"
        "1. **Мотивация (5 мин).** Демонстрация явления, проблемный вопрос.\n"
        "2. **Изучение нового (20 мин).** Вывод соотношения, разбор примера F = m·a.\n"
        "3. **Закрепление (12 мин).** Решение задач в парах.\n"
        "4. **Рефлексия (3 мин).** Что нового узнали, где применимо.\n\n"
        "*(Это заглушка. С реальным ключом Claude материал будет полным и уникальным "
        "под вашу тему и класс.)*"
    )
