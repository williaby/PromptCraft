#!/usr/bin/env python3
# nosemgrep
"""
SQLite to PostgreSQL Migration Analysis Script

This script performs comprehensive analysis of SQLite databases to facilitate
migration to PostgreSQL. It extracts schema information, analyzes data patterns,
and generates PostgreSQL-equivalent schemas with migration complexity assessment.

Features:
- Complete schema extraction with column types and constraints
- Data pattern analysis and type mapping
- Index analysis and recommendations
- Foreign key relationship detection
- Data volume and complexity assessment
- PostgreSQL CREATE statement generation
- Migration complexity scoring

Usage:
    python sqlite_to_postgresql_analysis.py
"""

import json
import logging
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def validate_sql_identifier(identifier: str) -> str:
    """
    Validate and sanitize SQL identifier to prevent injection attacks.

    Args:
        identifier: The identifier to validate (table name, column name, etc.)

    Returns:
        The validated identifier

    Raises:
        ValueError: If identifier contains invalid characters
    """
    if not identifier:
        raise ValueError("Identifier cannot be empty")

    # Only allow alphanumeric characters, underscores, and hyphens
    if not re.match(r"^[a-zA-Z0-9_-]+$", identifier):
        raise ValueError(f"Invalid identifier: {identifier}. Only alphanumeric, underscore, and hyphen allowed.")

    # Ensure it doesn't start with a number (SQL standard)
    if identifier[0].isdigit():
        raise ValueError(f"Identifier cannot start with a number: {identifier}")

    return identifier


@dataclass
class ColumnInfo:
    """Information about a database column."""

    name: str
    sqlite_type: str
    postgresql_type: str
    nullable: bool
    default_value: str | None
    primary_key: bool
    auto_increment: bool
    unique: bool
    migration_notes: list[str]


@dataclass
class IndexInfo:
    """Information about database indexes."""

    name: str
    table_name: str
    columns: list[str]
    unique: bool
    partial: bool
    postgresql_equivalent: str


@dataclass
class ForeignKeyInfo:
    """Information about foreign key constraints."""

    table: str
    column: str
    referenced_table: str
    referenced_column: str
    on_delete: str | None
    on_update: str | None


@dataclass
class TableAnalysis:
    """Complete analysis of a database table."""

    name: str
    columns: list[ColumnInfo]
    indexes: list[IndexInfo]
    foreign_keys: list[ForeignKeyInfo]
    row_count: int
    estimated_size_mb: float
    data_samples: list[dict[str, Any]]
    complexity_score: int
    migration_notes: list[str]


@dataclass
class DatabaseAnalysis:
    """Complete analysis of a SQLite database."""

    name: str
    file_path: str
    file_size_mb: float
    tables: list[TableAnalysis]
    total_rows: int
    overall_complexity: int
    migration_priority: str
    postgresql_schema: str
    migration_strategy: list[str]


