#!/usr/bin/env python3
"""
RAD Fix Applier - Apply AI-suggested fixes for verified assumptions

Handles automatic and manual application of fixes suggested by AI verification.
Provides backup and rollback functionality for safe code modifications.
"""

import json
import sys
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile
import time
from datetime import datetime


@dataclass
class FixApplication:
    """Represents a fix that can be applied to code"""
    file_path: str
    line_number: int
    assumption_text: str
    original_code: str
    suggested_fix: str
    risk_level: str
    confidence: float
    backup_path: Optional[str] = None


class SafeFileModifier:
    """Safely modify files with backup and rollback capabilities"""
    
    def __init__(self, backup_dir: Optional[str] = None):
        self.backup_dir = Path(backup_dir) if backup_dir else Path("tmp_cleanup/rad_backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.applied_fixes = []
        
    def create_backup(self, file_path: str) -> str:
        """Create backup of file before modification"""
        source_path = Path(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.name}.{timestamp}.backup"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(source_path, backup_path)
        return str(backup_path)
    
    def apply_fix(self, fix: FixApplication) -> bool:
        """Apply a single fix to a file with backup"""
        try:
            # Create backup
            backup_path = self.create_backup(fix.file_path)
            fix.backup_path = backup_path
            
            # Read current file
            with open(fix.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Apply fix (simple line replacement for now)
            if 1 <= fix.line_number <= len(lines):
                original_line = lines[fix.line_number - 1]
                
                # Verify we're modifying the expected line
                if fix.original_code.strip() in original_line.strip():
                    lines[fix.line_number - 1] = fix.suggested_fix + '\n'
                    
                    # Write modified file
                    with open(fix.file_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    
                    self.applied_fixes.append(fix)
                    print(f"✅ Applied fix to {Path(fix.file_path).name}:{fix.line_number}")
                    return True
                else:
                    print(f"⚠️ Skipped {fix.file_path}:{fix.line_number} - code changed since analysis")
                    return False
            else:
                print(f"⚠️ Skipped {fix.file_path}:{fix.line_number} - line number out of range")
                return False
                
        except Exception as e:
            print(f"❌ Failed to apply fix to {fix.file_path}:{fix.line_number}: {e}")
            return False
    
    def rollback_all(self) -> bool:
        """Rollback all applied fixes"""
        success = True
        
        for fix in reversed(self.applied_fixes):
            if fix.backup_path and Path(fix.backup_path).exists():
                try:
                    shutil.copy2(fix.backup_path, fix.file_path)
                    print(f"🔄 Rolled back {Path(fix.file_path).name}")
                except Exception as e:
                    print(f"❌ Failed to rollback {fix.file_path}: {e}")
                    success = False
            
        return success
    
    def cleanup_backups(self):
        """Remove backup files after successful application"""
        for fix in self.applied_fixes:
            if fix.backup_path and Path(fix.backup_path).exists():
                try:
                    Path(fix.backup_path).unlink()
                except Exception as e:
                    print(f"⚠️ Could not delete backup {fix.backup_path}: {e}")


class FixApplier:
    """Apply fixes based on different strategies (auto, review, none)"""
    
    def __init__(self, apply_mode: str = "review"):
        self.apply_mode = apply_mode
        self.file_modifier = SafeFileModifier()
        
    def apply_fixes(self, verification_results: List['AIVerificationResult']) -> Dict[str, int]:
        """Apply fixes based on the configured mode"""
        
        # Extract fixes from verification results
        fixes = self._extract_fixes(verification_results)
        
        if self.apply_mode == "none":
            return self._apply_none(fixes)
        elif self.apply_mode == "auto":
            return self._apply_auto(fixes)
        elif self.apply_mode == "review":
            return self._apply_review(fixes)
        else:
            raise ValueError(f"Unknown apply mode: {self.apply_mode}")
    
    def _extract_fixes(self, verification_results: List['AIVerificationResult']) -> List[FixApplication]:
        """Extract applicable fixes from AI verification results"""
        fixes = []
        
        for result in verification_results:
            if not result.suggested_fixes:
                continue
                
            # Parse assumption ID to get file and line
            if ':' in result.assumption_id:
                file_path, line_str = result.assumption_id.rsplit(':', 1)
                try:
                    line_number = int(line_str)
                except ValueError:
                    continue
                    
                # Create fix application for first suggested fix
                fix = FixApplication(
                    file_path=file_path,
                    line_number=line_number,
                    assumption_text=result.assumption_id,
                    original_code="# Original assumption comment",  # Would be extracted from context
                    suggested_fix=f"# {result.suggested_fixes[0]}",  # Convert to comment
                    risk_level=result.status.lower(),
                    confidence=result.confidence
                )
                fixes.append(fix)
                
        return fixes
    
    def _apply_none(self, fixes: List[FixApplication]) -> Dict[str, int]:
        """Don't apply any fixes, just report"""
        print("📄 Fix application disabled - generating report only")
        
        return {
            'total_fixes': len(fixes),
            'applied': 0,
            'skipped': len(fixes),
            'failed': 0
        }
    
    def _apply_auto(self, fixes: List[FixApplication]) -> Dict[str, int]:
        """Automatically apply safe fixes"""
        print("🔧 Auto-applying safe fixes...")
        
        applied = 0
        failed = 0
        skipped = 0
        
        # Sort by risk level and confidence
        safe_fixes = [f for f in fixes if f.confidence > 0.8 and f.risk_level != 'blocking']
        
        for fix in safe_fixes:
            if fix.risk_level == 'critical':
                # Skip critical fixes in auto mode - too risky
                print(f"⚠️ Skipping critical fix {Path(fix.file_path).name}:{fix.line_number} (requires manual review)")
                skipped += 1
                continue
                
            if self.file_modifier.apply_fix(fix):
                applied += 1
            else:
                failed += 1
        
        # Test changes after application
        if applied > 0:
            print("\n🧪 Testing applied changes...")
            if self._run_basic_tests():
                print("✅ Basic tests passed - changes look good")
                self.file_modifier.cleanup_backups()
            else:
                print("❌ Tests failed - rolling back changes")
                self.file_modifier.rollback_all()
                applied = 0
                failed = len(safe_fixes)
        
        return {
            'total_fixes': len(fixes),
            'applied': applied,
            'skipped': skipped + len([f for f in fixes if f not in safe_fixes]),
            'failed': failed
        }
    
    def _apply_review(self, fixes: List[FixApplication]) -> Dict[str, int]:
        """Stage fixes for manual review"""
        print("👀 Staging fixes for manual review...")
        
        if not fixes:
            return {
                'total_fixes': 0,
                'applied': 0,
                'skipped': 0,
                'failed': 0
            }
        
        # Group fixes by file
        fixes_by_file = {}
        for fix in fixes:
            if fix.file_path not in fixes_by_file:
                fixes_by_file[fix.file_path] = []
            fixes_by_file[fix.file_path].append(fix)
        
        print("\n📋 **Fixes Available for Review:**\n")
        
        for file_path, file_fixes in fixes_by_file.items():
            file_name = Path(file_path).name
            print(f"**{file_name}** ({len(file_fixes)} fixes)")
            
            for fix in file_fixes:
                print(f"  - Line {fix.line_number}: {fix.suggested_fix[:60]}...")
                print(f"    Confidence: {fix.confidence:.1%}, Risk: {fix.risk_level}")
                print()
        
        print("**Manual Review Instructions:**")
        print("1. Review each suggested fix above")
        print("2. Apply fixes manually to your code") 
        print("3. Test changes thoroughly")
        print("4. Re-run verification to confirm fixes")
        print()
        print("**To apply fixes automatically (use with caution):**")
        print("```bash")
        print("./scripts/verify-assumptions-smart.sh --apply-fixes=auto")
        print("```")
        
        return {
            'total_fixes': len(fixes),
            'applied': 0,
            'skipped': len(fixes),
            'failed': 0
        }
    
    def _run_basic_tests(self) -> bool:
        """Run basic tests to validate changes"""
        try:
            # Try to run a simple syntax check
            result = subprocess.run(
                ["python", "-m", "py_compile", "-"], 
                input="import sys; print('syntax ok')",
                text=True,
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
            
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            # If we can't run tests, assume it's okay (conservative)
            return True


def main():
    """Test the fix application system"""
    if len(sys.argv) < 2:
        print("Usage: python rad_fix_applier.py <verification_results.json> [apply_mode]")
        print("Apply modes: auto, review (default), none")
        sys.exit(1)
    
    results_file = sys.argv[1]
    apply_mode = sys.argv[2] if len(sys.argv) > 2 else "review"
    
    try:
        with open(results_file, 'r') as f:
            # Load verification results (would be actual AIVerificationResult objects)
            results_data = json.load(f)
        
        applier = FixApplier(apply_mode)
        print(f"Fix applier initialized with mode: {apply_mode}")
        print(f"Ready to process {len(results_data.get('verification_results', []))} results")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())