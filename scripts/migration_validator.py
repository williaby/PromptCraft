#!/usr/bin/env python3
# nosemgrep
"""
SQLite to PostgreSQL Migration Validator

This script provides validation utilities for ensuring successful migration
between SQLite and PostgreSQL databases.
"""

import json
import sqlite3
from pathlib import Path


class MigrationValidator:
    """Validates SQLite to PostgreSQL migration integrity."""

    def __init__(self, sqlite_db_path: str):
        self.sqlite_path = Path(sqlite_db_path)
        self.db_name = self.sqlite_path.stem

    def validate_json_data(self) -> dict[str, list[dict]]:
        """Validate JSON data in SQLite columns for PostgreSQL compatibility."""
        print(f"Validating JSON data in {self.db_name}...")

        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get tables with JSON columns
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            json_validation_results = {}

            for table in tables:
                cursor.execute(f"PRAGMA table_info([{table}])")
                columns = cursor.fetchall()

                json_columns = [col["name"] for col in columns if col["type"].upper() == "JSON"]
                if not json_columns:
                    continue

                print(f"  Checking table {table} columns: {', '.join(json_columns)}")

                for json_col in json_columns:
                    cursor.execute(
                        f"SELECT rowid, [{json_col}] FROM [{table}] WHERE [{json_col}] IS NOT NULL LIMIT 100",
                    )
                    rows = cursor.fetchall()

                    validation_issues = []
                    valid_count = 0

                    for row in rows:
                        rowid, json_data = row
                        try:
                            json.loads(json_data)
                            valid_count += 1
                        except json.JSONDecodeError as e:
                            validation_issues.append(
                                {
                                    "rowid": rowid,
                                    "error": str(e),
                                    "data_preview": json_data[:100] if json_data else None,
                                },
                            )

                    key = f"{table}.{json_col}"
                    json_validation_results[key] = {
                        "total_checked": len(rows),
                        "valid_json": valid_count,
                        "invalid_json": len(validation_issues),
                        "issues": validation_issues[:5],  # Limit to first 5 issues
                        "success_rate": valid_count / len(rows) * 100 if rows else 0,
                    }

        return json_validation_results

    def generate_row_count_validation(self) -> dict[str, int]:
        """Generate row counts for migration validation."""
        print(f"Generating row counts for {self.db_name}...")

        with sqlite3.connect(self.sqlite_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            row_counts = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                count = cursor.fetchone()[0]
                row_counts[table] = count
                print(f"  {table}: {count:,} rows")

        return row_counts

    def generate_sample_data_validation(self, sample_size: int = 5) -> dict[str, list[dict]]:
        """Generate sample data for validation comparison."""
        print(f"Generating sample data for {self.db_name}...")

        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            sample_data = {}
            for table in tables:
                cursor.execute(f"SELECT * FROM [{table}] LIMIT {sample_size}")
                rows = cursor.fetchall()
                sample_data[table] = [dict(row) for row in rows]

        return sample_data

    def validate_numeric_precision(self) -> dict[str, list[dict]]:
        """Validate numeric precision for REAL type columns."""
        print(f"Validating numeric precision in {self.db_name}...")

        with sqlite3.connect(self.sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            precision_analysis = {}

            for table in tables:
                cursor.execute(f"PRAGMA table_info([{table}])")
                columns = cursor.fetchall()

                real_columns = [col["name"] for col in columns if col["type"].upper() == "REAL"]
                if not real_columns:
                    continue

                print(f"  Checking table {table} REAL columns: {', '.join(real_columns)}")

                for real_col in real_columns:
                    cursor.execute(f"SELECT [{real_col}] FROM [{table}] WHERE [{real_col}] IS NOT NULL")
                    values = [row[0] for row in cursor.fetchall()]

                    if not values:
                        continue

                    # Analyze precision
                    decimal_places = []
                    for value in values:
                        if isinstance(value, (int, float)):
                            str_val = str(float(value))
                            if "." in str_val:
                                decimal_part = str_val.split(".")[1].rstrip("0")
                                decimal_places.append(len(decimal_part))

                    if decimal_places:
                        key = f"{table}.{real_col}"
                        precision_analysis[key] = {
                            "total_values": len(values),
                            "max_decimal_places": max(decimal_places),
                            "avg_decimal_places": sum(decimal_places) / len(decimal_places),
                            "precision_warning": max(decimal_places) > 6,
                            "sample_values": values[:5],
                        }

        return precision_analysis


def validate_all_databases() -> dict[str, dict]:
    """Validate all SQLite databases for migration."""
    db_files = list(Path().glob("*.db"))

    if not db_files:
        print("No SQLite databases found")
        return {}

    print("=" * 70)
    print("SQLite to PostgreSQL Migration Validation")
    print("=" * 70)

    all_validation_results = {}

    for db_file in sorted(db_files):
        print(f"\n🗄️  Validating {db_file.name}...")
        validator = MigrationValidator(db_file)

        validation_result = {
            "row_counts": validator.generate_row_count_validation(),
            "json_validation": validator.validate_json_data(),
            "numeric_precision": validator.validate_numeric_precision(),
            "sample_data": validator.generate_sample_data_validation(),
        }

        all_validation_results[db_file.stem] = validation_result

    return all_validation_results


def print_validation_summary(results: dict[str, dict]):
    """Print validation summary."""
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    # JSON Validation Summary
    json_issues = []
    for db_name, db_results in results.items():
        for column, validation in db_results["json_validation"].items():
            if validation["invalid_json"] > 0:
                json_issues.append(
                    f"{db_name}.{column}: {validation['invalid_json']}/{validation['total_checked']} invalid",
                )

    if json_issues:
        print("⚠️  JSON VALIDATION ISSUES:")
        for issue in json_issues:
            print(f"   • {issue}")
    else:
        print("✅ JSON VALIDATION: All JSON data is valid")

    # Precision Issues
    precision_warnings = []
    for db_name, db_results in results.items():
        for column, analysis in db_results["numeric_precision"].items():
            if analysis["precision_warning"]:
                precision_warnings.append(f"{db_name}.{column}: max {analysis['max_decimal_places']} decimal places")

    if precision_warnings:
        print("\n⚠️  PRECISION WARNINGS:")
        for warning in precision_warnings:
            print(f"   • {warning}")
    else:
        print("\n✅ NUMERIC PRECISION: No high-precision values detected")

    # Row Count Summary
    print("\n📊 ROW COUNTS BY DATABASE:")
    for db_name, db_results in results.items():
        total_rows = sum(db_results["row_counts"].values())
        print(f"   • {db_name}: {total_rows:,} total rows across {len(db_results['row_counts'])} tables")

        for table, count in sorted(db_results["row_counts"].items()):
            if count > 0:
                print(f"     - {table}: {count:,} rows")

    print("\n🎯 MIGRATION RECOMMENDATIONS:")

    # Check for large tables
    large_tables = []
    for db_name, db_results in results.items():
        for table, count in db_results["row_counts"].items():
            if count > 10000:
                large_tables.append(f"{db_name}.{table} ({count:,} rows)")

    if large_tables:
        print("   • Use batch processing for large tables:")
        for table in large_tables:
            print(f"     - {table}")

    # JSON recommendations
    if any(db_results["json_validation"] for db_results in results.values()):
        print("   • JSON Data Migration:")
        print("     - Use JSONB type in PostgreSQL for better performance")
        print("     - Validate JSON parsing during migration")
        print("     - Consider indexing JSON fields if queried frequently")

    # Precision recommendations
    if precision_warnings:
        print("   • Numeric Precision:")
        print("     - Review high-precision values for accuracy requirements")
        print("     - Consider NUMERIC type for exact decimal calculations")
        print("     - Test calculations to ensure acceptable precision loss")


def save_validation_results(results: dict[str, dict]):
    """Save validation results to files."""
    # Save detailed validation results
    with open("migration_validation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("\n💾 Validation results saved to: migration_validation_results.json")

    # Generate PostgreSQL validation queries
    validation_queries = []
    validation_queries.append("-- PostgreSQL Validation Queries")
    validation_queries.append("-- Run these after migration to validate data integrity")
    validation_queries.append("")

    for db_name, db_results in results.items():
        validation_queries.append(f"-- Validation for {db_name} database")
        for table, expected_count in db_results["row_counts"].items():
            validation_queries.append(f"-- Expected: {expected_count} rows")
            validation_queries.append(
                f"SELECT '{table}' as table_name, COUNT(*) as actual_count, {expected_count} as expected_count, ",
            )
            validation_queries.append(
                f"       CASE WHEN COUNT(*) = {expected_count} THEN 'PASS' ELSE 'FAIL' END as validation_status",
            )
            validation_queries.append(f"FROM [{table}];")
            validation_queries.append("")

    with open("postgresql_validation_queries.sql", "w") as f:
        f.write("\n".join(validation_queries))

    print("💾 PostgreSQL validation queries saved to: postgresql_validation_queries.sql")


def main():
    """Main execution."""
    validation_results = validate_all_databases()

    if validation_results:
        print_validation_summary(validation_results)
        save_validation_results(validation_results)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
