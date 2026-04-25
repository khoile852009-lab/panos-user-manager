[![GitHub Release](https://img.shields.io/github/release/snell-evan-itt/panos-user-manager.svg?style=for-the-badge&color=blue)](https://github.com/snell-evan-itt/panos-user-manager/releases)
[![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/snell-evan-itt/panos-user-manager/total?style=for-the-badge)](https://github.com/snell-evan-itt/panos-user-manager/releases/latest)
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/snell.evan.itt)

# PAN-OS User Manager

A single-file CLI tool for managing local administrator accounts on Palo Alto Networks firewalls and Panorama via the XML API.

## Features

- **List** all local admin accounts and their roles
- **Create** a new admin account with a hashed password
- **Update** an existing account's password and/or role
- **Delete** an admin account
- **Commit** changes automatically with optional partial-commit scoped to your login admin
- Multi-host support — point it at a file of IP/hostname entries and run the same operation across all of them
- Credentials via CLI arg, environment variables, or interactive prompt — no cleartext passwords required

---

## Download

Pre-built binaries are available from the [Releases](../../releases) page.

| Platform | File |
|----------|------|
| Windows  | `panos_manage_user-windows.exe` |
| Linux    | `panos_manage_user-linux` |

---

## Running from source

Requires Python 3.8 or later. No `pip install` needed — the script uses only the standard library.

```bash
python panos_manage_user.py --help
```

---

## Host file format

Create a plain-text file with one hostname or IP address per line. Lines starting with `#` are treated as comments.

```
# Production firewalls
192.168.1.1
fw-edge-01.corp.internal
fw-edge-02.corp.internal

# Panorama
panorama.corp.internal
```

---

## Authentication

Authentication is resolved in this priority order for each credential:

1. CLI argument
2. Environment variable
3. Interactive prompt

### Option A — Username / password

```bash
# Full credentials in one arg (not recommended for shared terminals)
--auth admin:MyPassword

# Username only — password is prompted securely
--auth admin

# Environment variables — no CLI args needed
export PANOS_AUTH=admin           # or admin:MyPassword
export PANOS_PASSWORD=MyPassword  # used when PANOS_AUTH contains no ":"
```

### Option B — API key

```bash
--auth-api-key LUFRPT14...

# Or via environment variable
export PANOS_API_KEY=LUFRPT14...
```

### Target user password (create / update)

```bash
# Prompted if not supplied
--password NewP@ss1

# Or via environment variable
export PANOS_USER_PASSWORD=NewP@ss1
```

---

## Usage

### List all local admins

```bash
panos_manage_user --firewall hosts.txt --auth admin --operation list
```

### Create a new admin

```bash
panos_manage_user --firewall hosts.txt --auth admin --operation create \
  --username jsmith --role superuser
```

Role is `superuser` by default. Omitting `--password` triggers a secure prompt.

### Create and immediately commit

```bash
panos_manage_user --firewall hosts.txt --auth admin --operation create \
  --username jsmith --role device-admin --commit
```

The `--commit` flag issues a **partial commit** scoped to your login admin ID automatically. When using `--auth-api-key` (no admin identity), it falls back to a full commit.

### Update password and/or role

```bash
# Change password only
panos_manage_user --firewall hosts.txt --auth admin --operation update \
  --username jsmith --commit

# Change role only
panos_manage_user --firewall hosts.txt --auth admin --operation update \
  --username jsmith --role superreader --commit

# Change both
panos_manage_user --firewall hosts.txt --auth admin --operation update \
  --username jsmith --role device-admin --commit
```

### Delete an admin

```bash
panos_manage_user --firewall hosts.txt --auth admin --operation delete \
  --username jsmith --commit
```

### Panorama targets

Replace `--firewall` with `--panorama`:

```bash
panos_manage_user --panorama panorama_hosts.txt --auth admin --operation list
```

By default only **Panorama-level** admin accounts are shown. Use `--scope` to also include device-template admins.

```bash
# Panorama-level admins only (default)
panos_manage_user --panorama panorama_hosts.txt --auth admin --operation list --scope panorama

# All device-template admins only
panos_manage_user --panorama panorama_hosts.txt --auth admin --operation list --scope templates

# Panorama-level + all device-template admins
panos_manage_user --panorama panorama_hosts.txt --auth admin --operation list --scope all

# Target a single named template
panos_manage_user --panorama panorama_hosts.txt --auth admin --operation list \
  --scope templates --template MyTemplate
```

`--scope templates` and `--scope all` require `--panorama`. You can combine `--scope` with any operation (list, create, update, delete), and `--commit` works across all scopes.

### Export list results to Excel

Requires `openpyxl`:

```bash
pip install openpyxl
```

```bash
panos_manage_user --panorama panorama_hosts.txt --auth admin --operation list \
  --scope all --output-xlsx admins.xlsx
```

One worksheet is created per host, with columns for Scope, Username, and Role.

---

## Roles

| `--role` value | PAN-OS role |
|----------------|-------------|
| `superuser` (default) | Full read/write access |
| `superreader` | Full read-only access |
| `device-admin` | Device administrator |
| `device-admin-read-only` | Device administrator (read-only) |
| any other value | Treated as a custom admin role profile name |

---

## CLI reference

```
usage: panos_manage_user [--firewall FILE | --panorama FILE]
                         [--auth USER[:PASS] | --auth-api-key KEY]
                         --operation {list,create,update,delete}
                         [--username USERNAME]
                         [--password PASSWORD]
                         [--role ROLE]
                         [--commit]
                         [--scope {panorama,templates,all}]
                         [--template NAME]
                         [--output-xlsx FILE]

options:
  --firewall FILE        File of firewall hostnames/IPs (mutually exclusive with --panorama)
  --panorama FILE        File of Panorama hostnames/IPs (mutually exclusive with --firewall)

  --auth USER[:PASS]     Login credentials. If no ":" is present, password is prompted.
                         Env vars: PANOS_AUTH, PANOS_PASSWORD
  --auth-api-key KEY     API key sent as X-PAN-KEY header.
                         Env var: PANOS_API_KEY

  --operation            One of: list, create, update, delete
  --username USERNAME    Target admin account name (required for create/update/delete)
  --password PASSWORD    Password for the target account (required for create, optional for
                         update). Prompted for create if omitted. Env var: PANOS_USER_PASSWORD
  --role ROLE            Admin role (default for create: superuser). See Roles table above.
                         For update, omitting --role leaves the existing role unchanged.
  --commit               Commit candidate config after each change.

  --scope                panorama (default) | templates | all
                         Controls which admin stores are targeted on Panorama hosts.
                         templates/all require --panorama.
  --template NAME        Target a single device template by name. Used with
                         --scope templates|all; omit to target all templates.
  --output-xlsx FILE     Write list results to an xlsx file (one sheet per host).
                         Requires openpyxl (pip install openpyxl). Only valid with
                         --operation list.
```

---

## Example output

```
====================================================================
  PAN-OS User Manager
====================================================================
  Operation              CREATE
  Device type            firewall
  Hosts                  2
  Target user            jsmith
  Role                   superuser
  Commit                 partial (admin=admin)
====================================================================

[1/2] 192.168.1.1
--------------------------------------------------------------------
  ... Hashing password...
  [+] User 'jsmith' created  (role=superuser)
  ... Commit job 42 queued (partial (admin=admin)) — polling...
  [+] Commit job 42 succeeded

[2/2] 192.168.1.2
--------------------------------------------------------------------
  ... Hashing password...
  [+] User 'jsmith' created  (role=superuser)
  ... Commit job 43 queued (partial (admin=admin)) — polling...
  [+] Commit job 43 succeeded

====================================================================
  Summary
====================================================================
  Operation              CREATE
  Hosts processed        2
  Succeeded              2
  Commits OK             2
====================================================================
```

---

## Notes

- HTTPS is used for all API calls. SSL certificate verification is performed by Python's default trust store. If your management interface uses a self-signed cert, import it into your OS trust store or replace it with a signed cert before using this tool.
- Commit polling waits up to 3 minutes (60 × 3 s). If a commit job is still running after that, you will be warned to check the device manually.
- Partial commit requires the login admin to have pending changes. If there are no pending changes, the device returns no job ID and the tool reports that gracefully.

---
