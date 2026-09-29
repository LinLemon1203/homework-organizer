# hw-organizer 作业文件批量整理小工具

一个用于整理课程作业文件的命令行小工具（Python 标准库实现，零第三方依赖）。

## 项目规划

| 需求 | 内容 | 状态 |
| ---- | ---- | ---- |
| 需求 1 | 扫描指定文件夹，列出文件（大小、修改时间），支持按扩展名过滤 | ✅ 已实现（PR #1） |
| 需求 2 | 按规则批量改名，先预览确认再执行，重名冲突不覆盖 | 开发中（PR #2） |
| 需求 3 | 按学期/类别归档到子文件夹，生成整理报告，支持撤销上次操作 | 开发中（PR #3） |

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

## 运行测试

```bash
python -m unittest discover tests -v
```
