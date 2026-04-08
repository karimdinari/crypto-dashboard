from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

from app.config.logging_config import get_logger
from app.config.settings import (
    DEFAULT_REQUEST_TIMEOUT_SECONDS,
    DEFAULT_RETRY_BACKOFF_SECONDS,
    DEFAULT_RETRY_COUNT,
)
from app.utils.retry import retry


class BaseIngestor(ABC):
    """
    Base class for all batch ingestors.
    Provides common logging, request handling, and metadata helpers.
    """

    def __init__(self, source_name: str) -> None:
        self.source_name = source_name
        self.logger = get_logger(self.__class__.__name__)

    @staticmethod
    def get_ingestion_time() -> datetime:
        return datetime.now(timezone.utc)

    @retry(
        max_attempts=DEFAULT_RETRY_COUNT,
        backoff_seconds=DEFAULT_RETRY_BACKOFF_SECONDS,
    )
    def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    ) -> Any:
        self.logger.info(
            "Sending GET request",
            extra={
                "source": self.source_name,
                "url": url,
                "params": params or {},
            },
        )
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def attach_standard_metadata(self, record: Dict[str, Any], market_type: str, symbol: str) -> Dict[str, Any]:
        record["source"] = self.source_name
        record["market_type"] = market_type
        record["symbol"] = symbol
        record["ingestion_time"] = self.get_ingestion_time().isoformat()
        return record

    @abstractmethod
    def fetch(self):
        """
        Fetch raw data from the source and return a pandas DataFrame.
        """
        raise NotImplementedError