class SQLiteTypeMapper:
    """Maps SQLite types to PostgreSQL equivalents."""

    TYPE_MAPPING: ClassVar[dict[str, str]] = {
        # Integer types
        "INTEGER": "INTEGER",
        "INT": "INTEGER",
        "TINYINT": "SMALLINT",
        "SMALLINT": "SMALLINT",
        "MEDIUMINT": "INTEGER",
        "BIGINT": "BIGINT",
        "INT2": "SMALLINT",
        "INT8": "BIGINT",
        # Text types
        "TEXT": "TEXT",
        "CHARACTER": "VARCHAR",
        "VARCHAR": "VARCHAR",
        "VARYING CHARACTER": "VARCHAR",
        "NCHAR": "CHAR",
        "NATIVE CHARACTER": "VARCHAR",
        "NVARCHAR": "VARCHAR",
        "CLOB": "TEXT",
        # Numeric types
        "REAL": "REAL",
        "DOUBLE": "DOUBLE PRECISION",
        "DOUBLE PRECISION": "DOUBLE PRECISION",
        "FLOAT": "REAL",
        "NUMERIC": "NUMERIC",
        "DECIMAL": "DECIMAL",
        # Boolean
        "BOOLEAN": "BOOLEAN",
        # Date/Time
        "DATE": "DATE",
        "DATETIME": "TIMESTAMP",
        "TIMESTAMP": "TIMESTAMP",
        "TIME": "TIME",
        # Binary
        "BLOB": "BYTEA",
        "BINARY": "BYTEA",
        "VARBINARY": "BYTEA",
        # JSON (SQLite extension)
        "JSON": "JSONB",
    }

    @classmethod
    def map_type(cls, sqlite_type: str) -> tuple[str, list[str]]:
        """Map SQLite type to PostgreSQL with migration notes."""
        if not sqlite_type:
            return "TEXT", ["No type specified - defaulting to TEXT"]

        sqlite_type = sqlite_type.upper().strip()
        notes = []

        # Handle parameterized types like VARCHAR(255)
        base_type = sqlite_type.split("(")[0]

        if base_type in cls.TYPE_MAPPING:
            pg_type = cls.TYPE_MAPPING[base_type]

            # Preserve parameters for appropriate types
            if "(" in sqlite_type and base_type in ["VARCHAR", "CHAR", "DECIMAL", "NUMERIC"]:
                param = sqlite_type[sqlite_type.index("(") :]
                pg_type += param

            # Add specific migration notes
            if base_type == "REAL":
                notes.append("REAL type may have precision differences")
            elif base_type == "BLOB":
                notes.append("BLOB data requires binary conversion")
            elif base_type == "DATETIME":
                notes.append("DateTime strings need parsing to TIMESTAMP")

            return pg_type, notes

        # Handle SQLite's flexible typing
        if any(keyword in sqlite_type for keyword in ["CHAR", "CLOB", "TEXT"]):
            return "TEXT", ["SQLite affinity rule: text type"]
        if any(keyword in sqlite_type for keyword in ["INT"]):
            return "INTEGER", ["SQLite affinity rule: integer type"]
        if any(keyword in sqlite_type for keyword in ["REAL", "FLOA", "DOUB"]):
            return "REAL", ["SQLite affinity rule: real type", "Verify precision requirements"]
        return "TEXT", [f'Unknown SQLite type "{sqlite_type}" - defaulting to TEXT']


