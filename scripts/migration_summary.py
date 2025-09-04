#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Executive Summary

This script provides a concise executive summary of the migration analysis
with actionable recommendations and complexity assessment.
"""

import json
from pathlib import Path
from typing import Any


def load_analysis() -> dict[str, Any]:
    """Load the migration analysis JSON."""
    json_file = Path("sqlite_migration_analysis.json")
    if not json_file.exists():
        raise FileNotFoundError("Run sqlite_to_postgresql_analysis.py first to generate analysis")

    with open(json_file) as f:
        return json.load(f)


class ExecutiveSummaryPrinter:
    """Prints the executive summary of the migration analysis."""

    def __init__(self, analysis: dict[str, Any]):
        self.analysis = analysis

    def print_summary(self):
        """Prints the complete executive summary."""
        self._print_header()
        self._print_overview()
        self._print_priority()
        self._print_key_findings()
        self._print_migration_strategy()
        self._print_technical_recommendations()
        self._print_risk_assessment()
        self._print_next_steps()
        self._print_footer()

    def _print_header(self):
        print("=" * 70)
        print("SQLite to PostgreSQL Migration - Executive Summary")
        print("=" * 70)

    def _print_overview(self):
        total_size = sum(db["file_size_mb"] for db in self.analysis.values())
        total_rows = sum(db["total_rows"] for db in self.analysis.values())
        total_tables = sum(len(db["tables"]) for db in self.analysis.values())

        print("\n📊 DATABASE OVERVIEW:")
        print(f"   • {len(self.analysis)} databases ({total_size:.1f}MB total)")
        print(f"   • {total_tables} tables with {total_rows:,} total rows")
        print(f"   • Primary data in 'analytics' DB ({self.analysis['analytics']['total_rows']:,} rows)")

    def _print_priority(self):
        high_priority = [name for name, db in self.analysis.items() if db["migration_priority"] == "HIGH"]
        medium_priority = [name for name, db in self.analysis.items() if db["migration_priority"] == "MEDIUM"]
        low_priority = [name for name, db in self.analysis.items() if db["migration_priority"] == "LOW"]

        print("\n🎯 MIGRATION PRIORITY:")
        if high_priority:
            print(f"   • HIGH:   {', '.join(high_priority)}")
        if medium_priority:
            print(f"   • MEDIUM: {', '.join(medium_priority)}")
        if low_priority:
            print(f"   • LOW:    {', '.join(low_priority)}")

    def _print_key_findings(self):
        print("\n🔍 KEY FINDINGS:")
        self._print_json_data_detection()
        self._print_data_volume_analysis()
        self._print_type_conversion_issues()

    def _print_json_data_detection(self):
        json_tables = []
        for db_name, db_data in self.analysis.items():
            for table in db_data["tables"]:
                for col in table["columns"]:
                    if any("json" in note.lower() for note in col["migration_notes"]):
                        json_tables.append(f"{db_name}.{table['name']}")
                        break
        if json_tables:
            print(f"   • JSON Data: {len(json_tables)} tables contain JSON columns")
            for table in json_tables:
                print(f"     - {table}")

    def _print_data_volume_analysis(self):
        large_tables = []
        for db_name, db_data in self.analysis.items():
            for table in db_data["tables"]:
                if table["row_count"] > 1000:
                    large_tables.append((f"{db_name}.{table['name']}", table["row_count"]))
        if large_tables:
            print(f"   • Large Tables: {len(large_tables)} tables with >1K rows")
            for table_name, count in large_tables:
                print(f"     - {table_name}: {count:,} rows")

    def _print_type_conversion_issues(self):
        precision_issues = []
        for db_name, db_data in self.analysis.items():
            for table in db_data["tables"]:
                for col in table["columns"]:
                    if any("precision" in note.lower() for note in col["migration_notes"]):
                        precision_issues.append(f"{db_name}.{table['name']}.{col['name']}")
        if precision_issues:
            print(f"   • Precision Issues: {len(precision_issues)} columns need attention")
            for col in precision_issues:
                print(f"     - {col} (REAL type precision)")

    def _print_migration_strategy(self):
        print("\n⚙️  MIGRATION STRATEGY:")
        avg_complexity = sum(db["overall_complexity"] for db in self.analysis.values()) / len(self.analysis)
        if avg_complexity <= 3:
            complexity_assessment = "LOW - Straightforward migration"
        elif avg_complexity <= 6:
            complexity_assessment = "MEDIUM - Some challenges expected"
        else:
            complexity_assessment = "HIGH - Complex migration requiring careful planning"

        print(f"   • Complexity: {complexity_assessment} (avg {avg_complexity:.1f}/10)")
        print("   • Recommended Migration Order:")
        print("     1. security_events (empty, establish structure)")
        print("     2. metrics (empty, validate schema)")
        print("     3. ab_testing (small dataset, test JSON handling)")
        print("     4. analytics (largest dataset, production migration)")

    def _print_technical_recommendations(self):
        print("\n🛠️  TECHNICAL RECOMMENDATIONS:")
        print("   • Schema Changes:")
        print("     - Convert JSON columns to JSONB for better performance")
        print("     - Review TIMESTAMP vs TEXT for date fields")
        print("     - Validate REAL precision requirements")
        print("   • Migration Process:")
        print("     - Create PostgreSQL schemas first")
        print("     - Test with empty databases (security_events, metrics)")
        print("     - Validate JSON data integrity before migration")
        print("     - Use batch processing for analytics table (12K+ rows)")
        print("   • Quality Assurance:")
        print("     - Compare row counts before/after migration")
        print("     - Validate JSON data parsing")
        print("     - Test index performance")
        print("     - Verify data types handle production loads")

    def _print_risk_assessment(self):
        print("\n⚠️  RISK ASSESSMENT:")
        risks = []
        if any(db["total_rows"] > 10000 for db in self.analysis.values()):
            risks.append("Large dataset migration - test thoroughly")

        json_tables_exist = any(
            "json" in note.lower()
            for db in self.analysis.values()
            for table in db["tables"]
            for col in table["columns"]
            for note in col["migration_notes"]
        )
        if json_tables_exist:
            risks.append("JSON data conversion - validate format compatibility")

        precision_issues_exist = any(
            "precision" in note.lower()
            for db in self.analysis.values()
            for table in db["tables"]
            for col in table["columns"]
            for note in col["migration_notes"]
        )
        if precision_issues_exist:
            risks.append("Numeric precision changes - verify calculation accuracy")

        if not risks:
            risks.append("Low risk - small datasets with straightforward schemas")

        for i, risk in enumerate(risks, 1):
            print(f"   {i}. {risk}")

    def _print_next_steps(self):
        print("\n🚀 IMMEDIATE NEXT STEPS:")
        print("   1. Review generated PostgreSQL schemas (*.sql files)")
        print("   2. Set up PostgreSQL development environment")
        print("   3. Test schema creation with empty databases")
        print("   4. Develop migration scripts for data transfer")
        print("   5. Create validation scripts for data integrity checks")
        print("\n📁 Generated Files:")
        print("   • sqlite_migration_analysis.json - Detailed analysis")
        print("   • sqlite_to_postgresql_migration_report.md - Complete report")
        print("   • *_postgresql_schema.sql - PostgreSQL DDL scripts")

    def _print_footer(self):
        print("=" * 70)


def print_executive_summary():
    """Print executive summary of migration analysis."""
    try:
        analysis = load_analysis()
        printer = ExecutiveSummaryPrinter(analysis)
        printer.print_summary()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    print_executive_summary()
