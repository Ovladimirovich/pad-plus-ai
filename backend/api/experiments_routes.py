import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query, Depends, HTTPException

from core.auth_manager import get_current_user

logger = logging.getLogger("padplus.api.experiments")

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent.parent / "experiments"
RUNS_DIR = EXPERIMENTS_DIR / "runs"
REPORTS_DIR = EXPERIMENTS_DIR / "reports"


def _scan_dir(directory: Path) -> list[dict]:
    if not directory.exists():
        return []
    runs = []
    for run_dir in sorted(directory.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        config_path = run_dir / "experiment_config.json"
        raw_path = run_dir / "raw_responses.json"
        report_path = run_dir / "REPORT.md"

        name = run_dir.name
        config = {}
        raw = {}

        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        if raw_path.exists():
            try:
                raw = json.loads(raw_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        total = len(raw.get("results", [])) if raw else 0
        successful = sum(1 for r in raw.get("results", []) if r.get("success")) if raw else 0

        runs.append({
            "name": name,
            "display_name": config.get("name", name),
            "description": config.get("description", ""),
            "provider": config.get("provider", ""),
            "model": config.get("model", ""),
            "profiles": list(config.get("profiles", {}).keys()),
            "timestamp": raw.get("timestamp", ""),
            "total_runs": total,
            "successful": successful,
            "has_report": report_path.exists(),
            "path": str(run_dir),
        })
    return runs


def _process_run_dir(run_dir: Path) -> dict | None:
    """Process a single run directory, return run dict or None."""
    config_path = run_dir / "experiment_config.json"
    raw_path = run_dir / "raw_responses.json"
    report_path = run_dir / "REPORT.md"
    if not raw_path.exists() and not config_path.exists():
        return None

    name = run_dir.name
    config = {}
    raw = {}

    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    if raw_path.exists():
        try:
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    total = len(raw.get("results", [])) if raw else 0
    successful = sum(1 for r in raw.get("results", []) if r.get("success")) if raw else 0

    return {
        "name": name,
        "display_name": config.get("name", name),
        "description": config.get("description", ""),
        "provider": config.get("provider", ""),
        "model": config.get("model", ""),
        "profiles": list(config.get("profiles", {}).keys()),
        "timestamp": raw.get("timestamp", ""),
        "total_runs": total,
        "successful": successful,
        "has_report": report_path.exists(),
        "path": str(run_dir),
    }


def _list_runs() -> list[dict]:
    # Гарантируем наличие директорий (на Render experiments/ не коммитится)
    try:
        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Cannot create experiments dirs: {e}")
    runs = _scan_dir(RUNS_DIR)
    if not EXPERIMENTS_DIR.exists():
        return runs
    for d in sorted(EXPERIMENTS_DIR.iterdir(), reverse=True):
        if d.name.startswith("I-") and d.is_dir():
            entry = _process_run_dir(d)
            if entry:
                runs.append(entry)
    return runs


@router.get("/runs")
async def list_experiments():
    runs = _list_runs()
    return {"runs": runs, "total": len(runs)}


@router.get("/runs/{name}")
async def get_run(name: str):
    run_dir = RUNS_DIR / name
    if not run_dir.exists() or not run_dir.is_dir():
        run_dir = EXPERIMENTS_DIR / name
    if not run_dir.exists() or not run_dir.is_dir():
        from fastapi import HTTPException
        raise HTTPException(404, f"Run '{name}' not found")

    raw_path = run_dir / "raw_responses.json"
    config_path = run_dir / "experiment_config.json"
    report_path = run_dir / "REPORT.md"

    data = {}
    if raw_path.exists():
        try:
            data = json.loads(raw_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to read {raw_path}: {e}")

    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to read {config_path}: {e}")

    report_text = ""
    if report_path.exists():
        try:
            report_text = report_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read {report_path}: {e}")

    return {"name": name, "data": data, "config": config, "report": report_text}


@router.get("/runs/{name}/report")
async def get_run_report(name: str):
    report_path = RUNS_DIR / name / "REPORT.md"
    if not report_path.exists():
        report_path = EXPERIMENTS_DIR / name / "REPORT.md"
    if not report_path.exists():
        from fastapi import HTTPException
        raise HTTPException(404, f"Report for '{name}' not found")

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=report_path.read_text(encoding="utf-8"),
        media_type="text/markdown",
    )


def _extract_profiles(data: dict) -> dict[str, dict]:
    """Извлекает профили из raw_responses.json любого формата."""
    results = data.get("results", [])
    if results and isinstance(results, list):
        return {r["profile"]: r for r in results if "profile" in r}

    # Старый формат: responses {Q1: {summary, vs_...}}
    responses = data.get("responses", {})
    if responses and isinstance(responses, dict):
        profiles = {}
        for qid, resp in responses.items():
            profiles[qid] = {
                "profile": qid,
                "question": qid,
                "response": resp.get("summary", ""),
                "success": True,
            }
        return profiles

    return {}


def _extract_metadata(data: dict) -> dict:
    return {
        "provider": data.get("provider", ""),
        "model": data.get("model", ""),
        "format": "new" if "results" in data else "old" if "responses" in data else "unknown",
    }


@router.get("/compare")
async def compare_runs(
    baseline: str = Query(),
    treatment: str = Query(),
):
    from backend.evals.comparator import compare_runs as compare_fn

    base_path = RUNS_DIR / baseline / "raw_responses.json"
    if not base_path.exists():
        base_path = EXPERIMENTS_DIR / baseline / "raw_responses.json"
    treat_path = RUNS_DIR / treatment / "raw_responses.json"
    if not treat_path.exists():
        treat_path = EXPERIMENTS_DIR / treatment / "raw_responses.json"

    if not base_path.exists():
        from fastapi import HTTPException
        raise HTTPException(404, f"Baseline run '{baseline}' not found")
    if not treat_path.exists():
        from fastapi import HTTPException
        raise HTTPException(404, f"Treatment run '{treatment}' not found")

    base_data = json.loads(base_path.read_text(encoding="utf-8"))
    treat_data = json.loads(treat_path.read_text(encoding="utf-8"))

    profiles_baseline = _extract_profiles(base_data)
    profiles_treatment = _extract_profiles(treat_data)
    all_profiles = sorted(set(list(profiles_baseline.keys()) + list(profiles_treatment.keys())))

    if not all_profiles:
        return {
            "baseline": baseline,
            "treatment": treatment,
            "comparisons": {},
            "profiles": [],
            "status": "no_data",
            "message": "Ни один из запусков не содержит результатов для сравнения. "
                       "Проверьте формат данных — нужен массив results с полем profile.",
            "baseline_meta": _extract_metadata(base_data),
            "treatment_meta": _extract_metadata(treat_data),
        }

    comparisons = {}
    for profile in all_profiles:
        b = profiles_baseline.get(profile)
        t = profiles_treatment.get(profile)
        if b and t:
            comp = compare_fn(
                baseline=b,
                treatment=t,
                baseline_name=baseline,
                treatment_name=treatment,
            )
            comparisons[profile] = comp.to_dict()
        elif b and not t:
            comparisons[profile] = {"error": "только в baseline", "metrics": {}}
        elif t and not b:
            comparisons[profile] = {"error": "только в treatment", "metrics": {}}

    return {
        "baseline": baseline,
        "treatment": treatment,
        "comparisons": comparisons,
        "profiles": all_profiles,
        "status": "ok",
        "baseline_meta": _extract_metadata(base_data),
        "treatment_meta": _extract_metadata(treat_data),
    }


@router.get("/traces")
async def list_traces(limit: int = Query(50, le=200)):
    from core.xray import get_xray_history
    history = get_xray_history()
    sessions = history.list_sessions(limit=limit)
    return {"traces": sessions, "total": len(sessions)}


@router.get("/traces/{trace_id}")
async def get_trace(trace_id: str):
    from core.xray import get_xray_history
    history = get_xray_history()
    trace = history.load_session(trace_id)
    if not trace:
        from fastapi import HTTPException
        raise HTTPException(404, f"Trace '{trace_id}' not found")
    return trace


@router.get("/pipeline/registry")
async def get_pipeline_registry():
    from core.pipeline.registry import get_registry
    reg = get_registry()
    details = reg.list_details()
    return {"phases": [d["name"] for d in details], "details": details, "count": len(details)}


# ─── Eval Scores ──────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"
EVAL_DIMENSIONS = ["completeness", "consistency", "safety", "confidence", "latency_score", "novelty", "overall"]


def _scan_evals(limit: int = 200) -> list[dict]:
    entries = []
    dialogs_dir = DATA_DIR / "dialogs"
    if not dialogs_dir.exists():
        return entries
    for ym_dir in sorted(dialogs_dir.iterdir(), reverse=True):
        if not ym_dir.is_dir():
            continue
        for jsonl_file in sorted(ym_dir.iterdir(), reverse=True):
            if jsonl_file.suffix != ".jsonl":
                continue
            try:
                with open(jsonl_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                eval_data = entry.get("evaluation", {})
                                if eval_data and isinstance(eval_data, dict) and "overall" in eval_data:
                                    entries.append({
                                        "id": entry.get("id", ""),
                                        "timestamp": entry.get("timestamp", ""),
                                        "evaluation": {
                                            k: eval_data.get(k) for k in EVAL_DIMENSIONS
                                            if k in eval_data
                                        },
                                        "strategy": entry.get("metadata", {}).get("strategy", "unknown"),
                                        "provider": entry.get("metadata", {}).get("provider", "unknown"),
                                        "model": entry.get("metadata", {}).get("model", "unknown"),
                                        "response_length": eval_data.get("details", {}).get("response_length", 0),
                                        "prompt_length": eval_data.get("details", {}).get("prompt_length", 0),
                                    })
                            except json.JSONDecodeError:
                                continue
            except OSError:
                continue
            if len(entries) >= limit:
                break
        if len(entries) >= limit:
            break
    return entries


# ─── Snapshots ──────────────────────────────────────────────


@router.post("/snapshot")
async def create_snapshot(label: str = ""):
    from experiments.snapshot import capture_snapshot
    snap = capture_snapshot(label=label)
    return {"snapshot": snap.to_dict(), "status": "created"}


@router.get("/snapshots")
async def list_snapshots(limit: int = 50):
    from experiments.snapshot import list_snapshots as ls
    snaps = ls(limit=limit)
    return {"snapshots": snaps, "total": len(snaps)}


@router.get("/snapshots/{snapshot_id}")
async def get_snapshot(snapshot_id: str):
    from experiments.snapshot import load_snapshot
    snap = load_snapshot(snapshot_id)
    if not snap:
        from fastapi import HTTPException
        raise HTTPException(404, f"Snapshot '{snapshot_id}' not found")
    return {"snapshot": snap.to_dict()}


@router.post("/snapshots/{snapshot_id}/link-to-run/{run_name}")
async def link_snapshot_to_run(snapshot_id: str, run_name: str):
    """Привязывает существующий снэпшот к прогону (записывает snapshot_id в raw_responses.json)."""
    from experiments.snapshot import load_snapshot
    snap = load_snapshot(snapshot_id)
    if not snap:
        from fastapi import HTTPException
        raise HTTPException(404, f"Snapshot '{snapshot_id}' not found")

    run_dir = RUNS_DIR / run_name
    if not run_dir.exists() or not run_dir.is_dir():
        run_dir = EXPERIMENTS_DIR / run_name
    if not run_dir.exists() or not run_dir.is_dir():
        from fastapi import HTTPException
        raise HTTPException(404, f"Run '{run_name}' not found")

    raw_path = run_dir / "raw_responses.json"
    if raw_path.exists():
        try:
            data = json.loads(raw_path.read_text(encoding="utf-8"))
            data["snapshot_id"] = snapshot_id
            raw_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return {"status": "linked", "run": run_name, "snapshot_id": snapshot_id}
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(500, f"Failed to link snapshot: {e}")

    # Нет raw_responses — записываем snapshot_id как отдельный файл
    link_path = run_dir / ".snapshot_link"
    link_path.write_text(snapshot_id, encoding="utf-8")
    return {"status": "linked (no raw_responses)", "run": run_name, "snapshot_id": snapshot_id}


@router.get("/snapshots/{snapshot_id}/decisions")
async def get_snapshot_decisions(snapshot_id: str, limit: int = 100):
    """Решения Decision Log, записанные после снэпшота (кросс-ссылка Snapshot → Decision Log)."""
    from experiments.snapshot import get_snapshot_decisions as gsd
    decisions = gsd(snapshot_id, limit=limit)
    return {"snapshot_id": snapshot_id, "decisions": decisions, "total": len(decisions)}


@router.get("/evals")
async def get_eval_scores(limit: int = 200):
    entries = _scan_evals(limit=limit)
    if not entries:
        return {
            "total_entries": 0,
            "averages": {},
            "by_strategy": {},
            "by_provider": {},
            "timeseries": [],
            "recent": [],
        }

    # averages
    totals: dict[str, float] = {k: 0.0 for k in EVAL_DIMENSIONS}
    for e in entries:
        for k in EVAL_DIMENSIONS:
            v = e["evaluation"].get(k)
            if v is not None:
                totals[k] += float(v)
    n = len(entries)
    averages = {k: round(v / n, 3) for k, v in totals.items()}

    # by strategy
    by_strategy: dict[str, dict] = {}
    for e in entries:
        strat = e["strategy"]
        if strat not in by_strategy:
            by_strategy[strat] = {"count": 0, "sum": {k: 0.0 for k in EVAL_DIMENSIONS}}
        by_strategy[strat]["count"] += 1
        for k in EVAL_DIMENSIONS:
            v = e["evaluation"].get(k)
            if v is not None:
                by_strategy[strat]["sum"][k] += float(v)
    for s, d in by_strategy.items():
        c = d["count"]
        d["averages"] = {k: round(v / c, 3) for k, v in d["sum"].items()}
        d.pop("sum", None)

    # by provider
    by_provider: dict[str, dict] = {}
    for e in entries:
        prov = e["provider"]
        if prov not in by_provider:
            by_provider[prov] = {"count": 0, "sum": {k: 0.0 for k in EVAL_DIMENSIONS}}
        by_provider[prov]["count"] += 1
        for k in EVAL_DIMENSIONS:
            v = e["evaluation"].get(k)
            if v is not None:
                by_provider[prov]["sum"][k] += float(v)
    for p, d in by_provider.items():
        c = d["count"]
        d["averages"] = {k: round(v / c, 3) for k, v in d["sum"].items()}
        d.pop("sum", None)

    # timeseries by date
    by_date: dict[str, dict] = {}
    for e in entries:
        day = e["timestamp"][:10] if e["timestamp"] else "unknown"
        if day not in by_date:
            by_date[day] = {"count": 0, "sum": {k: 0.0 for k in EVAL_DIMENSIONS}}
        by_date[day]["count"] += 1
        for k in EVAL_DIMENSIONS:
            v = e["evaluation"].get(k)
            if v is not None:
                by_date[day]["sum"][k] += float(v)
    timeseries = []
    for day in sorted(by_date.keys()):
        d = by_date[day]
        c = d["count"]
        timeseries.append({
            "date": day,
            "count": c,
            **{k: round(v / c, 3) for k, v in d["sum"].items()},
        })

    return {
        "total_entries": n,
        "averages": averages,
        "by_strategy": by_strategy,
        "by_provider": by_provider,
        "timeseries": timeseries,
        "recent": entries[:20],
    }


@router.post("/replay")
async def replay_trace(
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """
    Replay — повторный прогон сохранённого сценария через тот же pipeline.

    Требует авторизации (как основной чат). API-ключ берётся строго из
    пользовательских ключей (user_api_keys), привязанных к user_id.
    Принимает request_id (из X-Ray history) или user_message + context.
    """
    user_id = current_user["id"]

    request_id = payload.get("request_id")
    user_message = payload.get("user_message")
    context = payload.get("context") or {}

    # Достаём исходное сообщение из истории трассировки, если передан request_id
    if not user_message and request_id:
        try:
            from core.xray.history_recorder import get_xray_history
            trace = get_xray_history().get_trace(request_id)
            if trace:
                user_message = trace.get("user_message")
                if not context and trace.get("thinking_mode"):
                    context = {"replay_strategy": trace.get("thinking_mode")}
        except Exception as e:
            logger.warning(f"Replay history lookup error: {e}")

    if not user_message:
        raise HTTPException(status_code=400, detail="Необходим request_id или user_message")

    # === Извлечение API-ключа пользователя (идентично frontend_routes.py) ===
    api_key = None
    provider = payload.get("provider")
    model = payload.get("model") or "auto"

    try:
        from core.supabase_client import get_db_client
        from core.encryption import get_encryptor

        supabase = get_db_client(current_user)
        encryptor = get_encryptor()

        key_id = payload.get("key_id")
        if key_id:
            key_res = supabase.table("user_api_keys") \
                .select("*").eq("id", key_id).eq("user_id", user_id).execute()
            if key_res.data:
                kd = key_res.data[0]
                raw = encryptor.decrypt(kd["api_key_encrypted"])
                if not isinstance(raw, str):
                    raw = getattr(raw, "text", None) or getattr(raw, "response", None) or str(raw)
                api_key = raw.strip().encode("ascii", errors="ignore").decode("ascii")
                provider = kd["provider"]
                model = kd.get("model_preference") or "auto"

        if not api_key:
            # default-ключ пользователя
            def_res = supabase.table("user_api_keys") \
                .select("*").eq("user_id", user_id).eq("is_default", True).execute()
            if def_res.data:
                kd = def_res.data[0]
                raw = encryptor.decrypt(kd["api_key_encrypted"])
                if not isinstance(raw, str):
                    raw = getattr(raw, "text", None) or getattr(raw, "response", None) or str(raw)
                api_key = raw.strip().encode("ascii", errors="ignore").decode("ascii")
                provider = kd["provider"]
                model = kd.get("model_preference") or "auto"
    except Exception as e:
        logger.warning(f"Replay key lookup error: {e}")

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Не найден API-ключ пользователя. Добавьте ключ в разделе «Провайдеры».",
        )

    try:
        from core.dependencies import get_pipeline
        pipeline = get_pipeline()
        result = await pipeline.execute(
            user_message=user_message,
            context={**context, "user_id": user_id, "key_id": key_id},
            provider=provider,
            api_key=api_key,
        )
    except Exception as e:
        logger.error(f"Replay pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения pipeline: {e}")

    new_request_id = None
    try:
        from api.xray_routes import _latest_pipeline_result
        new_request_id = _latest_pipeline_result.get("request_id") if _latest_pipeline_result else None
    except Exception:
        pass

    return {
        "status": "ok",
        "replay_of": request_id,
        "new_request_id": new_request_id,
        "user_message": user_message,
        "response": result.response,
        "strategy": result.strategy,
        "intent": result.intent,
        "confidence": result.confidence,
        "truth_confidence": result.truth_confidence,
        "execution_time_ms": result.execution_time_ms,
        "success": result.success,
        "provider": result.sources.get("llm", {}).get("provider", ""),
        "model": result.sources.get("llm", {}).get("model", ""),
        "evaluation": result.metadata.get("evaluation"),
        "new_request_id_note": "structured explanation доступен через GET /api/v1/xray/current по new_request_id",
    }


@router.post("/compare-providers")
async def compare_providers(
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """
    Compare Providers — один prompt, один контекст, разные провайдеры.

    Для каждого провайдера прогоняет один и тот же prompt через
    ProviderManager (строго через core_client, без системного прокси),
    оценивает ответ через SelfEvaluator и собирает сводку.
    """
    user_id = current_user["id"]
    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Необходим prompt")

    providers = payload.get("providers") or []
    if not providers:
        # Дефолтный набор: попробовать ключи пользователя
        try:
            from core.supabase_client import get_db_client
            supabase = get_db_client(current_user)
            keys = supabase.table("user_api_keys").select("*").eq("user_id", user_id).execute()
            providers = [
                {"provider": k["provider"], "model": k.get("model_preference") or "auto", "key_id": k["id"]}
                for k in (keys.data or [])
            ]
        except Exception as e:
            logger.warning(f"Compare providers key lookup error: {e}")

    if not providers:
        raise HTTPException(
            status_code=400,
            detail="Не найдены провайдеры. Добавьте ключи в «Провайдеры» или укажите providers вручную.",
        )

    # Подготовка ключей пользователя
    key_map = {}
    try:
        from core.supabase_client import get_db_client
        from core.encryption import get_encryptor
        supabase = get_db_client(current_user)
        encryptor = get_encryptor()
        keys = supabase.table("user_api_keys").select("*").eq("user_id", user_id).execute()
        for k in (keys.data or []):
            raw = encryptor.decrypt(k["api_key_encrypted"])
            if not isinstance(raw, str):
                raw = getattr(raw, "text", None) or getattr(raw, "response", None) or str(raw)
            key_map[k["id"]] = raw.strip().encode("ascii", errors="ignore").decode("ascii")
            key_map[k["provider"]] = key_map[k["id"]]
    except Exception as e:
        logger.warning(f"Compare providers key map error: {e}")

    from runtime.provider_manager import get_provider_manager
    from learning.evaluator import get_evaluator

    pm = get_provider_manager()
    evaluator = get_evaluator()

    results = []
    for p in providers:
        provider = p.get("provider")
        model = p.get("model") or "auto"
        api_key = key_map.get(p.get("key_id")) or key_map.get(provider)
        try:
            import os as _os
            _dbg = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "debug_compare.txt")
            with open(_dbg, "a", encoding="utf-8") as _f:
                _f.write(f"{provider}: api_key_type={type(api_key)} key_map_keys={list(key_map.keys())} p.key_id={p.get('key_id')} api_key_repr={repr(api_key)[:300]}\n")
        except Exception as _ef:
            try:
                _fallback = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "data", "debug_compare_fallback.txt")
                with open(_fallback, "a", encoding="utf-8") as _f:
                    _f.write(f"ERR writing: {_ef}\n")
            except Exception:
                pass
        if not api_key:
            results.append({
                "provider": provider, "model": model,
                "success": False, "error": "нет API-ключа для провайдера",
            })
            continue
        try:
            if not isinstance(api_key, str):
                api_key = getattr(api_key, "text", None) or getattr(api_key, "response", None) or str(api_key)
            api_key = api_key.strip().encode("ascii", errors="ignore").decode("ascii")
            pr = await pm.generate(prompt=prompt, api_key=api_key, model=model, provider=provider, max_tokens=1024)
            _resp_obj = getattr(pr, "response", pr)
            response_text = getattr(_resp_obj, "text", None) or str(_resp_obj)
            meta = {"latency_ms": getattr(pr, "latency_ms", None)}
            eval_result = evaluator.evaluate(prompt=prompt, response=response_text, metadata=meta)
            ev = eval_result.to_dict() if hasattr(eval_result, "to_dict") else eval_result
            results.append({
                "provider": provider,
                "model": getattr(pr, "model", model),
                "success": True,
                "response": response_text,
                "latency_ms": getattr(pr, "latency_ms", None),
                "evaluation": ev,
            })
        except Exception as e:
            import traceback as _tb
            logger.error(f"Compare provider {provider} error: {e}\n{_tb.format_exc()}")
            results.append({
                "provider": provider, "model": model,
                "success": False, "error": f"{type(e).__name__}: {e}",
                "traceback": _tb.format_exc()[-1500:],
            })

    # Сохраняем как run для replay/сравнения
    run_name = f"compare-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    try:
        run_dir = RUNS_DIR / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "experiment_config.json").write_text(json.dumps({
            "name": "Compare Providers",
            "description": prompt[:200],
            "type": "compare_providers",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        (run_dir / "raw_responses.json").write_text(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "results": results,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Compare providers save error: {e}")

    return {
        "status": "ok",
        "prompt": prompt,
        "run_name": run_name,
        "results": results,
    }


@router.get("/_debug_compare")
async def _debug_compare():
    """Временная диагностика (GET, без CSRF): подтверждает версию кода."""
    return {"status": "ok", "code_version": "v3-with-debug", "file": __file__}


SEED_EXPERIMENTS = [
    {"prompt": "Объясни разницу между корутинами и потоками в одном абзаце.", "providers": []},
    {"prompt": "Напиши краткий план исследования по влиянию LLM на образование.", "providers": []},
    {"prompt": "Сформулируй 3 гипотезы, почему пользователи доверяют AI-ассистентам.", "providers": []},
    {"prompt": "Какие риски несёт автоматизация принятия решений? Дай структурированный ответ.", "providers": []},
    {"prompt": "Переведи на английский: 'Когнитивная архитектура требует баланса между эмоциями и логикой.'", "providers": []},
]


@router.get("/seed-experiments")
async def get_seed_experiments():
    """Готовые prompts для Compare Providers (чтобы UI не пустовал)."""
    return {"seeds": SEED_EXPERIMENTS}
