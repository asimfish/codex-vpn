# Release checks — v0.1.0

This record describes observed local checks, not a promise for every host or provider.

- Python 3.9.6 on Apple Silicon macOS: seven unittest cases passed, including fresh initialization in a temporary HOME, no-overwrite behavior, private config mode, installed remote runner import from outside the checkout, status expiry/mismatch, mocked sampler evidence separation, and loopback HTTP/Host rejection.
- Node 24: four Worker handler tests passed (device authentication, private history, no X-Forwarded-For trust, missing edge IP remains unverified). D1 is mocked in these tests.
- The generic public Python sampler was exercised against the developer's existing local proxy/controller without changing their configuration: both independent exit sources and selected node matched, with a PID-associated Codex connection observed. Addresses/secrets from that test are not included in this repository.
- Native Swift compiler: Apple Swift 6.3.3. Build-only app installation uses an isolated destination and does not register a login item or launch the app. Native status assertions cover ten outcomes. An isolated /tmp app bundle passed codesign --verify --deep --strict; no login item was installed for that test.
- Website and widget are independent collectors; simultaneous execution can duplicate probes.

Not verified for this public release: Intel Mac runtime, Windows, a fresh third-party Cloudflare account deployment, arbitrary SSH-agent configurations at login, and every terminal/proxy combination. The SSH wrapper uses a fixed installed runner and is tested for runner installation/import; it does not attest remote-host integrity.

The existing private deployment that motivated this project is not the public Worker template and is not evidence of this template being deployed. Run `docs/ONLINE.md` acceptance checks on your own service.

CI is configured in `.github/workflows/test.yml`; consult actual GitHub Actions results for the published commit. No mock or compile-only result is labeled as a full network or leak-prevention test.
