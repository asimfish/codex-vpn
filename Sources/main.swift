import AppKit
import SwiftUI

struct Node: Decodable { let name: String; let delay: Double? }
struct Device: Decodable, Identifiable {
    let id, name, ip, secondary, node, status, codex: String
    let checked_at: Double
    let delay: Double?
    let proxy_port, controller_port: Int?
    let nodes: [Node]
}
struct Snapshot: Decodable { let at: Double; let target, node: String; let devices: [Device] }
final class Model: ObservableObject {
    @Published var snapshot: Snapshot?
    @Published var now = Date().timeIntervalSince1970 * 1000
    @Published var expanded = false
    var toggleCompact: (() -> Void)?
    @Published var opacity = UserDefaults.standard.object(forKey: "opacity") as? Double ?? 0.88
    @Published var scale = UserDefaults.standard.object(forKey: "scale") as? Double ?? 1.0
    var timer: Timer?
    init() {
        refresh()
        timer = Timer.scheduledTimer(withTimeInterval: 2, repeats: true) { [weak self] _ in self?.refresh() }
    }
    func refresh() {
        now = Date().timeIntervalSince1970 * 1000
        let url = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".local/share/codex-vpn/widget-snapshot.json")
        if let data = try? Data(contentsOf: url), let value = try? JSONDecoder().decode(Snapshot.self, from: data) { snapshot = value }
    }
    var countText: String {
        guard let s = snapshot else { return "0/0" }; let good = s.devices.filter { self.state($0) == "ok" }.count; return String(good)+"/"+String(s.devices.count)
    }
    func state(_ d: Device) -> String {
        if d.checked_at == 0 { return "unknown" }
        guard let s = snapshot, now-s.at < 100000, now-d.checked_at < 100000 else { return "stale" }
        return d.status
    }
}
func statusColor(_ status: String) -> Color { status == "ok" ? Color(red:0.7,green:0.92,blue:0.46) : status == "mismatch" ? .red : .orange }
func statusLabel(_ status: String) -> String { ["ok":"出口一致","mismatch":"IP/节点异常","stale":"数据过期","error":"检测失败","unknown":"等待数据"][status] ?? status }
func miniStatus(_ state: String, _ codex: String) -> String {
    if state == "stale" || state == "unknown" { return "pending" }
    if state == "mismatch" || state == "error" || codex == "路径不一致" { return "bad" }
    return state == "ok" && codex == "PID连接已观测" ? "good" : "pending"
}
func exitStatus(_ state: String) -> String {
    if state == "ok" { return "good" }
    if state == "mismatch" || state == "error" { return "bad" }
    return "pending"
}
struct MiniView: View {
    @ObservedObject var model: Model
    var body: some View {
        VStack(spacing:14) {
            Image(systemName:"network").foregroundStyle(.cyan).font(.system(size:12))
            if let s = model.snapshot {
                ForEach(s.devices) { d in
                    MiniDot(device:d,state:model.state(d),action:{ model.toggleCompact?() })
                }
            } else { Text("等待数据").font(.caption);Spacer() }
            Button { model.toggleCompact?() } label: { Image(systemName:"arrow.up.left.and.arrow.down.right").font(.system(size:11)) }.buttonStyle(.plain).help("展开完整窗口").accessibilityLabel("展开完整窗口")
        }
        .padding(.horizontal,7).padding(.vertical,12)
        .frame(maxWidth:.infinity,maxHeight:.infinity)
        .foregroundStyle(Color.black.opacity(0.78))
        .background(Color.white.opacity(model.opacity * 0.72))
        .clipShape(RoundedRectangle(cornerRadius:12))
        .overlay(RoundedRectangle(cornerRadius:12).stroke(.white.opacity(0.55)))
        .preferredColorScheme(.light)
    }
}
struct MiniDot: View {
    let device: Device
    let state: String
    let action: () -> Void
    var status: String { miniStatus(state,device.codex) }
    var color: Color { if exitStatus(state) == "good" { return .green }; if exitStatus(state) == "bad" { return .red }; return .orange }
    var codexColor: Color { if status == "good" { return .green }; if status == "bad" { return .red }; return .orange }
    var shortName: String { return String(device.id.prefix(6)) }
    var description: String { device.name + " · 圆点：" + statusLabel(state) + " · C：Codex " + device.codex + "；C黄色表示尚无充分连接证据，不是网速慢。点击展开" }
    var statusText: String { if status == "good" { return "绿色，已观测通过" }; if status == "bad" { return "红色，异常" }; return "黄色，待确认" }
    var body: some View {
        Button(action:action) {
            VStack(spacing:5) {
                Circle().fill(color).frame(width:11,height:11)
                HStack(spacing:2) {
                    Text(shortName).font(.system(size:8,weight:.medium)).lineLimit(1)
                    Text("C").font(.system(size:8,weight:.bold)).foregroundStyle(codexColor)
                }
            }.frame(maxWidth:.infinity)
        }.buttonStyle(.plain).help(description).accessibilityLabel(device.name + "：出口" + statusLabel(state) + "；Codex " + statusText)
    }
}
struct PanelView: View {
    @ObservedObject var model: Model
    var body: some View {
        VStack(alignment:.leading,spacing:12) {
            HStack {
                Image(systemName:"network").foregroundStyle(.cyan)
                Text("Codex VPN").font(.system(size:16*model.scale,weight:.semibold))
                Spacer()
                Button { model.toggleCompact?() } label: { Image(systemName:"arrow.down.right.and.arrow.up.left") }.help("折叠为每台机器一个点").accessibilityLabel("折叠为迷你状态条")
                Button { model.expanded.toggle() } label: { Image(systemName:model.expanded ? "chevron.up":"slider.horizontal.3") }.help("显示窗口设置与节点时延")
                Button { NSApp.windows.first?.orderOut(nil) } label: { Image(systemName:"minus") }.help("隐藏到菜单栏")
            }
            if let s = model.snapshot {
                HStack(alignment:.lastTextBaseline) {
                    Text(s.target).font(.system(size:22*model.scale,weight:.medium,design:.monospaced)).textSelection(.enabled)
                    Spacer()
                    Text(model.countText).foregroundStyle(.cyan)
                }
                Text("\(s.node) · 只读观测 · 每30秒采集").font(.system(size:11*model.scale)).foregroundStyle(.secondary)
                Divider()
                ScrollView {
                    VStack(spacing:10) {
                        ForEach(s.devices) { d in
                            VStack(alignment:.leading,spacing:5) {
                                HStack {
                                    Circle().fill(statusColor(model.state(d))).frame(width:7,height:7)
                                    Text(d.name).fontWeight(.semibold)
                                    Spacer()
                                    Text(d.delay.map { "\(Int($0)) ms" } ?? "—").monospacedDigit().foregroundStyle(.cyan)
                                }
                                HStack {
                                    Text(d.ip).font(.system(size:12*model.scale,design:.monospaced)).textSelection(.enabled)
                                    Spacer()
                                    Text(statusLabel(model.state(d))).foregroundStyle(statusColor(model.state(d)))
                                }.font(.system(size:11*model.scale))
                                Text("代理 :\(d.proxy_port.map(String.init) ?? "未登记") · 控制接口 :\(d.controller_port.map(String.init) ?? "未登记")").font(.system(size:10*model.scale)).foregroundStyle(.secondary)
                                Text("Codex · \(model.state(d)=="stale" ? "证据已过期" : d.codex)").font(.system(size:11*model.scale)).foregroundStyle(d.codex=="路径不一致" ? .red : .secondary)
                                if model.expanded {
                                    Text("ipify \(d.secondary) · \(d.node)").font(.system(size:10*model.scale,design:.monospaced)).foregroundStyle(.secondary)
                                    Text(d.nodes.map { "\($0.name.suffix(2)) \($0.delay.map { String(Int($0))+"ms" } ?? "—")" }.joined(separator:"  ·  ")).font(.system(size:10*model.scale)).foregroundStyle(.secondary).fixedSize(horizontal:false,vertical:true)
                                }
                            }.padding(10).background(.white.opacity(0.045),in:RoundedRectangle(cornerRadius:10))
                        }
                    }
                }
            } else {
                Text("正在读取设备真实样本…").foregroundStyle(.secondary)
                Text("首次采集可能需要30秒；失败不会显示通过。").font(.caption)
                Spacer()
            }
            if model.expanded {
                HStack { Text("透明度"); Slider(value:$model.opacity,in:0.35...1).onChange(of:model.opacity) { value in UserDefaults.standard.set(value,forKey:"opacity") } }.font(.caption)
                HStack { Text("文字缩放"); Slider(value:$model.scale,in:0.8...1.4).onChange(of:model.scale) { value in UserDefaults.standard.set(value,forKey:"scale") } }.font(.caption)
            }
            HStack {
                Button("完整监控台") { NSWorkspace.shared.open(URL(string:"http://127.0.0.1:8766/")!) }
                Spacer()
                Button("验证教程") { NSWorkspace.shared.open(Bundle.main.url(forResource:"Guide",withExtension:"html")!) }
            }.font(.system(size:11*model.scale))
            Text("出口通过 ≠ 每个 Codex 任务通过\n拖动标题或空白移动 · 拖动窗口边缘缩放").font(.system(size:10*model.scale)).foregroundStyle(.secondary)
        }
        .font(.system(size:13*model.scale))
        .padding(16)
        .frame(minWidth:330,minHeight:360)
        .background(Color(red:0.035,green:0.075,blue:0.12).opacity(model.opacity))
        .clipShape(RoundedRectangle(cornerRadius:16))
        .overlay(RoundedRectangle(cornerRadius:16).stroke(.white.opacity(0.15)))
        .preferredColorScheme(.dark)
    }
}
final class FloatingPanel: NSPanel { override var canBecomeKey: Bool { true }; override var canBecomeMain: Bool { false } }
final class Delegate: NSObject, NSApplicationDelegate {
    var panel: FloatingPanel!
    var status: NSStatusItem!
    var child: Process?
    var compact = false
    var fullSize = NSSize(width:390,height:690)
    let model = Model()
    func applicationDidFinishLaunching(_ notification: Notification) {
        if NSRunningApplication.runningApplications(withBundleIdentifier:"com.asimfish.codex-vpn").count > 1 { NSApp.terminate(nil); return }
        panel = FloatingPanel(contentRect:NSRect(x:100,y:100,width:390,height:690),styleMask:[.borderless,.resizable,.nonactivatingPanel],backing:.buffered,defer:false)
        panel.title="Codex VPN悬浮窗"; panel.level = .floating; panel.isOpaque=false; panel.backgroundColor = .clear
        panel.hasShadow=true; panel.isMovableByWindowBackground=true; panel.hidesOnDeactivate=false
        panel.collectionBehavior=[.canJoinAllSpaces,.fullScreenAuxiliary]
        panel.minSize=NSSize(width:330,height:360)
        panel.contentView=NSHostingView(rootView:PanelView(model:model))
        panel.setFrameAutosaveName("IPWatchFloatingPanel")
        if !panel.setFrameUsingName("IPWatchFloatingPanel"), let screen=NSScreen.main { panel.setFrameOrigin(NSPoint(x:screen.visibleFrame.maxX-410,y:screen.visibleFrame.maxY-720)) }
        status=NSStatusBar.system.statusItem(withLength:NSStatusItem.variableLength)
        status.button?.title="◉ IP"
        let menu=NSMenu()
        for (title,selector) in [("显示悬浮窗",#selector(show)),("迷你 / 完整窗口",#selector(toggleCompact)),("隐藏悬浮窗",#selector(hide)),("切换置顶",#selector(toggleLevel)),("退出",#selector(quit))] {
            let item=NSMenuItem(title:title,action:selector,keyEquivalent:"");item.target=self;menu.addItem(item)
        }
        status.menu=menu
        model.toggleCompact = { [weak self] in self?.toggleCompact() }
        if UserDefaults.standard.bool(forKey:"compact") { toggleCompact() }
        startCollector();panel.orderFrontRegardless()
    }
    func startCollector() {
        guard let script=Bundle.main.path(forResource:"collector",ofType:"py") else { return }
        let p=Process();p.executableURL=URL(fileURLWithPath:"/usr/bin/python3");p.arguments=[script]
        p.standardOutput=FileHandle.nullDevice;p.standardError=FileHandle.nullDevice
        do { try p.run();child=p } catch { }
    }
    @objc func show() { panel.orderFrontRegardless() }
    @objc func hide() { panel.orderOut(nil) }
    @objc func toggleLevel() { panel.level = panel.level == .floating ? .normal : .floating }
    @objc func toggleCompact() {
        let old = panel.frame
        if !compact {
            fullSize=old.size
            panel.saveFrame(usingName:"IPWatchFloatingPanel")
        }
        compact.toggle()
        UserDefaults.standard.set(compact,forKey:"compact")
        panel.setFrameAutosaveName(compact ? "IPWatchMiniPanel" : "IPWatchFloatingPanel")
        panel.minSize = compact ? NSSize(width:52,height:240) : NSSize(width:330,height:360)
        panel.contentView = compact ? NSHostingView(rootView:MiniView(model:model)) : NSHostingView(rootView:PanelView(model:model))
        let size = compact ? NSSize(width:58,height:max(270,CGFloat(model.snapshot?.devices.count ?? 5)*43+65)) : fullSize
        var origin=NSPoint(x:old.maxX-size.width,y:old.maxY-size.height)
        if let screen=panel.screen?.visibleFrame { origin.x=max(screen.minX,min(origin.x,screen.maxX-size.width));origin.y=max(screen.minY,min(origin.y,screen.maxY-size.height)) }
        panel.setFrame(NSRect(origin:origin,size:size),display:true)
        panel.orderFrontRegardless()
    }
    @objc func quit() { NSApp.terminate(nil) }
    func applicationWillTerminate(_ notification: Notification) { child?.terminate();panel.saveFrame(usingName:compact ? "IPWatchMiniPanel" : "IPWatchFloatingPanel") }
}
if CommandLine.arguments.contains("--self-test") {
    assert(miniStatus("ok","PID连接已观测")=="good")
    assert(miniStatus("ok","仅环境配置")=="pending")
    assert(miniStatus("stale","PID连接已观测")=="pending")
    assert(miniStatus("mismatch","PID连接已观测")=="bad")
    assert(miniStatus("ok","路径不一致")=="bad")
    assert(miniStatus("error","未验证")=="bad")
    assert(exitStatus("ok")=="good")
    assert(exitStatus("stale")=="pending")
    assert(exitStatus("mismatch")=="bad")
    assert(exitStatus("error")=="bad")
    print("MINI_STATUS_TESTS_PASS 10");exit(0)
}
let app=NSApplication.shared
let delegate=Delegate()
app.delegate=delegate
app.setActivationPolicy(.accessory)
app.run()
