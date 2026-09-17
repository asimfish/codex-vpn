# Deploy your own online IP checker / 部署在线出口检测

This optional component runs on **your Cloudflare account**, independently of the local dashboard. It uses an HTTPS Worker and D1 for 24-hour history. Cloudflare account limits/billing apply. No production service is bundled or implied by cloning.

需要你自己的 Cloudflare Workers + D1 账户。仓库不提供共享服务器或令牌。`localhost:8766` 是本地页面；下面部署后得到的 `workers.dev` 才是公网网址。

## 1. Prepare Wrangler

From the repository:

```bash
cd online
npx wrangler@4.92.0 login
npx wrangler@4.92.0 d1 create codex-vpn-checks
cp wrangler.example.json wrangler.json
```

Edit the ignored `wrangler.json`. Replace `REPLACE_WITH_YOUR_D1_DATABASE_ID` with the returned database ID. Replace `EXPECTED_IP` with your real expected exit IP. Choose an available Worker `name` if the example name is occupied. Never put secret values in this file.

`wrangler.json` is local and ignored by Git. It identifies **your** database and worker. The example's documentation IP will not pass a real test.

## 2. Create schema and credentials

```bash
npx wrangler@4.92.0 d1 execute codex-vpn-checks --remote --file schema.sql
npx wrangler@4.92.0 secret put DEVICE_TOKENS
npx wrangler@4.92.0 secret put ADMIN_TOKEN
```

At the `DEVICE_TOKENS` prompt paste a JSON object mapping configured device IDs to **different high-entropy random tokens**, for example the structure `{"local":"YOUR_RANDOM_TOKEN","gpu-a":"ANOTHER_RANDOM_TOKEN"}`. Do not use those literal example strings as credentials. Use a password manager to generate/store at least 32 random bytes per token.

At the `ADMIN_TOKEN` prompt use a separate random token. Device credentials only permit that device's `/check` requests; administrator credentials permit `/history`. Avoid entering tokens in shell command arguments, chat prompts, screenshots or tracked files.

设备 token 与管理员 token 不共用。设备名称来自凭据，不是硬件认证；持有该 token 的程序可以提交该设备名下的测试。

## 3. Deploy

```bash
npx wrangler@4.92.0 deploy --config wrangler.json
```

Copy the **actual URL printed by Wrangler**. Visit it to open the small history page. Enter the admin token and click “Load recent checks”. The page keeps the token in memory only, does not store it in localStorage, and does not show anyone else's records without authentication.

Re-run `deploy` after code/configuration changes. Database initialization uses `IF NOT EXISTS`; migrations for later releases must be reviewed separately. The UI has manual refresh; the local dashboard is a separate application.

## 4. Configure clients

Add this top-level field to each private `~/.config/codex-vpn/config.json`:

```json
"online": {
  "url": "https://YOUR-ACTUAL-WORKER.workers.dev/check",
  "token_env": "CODEX_VPN_CHECK_TOKEN"
}
```

Use the matching device ID. Put its token into `CODEX_VPN_CHECK_TOKEN` using your shell's secure input or secret manager; do not save a plaintext export in the repository. Bash example that does not put the token value into history:

```bash
read -r -s -p 'Device token: ' CODEX_VPN_CHECK_TOKEN
echo
export CODEX_VPN_CHECK_TOKEN
```

Then, from the repository root on the **target machine**:

```bash
python3 -m codex_vpn online-check --device local
python3 -m codex_vpn online-check --device local --explicit-proxy
```

Wait at least 3 seconds between requests for a device. Default follows the current Python HTTP client's proxy environment; explicit mode uses the configured Clash proxy. `MATCH` means this request's observed source matched the configured target. `MISMATCH` is not a pass. `UNVERIFIED` means the edge source/target was unavailable. Successful MATCH exits 0; other results/errors are nonzero.

**用 Codex 执行上述命令，只能证明它执行的 HTTP 客户端请求的出口，不自动证明模型请求的出口。** 后者仍要用 `watch --pid`，并理解连接观测的限制。

## 5. Acceptance checks on your deployment

- Unauthorized `/check` and `/history` return 401.
- Correct device token with an independent known exit returns the same source IP as an independent IP service.
- Wrong expected IP returns MISMATCH rather than green.
- Caller `X-Forwarded-For` and `X-Real-IP` must not alter the returned IP.
- Spoofing `CF-Connecting-IP` must be rejected or overwritten by Cloudflare ingress. Never put this worker behind a custom proxy that forwards untrusted client values as authoritative edge headers.
- Worker-to-worker placeholder addresses produce UNVERIFIED.
- Check history is private and old records are removed on subsequent checks after 24 hours. Cleanup is request-driven, not a scheduled deletion job.

The Worker trusts Cloudflare's own ingress `CF-Connecting-IP`, **not** arbitrary forwarded headers. Local Node mocks cannot prove the deployed platform's header behavior; run these checks on your own live deployment. This optional Worker template's handler tests run in CI; a fresh account deployment is a user-side acceptance step.

Reference: [Cloudflare request headers](https://developers.cloudflare.com/fundamentals/reference/http-headers/), [D1 commands](https://developers.cloudflare.com/d1/wrangler-commands/).

## Remove the optional service

Use the Cloudflare dashboard to remove only the Worker and D1 database you created after exporting any records you want to keep. The local uninstaller intentionally does not delete cloud resources or change billing.
