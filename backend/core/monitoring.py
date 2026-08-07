"""
📊 Monitoring — Система мониторинга и алертинга для PAD+ AI

Предоставляет:
- Health checks
- Performance metrics
- Error tracking
- Resource monitoring
- Alerting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

import os

# Пытаемся импортировать psutil
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

from core.config_manager import get_config
from core.cache_manager import get_cache_manager

logger = logging.getLogger("padplus.monitoring")


@dataclass
class SystemMetrics:
    """Метрики системы"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: int
    network_recv: int
    active_connections: int
    response_time_avg: float
    error_rate: float
    cache_hit_rate: float
    queue_size: int
    # Session isolation metrics
    active_sessions: int = 0
    session_isolation_ok: bool = True
    emotion_leakage_detected: int = 0
    impulse_leakage_detected: int = 0
    session_store_errors: int = 0


@dataclass
class Alert:
    """Алерт"""
    severity: str  # info, warning, error, critical
    category: str
    message: str
    timestamp: datetime
    resolved: bool = False


class MonitoringSystem:
    """
    📊 Система мониторинга
    
    Собирает метрики, отслеживает производительность и отправляет алерты
    """
    
    def __init__(self):
        self.config = get_config()
        self.cache_manager = get_cache_manager()
        self.metrics_history: deque = deque(maxlen=1000)
        self.alerts: List[Alert] = []
        self.alert_rules = self._load_alert_rules()
        self.performance_stats = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.start_time = datetime.now()
        self.monitoring_task: Optional[asyncio.Task] = None
        self._connections_getter: Optional[Callable[[], int]] = None
        self._queue_size_getter: Optional[Callable[[], int]] = None
        
        # Пороги для алертов (из .env или по умолчанию)
        self.thresholds = {
            "cpu_critical": float(os.getenv("MON_CPU_CRITICAL", "90.0")),
            "cpu_warning": float(os.getenv("MON_CPU_WARNING", "70.0")),
            "memory_critical": float(os.getenv("MON_MEM_CRITICAL", "90.0")),
            "memory_warning": float(os.getenv("MON_MEM_WARNING", "70.0")),
            "disk_critical": float(os.getenv("MON_DISK_CRITICAL", "95.0")),
            "disk_warning": float(os.getenv("MON_DISK_WARNING", "80.0")),
            "response_time_critical": float(os.getenv("MON_RESP_TIME_CRITICAL", "5.0")),
            "response_time_warning": float(os.getenv("MON_RESP_TIME_WARNING", "2.0")),
            "error_rate_critical": float(os.getenv("MON_ERROR_RATE_CRITICAL", "0.1")),
            "error_rate_warning": float(os.getenv("MON_ERROR_RATE_WARNING", "0.05")),
            "cache_hit_rate_critical": float(os.getenv("MON_CACHE_HIT_CRITICAL", "0.3")),
            "cache_hit_rate_warning": float(os.getenv("MON_CACHE_HIT_WARNING", "0.5")),
        }
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Загружает правила алертинга из конфигурации"""
        return {
            "cpu_high": {
                "condition": lambda m: m.cpu_percent > self.thresholds["cpu_critical"],
                "message": "High CPU usage detected",
                "severity": "critical"
            },
            "memory_high": {
                "condition": lambda m: m.memory_percent > self.thresholds["memory_critical"],
                "message": "High memory usage detected",
                "severity": "critical"
            },
            "response_time_high": {
                "condition": lambda m: m.response_time_avg > self.thresholds["response_time_critical"],
                "message": "High response time detected",
                "severity": "warning"
            },
            "error_rate_high": {
                "condition": lambda m: m.error_rate > self.thresholds["error_rate_critical"],
                "message": "High error rate detected",
                "severity": "critical"
            },
            "cache_hit_rate_low": {
                "condition": lambda m: m.cache_hit_rate < self.thresholds["cache_hit_rate_critical"] and self._cache_total_lookups() >= 20,
                "message": "Low cache hit rate detected",
                "severity": "warning"
            },
            # Session isolation alerts
            "session_isolation_broken": {
                "condition": lambda m: not m.session_isolation_ok,
                "message": "Session isolation broken: emotion/impulse leakage detected",
                "severity": "critical"
            },
            "session_emotion_leakage": {
                "condition": lambda m: m.emotion_leakage_detected > 0,
                "message": f"Emotion leakage detected across {{m.emotion_leakage_detected}} sessions",
                "severity": "critical"
            },
            "session_impulse_leakage": {
                "condition": lambda m: m.impulse_leakage_detected > 0,
                "message": f"Impulse leakage detected across {{m.impulse_leakage_detected}} sessions",
                "severity": "critical"
            },
            "session_store_errors": {
                "condition": lambda m: m.session_store_errors > 5,
                "message": f"High session store error rate: {{m.session_store_errors}} errors",
                "severity": "warning"
            },
            "too_many_active_sessions": {
                "condition": lambda m: m.active_sessions > 100,
                "message": f"High number of active sessions: {{m.active_sessions}}",
                "severity": "warning"
            }
        }
    
    async def start_monitoring(self):
        """Запускает фоновый мониторинг"""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            logger.info("📊 Мониторинг запущен")
    
    async def stop_monitoring(self):
        """Останавливает фоновый мониторинг"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("📊 Мониторинг остановлен")
    
    async def _monitoring_loop(self):
        """Фоновый цикл мониторинга"""
        while True:
            try:
                await self._collect_metrics()
                await self._check_alerts()
                await asyncio.sleep(30)  # Сбор метрик каждые 30 секунд
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(60)  # Пауза при ошибке
    
    async def _collect_metrics(self):
        """Собирает системные метрики"""
        try:
            # Системные метрики
            if HAS_PSUTIL:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
            else:
                cpu_percent = 0.0
                memory = type('obj', (object,), {'percent': 0.0})()
                disk = type('obj', (object,), {'percent': 0.0})()
                network = type('obj', (object,), {'bytes_sent': 0, 'bytes_recv': 0})()
            
            # Прикладные метрики
            cache_stats = self.cache_manager.get_stats()
            response_time_avg = self._calculate_avg_response_time()
            error_rate = self._calculate_error_rate()
            active_connections = self._get_active_connections()
            queue_size = self._get_queue_size()
            
            # Session isolation metrics
            session_metrics = await self._collect_session_metrics()
            
            # Создаем метрики
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                network_sent=network.bytes_sent,
                network_recv=network.bytes_recv,
                active_connections=active_connections,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                cache_hit_rate=cache_stats.get("memory", {}).get("hit_rate", 0.0),
                queue_size=queue_size,
                active_sessions=session_metrics.get("active_sessions", 0),
                session_isolation_ok=session_metrics.get("isolation_ok", True),
                emotion_leakage_detected=session_metrics.get("emotion_leakage", 0),
                impulse_leakage_detected=session_metrics.get("impulse_leakage", 0),
                session_store_errors=session_metrics.get("store_errors", 0)
            )
            
            self.metrics_history.append(metrics)
            logger.debug(f"📊 Метрики собраны: CPU={cpu_percent:.1f}%, Memory={memory.percent:.1f}%")
            
        except Exception as e:
            logger.error(f"Ошибка сбора метрик: {e}")
    
    def set_connections_getter(self, getter: Callable[[], int]) -> None:
        """Регистрирует функцию получения активных соединений"""
        self._connections_getter = getter

    def set_queue_size_getter(self, getter: Callable[[], int]) -> None:
        """Регистрирует функцию получения размера очереди"""
        self._queue_size_getter = getter

    def _calculate_avg_response_time(self) -> float:
        """Рассчитывает среднее время ответа по реальным данным"""
        response_times = self.performance_stats.get("response_times", [])
        if response_times:
            return sum(response_times) / len(response_times)
        return 0.0

    def _calculate_error_rate(self) -> float:
        """Рассчитывает rate ошибок"""
        total_requests = sum(self.error_counts.values()) + sum(
            self.performance_stats["success"]
        )
        if total_requests == 0:
            return 0.0
        error_count = sum(self.error_counts.values())
        return error_count / total_requests

    def _get_active_connections(self) -> int:
        """Получает количество активных соединений"""
        if self._connections_getter:
            return self._connections_getter()
        return 0

    def _get_queue_size(self) -> int:
        """Получает размер очереди задач"""
        if self._queue_size_getter:
            return self._queue_size_getter()
        return 0
    
    def _cache_total_lookups(self) -> int:
        """Общее количество обращений к кэшу (для фильтрации ложных алертов)"""
        try:
            stats = self.cache_manager.get_stats()
            mem = stats.get("memory", {})
            redis = stats.get("redis", {})
            return mem.get("hits", 0) + mem.get("misses", 0) + redis.get("hits", 0) + redis.get("misses", 0)
        except Exception:
            return 0
    
    async def _collect_session_metrics(self) -> Dict[str, Any]:
        """Собирает метрики сессионной изоляции"""
        try:
            metrics = {
                "active_sessions": 0,
                "isolation_ok": True,
                "emotion_leakage": 0,
                "impulse_leakage": 0,
                "store_errors": 0
            }
            
            # Emotion store
            try:
                from emotion.session_store import get_session_emotion_store
                emotion_store = get_session_emotion_store()
                emotion_count = emotion_store.get_active_count()
                metrics["active_sessions"] = emotion_count
            except Exception as e:
                logger.debug(f"Emotion store metrics error: {e}")
                metrics["store_errors"] += 1
            
            # Impulse store
            try:
                from core.impulse.session_store import get_session_impulse_store
                impulse_store = get_session_impulse_store()
                impulse_count = impulse_store.get_active_count()
                metrics["active_sessions"] = max(metrics["active_sessions"], impulse_count)
            except Exception as e:
                logger.debug(f"Impulse store metrics error: {e}")
                metrics["store_errors"] += 1
            
            # Check for leakage - simplified check
            # In real implementation, would compare cross-session data
            metrics["isolation_ok"] = True
            metrics["emotion_leakage"] = 0
            metrics["impulse_leakage"] = 0
            
            return metrics
        except Exception as e:
            logger.error(f"Session metrics collection error: {e}")
            return {
                "active_sessions": 0,
                "isolation_ok": False,
                "emotion_leakage": 0,
                "impulse_leakage": 0,
                "store_errors": 1
            }
    
    async def _check_alerts(self):
        """Проверяет условия для алертов"""
        if not self.metrics_history:
            return
        
        latest_metrics = self.metrics_history[-1]
        
        for rule_name, rule in self.alert_rules.items():
            if rule["condition"](latest_metrics):
                alert = Alert(
                    severity=rule["severity"],
                    category=rule_name,
                    message=rule["message"],
                    timestamp=datetime.now()
                )
                await self._send_alert(alert)
    
    async def _send_alert(self, alert: Alert):
        """Отправляет алерт"""
        # Проверяем, не было ли уже такого алерта
        for existing_alert in self.alerts:
            if (existing_alert.category == alert.category and
                not existing_alert.resolved and
                (datetime.now() - existing_alert.timestamp).seconds < 300):  # 5 минут
                return
        
        self.alerts.append(alert)
        logger.warning(f"🚨 Алерт [{alert.severity}]: {alert.message}")
        
        # Здесь можно добавить отправку в Slack, Telegram, email и т.д.
        await self._notify_alert(alert)

    async def _notify_alert(self, alert: Alert):
        """Уведомляет о алерте (интеграция с внешними сервисами)"""
        # Заглушка для интеграции с внешними сервисами уведомлений
        # Можно добавить Slack, Telegram, email и т.д.
        pass
    
    def record_request(self, endpoint: str, response_time: float, success: bool = True):
        """Регистрирует запрос для статистики"""
        self.performance_stats["response_times"].append(response_time)
        if success:
            self.performance_stats["success"].append(1)
        else:
            self.performance_stats["success"].append(0)
            self.error_counts[endpoint] += 1
    
    def record_error(self, error_type: str, error_message: str):
        """Регистрирует ошибку"""
        self.error_counts[error_type] += 1
        logger.error(f"❌ Ошибка [{error_type}]: {error_message}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Возвращает статус здоровья системы"""
        if not self.metrics_history:
            return {"status": "unknown", "message": "Нет данных"}
        
        latest = self.metrics_history[-1]
        critical_alerts = [a for a in self.alerts if a.severity == "critical" and not a.resolved]
        warning_alerts = [a for a in self.alerts if a.severity == "warning" and not a.resolved]
        
        # Определяем статус
        if critical_alerts:
            status = "critical"
        elif warning_alerts:
            status = "warning"
        elif (latest.cpu_percent < self.thresholds["cpu_warning"] and
              latest.memory_percent < self.thresholds["memory_warning"] and
              latest.response_time_avg < self.thresholds["response_time_warning"] and
              latest.error_rate < self.thresholds["error_rate_warning"]):
            status = "healthy"
        else:
            status = "degraded"
        
        return {
            "status": status,
            "uptime": str(datetime.now() - self.start_time),
            "latest_metrics": asdict(latest),
            "active_alerts": {
                "critical": len(critical_alerts),
                "warning": len(warning_alerts)
            },
            "error_counts": dict(self.error_counts),
            "cache_stats": self.cache_manager.get_stats()
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Возвращает отчет о производительности"""
        if not self.performance_stats["response_times"]:
            return {"message": "Нет данных о производительности"}
        
        response_times = self.performance_stats["response_times"]
        success_count = sum(self.performance_stats["success"])
        total_count = len(self.performance_stats["success"])
        
        return {
            "total_requests": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": sorted(response_times)[int(0.95 * len(response_times))],
            "error_breakdown": dict(self.error_counts)
        }
    
    def get_metrics_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Возвращает историю метрик за указанное количество часов"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff]
        return [asdict(m) for m in recent_metrics]
    
    def clear_alerts(self, category: Optional[str] = None):
        """Очищает алерты"""
        if category:
            for alert in self.alerts:
                if alert.category == category:
                    alert.resolved = True
        else:
            self.alerts = []
        logger.info(f"✅ Алерты очищены: {category or 'все'}")


# Глобальный экземпляр
_monitoring_system: Optional[MonitoringSystem] = None


def get_monitoring_system() -> MonitoringSystem:
    """Возвращает глобальную систему мониторинга"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = MonitoringSystem()
    return _monitoring_system