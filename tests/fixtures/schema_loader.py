"""
Schema loading utilities for test database setup.

Provides utilities to load and validate SQL schema files for testing.
"""

from pathlib import Path
import re

import asyncpg


class SchemaLoader:
    """Utility class for loading and applying database schemas."""
    
    def __init__(self, project_root: Path):
        """
        Initialize schema loader.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.schema_files = [
            # Auth migrations first (dependencies)
            "src/database/migrations/001_auth_schema.sql",
            "src/database/migrations/002_auth_rbac_schema.sql",
            # Other schema files
            "analytics_postgresql_schema.sql",
            "security_events_postgresql_schema.sql", 
            "ab_testing_postgresql_schema.sql",
            "metrics_postgresql_schema.sql",
        ]
    
    def validate_schema_file(self, schema_file: Path) -> str:
        """
        Validate and fix common issues in schema files.
        
        Args:
            schema_file: Path to schema file
            
        Returns:
            Fixed schema SQL content
        """
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")
        
        content = schema_file.read_text()
        
        # Fix common schema issues
        # 1. Fix incorrect default timestamp values
        content = re.sub(
            r"DEFAULT\s+'CURRENT_TIMESTAMP'",
            "DEFAULT CURRENT_TIMESTAMP",
            content,
            flags=re.IGNORECASE,
        )
        
        # 2. Fix VARCHAR without length to TEXT for PostgreSQL
        content = re.sub(r"\bVARCHAR\b(?!\s*\()", "TEXT", content)
        
        # 3. Ensure proper semicolons at statement ends
        # Split by semicolon and rejoin with proper formatting
        statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]
        content = ";\n".join(statements) + ";"
        
        return content
    
    async def apply_schemas(self, connection: asyncpg.Connection) -> list[str]:
        """
        Apply all schema files to the database connection.
        
        Args:
            connection: AsyncPG database connection
            
        Returns:
            List of applied schema file names
        """
        applied_schemas = []
        
        for schema_file_name in self.schema_files:
            schema_path = self.project_root / schema_file_name
            
            if schema_path.exists():
                try:
                    schema_sql = self.validate_schema_file(schema_path)
                    
                    # Apply schema SQL
                    await connection.execute(schema_sql)
                    applied_schemas.append(schema_file_name)
                    print(f"✓ Applied schema: {schema_file_name}")
                    
                except Exception as e:
                    print(f"✗ Failed to apply schema {schema_file_name}: {e}")
                    raise
            else:
                print(f"⚠ Schema file not found: {schema_file_name}")
        
        return applied_schemas
    
    def get_missing_schemas(self) -> list[str]:
        """
        Get list of missing schema files.
        
        Returns:
            List of missing schema file names
        """
        missing = []
        for schema_file_name in self.schema_files:
            schema_path = self.project_root / schema_file_name
            if not schema_path.exists():
                missing.append(schema_file_name)
        return missing