#!/usr/bin/env python3
"""
Convert MCP JSON configurations to claude mcp add commands
"""

import json
import os
from pathlib import Path


def json_to_claude_command(name, config):
    """Convert a JSON MCP server config to a claude mcp add command"""
    
    # Base command
    cmd_parts = ["claude", "mcp", "add", "-s", "user", f'"{name}"']
    
    # Handle different transport types
    if "transport" in config:
        transport = config["transport"]
        cmd_parts.extend(["-t", transport])
        
        # For HTTP transport
        if transport == "http" and "url" in config:
            cmd_parts.append(f'"{config["url"]}"')
            
            # Add headers if present
            if "headers" in config:
                for key, value in config["headers"].items():
                    cmd_parts.extend(["-H", f'"{key}: {value}"'])
        
    # Default stdio transport
    elif "command" in config:
        cmd_parts.append(f'"{config["command"]}"')
        
        # Add args
        if "args" in config:
            for arg in config["args"]:
                cmd_parts.append(f'"{arg}"')
    
    # Add environment variables
    if "env" in config:
        for key, value in config["env"].items():
            cmd_parts.extend(["-e", f'"{key}={value}"'])
    
    return " ".join(cmd_parts)

def process_config_file(filepath):
    """Process a single MCP configuration file"""
    with open(filepath) as f:
        data = json.load(f)
    
    if "mcpServers" not in data:
        print(f"Warning: No mcpServers found in {filepath}")
        return []
    
    commands = []
    for name, config in data["mcpServers"].items():
        cmd = json_to_claude_command(name, config)
        commands.append((name, cmd))
    
    return commands

def main():
    config_dir = Path.home() / ".claude" / "mcp"
    
    print("MCP Configuration to Command Converter")
    print("=" * 40)
    
    # Process all JSON files in the mcp directory
    all_commands = []
    for json_file in config_dir.glob("*.json"):
        if json_file.name.endswith(".example"):
            continue
            
        print(f"\nProcessing {json_file.name}...")
        commands = process_config_file(json_file)
        all_commands.extend(commands)
        
        for name, cmd in commands:
            print(f"  - {name}")
    
    # Write commands to file
    output_file = Path.home() / ".claude" / "scripts" / "install-all-mcp.sh"
    with open(output_file, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Auto-generated MCP installation commands\n")
        f.write("# Generated from JSON configs in ~/.claude/mcp/\n\n")
        f.write("set -e\n\n")
        
        for name, cmd in all_commands:
            f.write(f"# Install {name}\n")
            f.write(f"echo 'Installing {name}...'\n")
            f.write(f"{cmd}\n\n")
    
    os.chmod(output_file, 0o755)
    
    print(f"\n✓ Generated {len(all_commands)} installation commands")
    print(f"✓ Output saved to: {output_file}")
    print("\nTo install all servers, run:")
    print(f"  {output_file}")

if __name__ == "__main__":
    main()