from __future__ import annotations

import signal
import subprocess
import sys
import time
from pathlib import Path

from app.config.logging_config import get_logger

logger = get_logger(__name__)

PROCESSES: list[subprocess.Popen] = []


def start_process(module_name: str) -> subprocess.Popen:
    """
    Start a Python module as a subprocess.
    Example:
        python -m app.ingestion.streaming.kafka_consumer
    """
    logger.info(f"Starting process: {module_name}")

    process = subprocess.Popen(
        [sys.executable, "-m", module_name],
        stdout=None,
        stderr=None,
    )
    PROCESSES.append(process)
    return process


def stop_all_processes() -> None:
    logger.info("Stopping all streaming processes")

    for proc in PROCESSES:
        if proc.poll() is None:  # still running
            try:
                proc.terminate()
            except Exception as exc:
                logger.warning(f"Failed to terminate process cleanly: {exc}")

    time.sleep(2)

    for proc in PROCESSES:
        if proc.poll() is None:
            try:
                proc.kill()
            except Exception as exc:
                logger.warning(f"Failed to kill process: {exc}")


def handle_shutdown(signum, frame) -> None:
    logger.info("Shutdown signal received in run_stream_pipeline")
    stop_all_processes()
    sys.exit(0)


def run_pipeline() -> None:
    """
    Starts:
    - Kafka consumer
    - Binance crypto producer
    - Finnhub forex producer
    - Metals replay producer
    """

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    logger.info("Starting full stream pipeline")

    # 1. Start consumer first so it is ready to receive messages
    start_process("app.ingestion.streaming.kafka_consumer")

    # small delay so consumer connects before producers publish
    time.sleep(3)

    # 2. Start producers
    start_process("app.ingestion.streaming.binance_ws_producer")
    start_process("app.ingestion.streaming.finnhub_ws_producer")
    start_process("app.ingestion.streaming.metals_stream_producer")

    logger.info("All stream processes started successfully")

    try:
        while True:
            # monitor subprocesses
            for proc in PROCESSES:
                if proc.poll() is not None:
                    logger.warning(
                        f"A streaming subprocess exited unexpectedly with code {proc.returncode}"
                    )
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
        stop_all_processes()


if __name__ == "__main__":
    run_pipeline()