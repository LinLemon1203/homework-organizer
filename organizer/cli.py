"""命令行入口。"""

import argparse
import os
import sys

from . import renamer, scanner


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
