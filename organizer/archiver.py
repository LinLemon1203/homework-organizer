"""需求 3：按学期/类别把文件移动到子文件夹，生成整理报告，并支持撤销上次操作。

归档方式：
- category：按扩展名类别（文档 / 表格 / 演示 / 图片 / 压缩包 / 其他）；
- semester：按修改时间推断学期（9 月-次年 2 月为「YYYY秋」，3-8 月为「YYYY春」），
  也可用 --semester 手动指定统一的目标文件夹名。

每次归档都会：
1. 先预览、确认后才移动；
2. 生成 Markdown 整理报告（处理了多少个、跳过多少个、为什么跳过）；
3. 把移动记录写入操作日志，供 undo 撤销。
"""

import os
import shutil
from datetime import datetime

from . import oplog

REPORT_PREFIX = "整理报告"

CATEGORIES = {
    "文档": {".docx", ".doc", ".pdf", ".txt", ".md", ".rtf"},
    "表格": {".xlsx", ".xls", ".csv"},
    "演示": {".pptx", ".ppt"},
    "图片": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"},
    "压缩包": {".zip", ".rar", ".7z"},
}
EXT2CAT = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}


def category_of(ext):
    return EXT2CAT.get(ext.lower(), "其他")


def semester_of(dt):
    """根据日期推断学期：9-12 月与次年 1-2 月为秋季学期。"""
    if dt.month >= 9:
        return f"{dt.year}秋"
    if dt.month <= 2:
        return f"{dt.year - 1}秋"
    return f"{dt.year}春"


def normalize_exts(exts):
    if not exts:
        return None
    return {str(e).lower().lstrip(".") for e in exts if str(e).lstrip(".")}


def plan_archive(folder, by="category", semester=None, exts=None):
    """生成归档计划。

    每项：{"name": 文件名, "sub": 目标子文件夹名, "reason": 跳过原因}
    reason 为空表示可以移动。
    """
    exts = normalize_exts(exts)
    moves = []

    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        # 不动隐藏文件和之前生成的整理报告
        if name.startswith(".") or name.startswith(REPORT_PREFIX):
            continue
        stem, ext = os.path.splitext(name)
        if exts and ext.lower().lstrip(".") not in exts:
            continue

        if by == "semester":
            sub = semester or semester_of(datetime.fromtimestamp(os.path.getmtime(path)))
        else:
            sub = category_of(ext)

        target = os.path.join(folder, sub, name)
        if os.path.exists(target):
            moves.append({
                "name": name,
                "sub": sub,
                "reason": f"子文件夹 {sub}/ 中已存在同名文件，为避免覆盖跳过",
            })
            continue

        moves.append({"name": name, "sub": sub, "reason": ""})

    return moves


def apply_archive(folder, moves):
    """执行归档计划（只执行 reason 为空的项），返回 (成功数, 记录)。"""
    changes = []
    done = 0
    for move in moves:
        if move["reason"]:
            continue
        src = os.path.join(folder, move["name"])
        dst_dir = os.path.join(folder, move["sub"])
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, move["name"])
        shutil.move(src, dst)
        changes.append({"from": os.path.abspath(src), "to": os.path.abspath(dst)})
        done += 1

    if changes:
        oplog.record(folder, "archive", changes)
    return done, changes


def write_report(folder, by, moves, done):
    """生成 Markdown 整理报告，返回报告文件路径。"""
    skipped = [m for m in moves if m["reason"]]
    now = datetime.now()
    report_name = f"{REPORT_PREFIX}_{now.strftime('%Y%m%d_%H%M%S')}.md"
    report_path = os.path.join(folder, report_name)

    lines = [
        "# 整理报告",
        "",
        f"- 整理时间：{now.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 整理文件夹：{os.path.abspath(folder)}",
        f"- 归档方式：{'按学期' if by == 'semester' else '按类别'}",
        f"- 处理：{done} 个文件",
        f"- 跳过：{len(skipped)} 个文件",
        "",
        "## 明细",
        "",
        "| 文件 | 去向/结果 | 说明 |",
        "| ---- | ---- | ---- |",
    ]
    for m in moves:
        if m["reason"]:
            lines.append(f"| {m['name']} | 未移动 | {m['reason']} |")
        else:
            lines.append(f"| {m['name']} | {m['sub']}/ | 已归档 |")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return report_path


def undo_last(folder):
    """撤销最近一次未撤销的操作（改名或归档）。

    返回 {"op": 操作记录, "restored": 恢复数, "errors": 错误列表}，
    若没有可撤销的操作则返回 None。
    """
    op = oplog.last_active(folder)
    if not op:
        return None

    errors = []
    restored = 0
    # 逆序恢复，保证目录回退顺序正确
    for change in reversed(op["changes"]):
        src, dst = change["to"], change["from"]
        if not os.path.exists(src):
            errors.append(f"找不到 {src}，可能已被手动移动")
            continue
        if os.path.exists(dst):
            errors.append(f"目标位置已存在 {dst}，为避免覆盖跳过")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        restored += 1

    # 清理因撤销而变空的子文件夹
    for change in op["changes"]:
        parent = os.path.dirname(change["to"])
        if (os.path.abspath(parent) != os.path.abspath(folder)
                and os.path.isdir(parent) and not os.listdir(parent)):
            os.rmdir(parent)

    oplog.mark_undone(folder, op["id"])
    return {"op": op, "restored": restored, "errors": errors}
