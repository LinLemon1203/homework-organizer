"""需求 1：scan 子命令实现。"""

import argparse
import os
import sys

from . import scanner


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


def build_parser():
    parser = argparse.ArgumentParser(
        prog="hw-organizer",
        description="作业文件批量整理小工具：扫描列出 / 批量改名 / 归档报告与撤销",
    )
    sub = parser.add_subparsers(dest="command")

    sp = sub.add_parser("scan", help="扫描文件夹并列出所有文件")
    sp.add_argument("folder", help="要扫描的文件夹路径")
    sp.add_argument(
        "--ext",
        nargs="*",
        metavar="EXT",
        help="只看指定扩展名，如 --ext docx pdf",
    )
    sp.add_argument("--recursive", action="store_true", help="递归扫描子文件夹")
    sp.add_argument(
        "--sort",
        choices=["name", "size", "time"],
        default="name",
        help="排序方式（默认按文件名）",
    )
    sp.set_defaults(func=cmd_scan)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    import sys

    sys.exit(main())
