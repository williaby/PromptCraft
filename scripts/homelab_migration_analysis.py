#!/usr/bin/env python3
# nosemgrep
"""Homelab Migration Feasibility Analysis for AUTH-4 Database Consolidation.

This script analyzes the feasibility of migrating multiple SQLite databases
to a consolidated PostgreSQL schema in a homelab environment, considering
processing power, storage constraints, and migration complexity.
"""

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class DatabaseInfo:
    """Information about a database to be migrated."""

    name: str
    file_path: Path
    size_mb: float
    table_count: int
    estimated_row_count: int
    schema_complexity: str  # "simple", "moderate", "complex"
    migration_priority: str  # "critical", "high", "medium", "low"


@dataclass
class MigrationPhase:
    """Represents a migration phase with specific databases."""

    phase_number: int
    databases: list[DatabaseInfo]
    estimated_duration_minutes: int
    estimated_memory_mb: int
    estimated_cpu_percent: float
    parallelizable: bool


class HomelabMigrationAnalyzer:
    """Analyzes migration feasibility for homelab environments."""

    def __init__(self, project_root: Path = None):
        """Initialize the migration analyzer."""
        self.project_root = project_root or Path.cwd()
        self.system_specs = self._get_system_specs()

    def _get_system_specs(self) -> dict[str, Any]:
        """Get current system specifications for migration planning."""
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage(str(self.project_root))

        return {
            "cpu_cores": psutil.cpu_count(),
            "total_memory_gb": memory_info.total / (1024**3),
            "available_memory_gb": memory_info.available / (1024**3),
            "available_disk_gb": disk_info.free / (1024**3),
            "current_cpu_percent": psutil.cpu_percent(interval=1),
            "current_memory_percent": memory_info.percent,
            "python_version": f"{psutil.os.sys.version_info.major}.{psutil.os.sys.version_info.minor}",
        }

    def discover_databases(self) -> list[DatabaseInfo]:
        """Discover existing SQLite databases in the project."""
        databases = []

        # Look for existing databases based on AUTH-4 consolidation requirements
        potential_dbs = [
            ("security_events.db", "critical"),
            ("ab_testing.db", "medium"),
            ("analytics.db", "high"),
            ("metrics.db", "medium"),
            # Add any other databases found in the project
        ]

        for db_name, priority in potential_dbs:
            db_path = self.project_root / db_name
            if db_path.exists():
                db_info = self._analyze_database(db_path, priority)
                if db_info:
                    databases.append(db_info)
                    logger.info(f"Found database: {db_name} ({db_info.size_mb:.1f}MB)")
            else:
                # Create a simulated database info for planning purposes
                db_info = self._create_simulated_database_info(db_name, priority)
                databases.append(db_info)
                logger.info(f"Simulated database for planning: {db_name}")

        return databases

    def _analyze_database(self, db_path: Path, priority: str) -> DatabaseInfo | None:
        """Analyze a specific SQLite database."""
        try:
            size_mb = db_path.stat().st_size / (1024 * 1024)

            # Connect and analyze structure
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get table count
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # Estimate total row count (sum across all tables)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            estimated_rows = 0
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    estimated_rows += row_count
                except sqlite3.Error:
                    # Table might not be accessible, estimate based on size
                    estimated_rows += int(size_mb * 1000)  # Rough estimate

            conn.close()

            # Determine schema complexity
            complexity = "simple"
            if table_count > 5 or estimated_rows > 100000:
                complexity = "moderate"
            if table_count > 10 or estimated_rows > 1000000:
                complexity = "complex"

            return DatabaseInfo(
                name=db_path.name,
                file_path=db_path,
                size_mb=size_mb,
                table_count=table_count,
                estimated_row_count=estimated_rows,
                schema_complexity=complexity,
                migration_priority=priority,
            )

        except Exception as e:
            logger.warning(f"Failed to analyze database {db_path}: {e}")
            return None

    def _create_simulated_database_info(self, db_name: str, priority: str) -> DatabaseInfo:
        """Create simulated database info for planning when actual DB doesn't exist."""
        # Simulate typical database characteristics based on name/type
        size_estimates = {
            "security_events.db": (50.0, 5, 100000),  # size_mb, tables, rows
            "ab_testing.db": (25.0, 3, 50000),
            "analytics.db": (100.0, 8, 250000),
            "metrics.db": (30.0, 4, 75000),
        }

        size_mb, table_count, estimated_rows = size_estimates.get(db_name, (10.0, 2, 10000))

        complexity = "simple"
        if table_count > 5 or estimated_rows > 100000:
            complexity = "moderate"
        if table_count > 10 or estimated_rows > 1000000:
            complexity = "complex"

        return DatabaseInfo(
            name=db_name,
            file_path=self.project_root / db_name,
            size_mb=size_mb,
            table_count=table_count,
            estimated_row_count=estimated_rows,
            schema_complexity=complexity,
            migration_priority=priority,
        )

    def plan_migration_phases(self, databases: list[DatabaseInfo]) -> list[MigrationPhase]:
        """Plan migration phases based on priority and system constraints."""
        # Sort databases by priority and complexity
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        sorted_dbs = sorted(
            databases,
            key=lambda db: (
                priority_order.get(db.migration_priority, 3),
                db.size_mb,  # Larger databases first within same priority
            ),
            reverse=True,
        )

        phases = []
        current_phase_dbs = []
        current_memory_mb = 0
        current_duration = 0
        phase_number = 1

        # Memory constraint (use at most 50% of available memory per phase)
        max_memory_per_phase = (self.system_specs["available_memory_gb"] * 1024) * 0.5

        for db in sorted_dbs:
            # Estimate migration requirements for this database
            estimated_memory = self._estimate_migration_memory(db)
            estimated_duration = self._estimate_migration_duration(db)

            # Check if we should start a new phase
            if (
                current_memory_mb + estimated_memory > max_memory_per_phase
                or current_duration + estimated_duration > 60
            ):  # Max 1 hour per phase

                if current_phase_dbs:
                    # Create phase with current databases
                    phases.append(
                        MigrationPhase(
                            phase_number=phase_number,
                            databases=current_phase_dbs.copy(),
                            estimated_duration_minutes=current_duration,
                            estimated_memory_mb=current_memory_mb,
                            estimated_cpu_percent=self._estimate_cpu_usage(current_phase_dbs),
                            parallelizable=self._can_parallelize(current_phase_dbs),
                        ),
                    )

                    # Start new phase
                    phase_number += 1
                    current_phase_dbs = []
                    current_memory_mb = 0
                    current_duration = 0

            current_phase_dbs.append(db)
            current_memory_mb += estimated_memory
            current_duration += estimated_duration

        # Add final phase if there are remaining databases
        if current_phase_dbs:
            phases.append(
                MigrationPhase(
                    phase_number=phase_number,
                    databases=current_phase_dbs,
                    estimated_duration_minutes=current_duration,
                    estimated_memory_mb=current_memory_mb,
                    estimated_cpu_percent=self._estimate_cpu_usage(current_phase_dbs),
                    parallelizable=self._can_parallelize(current_phase_dbs),
                ),
            )

        return phases

    def _estimate_migration_memory(self, db: DatabaseInfo) -> float:
        """Estimate memory requirements for migrating a database."""
        # Base memory requirement plus scaling factor
        base_memory = 50  # MB base requirement

        # Scale based on database size and complexity
        size_factor = db.size_mb * 2  # 2x database size for processing

        complexity_multiplier = {
            "simple": 1.0,
            "moderate": 1.5,
            "complex": 2.0,
        }

        return base_memory + (size_factor * complexity_multiplier[db.schema_complexity])

    def _estimate_migration_duration(self, db: DatabaseInfo) -> int:
        """Estimate migration duration in minutes."""
        # Base time plus scaling factors
        base_minutes = 5  # Base setup time

        # Time based on rows (assuming homelab processing speed)
        rows_per_minute = 5000  # Conservative homelab estimate
        row_time = max(1, db.estimated_row_count // rows_per_minute)

        # Complexity overhead
        complexity_overhead = {
            "simple": 1.0,
            "moderate": 1.3,
            "complex": 1.6,
        }

        total_time = base_minutes + (row_time * complexity_overhead[db.schema_complexity])
        return int(total_time)

    def _estimate_cpu_usage(self, databases: list[DatabaseInfo]) -> float:
        """Estimate CPU usage percentage for migrating these databases."""
        # Base CPU usage plus scaling
        base_cpu = 20.0  # Base PostgreSQL + Python overhead

        # Additional CPU per database being processed
        cpu_per_db = 5.0

        # Cap at reasonable level for homelab
        estimated_cpu = min(80.0, base_cpu + (len(databases) * cpu_per_db))
        return estimated_cpu

    def _can_parallelize(self, databases: list[DatabaseInfo]) -> bool:
        """Determine if databases in this phase can be migrated in parallel."""
        # Simple heuristic: can parallelize if multiple small databases
        if len(databases) <= 1:
            return False

        # Check if all databases are relatively small and simple
        all_small = all(db.size_mb < 25 and db.schema_complexity == "simple" for db in databases)
        return all_small

    def assess_migration_feasibility(self, phases: list[MigrationPhase]) -> dict[str, Any]:
        """Assess overall migration feasibility for homelab environment."""
        assessment = {
            "total_phases": len(phases),
            "total_duration_hours": sum(phase.estimated_duration_minutes for phase in phases) / 60,
            "peak_memory_usage_mb": max(phase.estimated_memory_mb for phase in phases) if phases else 0,
            "peak_cpu_usage_percent": max(phase.estimated_cpu_percent for phase in phases) if phases else 0,
            "feasibility": "UNKNOWN",
            "risks": [],
            "recommendations": [],
            "phase_details": [],
        }

        # Analyze each phase
        for phase in phases:
            phase_analysis = {
                "phase": phase.phase_number,
                "duration_minutes": phase.estimated_duration_minutes,
                "memory_mb": phase.estimated_memory_mb,
                "cpu_percent": phase.estimated_cpu_percent,
                "database_count": len(phase.databases),
                "parallelizable": phase.parallelizable,
                "status": "FEASIBLE",
                "concerns": [],
            }

            # Check resource constraints
            memory_usage_percent = (phase.estimated_memory_mb / (self.system_specs["available_memory_gb"] * 1024)) * 100

            if memory_usage_percent > 80:
                phase_analysis["status"] = "HIGH_RISK"
                phase_analysis["concerns"].append(f"High memory usage: {memory_usage_percent:.1f}%")
            elif memory_usage_percent > 60:
                phase_analysis["status"] = "MODERATE_RISK"
                phase_analysis["concerns"].append(f"Moderate memory usage: {memory_usage_percent:.1f}%")

            if phase.estimated_cpu_percent > 90:
                phase_analysis["status"] = "HIGH_RISK"
                phase_analysis["concerns"].append(f"High CPU usage: {phase.estimated_cpu_percent:.1f}%")

            if phase.estimated_duration_minutes > 120:
                phase_analysis["concerns"].append(f"Long duration: {phase.estimated_duration_minutes} minutes")

            assessment["phase_details"].append(phase_analysis)

        # Overall feasibility assessment
        high_risk_phases = sum(1 for phase in assessment["phase_details"] if phase["status"] == "HIGH_RISK")
        moderate_risk_phases = sum(1 for phase in assessment["phase_details"] if phase["status"] == "MODERATE_RISK")

        if high_risk_phases > 0:
            assessment["feasibility"] = "HIGH_RISK"
            assessment["risks"].append(f"{high_risk_phases} phases have high resource requirements")
        elif moderate_risk_phases > len(phases) // 2:
            assessment["feasibility"] = "MODERATE_RISK"
            assessment["risks"].append("Multiple phases have moderate resource requirements")
        else:
            assessment["feasibility"] = "FEASIBLE"

        # Generate recommendations
        if assessment["total_duration_hours"] > 6:
            assessment["recommendations"].append("Consider splitting migration across multiple days")

        if assessment["peak_memory_usage_mb"] > self.system_specs["available_memory_gb"] * 1024 * 0.7:
            assessment["recommendations"].append("Close non-essential applications during migration")
            assessment["recommendations"].append("Consider increasing system memory if possible")

        if high_risk_phases > 0:
            assessment["recommendations"].append("Test migration process with backup data first")
            assessment["recommendations"].append("Implement rollback procedures before starting")

        assessment["recommendations"].append("Monitor system resources during migration")
        assessment["recommendations"].append("Schedule migration during low-usage periods")

        return assessment

    def analyze(self) -> dict[str, Any]:
        """Perform complete migration feasibility analysis."""
        logger.info("Starting homelab migration feasibility analysis...")

        # Discover databases to migrate
        databases = self.discover_databases()
        logger.info(f"Found {len(databases)} databases to migrate")

        # Plan migration phases
        phases = self.plan_migration_phases(databases)
        logger.info(f"Planned migration in {len(phases)} phases")

        # Assess feasibility
        assessment = self.assess_migration_feasibility(phases)
        assessment["system_specs"] = self.system_specs
        assessment["databases"] = databases
        assessment["phases"] = phases

        return assessment


def print_migration_analysis(results: dict[str, Any]) -> None:
    """Print formatted migration analysis results."""
    print("\n" + "=" * 80)
    print("HOMELAB MIGRATION FEASIBILITY ANALYSIS")
    print("=" * 80)

    specs = results["system_specs"]
    print("\nSystem Specifications:")
    print(f"- CPU Cores: {specs['cpu_cores']}")
    print(f"- Available Memory: {specs['available_memory_gb']:.1f}GB")
    print(f"- Available Disk Space: {specs['available_disk_gb']:.1f}GB")
    print(
        f"- Current Resource Usage: {specs['current_cpu_percent']:.1f}% CPU, {specs['current_memory_percent']:.1f}% Memory",
    )

    databases = results["databases"]
    print(f"\nDatabases to Migrate ({len(databases)}):")
    for db in databases:
        print(f"- {db.name}: {db.size_mb:.1f}MB, {db.estimated_row_count:,} rows, {db.migration_priority} priority")

    assessment = results
    print("\nMigration Overview:")
    print(f"- Total Phases: {assessment['total_phases']}")
    print(f"- Estimated Duration: {assessment['total_duration_hours']:.1f} hours")
    print(f"- Peak Memory Usage: {assessment['peak_memory_usage_mb']:.0f}MB")
    print(f"- Peak CPU Usage: {assessment['peak_cpu_usage_percent']:.0f}%")
    print(f"- Overall Feasibility: {assessment['feasibility']}")

    print("\nPhase-by-Phase Analysis:")
    print("-" * 60)

    for phase_detail in assessment["phase_details"]:
        phase_num = phase_detail["phase"]
        phase = results["phases"][phase_num - 1]

        print(f"\nPhase {phase_num}: {phase_detail['status']}")
        print(f"  Databases: {', '.join([db.name for db in phase.databases])}")
        print(f"  Duration: {phase_detail['duration_minutes']} minutes")
        print(f"  Memory Required: {phase_detail['memory_mb']:.0f}MB")
        print(f"  CPU Usage: {phase_detail['cpu_percent']:.0f}%")
        print(f"  Parallelizable: {'Yes' if phase_detail['parallelizable'] else 'No'}")

        if phase_detail["concerns"]:
            print(f"  Concerns: {', '.join(phase_detail['concerns'])}")

    if assessment["risks"]:
        print("\nRisks Identified:")
        for risk in assessment["risks"]:
            print(f"- {risk}")

    if assessment["recommendations"]:
        print("\nRecommendations:")
        for rec in assessment["recommendations"]:
            print(f"- {rec}")

    print("\n" + "=" * 80)


def main():
    """Main function."""
    analyzer = HomelabMigrationAnalyzer()
    results = analyzer.analyze()
    print_migration_analysis(results)
    return results


if __name__ == "__main__":
    main()
