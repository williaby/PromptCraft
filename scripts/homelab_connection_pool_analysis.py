#!/usr/bin/env python3
"""Homelab Connection Pool Configuration Analysis.

This script analyzes optimal connection pool settings for homelab environments,
considering limited CPU and memory resources while maintaining good performance
for the AUTH-4 database consolidation.
"""

import logging
from dataclasses import dataclass
from typing import Any

import psutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class PoolConfiguration:
    """Connection pool configuration parameters."""

    pool_size: int
    max_overflow: int
    pool_timeout: int
    pool_recycle: int
    expected_memory_mb: float
    expected_cpu_percent: float
    scenario: str


class HomelabPoolAnalyzer:
    """Analyzes optimal connection pool configurations for homelab environments."""

    def __init__(self):
        """Initialize the pool analyzer."""
        self.system_specs = self._get_system_specs()

    def _get_system_specs(self) -> dict[str, Any]:
        """Get current system specifications."""
        memory_info = psutil.virtual_memory()

        return {
            "cpu_cores": psutil.cpu_count(),
            "total_memory_gb": memory_info.total / (1024**3),
            "available_memory_gb": memory_info.available / (1024**3),
            "current_cpu_percent": psutil.cpu_percent(interval=1),
            "current_memory_percent": memory_info.percent,
        }

    def calculate_optimal_pool_sizes(self) -> list[PoolConfiguration]:
        """Calculate optimal pool configurations for different scenarios."""
        specs = self.system_specs

        # Base calculations
        available_memory_mb = specs["available_memory_gb"] * 1024
        cpu_cores = specs["cpu_cores"]

        # Estimated memory per connection (PostgreSQL + overhead)
        memory_per_connection_mb = 5  # Conservative estimate for homelab

        # Calculate configurations for different scenarios
        configs = []

        # 1. Conservative (low resource usage)
        conservative_pool_size = max(2, min(cpu_cores // 4, int(available_memory_mb / (memory_per_connection_mb * 4))))
        conservative_max_overflow = max(2, conservative_pool_size // 2)

        configs.append(
            PoolConfiguration(
                pool_size=conservative_pool_size,
                max_overflow=conservative_max_overflow,
                pool_timeout=30,
                pool_recycle=3600,
                expected_memory_mb=(conservative_pool_size + conservative_max_overflow) * memory_per_connection_mb,
                expected_cpu_percent=2.0,
                scenario="Conservative (Minimal Resource Usage)",
            ),
        )

        # 2. Balanced (moderate resource usage)
        balanced_pool_size = max(3, min(cpu_cores // 2, int(available_memory_mb / (memory_per_connection_mb * 2))))
        balanced_max_overflow = max(3, balanced_pool_size)

        configs.append(
            PoolConfiguration(
                pool_size=balanced_pool_size,
                max_overflow=balanced_max_overflow,
                pool_timeout=20,
                pool_recycle=3600,
                expected_memory_mb=(balanced_pool_size + balanced_max_overflow) * memory_per_connection_mb,
                expected_cpu_percent=5.0,
                scenario="Balanced (Moderate Resource Usage)",
            ),
        )

        # 3. Performance (higher resource usage)
        performance_pool_size = max(5, min(cpu_cores, int(available_memory_mb / (memory_per_connection_mb * 1.5))))
        performance_max_overflow = max(5, performance_pool_size * 2)

        configs.append(
            PoolConfiguration(
                pool_size=performance_pool_size,
                max_overflow=performance_max_overflow,
                pool_timeout=15,
                pool_recycle=3600,
                expected_memory_mb=(performance_pool_size + performance_max_overflow) * memory_per_connection_mb,
                expected_cpu_percent=10.0,
                scenario="Performance (Higher Resource Usage)",
            ),
        )

        # 4. Current production settings (for comparison)
        configs.append(
            PoolConfiguration(
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                expected_memory_mb=30 * memory_per_connection_mb,
                expected_cpu_percent=15.0,
                scenario="Current Production Settings (May be too high for homelab)",
            ),
        )

        return configs

    def assess_configurations(self, configs: list[PoolConfiguration]) -> dict[str, Any]:
        """Assess each configuration for homelab suitability."""
        specs = self.system_specs
        assessment = {
            "system_specs": specs,
            "configuration_analysis": [],
            "recommendations": [],
        }

        available_memory_mb = specs["available_memory_gb"] * 1024

        for config in configs:
            # Calculate resource utilization
            memory_usage_percent = (config.expected_memory_mb / available_memory_mb) * 100
            memory_headroom = available_memory_mb - config.expected_memory_mb

            # Assess suitability
            suitability = "SUITABLE"
            concerns = []
            benefits = []

            if memory_usage_percent > 50:
                suitability = "RISKY"
                concerns.append(f"High memory usage: {memory_usage_percent:.1f}%")
            elif memory_usage_percent > 30:
                suitability = "CAUTION"
                concerns.append(f"Moderate memory usage: {memory_usage_percent:.1f}%")
            else:
                benefits.append(f"Low memory usage: {memory_usage_percent:.1f}%")

            if config.expected_cpu_percent > 20:
                if suitability == "SUITABLE":
                    suitability = "CAUTION"
                concerns.append(f"High CPU overhead expected: {config.expected_cpu_percent}%")
            else:
                benefits.append(f"Reasonable CPU overhead: {config.expected_cpu_percent}%")

            if memory_headroom < 100:  # Less than 100MB headroom
                suitability = "RISKY"
                concerns.append("Insufficient memory headroom for system operations")

            # Calculate concurrent user capacity
            max_concurrent_users = config.pool_size + config.max_overflow

            analysis = {
                "configuration": config,
                "memory_usage_percent": round(memory_usage_percent, 1),
                "memory_headroom_mb": round(memory_headroom, 1),
                "max_concurrent_users": max_concurrent_users,
                "suitability": suitability,
                "concerns": concerns,
                "benefits": benefits,
            }

            assessment["configuration_analysis"].append(analysis)

        # Generate recommendations
        suitable_configs = [
            analysis
            for analysis in assessment["configuration_analysis"]
            if analysis["suitability"] in ["SUITABLE", "CAUTION"]
        ]

        if suitable_configs:
            # Recommend the most balanced suitable configuration
            recommended = min(
                suitable_configs, key=lambda x: abs(x["memory_usage_percent"] - 25),  # Target ~25% memory usage
            )
            assessment["recommendations"].append(
                {
                    "type": "RECOMMENDED",
                    "config": recommended,
                    "reason": "Best balance of performance and resource efficiency for homelab",
                },
            )

            # Also recommend the most conservative
            conservative = min(suitable_configs, key=lambda x: x["memory_usage_percent"])
            if conservative != recommended:
                assessment["recommendations"].append(
                    {
                        "type": "SAFE_ALTERNATIVE",
                        "config": conservative,
                        "reason": "Lowest resource usage, good for resource-constrained environments",
                    },
                )
        else:
            assessment["recommendations"].append(
                {
                    "type": "WARNING",
                    "config": None,
                    "reason": "No configurations appear suitable for this homelab environment",
                },
            )

        return assessment

    def generate_sqlalchemy_config(self, config: PoolConfiguration) -> dict[str, Any]:
        """Generate SQLAlchemy configuration parameters."""
        return {
            "pool_size": config.pool_size,
            "max_overflow": config.max_overflow,
            "pool_timeout": config.pool_timeout,
            "pool_recycle": config.pool_recycle,
            "pool_pre_ping": True,  # Always recommended for homelab
            # Additional homelab-specific settings
            "connect_args": {
                "server_settings": {
                    "application_name": "promptcraft-auth-homelab",
                    "jit": "off",  # Disable JIT for faster connections on limited CPU
                },
                "command_timeout": 30.0,  # Longer timeout for homelab
            },
        }

    def analyze(self) -> dict[str, Any]:
        """Perform complete connection pool analysis."""
        logger.info("Starting homelab connection pool analysis...")

        configs = self.calculate_optimal_pool_sizes()
        assessment = self.assess_configurations(configs)

        # Add SQLAlchemy configurations for recommended setups
        for rec in assessment["recommendations"]:
            if rec["config"]:
                rec["sqlalchemy_config"] = self.generate_sqlalchemy_config(rec["config"]["configuration"])

        return assessment


def print_analysis_results(results: dict[str, Any]) -> None:
    """Print formatted analysis results."""
    print("\n" + "=" * 80)
    print("HOMELAB CONNECTION POOL CONFIGURATION ANALYSIS")
    print("=" * 80)

    specs = results["system_specs"]
    print("\nSystem Specifications:")
    print(f"- CPU Cores: {specs['cpu_cores']}")
    print(f"- Available Memory: {specs['available_memory_gb']:.1f}GB")
    print(f"- Current CPU Usage: {specs['current_cpu_percent']:.1f}%")
    print(f"- Current Memory Usage: {specs['current_memory_percent']:.1f}%")

    print("\nConfiguration Analysis:")
    print("-" * 80)

    for analysis in results["configuration_analysis"]:
        config = analysis["configuration"]
        print(f"\n{config.scenario}")
        print(f"  Pool Size: {config.pool_size}, Max Overflow: {config.max_overflow}")
        print(f"  Expected Memory Usage: {analysis['memory_usage_percent']}% ({config.expected_memory_mb:.1f}MB)")
        print(f"  Max Concurrent Users: {analysis['max_concurrent_users']}")
        print(f"  Memory Headroom: {analysis['memory_headroom_mb']:.1f}MB")
        print(f"  Suitability: {analysis['suitability']}")

        if analysis["benefits"]:
            print(f"  Benefits: {', '.join(analysis['benefits'])}")
        if analysis["concerns"]:
            print(f"  Concerns: {', '.join(analysis['concerns'])}")

    print("\nRecommendations:")
    print("-" * 40)

    for rec in results["recommendations"]:
        print(f"\n{rec['type']}: {rec['reason']}")
        if rec["config"]:
            config = rec["config"]["configuration"]
            print(f"  → Pool Size: {config.pool_size}")
            print(f"  → Max Overflow: {config.max_overflow}")
            print(f"  → Pool Timeout: {config.pool_timeout}s")
            print(f"  → Expected Memory: {config.expected_memory_mb:.1f}MB")
            print(f"  → Max Users: {config.pool_size + config.max_overflow}")

            if "sqlalchemy_config" in rec:
                print(f"  → SQLAlchemy Config: {rec['sqlalchemy_config']}")

    print("\n" + "=" * 80)


def main():
    """Main function."""
    analyzer = HomelabPoolAnalyzer()
    results = analyzer.analyze()
    print_analysis_results(results)
    return results


if __name__ == "__main__":
    main()