class SQLiteDatabaseAnalyzer:
    """Analyzes SQLite databases for PostgreSQL migration."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_name = self.db_path.stem
        self.type_mapper = SQLiteTypeMapper()

    def analyze_database(self) -> DatabaseAnalysis:
        """Perform complete database analysis."""
        logger.info(f"Analyzing database: {self.db_name}")

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get file size
                file_size_mb = self.db_path.stat().st_size / (1024 * 1024)

                # Get all tables
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """,
                )
                table_names = [row[0] for row in cursor.fetchall()]

                if not table_names:
                    logger.warning(f"No user tables found in {self.db_name}")
                    return self._create_empty_analysis(file_size_mb)

                # Analyze each table
                tables = []
                total_rows = 0

                for table_name in table_names:
                    table_analysis = self._analyze_table(cursor, table_name)
                    tables.append(table_analysis)
                    total_rows += table_analysis.row_count

                # Calculate overall complexity
                overall_complexity = self._calculate_overall_complexity(tables)

                # Generate PostgreSQL schema
                postgresql_schema = self._generate_postgresql_schema(tables)

                # Determine migration strategy
                migration_strategy = self._determine_migration_strategy(tables, file_size_mb, total_rows)

                # Set migration priority
                priority = self._determine_priority(overall_complexity, file_size_mb, total_rows)

                return DatabaseAnalysis(
                    name=self.db_name,
                    file_path=str(self.db_path),
                    file_size_mb=file_size_mb,
                    tables=tables,
                    total_rows=total_rows,
                    overall_complexity=overall_complexity,
                    migration_priority=priority,
                    postgresql_schema=postgresql_schema,
                    migration_strategy=migration_strategy,
                )

        except sqlite3.Error as e:
            logger.error(f"SQLite error analyzing {self.db_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error analyzing {self.db_name}: {e}")
            raise

    def _analyze_table(self, cursor: sqlite3.Cursor, table_name: str) -> TableAnalysis:
        """Analyze a single table."""
        logger.info(f"  Analyzing table: {table_name}")

        # Get table info - SECURITY: Validate table name to prevent SQL injection
        safe_table_name = validate_sql_identifier(table_name)
        cursor.execute(f"PRAGMA table_info([{safe_table_name}])")  # nosec B608
        pragma_info = cursor.fetchall()

        # Get row count - using already validated safe_table_name
        cursor.execute(f"SELECT COUNT(*) FROM [{safe_table_name}]")  # nosec B608
        row_count = cursor.fetchone()[0]

        # Get estimated size (rough calculation)
        estimated_size_mb = row_count * len(pragma_info) * 50 / (1024 * 1024)  # Rough estimate

        # Get data samples
        data_samples = self._get_data_samples(cursor, table_name)

        # Analyze columns
        columns = self._analyze_columns(pragma_info, data_samples)

        # Analyze indexes
        indexes = self._analyze_indexes(cursor, table_name)

        # Analyze foreign keys
        foreign_keys = self._analyze_foreign_keys(cursor, table_name)

        # Calculate complexity score
        complexity_score = self._calculate_table_complexity(columns, indexes, foreign_keys, row_count)

        # Generate migration notes
        migration_notes = self._generate_table_migration_notes(columns, indexes, foreign_keys, row_count)

        return TableAnalysis(
            name=table_name,
            columns=columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            row_count=row_count,
            estimated_size_mb=estimated_size_mb,
            data_samples=data_samples[:3],  # Limit samples for output
            complexity_score=complexity_score,
            migration_notes=migration_notes,
        )

    def _analyze_columns(self, pragma_info: list[sqlite3.Row], data_samples: list[dict]) -> list[ColumnInfo]:
        """Analyze table columns."""
        columns = []

        for col_info in pragma_info:
            name = col_info["name"]
            sqlite_type = col_info["type"] or ""
            nullable = not col_info["notnull"]
            default_value = col_info["dflt_value"]
            primary_key = bool(col_info["pk"])

            # Map to PostgreSQL type
            postgresql_type, type_notes = self.type_mapper.map_type(sqlite_type)

            # Check for auto-increment
            auto_increment = primary_key and sqlite_type.upper() == "INTEGER"
            if auto_increment:
                postgresql_type = "SERIAL"
                type_notes.append("INTEGER PRIMARY KEY converted to SERIAL")

            # Analyze data patterns from samples
            column_notes = type_notes.copy()
            column_notes.extend(self._analyze_column_data_patterns(name, data_samples))

            columns.append(
                ColumnInfo(
                    name=name,
                    sqlite_type=sqlite_type or "NULL",
                    postgresql_type=postgresql_type,
                    nullable=nullable,
                    default_value=default_value,
                    primary_key=primary_key,
                    auto_increment=auto_increment,
                    unique=False,  # Will be updated from index analysis
                    migration_notes=column_notes,
                ),
            )

        return columns

    def _analyze_indexes(self, cursor: sqlite3.Cursor, table_name: str) -> list[IndexInfo]:
        """Analyze table indexes."""
        indexes = []

        # Get index list - SECURITY: Validate table name to prevent SQL injection
        safe_table_name = validate_sql_identifier(table_name)
        cursor.execute(f"PRAGMA index_list([{safe_table_name}])")  # nosec B608
        index_list = cursor.fetchall()

        for idx_info in index_list:
            idx_name = idx_info["name"]
            unique = bool(idx_info["unique"])
            partial = bool(idx_info["partial"])

            # Get index columns - SECURITY: Validate index name to prevent SQL injection
            safe_idx_name = validate_sql_identifier(idx_name)
            cursor.execute(f"PRAGMA index_info([{safe_idx_name}])")  # nosec B608
            index_columns = cursor.fetchall()

            columns = [col["name"] for col in index_columns]

            # Generate PostgreSQL equivalent
            if unique:
                if len(columns) == 1:
                    pg_equivalent = (
                        f'CREATE UNIQUE INDEX "idx_{table_name}_{columns[0]}" ON "{table_name}" ("{columns[0]}")'
                    )
                else:
                    col_list = ", ".join([f'"{c}"' for c in columns])
                    index_name = f"idx_{table_name}_{'_'.join(columns)}"
                    pg_equivalent = f'CREATE UNIQUE INDEX "{index_name}" ON "{table_name}" ({col_list})'
            else:
                col_list = ", ".join([f'"{c}"' for c in columns])
                index_name = f"idx_{table_name}_{'_'.join(columns)}"
                pg_equivalent = f'CREATE INDEX "{index_name}" ON "{table_name}" ({col_list})'

            indexes.append(
                IndexInfo(
                    name=idx_name,
                    table_name=table_name,
                    columns=columns,
                    unique=unique,
                    partial=partial,
                    postgresql_equivalent=pg_equivalent,
                ),
            )

        return indexes

    def _analyze_foreign_keys(self, cursor: sqlite3.Cursor, table_name: str) -> list[ForeignKeyInfo]:
        """Analyze foreign key constraints."""
        foreign_keys = []

        # SECURITY: Validate table name to prevent SQL injection
        safe_table_name = validate_sql_identifier(table_name)
        cursor.execute(f"PRAGMA foreign_key_list([{safe_table_name}])")  # nosec B608
        fk_list = cursor.fetchall()

        for fk_info in fk_list:
            foreign_keys.append(
                ForeignKeyInfo(
                    table=table_name,
                    column=fk_info["from"],
                    referenced_table=fk_info["table"],
                    referenced_column=fk_info["to"],
                    on_delete=fk_info["on_delete"],
                    on_update=fk_info["on_update"],
                ),
            )

        return foreign_keys

    def _get_data_samples(self, cursor: sqlite3.Cursor, table_name: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get sample data from table."""
        try:
            # SECURITY: Validate table name to prevent SQL injection
            safe_table_name = validate_sql_identifier(table_name)
            cursor.execute(f"SELECT * FROM [{safe_table_name}] LIMIT {limit}")  # nosec
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error:
            return []

    def _analyze_column_data_patterns(self, column_name: str, data_samples: list[dict]) -> list[str]:
        """Analyze data patterns in column samples."""
        if not data_samples:
            return []

        notes = []
        values = [sample.get(column_name) for sample in data_samples if sample.get(column_name) is not None]

        if not values:
            return ["No sample data available"]

        # Check for JSON strings
        json_like = 0
        for value in values:
            if isinstance(value, str) and value.strip().startswith(("{ ", "[ ")):
                json_like += 1

        if json_like > len(values) * 0.5:
            notes.append("Contains JSON-like strings - consider JSONB type")

        # Check for datetime strings
        datetime_like = 0
        for value in values:
            if isinstance(value, str) and any(sep in value for sep in ["-", "/", " ", ":"]):
                try:
                    # Simple datetime pattern check
                    if len(value) > 8 and any(char.isdigit() for char in value):
                        datetime_like += 1
                except (ValueError, TypeError):
                    # Skip values that can't be processed as datetime
                    continue

        if datetime_like > len(values) * 0.5:
            notes.append("Contains datetime-like strings - verify format")

        # Check for large text values
        if any(isinstance(v, str) and len(v) > 1000 for v in values):
            notes.append("Contains large text values - consider TEXT type")

        # Check for numeric precision
        real_values = [v for v in values if isinstance(v, float)]
        if real_values:
            max_precision = max(len(str(v).split(".")[-1]) for v in real_values if "." in str(v))
            if max_precision > 6:
                notes.append(f"High precision decimals detected (max {max_precision} digits)")

        return notes

    def _calculate_table_complexity(
        self,
        columns: list[ColumnInfo],
        indexes: list[IndexInfo],
        foreign_keys: list[ForeignKeyInfo],
        row_count: int,
    ) -> int:
        """Calculate table migration complexity score (1-10)."""
        score = 1

        # Column complexity
        for col in columns:
            if col.migration_notes:
                score += len(
                    [
                        note
                        for note in col.migration_notes
                        if "precision" in note.lower() or "conversion" in note.lower()
                    ],
                )

        # Index complexity
        score += len(indexes) * 0.5

        # Foreign key complexity
        score += len(foreign_keys)

        # Data volume complexity
        if row_count > 100000:
            score += 2
        elif row_count > 10000:
            score += 1

        return min(int(score), 10)

    def _generate_table_migration_notes(
        self,
        columns: list[ColumnInfo],
        indexes: list[IndexInfo],
        foreign_keys: list[ForeignKeyInfo],
        row_count: int,
    ) -> list[str]:
        """Generate migration notes for table."""
        notes = []

        if row_count > 100000:
            notes.append(f"Large table ({row_count:,} rows) - consider batch migration")

        complex_columns = [col for col in columns if len(col.migration_notes) > 1]
        if complex_columns:
            notes.append(f"Complex columns requiring attention: {', '.join(col.name for col in complex_columns)}")

        if indexes:
            notes.append(f"Recreate {len(indexes)} indexes after data migration")

        if foreign_keys:
            notes.append(f"Re-establish {len(foreign_keys)} foreign key constraints after migration")

        return notes

    def _calculate_overall_complexity(self, tables: list[TableAnalysis]) -> int:
        """Calculate overall database complexity (1-10)."""
        if not tables:
            return 1

        avg_complexity = sum(table.complexity_score for table in tables) / len(tables)
        table_count_factor = min(len(tables) * 0.5, 3)

        return min(int(avg_complexity + table_count_factor), 10)

    def _determine_priority(self, complexity: int, size_mb: float, total_rows: int) -> str:
        """Determine migration priority."""
        if size_mb > 10 or total_rows > 100000 or complexity > 7:
            return "HIGH"
        if size_mb > 1 or total_rows > 10000 or complexity > 4:
            return "MEDIUM"
        return "LOW"

    def _determine_migration_strategy(self, tables: list[TableAnalysis], size_mb: float, total_rows: int) -> list[str]:
        """Determine migration strategy recommendations."""
        strategies = []

        if size_mb > 5:
            strategies.append("Use batch processing for data migration")
            strategies.append("Consider parallel processing for large tables")

        if any(table.row_count > 50000 for table in tables):
            strategies.append("Migrate large tables during maintenance window")
            strategies.append("Implement incremental migration with timestamps")

        foreign_key_tables = [table for table in tables if table.foreign_keys]
        if foreign_key_tables:
            strategies.append("Disable foreign key constraints during migration")
            strategies.append("Migrate in dependency order")

        json_tables = []
        for table in tables:
            for col in table.columns:
                if any("json" in note.lower() for note in col.migration_notes):
                    json_tables.append(table.name)
                    break

        if json_tables:
            strategies.append(f"Validate JSON data in tables: {', '.join(json_tables)}")
            strategies.append("Consider JSONB type for better performance")

        if not strategies:
            strategies.append("Direct migration suitable - low complexity")

        return strategies

    def _generate_postgresql_schema(self, tables: list[TableAnalysis]) -> str:
        """Generate PostgreSQL schema DDL."""
        if not tables:
            return "-- No tables found"

        schema_parts = []
        schema_parts.append(f"-- PostgreSQL schema for {self.db_name}")
        schema_parts.append(f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        schema_parts.append("")

        # Create tables
        for table in tables:
            schema_parts.append(f"-- Table: {table.name}")
            schema_parts.append(f'CREATE TABLE "{table.name}" (')

            column_defs = []
            for col in table.columns:
                col_def = f'    "{col.name}" {col.postgresql_type}'

                if not col.nullable:
                    col_def += " NOT NULL"

                if col.default_value:
                    # Handle default value formatting
                    if col.postgresql_type in ["TEXT", "VARCHAR"]:
                        col_def += f" DEFAULT '{col.default_value}'"
                    else:
                        col_def += f" DEFAULT {col.default_value}"

                column_defs.append(col_def)

            # Add primary key constraint
            pk_columns = [col.name for col in table.columns if col.primary_key]
            if pk_columns:
                pk_cols_str = ", ".join([f'"{c}"' for c in pk_columns])
                column_defs.append(f"    PRIMARY KEY ({pk_cols_str})")

            schema_parts.append(",\n".join(column_defs))
            schema_parts.append(");")
            schema_parts.append("")

        # Add indexes
        for table in tables:
            if table.indexes:
                schema_parts.append(f"-- Indexes for {table.name}")
                for index in table.indexes:
                    schema_parts.append(f"{index.postgresql_equivalent};")
                schema_parts.append("")

        # Add foreign keys
        fk_statements = []
        for table in tables:
            for fk in table.foreign_keys:
                fk_name = f"fk_{table.name}_{fk.column}"
                fk_stmt = f'ALTER TABLE "{fk.table}" ADD CONSTRAINT "{fk_name}" '
                fk_stmt += f'FOREIGN KEY ("{fk.column}") REFERENCES "{fk.referenced_table}"("{fk.referenced_column}")'

                if fk.on_delete:
                    fk_stmt += f" ON DELETE {fk.on_delete}"
                if fk.on_update:
                    fk_stmt += f" ON UPDATE {fk.on_update}"

                fk_statements.append(fk_stmt + ";")

        if fk_statements:
            schema_parts.append("-- Foreign Key Constraints")
            schema_parts.extend(fk_statements)

        return "\n".join(schema_parts)

    def _create_empty_analysis(self, file_size_mb: float) -> DatabaseAnalysis:
        """Create analysis for empty database."""
        return DatabaseAnalysis(
            name=self.db_name,
            file_path=str(self.db_path),
            file_size_mb=file_size_mb,
            tables=[],
            total_rows=0,
            overall_complexity=1,
            migration_priority="LOW",
            postgresql_schema="-- No tables found",
            migration_strategy=["Database is empty - no migration needed"],
        )


class MigrationReportGenerator:
    """Generates a migration report from database analyses."""

    def __init__(self, analyses: dict[str, DatabaseAnalysis]):
        self.analyses = analyses
        self.report: list[str] = []

    def generate_report(self) -> str:
        """Generate the full migration report."""
        if not self.analyses:
            return "No databases analyzed"

        self._generate_header()
        self._generate_executive_summary()
        self._generate_detailed_analysis()
        self._generate_schema_details()
        self._generate_complexity_assessment()
        self._generate_recommendations()

        return "\n".join(self.report)

    def _generate_header(self):
        self.report.append("# SQLite to PostgreSQL Migration Analysis Report")
        self.report.append(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.report.append("")

    def _generate_executive_summary(self):
        self.report.append("## Executive Summary")
        self.report.append("")
        total_size = sum(db.file_size_mb for db in self.analyses.values())
        total_rows = sum(db.total_rows for db in self.analyses.values())
        total_tables = sum(len(db.tables) for db in self.analyses.values())
        avg_complexity = sum(db.overall_complexity for db in self.analyses.values()) / len(self.analyses)

        self.report.append(f"- **Databases**: {len(self.analyses)}")
        self.report.append(f"- **Total Size**: {total_size:.1f} MB")
        self.report.append(f"- **Total Tables**: {total_tables}")
        self.report.append(f"- **Total Rows**: {total_rows:,}")
        self.report.append(f"- **Average Complexity**: {avg_complexity:.1f}/10")
        self.report.append("")

        high_priority = [name for name, db in self.analyses.items() if db.migration_priority == "HIGH"]
        medium_priority = [name for name, db in self.analyses.items() if db.migration_priority == "MEDIUM"]
        low_priority = [name for name, db in self.analyses.items() if db.migration_priority == "LOW"]

        self.report.append("### Migration Priority")
        if high_priority:
            self.report.append(f"- **HIGH**: {', '.join(high_priority)}")
        if medium_priority:
            self.report.append(f"- **MEDIUM**: {', '.join(medium_priority)}")
        if low_priority:
            self.report.append(f"- **LOW**: {', '.join(low_priority)}")
        self.report.append("")

    def _generate_detailed_analysis(self):
        self.report.append("## Detailed Database Analysis")
        self.report.append("")

        for db_name, analysis in sorted(
            self.analyses.items(),
            key=lambda x: x[1].migration_priority == "HIGH",
            reverse=True,
        ):
            self.report.append(f"### {db_name} Database")
            self.report.append("")
            self.report.append(f"- **File Size**: {analysis.file_size_mb:.2f} MB")
            self.report.append(f"- **Tables**: {len(analysis.tables)}")
            self.report.append(f"- **Total Rows**: {analysis.total_rows:,}")
            self.report.append(f"- **Complexity**: {analysis.overall_complexity}/10")
            self.report.append(f"- **Priority**: {analysis.migration_priority}")
            self.report.append("")

            if analysis.tables:
                self.report.append("#### Tables")
                for table in analysis.tables:
                    self.report.append(
                        f"- **{table.name}**: {table.row_count:,} rows, "
                        f"{len(table.columns)} columns, complexity {table.complexity_score}/10",
                    )
                    complex_cols = [col for col in table.columns if len(col.migration_notes) > 1]
                    if complex_cols:
                        self.report.append(f"  - Complex columns: {', '.join(col.name for col in complex_cols)}")
                self.report.append("")

            if analysis.migration_strategy:
                self.report.append("#### Migration Strategy")
                for strategy in analysis.migration_strategy:
                    self.report.append(f"- {strategy}")
                self.report.append("")

    def _generate_schema_details(self):
        self.report.append("## PostgreSQL Schema Generation")
        self.report.append("")
        for db_name, analysis in self.analyses.items():
            if analysis.tables:
                self.report.append(f"### {db_name} Schema")
                self.report.append("")
                self.report.append("```sql")
                self.report.append(analysis.postgresql_schema)
                self.report.append("```")
                self.report.append("")

    def _generate_complexity_assessment(self):
        self.report.append("## Migration Complexity Assessment")
        self.report.append("")
        type_issues = {}
        for analysis in self.analyses.values():
            for table in analysis.tables:
                for col in table.columns:
                    for note in col.migration_notes:
                        if "precision" in note.lower() or "conversion" in note.lower():
                            if analysis.name not in type_issues:
                                type_issues[analysis.name] = []
                            type_issues[analysis.name].append(f"{table.name}.{col.name}: {note}")
        if type_issues:
            self.report.append("### Type Conversion Issues")
            for db_name, issues in type_issues.items():
                self.report.append(f"#### {db_name}")
                for issue in issues:
                    self.report.append(f"- {issue}")
            self.report.append("")

    def _generate_recommendations(self):
        self.report.append("## Recommendations")
        self.report.append("")
        total_size = sum(db.file_size_mb for db in self.analyses.values())
        if total_size > 10:
            self.report.append("- **Large Dataset**: Consider staging migration in development environment first")

        high_priority = [name for name, db in self.analyses.items() if db.migration_priority == "HIGH"]
        if high_priority:
            self.report.append(f"- **High Priority Databases**: Focus on {', '.join(high_priority)} first")

        if any(len(db.tables) > 5 for db in self.analyses.values()):
            self.report.append("- **Complex Schemas**: Plan foreign key dependency migration order")

        if any(
            "json" in note.lower()
            for db in self.analyses.values()
            for table in db.tables
            for col in table.columns
            for note in col.migration_notes
        ):
            self.report.append("- **JSON Data**: Validate JSON format and consider JSONB for better performance")

        self.report.append(
            "- **Testing**: Validate data integrity after migration using row counts and sample data verification",
        )
        self.report.append("- **Backup**: Create full SQLite backups before starting migration")
        self.report.append("")


def analyze_all_databases(base_path: str = ".") -> dict[str, DatabaseAnalysis]:
    """Analyze all SQLite databases in the specified path."""
    base_path = Path(base_path)
    db_files = list(base_path.glob("*.db"))

    if not db_files:
        logger.error("No SQLite database files (*.db) found")
        return {}

    logger.info(f"Found {len(db_files)} database files")

    analyses = {}
    for db_file in sorted(db_files):
        try:
            analyzer = SQLiteDatabaseAnalyzer(str(db_file))
            analysis = analyzer.analyze_database()
            analyses[analysis.name] = analysis
        except Exception as e:
            logger.error(f"Failed to analyze {db_file}: {e}")
            # Continue processing other databases if one fails
            continue

    return analyses


def generate_migration_report(analyses: dict[str, DatabaseAnalysis]) -> str:
    """Generate comprehensive migration report."""
    generator = MigrationReportGenerator(analyses)
    return generator.generate_report()


def save_results(analyses: dict[str, DatabaseAnalysis], output_dir: str = ".") -> None:
    """Save analysis results to files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Save detailed JSON analysis
    json_data = {name: asdict(analysis) for name, analysis in analyses.items()}
    json_file = output_path / "sqlite_migration_analysis.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, default=str)
    logger.info(f"Detailed analysis saved to: {json_file}")

    # Save migration report
    report = generate_migration_report(analyses)
    report_file = output_path / "sqlite_to_postgresql_migration_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"Migration report saved to: {report_file}")

    # Save individual PostgreSQL schemas
    for db_name, analysis in analyses.items():
        if analysis.tables:
            schema_file = output_path / f"{db_name}_postgresql_schema.sql"
            with open(schema_file, "w", encoding="utf-8") as f:
                f.write(analysis.postgresql_schema)
            logger.info(f"PostgreSQL schema saved to: {schema_file}")


def main():
    """Main execution function."""
    print("SQLite to PostgreSQL Migration Analysis")
    print("=" * 50)

    # Analyze databases
    analyses = analyze_all_databases()

    if not analyses:
        print("No databases found to analyze")
        return 1

    # Save results
    save_results(analyses)

    # Print summary
    print(f"\nAnalysis completed for {len(analyses)} databases:")
    for name, analysis in analyses.items():
        print(
            f"  {name}: {len(analysis.tables)} tables, "
            f"{analysis.total_rows:,} rows, "
            f"complexity {analysis.overall_complexity}/10, "
            f"priority {analysis.migration_priority}",
        )

    print("\nFiles generated:")
    print("  - sqlite_migration_analysis.json (detailed analysis)")
    print("  - sqlite_to_postgresql_migration_report.md (migration report)")
    print("  - [database]_postgresql_schema.sql (PostgreSQL schemas)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
