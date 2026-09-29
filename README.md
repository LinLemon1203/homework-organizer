# hw-organizer 作业文件批量整理小工具

一个用于整理课程作业文件的命令行小工具（Python 标准库实现，零第三方依赖）。

## 项目规划

| 需求 | 内容 | 状态 |
| ---- | ---- | ---- |
| 需求 1 | 扫描指定文件夹，列出文件（大小、修改时间），支持按扩展名过滤 | ✅ 已实现（PR #1） |
| 需求 2 | 按规则批量改名，先预览确认再执行，重名冲突不覆盖 | ✅ 已实现（PR #2） |
| 需求 3 | 按学期/类别归档到子文件夹，生成整理报告，支持撤销上次操作 | ✅ 已实现（PR #3） |

## 运行环境

- Python 3.8+（仅标准库，无需安装任何第三方包）

## 快速开始

### 需求 1：扫描与列出

```bash
# 扫描当前文件夹，列出所有文件（大小、修改时间）
python -m organizer scan "D:\课程作业"

# 只看 Word 和 PDF，按修改时间排序
python -m organizer scan "D:\课程作业" --ext docx pdf --sort time

# 递归扫描子文件夹，按大小排序
python -m organizer scan "D:\课程作业" --recursive --sort size
```

### 需求 2：批量改名

规则用「下划线分段模板」描述：`--from` 写原命名结构，`--to` 写目标结构，
标签名可以自定义，但 `--to` 里的标签必须都出现在 `--from` 中。

```bash
# 「学号_姓名_作业名.pdf」→「作业名_学号.pdf」
# 会先打印改名预览，输入 y 确认后才会真的改
python -m organizer rename "D:\课程作业" 学号_姓名_作业名 作业名_学号

# 只处理 PDF
python -m organizer rename "D:\课程作业" 学号_姓名_作业名 作业名_学号 --ext pdf

# 重名冲突时自动加 -1、-2 后缀（默认是跳过，绝不覆盖已有文件）
python -m organizer rename "D:\课程作业" 学号_姓名_作业名 作业名_学号 --on-conflict suffix
```

安全机制：

- **先预览后执行**：不确认（或按回车/N）就不会改动任何文件；
- **绝不覆盖**：目标名已存在时默认跳过并说明原因，可选 `--on-conflict suffix` 自动加后缀；
- **段数校验**：文件名段数与规则不符的文件会被跳过并说明原因；
- **可撤销**：每次改名都记入操作日志，供需求 3 的 `undo` 使用。

### 需求 3：归档、整理报告与撤销

```bash
# 按类别归档：文件移动到 文档/ 表格/ 演示/ 图片/ 压缩包/ 其他/ 子文件夹
python -m organizer archive "D:\课程作业"

# 按学期归档：根据文件修改时间自动推断（9月-次年2月为秋季学期）
python -m organizer archive "D:\课程作业" --by semester

# 按学期归档：手动指定统一的学期文件夹名
python -m organizer archive "D:\课程作业" --by semester --semester 2026秋

# 撤销最近一次操作（改名或归档均可）
python -m organizer undo "D:\课程作业"
```

归档同样遵循「先预览、确认后执行」，完成后会在文件夹里生成一份
`整理报告_时间.md`，内容包括：处理了多少个文件、跳过多少个、
每个被跳过文件的具体原因；所有移动都会记入操作日志。

## 撤销机制说明

工具把每次改名/归档记录在被整理文件夹下的 `.hw_organizer/operations.jsonl`
中（自动生成，请勿手动编辑）。`undo` 只撤销**最近一次**未撤销的操作，
文件会被移回原位置；因撤销而变空的子文件夹会被自动清理。

## 项目结构

```
homework-organizer/
├── README.md
├── organizer/
│   ├── __init__.py
│   ├── __main__.py      # python -m organizer 入口
│   ├── cli.py           # 命令行解析与各子命令
│   ├── scanner.py       # 需求1：扫描与列出
│   ├── renamer.py       # 需求2：批量改名
│   ├── archiver.py      # 需求3：归档、报告、撤销
│   └── oplog.py         # 操作日志（支撑撤销）
└── tests/
    ├── test_scanner.py
    ├── test_renamer.py
    └── test_archiver.py
```

## 分支与 PR 对应关系

每个需求在独立分支上开发，对应一个 Pull Request：

| 分支 | 需求 |
| ---- | ---- |
| `feat-1-scan-list` | 需求 1：扫描与列出 |
| `feat-2-batch-rename` | 需求 2：批量改名 |
| `feat-3-archive-report-undo` | 需求 3：归档、报告与撤销 |

## 运行测试

```bash
python -m unittest discover tests -v
```
