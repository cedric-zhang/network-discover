"""Application configuration center.

All tunable parameters live here. Values can be overridden via environment variables.
"""
from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class ScanConfig:
    """Scan-related configuration."""
    # Maximum scan duration in seconds (default 30 minutes)
    timeout: int = field(default_factory=lambda: int(os.getenv("SCAN_TIMEOUT", "1800")))

    # nmap --top-ports value (None = scan all ports, N = top N ports only)
    top_ports: Optional[int] = field(
        default_factory=lambda: int(os.getenv("NMAP_TOP_PORTS", "0")) or None
    )

    # nmap timing template (T0-T5), default T4 for speed
    timing_template: str = os.getenv("NMAP_TIMING", "T4")

    # Frontend poll interval in milliseconds
    poll_interval_ms: int = field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL_MS", "3000"))
    )

    # Stats reporting interval for nmap --stats-every flag (seconds)
    stats_every_seconds: int = 5


@dataclass
class AppConfig:
    """Application-level configuration."""
    version: str = "0.10.4"
    db_path: str = field(
        default_factory=lambda: os.getenv("DB_PATH", "data/network.db")
    )
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "").lower() in ("1", "true", "yes")
    )


# Singleton instances
scan_config = ScanConfig()
app_config = AppConfig()
