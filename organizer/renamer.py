"""需求 2：按规则批量改名。

规则用「下划线分段模板」描述：
    --from 学号_姓名_作业名  --to 作业名_学号
- --to 里的每个标签都必须出现在 --from 中；
- 文件名按下划线拆段后与 --from 对齐，段数不符的文件跳过；
- 目标名已存在时默认跳过（绝不覆盖），可选自动加 -1、-2 后缀；
- 执行前必须先预览并确认，执行后写入操作日志供撤销。
"""

import os

from . import oplog


def parse_rule(src_pattern, dst_pattern):
    """校验改名规则，返回 (源标签列表, 目标标签列表)。"""
    src_tokens = src_pattern.split("_")
    dst_tokens = dst_pattern.split("_")

    if len(set(src_tokens)) != len(src_tokens):
        raise ValueError("源规则里的标签不能重复，例如「学号_学号_作业名」不合法")
    for token in dst_tokens:
        if token not in src_tokens:
            raise ValueError(
                f"目标规则里的标签 {token!r} 不在源规则 {src_pattern!r} 中，"
                f"只能从源规则里挑选并重新排列")
    return src_tokens, dst_tokens


def _normalize_exts(exts):
    if not exts:
        return None
    return {str(e).lower().lstrip(".") for e in exts if str(e).lstrip(".")}


def plan_renames(folder, src_pattern, dst_pattern, exts=None, on_conflict="skip"):
    """生成改名计划（只计算，不实际改名）。

    每项：{"old": 原文件名, "new": 目标文件名（跳过时为 None）,
           "reason": 跳过原因（空串表示需要改名）}
    """
    src_tokens, dst_tokens = parse_rule(src_pattern, dst_pattern)
    exts = _normalize_exts(exts)

    plans = []
    # taken 记录本批次已占用的新名字，防止批内互相冲突
    taken = set()
    existing = set(os.listdir(folder))

    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        if name.startswith("."):
            continue
        stem, ext = os.path.splitext(name)
        if exts and ext.lower().lstrip(".") not in exts:
            continue

        parts = stem.split("_")
        if len(parts) != len(src_tokens):
            plans.append({
                "old": name,
                "new": None,
                "reason": f"文件名有 {len(parts)} 段，与规则需要的 "
                          f"{len(src_tokens)} 段不符，跳过",
            })
            continue

        mapping = dict(zip(src_tokens, parts))
        new_name = "_".join(mapping[token] for token in dst_tokens) + ext

        if new_name == name:
            plans.append({"old": name, "new": name, "reason": "命名已符合规则，跳过"})
            continue

        if new_name in existing or new_name in taken:
            if on_conflict == "suffix":
                stem2, ext2 = os.path.splitext(new_name)
                i = 1
                while f"{stem2}-{i}{ext2}" in existing or f"{stem2}-{i}{ext2}" in taken:
                    i += 1
                new_name = f"{stem2}-{i}{ext2}"
                plans.append({"old": name, "new": new_name, "reason": ""})
                taken.add(new_name)
            else:
                plans.append({
                    "old": name,
                    "new": None,
                    "reason": f"目标名 {new_name} 已存在，为避免覆盖跳过",
                })
            continue

        plans.append({"old": name, "new": new_name, "reason": ""})
        taken.add(new_name)

    return plans


def apply_renames(folder, plans):
    """执行改名计划（只执行 reason 为空的项），返回 (成功数, 改动记录)。"""
    changes = []
    done = 0
    for plan in plans:
        if plan["reason"] or not plan["new"] or plan["new"] == plan["old"]:
            continue
        src = os.path.join(folder, plan["old"])
        dst = os.path.join(folder, plan["new"])
        os.rename(src, dst)
        changes.append({"from": os.path.abspath(src), "to": os.path.abspath(dst)})
        done += 1

    if changes:
        oplog.record(folder, "rename", changes)
    return done, changes
