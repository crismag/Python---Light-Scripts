"""CLI: manage POSIX ACL permissions on a directory.

WARNING: changes filesystem permissions; Linux only. See SECURITY.md.
"""

import argparse
import sys
from pathlib import Path

from python_light_scripts.acl import manager
from python_light_scripts.acl.manager import AclError

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage ACL permissions on a folder.")
    parser.add_argument("folder", help="Target folder for ACL modification")
    parser.add_argument("--add", help="Add ACL entry (e.g., u:alice:rw)")
    parser.add_argument("--remove", help="Remove ACL entry (e.g., u:alice)")
    parser.add_argument("--default", action="store_true", help="Apply as default ACL")
    parser.add_argument("--recursive", action="store_true", help="Apply recursively")
    args = parser.parse_args()

    path = Path(args.folder).resolve()
    if not path.is_dir():
        print(f"Error: {path} is not a valid directory.")
        sys.exit(1)

    try:
        if args.add:
            manager.apply_acl_change(path, args.add, "add", args.default, args.recursive)
        elif args.remove:
            manager.apply_acl_change(path, args.remove, "remove", args.default, args.recursive)
        else:
            print("Error: provide either --add or --remove.")
            sys.exit(1)
    except AclError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
