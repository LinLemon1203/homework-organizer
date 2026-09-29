"""需求 1：扫描指定文件夹，列出所有文件（大小、修改时间），支持按扩展名过滤。"""

import os
from datetime import datetime

# 扫描时默认忽略的系统文件
SKIP_NAMES = {"desktop.ini", "thumbs.db", ".ds_store"}

# 列表里文件名一列的最大显示宽度（按字符数）
NAME_COLUMN_WIDTH = 44


def human_size(size):
    """把字节数转成人类可读的大小，如 1023 B / 12.3 KB / 5.0 MB。"""
    size = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.1f} {unit}"
        size /= 1024


def normalize_exts(exts):
    """把 ['docx', '.PDF'] 之类的输入统一成 {'docx', 'pdf'}。"""
    if not exts:
        return None
    return {str(e).lower().lstrip(".") for e in exts if str(e).lstrip(".")}


def file_info(path):
    """读取单个文件的基本信息。"""
    st = os.stat(path)
    name = os.path.basename(path)
    return {
        "path": path,
        "name": name,
        "ext": os.path.splitext(name)[1].lower().lstrip("."),
        "size": st.st_size,
        "mtime": st.st_mtime,
    }


def _keep(name, exts):
    """判断文件是否应该出现在扫描结果里。"""
    if name.lower() in SKIP_NAMES or name.startswith("."):
        return False
    if exts is None:
        return True
    return os.path.splitext(name)[1].lower().lstrip(".") in exts


def scan_files(folder, exts=None, recursive=False):
    """扫描文件夹，返回文件信息列表。

    :param exts: 扩展名白名单（可迭代），None 表示不过滤
    :param recursive: 是否递归扫描子文件夹
    """
    exts = normalize_exts(exts)
    results = []

    if recursive:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in files:
                if _keep(name, exts):
                    results.append(file_info(os.path.join(root, name)))
    else:
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if os.path.isfile(path) and _keep(name, exts):
                results.append(file_info(path))

    return results


def sort_items(items, key="name"):
    """排序：name 按名称、size 按大小、time 按修改时间，均从大到小/按字母序。"""
    keys = {
        "name": lambda i: i["name"].lower(),
        "size": lambda i: i["size"],
        "time": lambda i: i["mtime"],
    }
    return sorted(items, key=keys.get(key, keys["name"]))


def _display_name(name, width=NAME_COLUMN_WIDTH):
    if len(name) <= width:
        return name.ljust(width)
    return name[: width - 3] + "..."


def print_table(items):
    """以表格形式打印文件列表。"""
    print(f"{'文件名':<{NAME_COLUMN_WIDTH}}{'大小':>10}  修改时间")
    print("-" * (NAME_COLUMN_WIDTH + 32))
    if not items:
        print("（没有符合条件的文件）")
        return
    for item in items:
        mtime = datetime.fromtimestamp(item["mtime"]).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{_display_name(item['name'])}{human_size(item['size']):>10}  {mtime}")
