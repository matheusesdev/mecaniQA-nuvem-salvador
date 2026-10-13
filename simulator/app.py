import logging
import math
import os
import random
import signal
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

from prometheus_client import Counter, Gauge, Histogram, start_http_server


LOGGER = logging.getLogger("iot-simulator")
SAO_PAULO = ZoneInfo("America/Sao_Paulo")
SENSOR_TYPES = ("temperature", "electrical")
PEAK_MODES = ("scheduled", "always", "off")

iot_readings_total = Counter(
    "iot_readings_total",
    "Valid synthetic sensor readings processed locally.",
    ["sensor_type"],
)
iot_sensor_faults_total = Counter(
    "iot_sensor_faults_total",
    "Simulated automotive faults reported by sensors.",
    ["sensor_type"],
)
iot_sensor_value = Gauge(
    "iot_sensor_value",
    "Most recently processed synthetic sensor value.",
    ["sensor_type"],
)
iot_processing_errors_total = Counter(
    "iot_processing_errors_total",
    "Application errors and rejected sensor readings.",
)
iot_processing_seconds = Histogram(
    "iot_processing_seconds",
    "Local processing time per sensor reading; not network latency.",
)
iot_readings_in_progress = Gauge(
    "iot_readings_in_progress",
    "Number of readings currently being processed.",
)
iot_peak_active = Gauge(
    "iot_peak_active",
    "Whether the configured synthetic peak mode is currently active.",
)
iot_target_readings_per_second = Gauge(
    "iot_target_readings_per_second",
    "Configured target reading rate; not the observed rate.",
)


@dataclass(frozen=True)
class Settings:
    readings_per_second: float
    peak_multiplier: float
    peak_mode: str


def _positive_number(name: str, raw_value: str) -> float:
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive finite number") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    try:
        reciprocal = 1 / value
    except OverflowError as exc:
        raise ValueError(f"{name} is too small to schedule readings") from exc
    if not math.isfinite(reciprocal):
        raise ValueError(f"{name} is too small to schedule readings")
    return value


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    values = os.environ if environ is None else environ
    readings_per_second = _positive_number(
        "READINGS_PER_SECOND", values.get("READINGS_PER_SECOND", "1")
    )
    peak_multiplier = _positive_number(
        "PEAK_MULTIPLIER", values.get("PEAK_MULTIPLIER", "5")
    )
    if not math.isfinite(readings_per_second * peak_multiplier):
        raise ValueError("READINGS_PER_SECOND * PEAK_MULTIPLIER must be finite")
    peak_mode = values.get("PEAK_MODE", "scheduled").strip().lower()
    if peak_mode not in PEAK_MODES:
        raise ValueError(f"PEAK_MODE must be one of: {', '.join(PEAK_MODES)}")
    return Settings(readings_per_second, peak_multiplier, peak_mode)


def peak_is_active(
    mode: str, now: datetime | None = None
) -> bool:
    if mode == "always":
        return True
    if mode == "off":
        return False
    if mode != "scheduled":
        raise ValueError(f"Unsupported PEAK_MODE: {mode}")
    current_time = now or datetime.now(SAO_PAULO)
    local_time = (
        current_time.replace(tzinfo=SAO_PAULO)
        if current_time.tzinfo is None
        else current_time.astimezone(SAO_PAULO)
    )
    return local_time.hour in (8, 17) and local_time.minute < 10


def generate_reading(rng: random.Random | None = None) -> dict[str, object]:
    source = rng or random
    sensor_type = source.choice(SENSOR_TYPES)
    if sensor_type == "temperature":
        value = source.uniform(70.0, 115.0)
        fault = value >= 105.0
    else:
        value = source.uniform(10.0, 15.0)
        fault = value < 11.5 or value > 14.8
    return {"sensor_type": sensor_type, "value": value, "fault": fault}


def process_reading(reading: object) -> None:
    started_at = time.perf_counter()
    iot_readings_in_progress.inc()
    try:
        if not isinstance(reading, dict):
            raise ValueError("reading must be a dictionary")
        sensor_type = reading.get("sensor_type")
        value = reading.get("value")
        fault = reading.get("fault")
        if sensor_type not in SENSOR_TYPES:
            raise ValueError("sensor_type must be temperature or electrical")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("value must be a finite number")
        try:
            is_finite = math.isfinite(value)
        except OverflowError:
            is_finite = False
        if not is_finite:
            raise ValueError("value must be a finite number")
        if not isinstance(fault, bool):
            raise ValueError("fault must be a boolean")

        iot_sensor_value.labels(sensor_type=sensor_type).set(value)
        iot_readings_total.labels(sensor_type=sensor_type).inc()
        if fault:
            iot_sensor_faults_total.labels(sensor_type=sensor_type).inc()
    except Exception:
        iot_processing_errors_total.inc()
        raise
    finally:
        iot_processing_seconds.observe(time.perf_counter() - started_at)
        iot_readings_in_progress.dec()


def run(
    settings: Settings,
    stop_event: threading.Event,
    reading_factory: Callable[[], dict[str, object]] = generate_reading,
) -> None:
    next_reading_at = time.monotonic()
    while not stop_event.is_set():
        active_peak = peak_is_active(settings.peak_mode)
        target_rate = settings.readings_per_second * (
            settings.peak_multiplier if active_peak else 1
        )
        iot_peak_active.set(1 if active_peak else 0)
        iot_target_readings_per_second.set(target_rate)
        interval = 1 / target_rate

        now = time.monotonic()
        if now >= next_reading_at:
            try:
                process_reading(reading_factory())
            except ValueError as exc:
                LOGGER.warning("Rejected sensor reading: %s", exc)
            next_reading_at = max(next_reading_at + interval, time.monotonic())
        else:
            stop_event.wait(next_reading_at - now)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        settings = load_settings()
    except ValueError:
        LOGGER.exception("Invalid simulator configuration")
        raise SystemExit(2)

    stop_event = threading.Event()
    previous_handlers = {
        signum: signal.getsignal(signum) for signum in (signal.SIGTERM, signal.SIGINT)
    }
    for signum in previous_handlers:
        signal.signal(signum, lambda _signum, _frame: stop_event.set())

    server, server_thread = start_http_server(8000)
    LOGGER.info(
        "Metrics available on :8000/metrics; peak mode=%s",
        settings.peak_mode,
    )
    try:
        run(settings, stop_event)
    finally:
        stop_event.set()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        LOGGER.info("Simulator stopped")


if __name__ == "__main__":
    main()
