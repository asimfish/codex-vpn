# Security and privacy

## Boundaries

- Local controllers are contacted only at `127.0.0.1` with configured ports. This release uses GET requests only; there is no selector write, config reload, TUN/DNS update or subscription download.
- Controller credentials are read from a private file or named environment variable and are not put into subprocess arguments or snapshots.
- Samples contain public IPs, device labels and limited PID/domain/chain evidence. Treat them as private operational data. The snapshot is mode600; the user owns its directory.
- SSH hosts must be existing aliases; only a fixed Python sample runner is invoked with quoted validated parameters. Do not point the hub at untrusted remote hosts: their sample reports are not attested, and SSH configuration itself is trusted local input.
- The local dashboard is loopback-only, has no CORS permission, and rejects unrelated Host headers. It has no remote login system. Other processes under your user can still access it. Do not expose it publicly.
- Online checks use distinct device and administrator bearer tokens. The admin history is not public. Device IDs represent credential possession, not hardware identity.
- No Codex `auth.json`, model API token, account store or subscription secret is read or published.

## Known limitations

Connection sampling is best-effort and not a leak-prevention guarantee. Configured processes, auxiliary programs, namespace isolation and custom providers may defeat attribution. IPv4 probe success does not cover IPv6. The public Worker trusts direct Cloudflare ingress, not a generic proxy header on arbitrary infrastructure.

The macOS installer builds and ad-hoc signs locally. It removes only FinderInfo/ResourceFork metadata from its generated bundle if needed for signing, preserves quarantine attributes and does not request broad disk permissions. It creates a user login item only when requested by running the installer without `--no-autostart`. It never uses sudo.

Do not commit `config.json`, secret files, `.env`, deployment IDs or runtime samples. A fresh Git history is used for this public distribution; private operational history is not part of it.

## Reporting

Please report security issues through GitHub's private vulnerability reporting if enabled for this repository. Otherwise open an issue requesting a private contact without including exploitation details or credentials. Do not paste secrets into public issues. Rotate any exposed credential with its issuing service.
