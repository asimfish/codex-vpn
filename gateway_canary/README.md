# Session-scoped Codex turn-state canary

This is an isolated local relay for a dedicated test Codex session. It captures an upstream `X-Codex-Turn-State` only when its length matches a known normal shape (292 individual or 332 team), and in `inject` mode sends that captured value only for the same account label, model, egress profile and TTL.

Default mode is `off`. The relay binds `127.0.0.1:47891`; it never changes Clash 7890, system proxy, TUN, DNS or other Codex processes.

The implementation is deliberately memory-only: a captured state disappears on restart. It does not persist or log the complete header. Configure a dedicated upstream credential in the future; never copy a production `auth.json` or token into this directory.

`observe` captures metadata in memory; `inject` is a canary-only mode. A 312/356 length is a suspect signal, not proof of degraded reasoning. Validate with repeated same-account/same-model/same-input experiments before enabling inject.
