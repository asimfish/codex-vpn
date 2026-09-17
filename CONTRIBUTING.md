# Contributing

Keep this project read-only by default. Discuss any new remote-control or credential boundary before implementation. Use synthetic addresses from the documentation ranges in fixtures. Never include real subscriptions, device addresses or captured private logs.

Run Python tests and Worker handler tests as documented in README; compile Swift for native changes. Add a regression test when changing status semantics, authentication or attribution. Declare live checks separately from mocks. Do not claim CI passed until its run completes.

Source layout:

- `codex_vpn/`: configuration, local/SSH sampling, evidence, CLI and loopback dashboard.
- `Sources/main.swift`: native macOS widget.
- `scripts/`: build/install, uninstall and bundled collector.
- `online/`: optional independent Cloudflare Worker + D1 service.
- `tests/`: deterministic unit and handler tests.

The compact exit dot and Codex marker intentionally represent different claims. Preserve the unknown/stale states; never make them green to reduce visual noise.
