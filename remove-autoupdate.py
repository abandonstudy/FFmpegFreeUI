# -*- coding: utf-8 -*-
import os
import re
import sys
def info(msg):
    try:
        print("[remove-autoupdate]", msg)
    except UnicodeEncodeError:
        print("[remove-autoupdate]", msg.encode("ascii", "replace").decode("ascii"))


def read_text(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(text)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    repo = os.path.join(root, "FFmpegFreeUI")
    if not os.path.isdir(repo):
        raise SystemExit("未找到 FFmpegFreeUI 源码目录: " + os.path.abspath(repo))

    # ---------- 1. 删除更新引擎源文件 ----------
    delete_files = [
        "功能/网络功能/网络功能_v6_软件本体更新.vb",
        "功能/网络功能/网络功能_v6_更新器更新.vb",
        "功能/网络功能/网络功能_v6_更新源.vb",
    ]
    for rel in delete_files:
        path = os.path.join(repo, rel)
        if os.path.isfile(path):
            os.remove(path)
            info("已删除: " + rel)
        else:
            info("不存在（跳过）: " + rel)

    # ---------- 2. 网络功能.vb：截断更新相关门面成员 ----------
    facade = os.path.join(repo, "功能/网络功能/网络功能.vb")
    text = read_text(facade)
    marker = "当前是否正在进行本体更新"
    idx = text.find(marker)
    if idx >= 0:
        line_start = text.rfind("\n", 0, idx) + 1
        text = text[:line_start].rstrip() + "\r\nEnd Class\r\n"
        write_text(facade, text)
        info("网络功能.vb：已移除更新相关门面成员")
    else:
        info("网络功能.vb：未找到更新门面成员（可能已被处理或上游已改）")

    # ---------- 3. FormMain_v6.vb：移除启动自动检查调用 ----------
    main_form = os.path.join(repo, "界面 v6 主页面/FormMain_v6.vb")
    text = read_text(main_form)
    pattern = re.compile(
        r"(?m)^[ \t]*(询问国内更新服务器|网络功能\.检查软件本体更新|网络功能\.检查更新器更新)\(\)[ \t]*\r?\n"
    )
    new_text, count = pattern.subn("", text)
    if count:
        write_text(main_form, new_text)
        info("FormMain_v6.vb：已移除 %d 行自动检查调用" % count)
    else:
        info("FormMain_v6.vb：未找到自动检查调用（可能已被处理或上游已改）")

    # ---------- 4. Form_v6_起始页面.vb：移除“强制检查更新”按钮处理 ----------
    start_page = os.path.join(repo, "界面 v6 主页面/Form_v6_起始页面.vb")
    text = read_text(start_page)
    removed = 0
    for name in ("MB_软件本体更新", "MB_更新器更新"):
        pat = re.compile(
            r"(?s)^[ \t]*Private Sub "
            + re.escape(name)
            + r"_Click\(sender As Object, e As EventArgs\).*?^[ \t]*End Sub[ \t]*\r?$",
            re.M,
        )
        new_text, n = pat.subn("", text, count=1)
        if n:
            text = new_text
            removed += n
    if removed:
        write_text(start_page, text)
        info("Form_v6_起始页面.vb：已移除 %d 个强制检查更新按钮处理" % removed)
    else:
        info("Form_v6_起始页面.vb：未找到更新按钮处理（可能已被处理或上游已改）")

    # ---------- 5. Form_v6_起始页面.Designer.vb：移除更新卡片 UI ----------
    designer = os.path.join(repo, "界面 v6 主页面/Form_v6_起始页面.Designer.vb")
    text = read_text(designer)
    kept = []
    dropped = 0
    for line in text.splitlines(keepends=True):
        s = line.strip()
        skip = (
            s.startswith("MB_软件本体更新")
            or s.startswith("MB_更新器更新")
            or s.startswith("Friend WithEvents MB_软件本体更新")
            or s.startswith("Friend WithEvents MB_更新器更新")
            or s.startswith("' MB_软件本体更新")
            or s.startswith("' MB_更新器更新")
            or s.startswith("HtmlColorLabel4")
            or s.startswith("' HtmlColorLabel4")
            or s.startswith("Friend WithEvents HtmlColorLabel4")
            or "Controls.Add(MB_软件本体更新)" in s
            or "Controls.Add(MB_更新器更新)" in s
            or "Controls.Add(HtmlColorLabel4)" in s
        )
        if skip:
            dropped += 1
            continue
        kept.append(line)
    if dropped:
        write_text(designer, "".join(kept))
        info("Form_v6_起始页面.Designer.vb：已移除 %d 行更新卡片 UI" % dropped)
    else:
        info("Form_v6_起始页面.Designer.vb：未找到更新卡片 UI（可能已被处理或上游已改）")

    # ---------- 6. ApplicationEvents.vb：移除“禁止从桌面/下载/缓存目录启动”检查 ----------
    app_events = os.path.join(repo, "ApplicationEvents.vb")
    text = read_text(app_events)
    pat = re.compile(
        r"(?s)^[ \t]*Dim 禁止启动位置说明 = 获取禁止启动位置说明\(System\.Windows\.Forms\.Application\.StartupPath\).*?^[ \t]*End If[ \t]*\r?$",
        re.M,
    )
    new_text, n = pat.subn("", text, count=1)
    if n:
        write_text(app_events, new_text)
        info("ApplicationEvents.vb：已移除启动位置限制检查（可任意目录运行）")
    else:
        info("ApplicationEvents.vb：未找到启动位置检查（可能已被处理或上游已改）")

    info("处理完成")


if __name__ == "__main__":
    main()
