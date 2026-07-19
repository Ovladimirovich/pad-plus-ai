"""
🔬 X-Ray API Routes

Эндпоинты для системы полной наблюдаемости X-Ray
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger("padplus.xray")

router = APIRouter(prefix="/api/v1/xray", tags=["xray"])

# In-memory store for latest pipeline result
_latest_pipeline_result: Optional[Dict] = None


def set_latest_pipeline_result(result: dict):
    global _latest_pipeline_result
    _latest_pipeline_result = result


@router.get("/latest")
async def get_latest_pipeline_result():
    """Последний результат выполнения pipeline"""
    if _latest_pipeline_result is None:
        return {"status": "no_data", "message": "Нет данных. Отправьте запрос в чат."}
    return _latest_pipeline_result


@router.get("/current")
async def get_current_response():
    """
    Агрегированный «срез текущего ответа» для UI Microscope.

    Объединяет: последний pipeline-result, активную/последнюю сессию
    трассировки (фазы, метрики) и структурированное объяснение (explanation).
    Единый payload — без дублирующих endpoint-ов.
    """
    if _latest_pipeline_result is None:
        return {"status": "no_data", "message": "Нет данных. Отправьте запрос в чат."}

    latest = _latest_pipeline_result
    # Поддержка обоих форматов latest (pipeline.execute и fallback pm.generate)
    request_id = latest.get("request_id")
    pipeline = latest.get("pipeline", {})
    if not isinstance(pipeline, dict):
        pipeline = {}

    trace_session = None
    explanation = None
    if request_id:
        try:
            from core.xray import get_trace_collector
            session = get_trace_collector().get_session(request_id)
            if session is not None:
                trace_session = session.get_summary()
                trace_session["events"] = [e.to_dict() for e in session.events]
                explanation = (session.metadata or {}).get("explanation")
        except Exception as e:
            logger.warning(f"X-Ray current trace error: {e}")

    # Fallback: если request_id нет (fallback-ветка чата), берём последний trace из history
    if trace_session is None:
        try:
            from core.xray.history_recorder import get_xray_history
            traces = get_xray_history().list_sessions(limit=1)
            if traces:
                last = get_xray_history().get_trace(traces[0]["id"])
                if last:
                    trace_session = last
                    request_id = last.get("id")
                    explanation = (last.get("metadata") or {}).get("explanation")
        except Exception as e:
            logger.warning(f"X-Ray current history lookup error: {e}")

    eval_data = None
    if trace_session:
        _expl = (trace_session.get("metadata") or {}).get("explanation", {}) or {}
        # Новое поле explanation.evaluation (score/passed/summary/details)
        eval_data = _expl.get("evaluation") or _expl.get("evaluation_notes")

    return {
        "status": "ok",
        "user_message": latest.get("user_message"),
        "session_id": latest.get("session_id"),
        "request_id": request_id,
        "timestamp": latest.get("timestamp"),
        "strategy": pipeline.get("strategy"),
        "intent": pipeline.get("intent"),
        "provider": latest.get("provider"),
        "model": latest.get("model"),
        "confidence": pipeline.get("confidence"),
        "truth_confidence": pipeline.get("truth_confidence"),
        "latency_ms": pipeline.get("execution_time_ms"),
        "success": pipeline.get("success"),
        "phases": _build_phase_view(trace_session),
        "metrics": {
            "confidence": pipeline.get("confidence"),
            "truth_confidence": pipeline.get("truth_confidence"),
            "latency_ms": pipeline.get("execution_time_ms"),
        },
        "evaluation": eval_data,
        "explanation": explanation,
        "trace": trace_session,
    }


def _build_phase_view(trace_session: Optional[dict]) -> List[dict]:
    """Компактное представление фаз из сессии трассировки"""
    if not trace_session or not trace_session.get("events"):
        return []
    phases = []
    for ev in trace_session["events"]:
        phases.append({
            "phase": ev.get("data", {}).get("phase") or ev.get("stage"),
            "stage": ev.get("stage"),
            "status": ev.get("status"),
            "duration_ms": ev.get("duration_ms"),
            "error": ev.get("error"),
        })
    return phases


@router.get("/")
async def xray_root():
    """Информация о X-Ray системе"""
    from core.xray import (
        get_trace_collector,
        get_thought_visualizer,
        get_xray_broadcaster,
        get_xray_history
    )
    
    collector = get_trace_collector()
    visualizer = get_thought_visualizer()
    broadcaster = get_xray_broadcaster()
    recorder = get_xray_history()
    
    return {
        "name": "X-Ray System",
        "version": "1.0.0",
        "description": "Система полной наблюдаемости AI",
        "components": {
            "trace_collector": collector.get_stats(),
            "thought_visualizer": visualizer.get_stats(),
            "broadcaster": broadcaster.get_stats(),
            "history_recorder": recorder.get_stats()
        }
    }


@router.get("/sessions")
async def get_xray_sessions(limit: int = Query(10, le=50)):
    """Список сессий трассировки"""
    from core.xray import get_xray_history
    
    recorder = get_xray_history()
    sessions = recorder.list_sessions(limit=limit)
    
    return {
        "sessions": sessions,
        "total": len(sessions)
    }


@router.get("/sessions/{session_id}")
async def get_xray_session(session_id: str):
    """Детали конкретной сессии"""
    from core.xray import get_xray_history
    
    recorder = get_xray_history()
    session = recorder.load_session(session_id)
    
    if not session:
        return {"error": "Сессия не найдена", "status_code": 404}
    
    return session


@router.get("/sessions/{session_id}/export")
async def export_xray_session(
    session_id: str, 
    format: str = Query("json", pattern="^(json|csv)$")
):
    """Экспорт сессии в JSON или CSV"""
    from core.xray import get_xray_history
    
    recorder = get_xray_history()
    data = recorder.export_session(session_id, format=format)
    
    if not data:
        return {"error": "Сессия не найдена", "status_code": 404}
    
    if format == "csv":
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=xray_{session_id}.csv"
            }
        )
    
    return {"data": data}


@router.delete("/sessions/{session_id}")
async def delete_xray_session(session_id: str):
    """Удаление сессии"""
    from core.xray import get_xray_history
    
    recorder = get_xray_history()
    deleted = recorder.delete_session(session_id)
    
    if not deleted:
        return {"error": "Сессия не найдена", "status_code": 404}
    
    return {"message": "Сессия удалена"}


@router.get("/stats")
async def get_xray_stats():
    """Общая статистика X-Ray системы"""
    from core.xray import (
        get_trace_collector,
        get_thought_visualizer,
        get_xray_broadcaster,
        get_xray_history
    )
    
    collector = get_trace_collector()
    visualizer = get_thought_visualizer()
    broadcaster = get_xray_broadcaster()
    recorder = get_xray_history()
    
    return {
        "trace_collector": collector.get_stats(),
        "thought_visualizer": visualizer.get_stats(),
        "broadcaster": broadcaster.get_stats(),
        "history_recorder": recorder.get_stats()
    }


@router.get("/active")
async def get_active_sessions():
    """Активные сессии трассировки"""
    from core.xray import get_trace_collector
    
    collector = get_trace_collector()
    sessions = collector.get_active_sessions()
    
    return {
        "active_sessions": [s.get_summary() for s in sessions],
        "count": len(sessions)
    }


@router.websocket("/ws")
async def xray_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket подключение для real-time X-Ray событий
    
    Каналы:
    - trace: события трассировки
    - thought: поток мыслей
    - pipeline: статус пайплайна
    - emotion: эмоции
    - decision: принятие решений
    - all: все события
    """
    from core.xray import get_xray_broadcaster
    
    broadcaster = get_xray_broadcaster()
    
    await websocket.accept()
    
    # Генерируем уникальный ID клиента
    client_id = f"xray_{id(websocket)}"
    
    # Подключаем клиента
    await broadcaster.connect(client_id, websocket)
    
    try:
        while True:
            # Получаем сообщения от клиента
            data = await websocket.receive_text()
            
            try:
                import json
                message = json.loads(data)
                
                # Обработка команд
                if message.get("type") == "subscribe":
                    channels = message.get("channels", [])
                    broadcaster.subscribe(client_id, channels)
                    
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "channels": channels,
                        "timestamp": asyncio.get_event_loop().time()
                    }, ensure_ascii=False))
                
                elif message.get("type") == "unsubscribe":
                    channels = message.get("channels", [])
                    broadcaster.unsubscribe(client_id, channels)
                
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time()
                    }, ensure_ascii=False))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON",
                    "timestamp": asyncio.get_event_loop().time()
                }, ensure_ascii=False))
    
    except WebSocketDisconnect:
        logger.info(f"🔬 X-Ray WebSocket отключен: {client_id}")
    finally:
        broadcaster.disconnect(client_id)


