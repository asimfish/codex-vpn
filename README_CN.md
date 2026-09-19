# Codex VPN：出口 IP 与 Codex 连接监控

**多台机器是否走同一出口，一眼看清；代理出口与 Codex 连接证据分开判断。**

[English](README.md) · [在线检测部署](docs/ONLINE.md) · [验证原理](docs/VERIFICATION.md) · [安全边界](SECURITY.md)

这是独立的开源监控工具。支持本地网页、macOS 白色半透明悬浮窗、竖条状态点、SSH 多设备采集，以及自己部署的 HTTPS 出口检测服务。Python 运行时只用标准库。

> **不是 VPN 服务。** 你需要自己准备可用的 Clash/Mihomo 和节点。本项目不提供订阅，不改写代理配置，不开关 TUN，不设置防火墙，也不保证代理断线时禁止直连。

![界面示意，非真实运行截图](docs/widget-preview.svg)

## 目录

- [功能与颜色](#功能与颜色)
- [安装前准备](#安装前准备)
- [单机从零运行](#单机从零运行)
- [安装 macOS 悬浮窗](#安装-macos-悬浮窗)
- [添加服务器](#添加服务器)
- [五设备可复现实例](#五设备可复现实例)
- [检查 Codex 的实际连接](#检查-codex-的实际连接)
- [部署自己的在线检测网址](#部署自己的在线检测网址)
- [升级与卸载](#升级与卸载)
- [常见问题](#常见问题)
- [测试与适用范围](#测试与适用范围)

## 功能与颜色

- 分别访问 Cloudflare 和 ipify，核对本机代理的 IPv4 出口。
- 核对原生手动选择组当前节点；显示代理端口、控制接口端口、HTTPS 请求耗时。
- 显示 Codex 进程代理环境与活动连接证据，支持限定 PID 观察。
- 悬浮窗可拖动、缩放、置顶、隐藏；透明度与文字大小可调，登录后启动。
- 折叠为白色半透明竖条，每台机器一个大圆点，名称旁有独立的 `C` 标记。
- 配置驱动的 SSH 多服务器采集，无个人服务器地址、订阅或私有站点依赖。
- 可选部署 Cloudflare Worker + D1，查看网站实际收到请求时的来源 IP。

**大圆点表示代理出口：** 绿＝新鲜双源检测与目标节点一致；红＝检测失败或不一致；黄＝未取得有效数据或过期。

**小 C 表示 Codex：** 绿＝观测到 PID 关联的目标节点连接且出口正常；黄＝仅环境配置、未捕获或证据过期；红＝检测异常或连接路径冲突。空闲任务没有连接时，C 可以是黄色，不能为了好看标成绿色。

本公开版 v0.1 提供只读监控。**不包含**订阅导入、统一切换节点、自动故障转移或作者私人站点的发布集成。候选节点未主动测速时显示不可用，不把旧健康缓存冒充实时延迟。显示的耗时是单次 HTTPS 请求，不是 ping，也不是模型首 token 时间。

## 安装前准备

每台机器需要：

1. Python **3.9+**、`curl`。
2. 正常运行的 Clash/Mihomo，知道本机代理端口、控制接口端口、控制密钥和**手动选择组**名称。
3. Linux 需要 `/proc` 与 `ss`（一般由 `iproute2` 提供）；Mac 使用系统的 `ps` 与 `lsof`。
4. 多机器监控需要已经配置好的 SSH 别名和密钥登录。工具不会关闭主机密钥验证。

Mac 悬浮窗另需 macOS **14+** 和 Xcode Command Line Tools；在线 Worker 另需 Node **22+**、Cloudflare Workers/D1 账户。

## 单机从零运行

```bash
mkdir -p ~/Code
cd ~/Code
git clone https://github.com/asimfish/codex-vpn.git
cd codex-vpn
python3 -m codex_vpn init
```

成功会显示 `Created private config`。配置位于 `~/.config/codex-vpn/config.json`，权限为600；已有文件不会被覆盖。**以下命令默认在仓库目录执行，不需要 pip 安装。**

用编辑器打开配置文件，示例：

```json
{
  "node": "你的美国节点名称",
  "expected_ip": "203.0.113.10",
  "nodes": ["你的美国节点名称"],
  "devices": [
    {
      "id": "local",
      "name": "我的Mac",
      "proxy_port": 7890,
      "controller_port": 9090,
      "selector_group": "PROXY",
      "controller_secret_file": "~/.config/codex-vpn/controller.secret"
    }
  ]
}
```

`203.0.113.10` 是文档示例地址，**必须替换成你的真实预期出口**。节点名与组名必须和 Clash 一致；端口也要按本机现状填写，不要照搬。

用本地编辑器创建 `~/.config/codex-vpn/controller.secret`，内容只填控制密钥，然后执行：

```bash
chmod 600 ~/.config/codex-vpn/config.json
chmod 600 ~/.config/codex-vpn/controller.secret
python3 -m codex_vpn sample --device local
```

如果控制器没有密钥，可省略 `controller_secret_file`。也可使用 `controller_secret_env` 指向一个环境变量，默认名为 `CODEX_VPN_CONTROLLER_SECRET`。**悬浮窗登录启动推荐密钥文件**，因为 LaunchAgent 不继承你在终端 export 的变量。

成功标准：输出 `status: "ok"`，`ip`、`secondary` 均为预期出口，`node` 正确。`sample` 是诊断命令，不管结果如何都可能正常退出，所以要看 `status` 字段。

启动网页：

```bash
python3 -m codex_vpn serve
```

打开 `http://127.0.0.1:8766`。约30秒采集一次、5秒刷新网页，超过100秒的数据不算新鲜。Ctrl-C 停止。端口占用时可以加 `--port 8877`。

可选安装 CLI 到虚拟环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --no-deps .
.venv/bin/codex-vpn --help
```

构建隔离可能下载 setuptools，但程序本身没有第三方 Python 运行时依赖。

## 安装 macOS 悬浮窗

先让 `sample` 检查通过，再执行：

```bash
xcrun swiftc --version
python3 scripts/install_macos.py
```

没有编译器时先运行 `xcode-select --install`，完成苹果安装窗口后重试。**不要 sudo。**

安装成功输出 `APP_INSTALLED`，应用位于 `~/Applications/CodexVPN.app`，菜单栏出现 **◉ IP**。程序本机编译、ad-hoc签名，没有苹果公证；仓库不提供来源不明的预编译二进制。

- 右上收缩按钮切换迷你竖条，点任意状态点或底部箭头展开。
- 拖动空白处移动，拖动边缘缩放。
- 设置中调整透明度与文字大小；菜单栏可隐藏、显示、置顶、退出。
- 登录当前用户后自动启动，不是在开机登录前运行，也不会在睡眠时采集。
- 退出后不会强制立刻重启，下次登录仍启动。
- 小窗独立采集，不依赖浏览器；“完整监控台”按钮需要默认8766端口的 `serve` 正在运行。
- 同时运行网页与小窗会有两套采集循环；通常选择一个持续运行，减少重复请求。

只编译、不启动、不改登录项：

```bash
python3 scripts/install_macos.py --dest .build/CodexVPN.app --no-autostart --no-start
```

## 添加服务器

在**每台被监控服务器**上先克隆仓库并初始化：

```bash
git clone https://github.com/asimfish/codex-vpn.git
cd codex-vpn
python3 -m codex_vpn init
```

修改该服务器自己的配置，将 ID 设为例如 `gpu-a`，填入它实际的端口、组名与密钥文件。目标节点和出口与监控端保持一致。先运行：

```bash
python3 -m codex_vpn sample --device gpu-a
python3 -m codex_vpn agent-install
python3 ~/.local/share/codex-vpn/agent.py sample --device gpu-a
```

`agent-install` 只复制 Python 文件，不改代理服务、不装后台服务。更新仓库后要重新执行它。

然后在**监控端 Mac**的 devices 数组中加入：

```json
{
  "id": "gpu-a",
  "name": "GPU服务器",
  "ssh": "gpu-a",
  "remote_home": "/home/alice",
  "proxy_port": 7890,
  "controller_port": 9090,
  "selector_group": "PROXY"
}
```

`gpu-a` 是你已配置的 SSH 别名，`/home/alice` 替换成远端用户目录。代理密钥留在远端，不需要放进监控端配置。

验收：

```bash
ssh -o BatchMode=yes gpu-a 'python3 ~/.local/share/codex-vpn/agent.py sample --device gpu-a'
python3 -m codex_vpn collect
```

SSH 不可用时显示未取得数据，不沿用旧绿色。增加设备不需要改源码，下轮采集会读取配置。

## 五设备可复现实例

如果你需要一次复制五设备拓扑（30109、mainskill、5090、4090 和 Mac）的端口与节点组模板，请参阅 [`examples/five-device-lab/README_CN.md`](examples/five-device-lab/README_CN.md)。模板只包含脱敏配置；真实 SSH 别名、出口 IP 和控制密钥必须在本地填写。

## 检查 Codex 的实际连接

在**实际运行目标 Codex 进程的那台设备**执行：

```bash
pgrep -x codex
ps -o pid,ppid,tty,comm -p 12345
python3 -m codex_vpn watch --device local --seconds 120 --pid 12345
```

`local` 和 `12345` 要替换成实际设备ID与进程号。在观察时间内，去对应 Codex 任务发送真实请求。工具本身不自动调用模型。

- `CODEX_PATH_OBSERVED`：捕获到相关连接；还需确认 PID、域名、`source: socket-pid` 和 `chains` 包含目标节点。
- `CODEX_UNVERIFIED`：证据不足，可能任务空闲、请求很短、权限不足或 PID 不对。不能算通过。
- `CODEX_PATH_MISMATCH`：观测到的连接路径不符。网络前置检查失败也会非零退出并输出诊断。

不限定 PID 时可能看到同机另一个任务的请求。即使同一 PID 访问 OpenAI 域名，也不自动意味着就是刚刚那条模型请求。详见 [验证说明](docs/VERIFICATION.md)。

## 部署自己的在线检测网址

按 [在线部署教程](docs/ONLINE.md) 创建你自己的 Cloudflare Worker 和 D1。仓库不含作者私有域名、后台账号或令牌。

配置好 `online.url` 与设备 token 环境变量后运行：

```bash
python3 -m codex_vpn online-check --device local
python3 -m codex_vpn online-check --device local --explicit-proxy
```

第一条沿用当前进程的代理环境；第二条主动指定配置中的 Clash 端口。两种结果不能混为一谈。在线检测仅证明该 HTTP 客户端请求，不替代 Codex 模型连接验证。

## 升级与卸载

保存你自己的源码修改后，在仓库中运行 `git pull --ff-only`。Mac 先在菜单退出旧应用，再运行安装器；远端重新运行 `agent-install`。

```bash
python3 scripts/uninstall_macos.py
```

卸载只移除默认应用与登录项，保留 `~/.config/codex-vpn/` 和 `~/.local/share/codex-vpn/` 中的配置与样本。自定义 `--dest` 的测试应用由你自己移除。

## 常见问题

**端口怎么填？** 代理端口用于 HTTP 请求，控制接口端口用于读取 Clash 状态；两者不是同一个概念。`127.0.0.1` 指正在执行命令的主机。

**绿点为什么还有黄 C？** 出口检测通过，但没有捕获足够的 Codex 活动连接证据。这不是网速报警。

**需要开 TUN 吗？** 不需要为了检测开 TUN。显式代理能验证自身出口；未使用代理的其他程序可能直连。TUN 自身也不能保证故障断网。

**为什么时延抖？** 单次 HTTPS 请求包括握手、线路与目标服务响应；不是模型延迟，不会因为波动自动换节点。

**为什么没有其他节点的延迟？** v0.1 不创建额外探测监听，也不主动测试备选节点；不可用值不会显示成0ms。

**SSH终端可用但悬浮窗不行？** GUI启动可能缺少终端中的 SSH agent 环境；配置已有密钥登录，先用 BatchMode 命令验收。不要关闭主机密钥验证。

**能确保绝不泄漏真实IP吗？** 不能。本项目没有防火墙、完整直连审计、IPv6阻断或代理故障断网机制。IPv4请求通过也不能证明IPv6没有绕过。

## 测试与适用范围

```bash
python3 -m unittest discover -s tests -v
node --test tests/worker.test.mjs
xcrun swiftc Sources/main.swift -o /tmp/CodexVPN -framework AppKit -framework SwiftUI
/tmp/CodexVPN --self-test
```

已验证范围以 [发布检查记录](docs/RELEASE_CHECKS.md) 为准。不要把模拟控制器测试当作真实网络验收；不要在 GitHub Actions 尚未完成时宣称 CI 已通过。Intel Mac、Windows 当前没有真机验证。

## 致谢与许可

悬浮窗形态与 README 组织参考 [asimfish/codex_monitor](https://github.com/asimfish/codex_monitor)。本项目与其独立，不负责额度查询、账户管理或登录 token 操作，也不隶属于 OpenAI 或 Clash/Mihomo。

MIT，见 [LICENSE](LICENSE)。
