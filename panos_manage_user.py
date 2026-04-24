#!/usr/bin/env python3
"""
panos_manage_user.py - Manage local admin accounts on PAN-OS firewalls or Panoramas.

Usage:
    python panos_manage_user.py --firewall hosts.txt --auth admin:password --operation list
    python panos_manage_user.py --panorama hosts.txt --auth-api-key APIKEY --operation create --username bob --password P@ss --role superuser
    python panos_manage_user.py --firewall hosts.txt --auth admin:password --operation update --username bob --password NewP@ss
    python panos_manage_user.py --panorama hosts.txt --auth admin:password --operation delete --username bob

Supported roles:
    superuser, superreader, device-admin, device-admin-read-only, or any custom admin role profile name
"""

import argparse
import sys
import logging
import os
import time
import getpass
import xml.etree.ElementTree as ET
import base64
from typing import Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ADMIN_XPATH = "/config/mgt-config/users"
W = 68  # output width


def banner(text: str) -> None:
    print("=" * W)
    print(f"  {text}")
    print("=" * W)


def section(host: str, index: int, total: int) -> None:
    print(f"\n[{index}/{total}] {host}")
    print("-" * W)


def ok(msg: str) -> None:
    print(f"  [+] {msg}")


def fail(msg: str) -> None:
    print(f"  [-] {msg}")


def info(msg: str) -> None:
    print(f"  ... {msg}")


def resolve_auth(args) -> tuple:
    """Return (headers dict, commit_admin username or None).

    Priority order for each credential:
      1. CLI arg   2. Environment variable   3. Interactive prompt
    """
    # API key path
    api_key = args.auth_api_key or os.environ.get("PANOS_API_KEY")
    if api_key:
        return {"X-PAN-KEY": api_key}, None

    # Username / password path
    auth_str = args.auth or os.environ.get("PANOS_AUTH", "")
    if ":" in auth_str:
        username, password = auth_str.split(":", 1)
    else:
        username = auth_str or input("Login username: ").strip()
        password = os.environ.get("PANOS_PASSWORD") or getpass.getpass(f"Login password for '{username}': ")

    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}, username


def resolve_user_password(args) -> str:
    """Return the target account password from CLI arg, env var, or prompt."""
    if args.password:
        return args.password
    env_pw = os.environ.get("PANOS_USER_PASSWORD")
    if env_pw:
        return env_pw
    return getpass.getpass(f"Password for new/updated user '{args.username}': ")


def api_request(host: str, params: dict, headers: dict) -> ET.Element:
    url = f"https://{host}/api/?" + urlencode(params)
    req = Request(url, headers=headers)
    try:
        with urlopen(req) as resp:
            body = resp.read()
    except HTTPError as e:
        body = e.read()
        raise RuntimeError(f"HTTP {e.code}: {e.reason} — {body.decode(errors='replace')}") from e
    except URLError as e:
        raise RuntimeError(f"Connection error: {e.reason}") from e

    root = ET.fromstring(body)
    status = root.get("status")
    if status != "success":
        msg = root.findtext(".//msg") or ET.tostring(root, encoding="unicode")
        raise RuntimeError(f"API error ({status}): {msg}")
    return root


def hash_password(host: str, headers: dict, password: str) -> str:
    cmd_root = ET.Element("request")
    pw_hash = ET.SubElement(cmd_root, "password-hash")
    pw = ET.SubElement(pw_hash, "password")
    pw.text = password
    cmd_xml = ET.tostring(cmd_root, encoding="unicode")

    root = api_request(host, {"type": "op", "cmd": cmd_xml}, headers)
    phash = root.findtext(".//phash")
    if not phash:
        raise RuntimeError("password-hash response missing <phash>")
    return phash


def _parse_role(entry: ET.Element) -> str:
    role_based = entry.find("permissions/role-based")
    if role_based is None:
        return "unknown"
    if role_based.find("superuser") is not None:
        return "superuser"
    if role_based.find("superreader") is not None:
        return "superreader"
    if role_based.find("deviceadmin") is not None:
        return "device-admin"
    if role_based.find("devicereader") is not None:
        return "device-admin-read-only"
    custom = role_based.find("custom/profile")
    if custom is not None and custom.text:
        return f"custom:{custom.text}"
    return "unknown"


def _build_role_element(role: str) -> ET.Element:
    permissions = ET.Element("permissions")
    role_based = ET.SubElement(permissions, "role-based")
    role_lower = role.lower()

    if role_lower == "superuser":
        ET.SubElement(role_based, "superuser").text = "yes"
    elif role_lower == "superreader":
        ET.SubElement(role_based, "superreader").text = "yes"
    elif role_lower in ("device-admin", "deviceadmin"):
        ET.SubElement(role_based, "deviceadmin").text = "yes"
    elif role_lower in ("device-admin-read-only", "deviceadminreadonly"):
        ET.SubElement(role_based, "devicereader").text = "yes"
    else:
        custom = ET.SubElement(role_based, "custom")
        profile = ET.SubElement(custom, "profile")
        profile.text = role

    return permissions


