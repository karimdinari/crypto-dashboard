"""
Updated run_stream_pipeline.py
Starts all streaming processes including the news WS producer and consumer.
"""

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
        if proc.poll() is None:
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
    - Market tick Kafka consumer     (bronze/stream_ticks/)
    - News Kafka consumer            (bronze/stream_news/)
    - Binance crypto WS producer     (BTC/USD, ETH/USD)
    - Finnhub forex WS producer      (EUR/USD, GBP/USD)
    - Finnhub news WS producer       (all NEWS_TARGETS)
    - Metals yFinance poll producer  (XAU/USD, XAG/USD)
    """
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    logger.info("Starting full stream pipeline")

    # 1. Start consumers first so they are ready before any messages arrive
    start_process("app.ingestion.streaming.kafka_consumer")
    start_process("app.ingestion.streaming.news_kafka_consumer")

    # Small delay so consumers connect before producers publish
    time.sleep(3)

    # 2. Start market producers
    start_process("app.ingestion.streaming.binance_ws_producer")
    start_process("app.ingestion.streaming.finnhub_ws_producer")
    start_process("app.ingestion.streaming.yfinance_metals_producer")

    # 3. Start news producer
    start_process("app.ingestion.streaming.finnhub_news_ws_producer")

    logger.info("All stream processes started successfully")

    try:
        while True:
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