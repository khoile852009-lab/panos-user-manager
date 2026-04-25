## Summary

<!-- What does this PR do and why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup
- [ ] Documentation
- [ ] CI / build

---

## Environment

| Field | Value |
| ----- | ----- |
| PAN-OS version | |
| Device type | `firewall` / `panorama` |
| Auth method | `--auth` / `--auth-api-key` |
| OS tested on | Windows / Linux |
| Binary or source | `.exe` / `panos_manage_user-linux` / `python panos_manage_user.py` |

---

## Operations tested

- [ ] `list`
- [ ] `create`
- [ ] `update` (password)
- [ ] `update` (role)
- [ ] `delete`
- [ ] `--commit` (partial)
- [ ] `--commit` (full / API key fallback)
- [ ] `--scope panorama`
- [ ] `--scope templates`
- [ ] `--scope all`
- [ ] `--output-xlsx`
- [ ] Multi-host file

---

## Reproduction / test commands

```bash
# Paste the exact commands run to verify the change
```

---

## Relevant output or error

```text
# Paste truncated tool output, error messages, or API responses
# Remove any real hostnames, usernames, or credentials before posting
```

---

## Troubleshooting notes

<!-- Did anything unexpected happen during testing? SSL errors, commit timeouts, partial-commit fallback to full, API rejections, PyInstaller import issues, etc. Note it here even if resolved. -->

---

## Checklist

- [ ] Tested on a real PAN-OS device or Panorama (not just dry-run / syntax check)
- [ ] Binary tested if PyInstaller packaging is affected (`--onefile` import errors, missing deps)
- [ ] No credentials, API keys, or hostnames left in code, comments, or test output
- [ ] `--help` output still accurate if CLI args changed
- [ ] README and example output updated if behavior or output changed
- [ ] CodeQL / security: no new taint flows from credential inputs to log/print sinks