# ── operations ───────────────────────────────────────────────────────────────

def op_list(host: str, headers: dict) -> bool:
    try:
        root = api_request(host, {
            "type": "config",
            "action": "get",
            "xpath": ADMIN_XPATH,
        }, headers)
    except RuntimeError as e:
        fail(f"Could not retrieve users: {e}")
        return False

    entries = root.findall(".//entry")
    if not entries:
        info("No local admins found")
        return True

    for entry in entries:
        name = entry.get("name", "?")
        role = _parse_role(entry)
        print(f"  {'':2}{name:<30} role={role}")
    return True


def op_create(host: str, headers: dict, username: str, password: str, role: str) -> bool:
    try:
        info("Hashing password...")
        phash = hash_password(host, headers, password)

        entry = ET.Element("entry", attrib={"name": username})
        phash_el = ET.SubElement(entry, "phash")
        phash_el.text = phash
        entry.append(_build_role_element(role))

        api_request(host, {
            "type": "config",
            "action": "set",
            "xpath": ADMIN_XPATH,
            "element": ET.tostring(entry, encoding="unicode"),
        }, headers)
        ok(f"User '{username}' created  (role={role})")
        return True
    except RuntimeError as e:
        fail(f"Create '{username}' failed: {e}")
        return False


def op_update(host: str, headers: dict, username: str,
              password: Optional[str], role: Optional[str]) -> bool:
    if not password and not role:
        info("Nothing to update — pass --password and/or --role")
        return True

    xpath_entry = f"{ADMIN_XPATH}/entry[@name='{username}']"

    try:
        api_request(host, {"type": "config", "action": "get", "xpath": xpath_entry}, headers)
    except RuntimeError:
        fail(f"User '{username}' not found")
        return False

    changed = []
    try:
        if password:
            info("Hashing password...")
            phash = hash_password(host, headers, password)
            phash_el = ET.Element("phash")
            phash_el.text = phash
            api_request(host, {
                "type": "config",
                "action": "edit",
                "xpath": f"{xpath_entry}/phash",
                "element": ET.tostring(phash_el, encoding="unicode"),
            }, headers)
            changed.append("password")

        if role:
            api_request(host, {
                "type": "config",
                "action": "edit",
                "xpath": f"{xpath_entry}/permissions",
                "element": ET.tostring(_build_role_element(role), encoding="unicode"),
            }, headers)
            changed.append(f"role={role}")

        ok(f"User '{username}' updated  ({', '.join(changed)})")
        return True
    except RuntimeError as e:
        fail(f"Update '{username}' failed: {e}")
        return False


def op_delete(host: str, headers: dict, username: str) -> bool:
    xpath_entry = f"{ADMIN_XPATH}/entry[@name='{username}']"
    try:
        api_request(host, {
            "type": "config",
            "action": "delete",
            "xpath": xpath_entry,
        }, headers)
        ok(f"User '{username}' deleted")
        return True
    except RuntimeError as e:
        if "not found" in str(e).lower() or "No such node" in str(e):
            fail(f"User '{username}' not found")
        else:
            fail(f"Delete '{username}' failed: {e}")
        return False


def do_commit(host: str, headers: dict, admin_user: Optional[str]) -> bool:
    commit = ET.Element("commit")
    if admin_user:
        partial = ET.SubElement(commit, "partial")
        admins = ET.SubElement(partial, "admin")
        member = ET.SubElement(admins, "member")
        member.text = admin_user

    scope = f"partial (admin={admin_user})" if admin_user else "full"

    try:
        resp = api_request(host, {
            "type": "commit",
            "cmd": ET.tostring(commit, encoding="unicode"),
        }, headers)
    except RuntimeError as e:
        fail(f"Commit failed: {e}")
        return False

    job_id = resp.findtext(".//job")
    if not job_id:
        msg = resp.findtext(".//msg") or resp.findtext(".//line") or "no pending changes"
        info(f"Commit ({scope}): {msg}")
        return True

    info(f"Commit job {job_id} queued ({scope}) — polling...")

    show_cmd = ET.tostring(
        ET.fromstring(f"<show><jobs><id>{job_id}</id></jobs></show>"),
        encoding="unicode",
    )

    for elapsed in range(60):
        time.sleep(3)
        try:
            poll = api_request(host, {"type": "op", "cmd": show_cmd}, headers)
        except RuntimeError as e:
            fail(f"Poll job {job_id} failed: {e}")
            return False

        status = poll.findtext(".//job/status") or ""
        if status != "FIN":
            if elapsed % 5 == 4:
                info(f"  Job {job_id} still running ({(elapsed + 1) * 3}s)...")
            continue

        result = poll.findtext(".//job/result") or "unknown"
        details = [el.text for el in poll.findall(".//job/details/line") if el.text]
        detail_str = " | ".join(details) if details else ""
        suffix = f": {detail_str}" if detail_str else ""

        if result == "OK":
            ok(f"Commit job {job_id} succeeded{suffix}")
            return True
        else:
            fail(f"Commit job {job_id} failed ({result}){suffix}")
            return False

    fail(f"Commit job {job_id} still running after 3 min — check device manually")
    return False


