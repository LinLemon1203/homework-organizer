"""命令行入口。"""

import argparse
import os
import sys

from . import archiver, renamer, scanner


def _confirm(prompt):
    """交互式确认，输入 y / yes 才继续。"""
    return input(f"{prompt} (y/N): ").strip().lower() in ("y", "yes")


def cmd_scan(args):
    if not os.path.isdir(args.folder):
        print(f"错误：文件夹不存在或不是文件夹：{args.folder}", file=sys.stderr)
        return 2

    items = scanner.scan_files(args.folder, exts=args.ext, recursive=args.recursive)
    items = scanner.sort_items(items, key=args.sort)
    scanner.print_table(items)

    total = sum(i["size"] for i in items)
    scope = "（含子文件夹）" if args.recursive else ""
    ext_tip = (
        f"，扩展名过滤：{', '.join(sorted(scanner.normalize_exts(args.ext) or []))}"
        if args.ext else ""
    )
    print(f"\n共 {len(items)} 个文件{scope}{ext_tip}，合计 {scanner.human_size(total)}。")
    return 0


def cmd_rename(args):
    if not os.path.isdir(args.folder):
        print(f"错误：文件夹不存在或不是文件夹：{args.folder}", file=sys.stderr)
        return 2

    try:
        plans = renamer.plan_renames(
            args.folder, args.src_pattern, args.dst_pattern,
            exts=args.ext, on_conflict=args.on_conflict,
        )
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    # 先打印将要改成什么（预览），不直接改
    print(f"改名预览（规则：{args.src_pattern} -> {args.dst_pattern}）：\n")
    pending = 0
    for plan in plans:
        if plan["new"] and plan["new"] != plan["old"] and not plan["reason"]:
            print(f"  {plan['old']}  ->  {plan['new']}")
            pending += 1
        else:
            print(f"  {plan['old']}  （跳过：{plan['reason']}）")

    if pending == 0:
        print("\n没有需要改名的文件。")
        return 0

    print(f"\n共 {pending} 个文件将被改名。")
    if not args.yes and not _confirm("确认执行改名？"):
        print("已取消，未做任何修改。")
        return 0

    actionable = [
        p for p in plans
        if p["new"] and p["new"] != p["old"] and not p["reason"]
    ]
    done, _ = renamer.apply_renames(args.folder, actionable)
    print(f"完成：已改名 {done} 个文件（操作已记入日志，可通过 undo 撤销）。")
    return 0


def cmd_archive(args):
    if not os.path.isdir(args.folder):
        print(f"错误：文件夹不存在或不是文件夹：{args.folder}", file=sys.stderr)
        return 2
    if args.by == "semester" and args.semester:
        by_label = f"按学期（统一放入 {args.semester}/）"
    elif args.by == "semester":
        by_label = "按学期（根据文件修改时间自动推断）"
    else:
        by_label = "按类别（文档/表格/演示/图片/压缩包/其他）"

    moves = archiver.plan_archive(
        args.folder, by=args.by, semester=args.semester, exts=args.ext)

    print(f"归档预览（{by_label}）：\n")
    pending = 0
    for m in moves:
        if m["reason"]:
            print(f"  {m['name']}  （跳过：{m['reason']}）")
        else:
            print(f"  {m['name']}  ->  {m['sub']}/{m['name']}")
            pending += 1

    if pending == 0:
        print("\n没有需要归档的文件。")
        return 0

    print(f"\n共 {pending} 个文件将被移动到子文件夹。")
    if not args.yes and not _confirm("确认执行归档？"):
        print("已取消，未做任何修改。")
        return 0

    actionable = [m for m in moves if not m["reason"]]
    done, _ = archiver.apply_archive(args.folder, actionable)
    report_path = archiver.write_report(args.folder, args.by, moves, done)
    print(f"完成：已归档 {done} 个文件，跳过 {len(moves) - done} 个。")
    print(f"整理报告已生成：{report_path}")
    print("操作已记入日志，可通过 undo 撤销。")
    return 0


def cmd_undo(args):
    if not os.path.isdir(args.folder):
        print(f"错误：文件夹不存在或不是文件夹：{args.folder}", file=sys.stderr)
        return 2

    result = archiver.undo_last(args.folder)
    if result is None:
        print("没有可撤销的操作。")
        return 0

    op = result["op"]
    print(f"正在撤销最近一次操作：{op['type']}（{op['time']}，共 "
          f"{len(op['changes'])} 条改动）")
    print(f"已恢复 {result['restored']} 个文件。")
    for err in result["errors"]:
        print(f"警告：{err}")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="hw-organizer",
        description="作业文件批量整理小工具：扫描列出 / 批量改名 / 归档报告与撤销",
    )
    sub = parser.add_subparsers(dest="command")

    sp = sub.add_parser("scan", help="扫描文件夹并列出所有文件")
    sp.add_argument("folder", help="要扫描的文件夹路径")
    sp.add_argument("--ext", nargs="*", metavar="EXT",
                    help="只看指定扩展名，如 --ext docx pdf")
    sp.add_argument("--recursive", action="store_true", help="递归扫描子文件夹")
    sp.add_argument("--sort", choices=["name", "size", "time"], default="name",
                    help="排序方式（默认按文件名）")
    sp.set_defaults(func=cmd_scan)

    rp = sub.add_parser("rename", help="按规则批量改名（先预览，确认后执行）")
    rp.add_argument("folder", help="要整理的文件夹路径")
    rp.add_argument("src_pattern", help="原命名规则（下划线分段），如：学号_姓名_作业名")
    rp.add_argument("dst_pattern", help="目标命名规则，如：作业名_学号")
    rp.add_argument("--ext", nargs="*", metavar="EXT",
                    help="只处理指定扩展名，如 --ext pdf")
    rp.add_argument("--on-conflict", choices=["skip", "suffix"], default="skip",
                    help="重名冲突处理：skip=跳过（默认，绝不覆盖）；suffix=自动加 -1 后缀")
    rp.add_argument("--yes", action="store_true", help="跳过交互确认（脚本自动化用）")
    rp.set_defaults(func=cmd_rename)

    ap = sub.add_parser("archive", help="按学期/类别归档到子文件夹，并生成整理报告")
    ap.add_argument("folder", help="要整理的文件夹路径")
    ap.add_argument("--by", choices=["category", "semester"], default="category",
                    help="归档方式：category=按文件类别（默认）；semester=按学期")
    ap.add_argument("--semester", metavar="NAME",
                    help="手动指定学期文件夹名（配合 --by semester），如 2026秋")
    ap.add_argument("--ext", nargs="*", metavar="EXT",
                    help="只归档指定扩展名，如 --ext pdf")
    ap.add_argument("--yes", action="store_true", help="跳过交互确认（脚本自动化用）")
    ap.set_defaults(func=cmd_archive)

    up = sub.add_parser("undo", help="撤销最近一次改名或归档操作")
    up.add_argument("folder", help="被整理的文件夹路径")
    up.set_defaults(func=cmd_undo)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