@router.post("/trace/start")
async def start_trace_session(
    user_message: str,
    metadata: Optional[Dict] = None
):
    """Начало сессии трассировки"""
    from core.xray import get_trace_collector
    
    collector = get_trace_collector()
    request_id = collector.start_session(user_message, metadata)
    
    return {
        "request_id": request_id,
        "user_message": user_message,
        "started": True
    }


@router.post("/trace/complete")
async def complete_trace_session(
    request_id: str,
    final_data: Optional[Dict] = None
):
    """Завершение сессии трассировки"""
    from core.xray import get_trace_collector
    
    collector = get_trace_collector()
    collector.complete_session(request_id, final_data)
    
    return {
        "request_id": request_id,
        "completed": True
    }


@router.get("/recent")
async def get_recent_traces(limit: int = Query(10, le=50)):
    """Последние завершенные трассировки"""
    from core.xray import get_trace_collector
    
    collector = get_trace_collector()
    traces = collector.get_recent_sessions(limit=limit)
    
    return {
        "traces": traces,
        "count": len(traces)
    }


@router.get("/pipeline/stages")
async def get_pipeline_stages():
    """
    Список стадий пайплайна для визуализации
    
    Возвращает структуру, совместимую с XRayPipeline.jsx
    """
    return {
        "stages": [
            {"id": "input", "label": "Input", "icon": "📥", "description": "Входные данные"},
            {"id": "safety", "label": "Safety", "icon": "🛡️", "description": "Проверка безопасности"},
            {"id": "intent", "label": "Intent", "icon": "🎯", "description": "Классификация намерения"},
            {"id": "retrieve", "label": "Retrieve", "icon": "🔍", "description": "Поиск в памяти"},
            {"id": "persona", "label": "Persona", "icon": "👤", "description": "Контекст личности"},
            {"id": "generate", "label": "Generate", "icon": "🤖", "description": "Генерация ответа"},
            {"id": "verify", "label": "Verify", "icon": "✅", "description": "Верификация"},
            {"id": "remember", "label": "Remember", "icon": "💾", "description": "Сохранение"},
            {"id": "output", "label": "Output", "icon": "📤", "description": "Выходные данные"}
        ]
    }