# ── helpers ───────────────────────────────────────────────────────────────────

def load_hosts(path: str) -> list:
    try:
        with open(path) as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print(f"ERROR: host file not found: {path}")
        sys.exit(1)


def print_summary(results: list, operation: str) -> None:
    print()
    banner("Summary")
    total = len(results)
    op_ok = sum(1 for r in results if r["op_ok"])
    op_fail = total - op_ok

    col = 22
    print(f"  {'Operation':<{col}} {operation.upper()}")
    print(f"  {'Hosts processed':<{col}} {total}")
    print(f"  {'Succeeded':<{col}} {op_ok}")
    if op_fail:
        print(f"  {'Failed':<{col}} {op_fail}")

    commit_results = [r for r in results if r.get("commit_ok") is not None]
    if commit_results:
        c_ok = sum(1 for r in commit_results if r["commit_ok"])
        c_fail = len(commit_results) - c_ok
        print(f"  {'Commits OK':<{col}} {c_ok}")
        if c_fail:
            print(f"  {'Commits failed':<{col}} {c_fail}")

    if op_fail or any(not r.get("commit_ok", True) for r in commit_results):
        print()
        print("  Failed hosts:")
        for r in results:
            issues = []
            if not r["op_ok"]:
                issues.append("operation")
            if r.get("commit_ok") is False:
                issues.append("commit")
            if issues:
                print(f"    - {r['host']}  ({', '.join(issues)})")

    print("=" * W)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Manage local admin accounts on PAN-OS firewalls or Panoramas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--firewall", metavar="FILE", help="File of firewall hosts")
    target.add_argument("--panorama", metavar="FILE", help="File of Panorama hosts")

    auth = parser.add_mutually_exclusive_group(required=False)
    auth.add_argument("--auth", metavar="USER[:PASS]",
                      help="Login as USER:PASS (password prompted if omitted; "
                           "or set PANOS_AUTH / PANOS_PASSWORD env vars)")
    auth.add_argument("--auth-api-key", metavar="KEY",
                      help="API key sent as X-PAN-KEY header (or set PANOS_API_KEY env var)")

    parser.add_argument("--operation", required=True,
                        choices=["list", "create", "update", "delete"])
    parser.add_argument("--username", help="Target username (required for create/update/delete)")
    parser.add_argument("--password", help="Password (required for create, optional for update)")
    parser.add_argument("--role", default="superuser",
                        help="Role: superuser, superreader, device-admin, device-admin-read-only, "
                             "or a custom admin role profile name (default: superuser)")
    parser.add_argument("--commit", action="store_true",
                        help="Partial-commit after each change using the login admin from --auth "
                             "(full commit when using --auth-api-key)")

    args = parser.parse_args()

    if args.operation in ("create", "update", "delete") and not args.username:
        parser.error(f"--username is required for {args.operation}")

    device_type = "panorama" if args.panorama else "firewall"
    host_file = args.panorama or args.firewall
    hosts = load_hosts(host_file)
    if not hosts:
        print("ERROR: no hosts found in file")
        sys.exit(1)

    # Resolve credentials — may prompt interactively
    headers, commit_admin = resolve_auth(args)

    # Resolve target user password if needed — may prompt interactively
    user_password = ""
    if args.operation in ("create", "update"):
        user_password = resolve_user_password(args)

    col = 22
    banner("PAN-OS User Manager")
    print(f"  {'Operation':<{col}} {args.operation.upper()}")
    print(f"  {'Device type':<{col}} {device_type}")
    print(f"  {'Hosts':<{col}} {len(hosts)}")
    if args.username:
        print(f"  {'Target user':<{col}} {args.username}")
    if args.operation in ("create", "update") and args.role:
        print(f"  {'Role':<{col}} {args.role}")
    if args.commit:
        scope = f"partial (admin={commit_admin})" if commit_admin else "full"
        print(f"  {'Commit':<{col}} {scope}")
    print("=" * W)

    results = []

    for i, host in enumerate(hosts, 1):
        section(host, i, len(hosts))
        op_ok = False
        commit_ok = None

        if args.operation == "list":
            op_ok = op_list(host, headers)
        elif args.operation == "create":
            op_ok = op_create(host, headers, args.username, user_password, args.role)
        elif args.operation == "update":
            op_ok = op_update(host, headers, args.username, user_password,
                              args.role if args.role != "superuser" else None)
        elif args.operation == "delete":
            op_ok = op_delete(host, headers, args.username)

        if args.commit and args.operation != "list":
            commit_ok = do_commit(host, headers, commit_admin)

        results.append({"host": host, "op_ok": op_ok, "commit_ok": commit_ok})

    if args.operation != "list":
        print_summary(results, args.operation)


if __name__ == "__main__":
    main()
