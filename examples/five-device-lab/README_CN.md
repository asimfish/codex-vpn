# 五设备可复现实例

这个目录把一个五设备代理监控拓扑整理成了可复制的模板。它保留了端口、设备结构、五个美国节点和 `US-ONLY` 选择组的形状，但没有包含任何真实主机地址、订阅链接、控制密钥、网站 token、账号凭据或真实出口 IP。

## 拓扑

| 设备 | HTTP 代理端口 | Clash/Mihomo 控制端口 | SSH |
| --- | ---: | ---: | --- |
| 30109 | 7890 | 9090 | 需要填写自己的 SSH 别名 |
| mainskill | 7890 | 9097 | 需要填写自己的 SSH 别名 |
| 5090 | 7897 | 9097 | 需要填写自己的 SSH 别名 |
| liyufeng_4090 | 7890 | 9090 | 需要填写自己的 SSH 别名 |
| Mac | 7890 | 9097 | 本机 |

端口只是这个实例的配置样例。每台机器必须以实际监听端口为准；代理端口和控制端口不能混用。

源环境的覆盖范围记录如下，仅用于说明验证边界，不会由本项目自动修改：30109 与 mainskill 主要依赖显式 HTTP 代理；5090、liyufeng_4090 和 Mac 另有 TUN 覆盖。TUN 的用户、路由、DNS 和排除项因主机而异，复制此模板后必须逐台重新验证。

## 使用

1. 在监控端安装项目并初始化：

   ```bash
   git clone https://github.com/asimfish/codex-vpn.git
   cd codex-vpn
   python3 -m codex_vpn init
   cp examples/five-device-lab/config.example.json ~/.config/codex-vpn/config.json
   chmod 600 ~/.config/codex-vpn/config.json
   ```

2. 编辑 `~/.config/codex-vpn/config.json`：

   - 把 `203.0.113.10` 换成你自己的预期出口 IPv4；
   - 把 `REPLACE_WITH_SSH_ALIAS_*` 换成已经配置好密钥登录的 SSH 别名；
   - 把 `/home/REPLACE_WITH_USER` 换成每台远端机器上实际的用户目录；
   - 确认 `US-ONLY` 与五个节点名称和远端控制器完全一致。

3. 在每台远端机器上安装只读采集代理：

   ```bash
   git clone https://github.com/asimfish/codex-vpn.git
   cd codex-vpn
   python3 -m codex_vpn init
   python3 -m codex_vpn sample --device 30109
   python3 -m codex_vpn agent-install
   ```

   `agent-install` 不会修改 Clash/Mihomo、TUN、DNS、路由或系统代理。

4. 将控制器密钥只放在对应机器的环境变量或 `600` 权限文件中。不要把密钥放进 Git：

   ```bash
   export CODEX_VPN_CONTROLLER_SECRET_30109='在本机安全输入'
   ```

   更推荐使用本地密钥管理器或 `~/.config/codex-vpn/controller.secret`，并在配置中使用 `controller_secret_file`。不要把真实值贴进聊天、Issue 或仓库。

5. 先逐台验证，再启动监控：

   ```bash
   python3 -m codex_vpn sample --device mac
   ssh YOUR_ALIAS 'python3 ~/.local/share/codex-vpn/agent.py sample --device 30109'
   python3 -m codex_vpn serve
   ```

   只有 Cloudflare 与 ipify 都返回预期出口、控制器报告目标节点时，设备才会显示为通过。SSH 失败或样本过期会显示未知/黄色，不会沿用旧的绿色结果。

## 可选的会话级 canary

仓库中的 `gateway_canary/` 是独立的协议观察实验组件，默认 `off`，只绑定 `127.0.0.1:47891`。它不会接管机器代理，也不会修改 Clash、TUN 或 DNS。只有新建并明确指向该端口的测试会话才会经过它。真实上游 URL、测试凭据和状态头绝不能写进公开配置；先用 `observe` 多轮验证，再由操作者决定是否启用有限 TTL 的 `inject`。

## TUN 与这个模板的边界

这个模板只记录端口和只读监控参数，不会替你打开或关闭 TUN。显式代理和 TUN 的覆盖范围不同，必须在每台机器单独验证；不要因为五台机器的出口 IP 一致，就推断所有程序都经过代理。

## 公开仓库安全边界

下面这些内容永远不应放入公开仓库：

- 订阅 URL、节点密码、控制器密钥、网站 token、API key、OAuth/refresh token；
- 真实 SSH 主机地址、跳板机配置和私钥；
- `~/.codex/auth.json`、Whalent 凭据和完整请求头；
- 真实在线监控站的部署密钥或设备 token。

如果凭据曾经出现在日志、命令行或聊天记录中，应在对应服务中轮换，而不是只删除 Git 文件。
