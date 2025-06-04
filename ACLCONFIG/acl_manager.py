#!/usr/bin/env python3
"""
ACL Manager Tool for Linux Filesystems

This script provides an automated way to configure ACL (Access Control List) 
permissions on directories in Unix/Linux systems. It supports:
- Adding or removing ACL entries for users/groups
- Applying default and recursive ACLs
- Storing current ACL configuration in `.aclinfo`
- Logging all changes with timestamps in `.acllog`

Author: OpenAI ChatGPT
Python Version: 3.11+

Example usage:
--------------
# Add rw permission for user alice
python acl_manager.py /shared/data --add u:alice:rw

# Remove permission for user alice
python acl_manager.py /shared/data --remove u:alice

# Add default ACL for group devs
python acl_manager.py /shared/data --add g:devs:rwx --default

# Apply ACL recursively
python acl_manager.py /shared/data --add u:bob:rw --recursive
"""

import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import sys

def execute_command(command: str) -> str:
    """Executes a shell command and returns its output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def get_acl_info(path: Path) -> str:
    """Retrieves the current ACL information for a given path."""
    return execute_command(f"getfacl -p {path}")

def save_current_acl_snapshot(path: Path) -> None:
    """Saves the current ACL to a `.aclinfo` file in the target directory."""
    aclinfo_path = path / ".aclinfo"
    aclinfo_path.write_text(get_acl_info(path))

def log_acl_change(path: Path, action: str, acl_entry: str) -> None:
    """Logs a change to the `.acllog` file in the target directory."""
    acllog_path = path / ".acllog"
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] ACTION: {action.upper()} | ENTRY: {acl_entry}\n"
    with acllog_path.open("a") as f:
        f.write(log_entry)

def apply_acl_change(path: Path, acl_entry: str, action: str, use_default: bool = False, recursive: bool = False) -> None:
    """Applies an ACL change to the target directory."""
    flag = "-m" if action == "add" else "-x"
    if use_default:
        flag = f"-d {flag}"
    if recursive:
        flag = f"-R {flag}"
    command = f"setfacl {flag} {acl_entry} {path}"
    execute_command(command)
    log_acl_change(path, action, acl_entry)
    save_current_acl_snapshot(path)

def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments using argparse."""
    parser = argparse.ArgumentParser(description="Manage ACL permissions on a folder.")
    parser.add_argument("folder", help="Target folder for ACL modification")
    parser.add_argument("--add", help="Add ACL entry (e.g., u:alice:rw)")
    parser.add_argument("--remove", help="Remove ACL entry (e.g., u:alice)")
    parser.add_argument("--default", action="store_true", help="Apply as default ACL (for new files)")
    parser.add_argument("--recursive", action="store_true", help="Apply ACL recursively to all contents")
    return parser.parse_args()

def main() -> None:
    """Main entry point of the script."""
    args = parse_arguments()
    path = Path(args.folder).resolve()

    if not path.exists() or not path.is_dir():
        print(f"Error: {path} is not a valid directory.")
        sys.exit(1)

    if args.add:
        apply_acl_change(path, args.add, action="add", use_default=args.default, recursive=args.recursive)
    elif args.remove:
        apply_acl_change(path, args.remove, action="remove", use_default=args.default, recursive=args.recursive)
    else:
        print("Error: Please provide either --add or --remove option.")
        sys.exit(1)

if __name__ == "__main__":
    main()
