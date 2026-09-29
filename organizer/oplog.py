"""操作日志：把每次改名/归档记录成 JSONL，供 undo 撤销。"""

import json
import os
import uuid
from datetime import datetime

# 日志存放在被整理文件夹下的隐藏目录中
LOG_DIR = ".hw_organizer"


def log_path(folder):
    return os.path.join(folder, LOG_DIR, "operations.jsonl")


def record(folder, op_type, changes):
    """追加一条操作记录。

    :param changes: [{"from": 原路径, "to": 新路径}, ...]
    """
    entry = {
        "id": uuid.uuid4().hex[:8],
        "type": op_type,
        "time": datetime.now().isoformat(timespec="seconds"),
        "dir": os.path.abspath(folder),
        "changes": changes,
        "undone": False,
    }
    os.makedirs(os.path.dirname(log_path(folder)), exist_ok=True)
    with open(log_path(folder), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def load(folder):
    """读取全部操作记录（按时间先后）。"""
    path = log_path(folder)
    if not os.path.exists(path):
        return []
    ops = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                ops.append(json.loads(line))
    return ops


def last_active(folder):
    """最近一次尚未撤销的操作；没有则返回 None。"""
    active = [o for o in load(folder) if not o.get("undone")]
    return active[-1] if active else None


def mark_undone(folder, op_id):
    """把指定操作标记为已撤销。"""
    ops = load(folder)
    with open(log_path(folder), "w", encoding="utf-8") as f:
        for op in ops:
            if op["id"] == op_id:
                op["undone"] = True
            f.write(json.dumps(op, ensure_ascii=False) + "\n")
