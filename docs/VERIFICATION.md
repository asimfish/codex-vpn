# What a pass actually proves

## 1. Proxy egress

The sampler makes two IPv4 HTTPS requests using `curl --proxy http://127.0.0.1:PORT --noproxy ''`: Cloudflare trace and ipify. It compares both returned IPs to the configured target and reads the selected native group through the loopback Mihomo controller.

This tests these explicit proxy requests. It does not test every application's ambient environment, IPv6 routes, UDP, DNS leakage, or behavior when the proxy stops.

## 2. Process environment

Linux reads the current user's `/proc/.../comm` and selected environment variables for `codex` processes. Proxy environment matches and obvious NO_PROXY bypass patterns are configuration hints. It does not dump complete environments or command lines. An environment hint is never the same as a connection observation.

## 3. Socket and proxy chain

Linux uses `ss -Htnp`; macOS uses `ps` process names and `lsof` established TCP endpoints. Source IP and port are matched to the controller's `/connections` metadata. IPv4-mapped IPv6 loopback addresses are normalized. Ambiguous socket ownership is not promoted to a single PID. Target domains are restricted to OpenAI/ChatGPT by default; `codex_hosts` can change that for sampling when you understand the deployment.

The emitted record contains PID, target host, attribution source and proxy chain. `socket-pid` is stronger than the controller's own process metadata (`core-process`). Either is limited by OS visibility, process names, controller metadata and observation timing.

## What this cannot guarantee

- Absence of evidence is not evidence of direct access or of safe access.
- It does not read OpenAI's server-side source-IP logs.
- It does not comprehensively enumerate or block direct connections outside Clash.
- A matching domain/chain does not prove a specific model request: telemetry and other service traffic can use the same domain.
- Without an exact PID, the record may belong to another task. Helpers, subprocesses and custom API providers may not be recognized.
- A long-lived task working over SSH may make its model requests on the local Mac, not the server it is editing.
- A 30-second dashboard sample can miss short-lived connections. `watch` narrows the interval to approximately 2 seconds; it is still sampling, not packet capture.
- No firewall, TUN enforcement, DNS policy, IPv6 block or kill switch is installed.
- A provider can change a node's exit between requests. Matching node names alone do not guarantee fixed IPs.

If your requirement is “no direct egress even during proxy failure,” use a separately designed OS/network isolation policy and validate failure modes. This project is an observation tool, not that policy.

## Recommended self-check

1. On the actual machine, obtain a fresh sample with matching dual-source IP and selected node.
2. Identify the target task's PID without publishing command arguments or tokens.
3. Start `watch --device ID --pid PID --seconds 120`.
4. Send a real request from that task.
5. Inspect the correct PID's domain, `source` and chain. Treat UNVERIFIED as unresolved.
6. Optionally run your own online-check service, keeping its HTTP-client evidence separate.