@router.get("/brain/status")
async def get_brain_status():
    """Статус X-Ray Brain (устаревший - brain удалён)"""
    from core.xray import get_system_state_manager, get_meta_learner, get_reflection_loop
    state_manager = get_system_state_manager()
    meta = get_meta_learner()
    reflection = get_reflection_loop()
    
    return {
        "brain": {"status": "deprecated", "message": "XRayBrain was removed"},
        "system_state": state_manager.get_stats()["current_state"],
        "meta_learner": meta.get_stats(),
        "reflection": reflection.get_stats()
    }


@router.get("/brain/strategies")
async def get_brain_strategies():
    """Статистика по стратегиям Brain"""
    from core.xray import get_meta_learner
    
    meta = get_meta_learner()
    return meta.get_stats()


@router.post("/brain/strategy")
async def set_brain_strategy(body: dict):
    """Принудительно установить стратегию обработки.
    Тело: {"strategy": "reflective"} или {"strategy": ""} для авто.
    Доступные: simple, retrieval, reasoning, creative, reflective, learning
    """
    strategy = body.get("strategy", "")
    valid = {"simple", "retrieval", "reasoning", "creative", "reflective", "learning", ""}

    if strategy not in valid:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимая стратегия. Допустимые: {', '.join(v for v in valid if v)}",
        )

    from core.pipeline.executor import set_strategy_override
    set_strategy_override(strategy or None)

    from core.xray import get_meta_learner
    meta = get_meta_learner()

    return {
        "status": "ok",
        "strategy": strategy or "auto",
        "override_active": bool(strategy),
        "strategies": meta.get_stats(),
    }
