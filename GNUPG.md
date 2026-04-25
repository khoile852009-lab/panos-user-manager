# Release Signature Verification

All release binaries are signed with a GPG detached signature. Each release includes `.sig` files alongside the executables.

## Signing key

| Field       | Value                                          |
|-------------|------------------------------------------------|
| Key ID      | `8E234342277586D9`                             |
| Key type    | RSA 4096                                       |
| Owner       | Evan S                                         |
| Keyserver   | `keys.openpgp.org`                             |

## Import the public key

```bash
gpg --keyserver keys.openpgp.org --recv-keys 8E234342277586D9
```

## Verify a release binary

Download both the binary and its `.sig` file from the [Releases](../../releases) page, then run:

```bash
# Windows
gpg --verify panos_manage_user-windows.exe.sig panos_manage_user-windows.exe

# Linux
gpg --verify panos_manage_user-linux.sig panos_manage_user-linux
```

A good signature looks like:

```
gpg: Signature made ...
gpg:                using RSA key 8E234342277586D9
gpg: Good signature from "Evan S <...>"
```

A `BAD signature` result means the file has been tampered with and should not be used.
