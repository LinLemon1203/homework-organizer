"""命令行入口。

当前为项目骨架，scan / rename / archive / undo 四个子命令
将分别随需求 1、2、3 的 PR 逐步实现。
"""

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="hw-organizer",
        description="作业文件批量整理小工具：扫描列出 / 批量改名 / 归档报告与撤销",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["scan", "rename", "archive", "undo"],
        help="要执行的子命令",
    )
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    print(f"子命令 {args.command!r} 尚未实现，将在后续 PR 中提供。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
