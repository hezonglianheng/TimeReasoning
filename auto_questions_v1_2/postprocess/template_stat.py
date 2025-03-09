# encoding: utf8

"""统计模板库的相关情况"""

import json5
from pathlib import Path
import sys

# 将上级目录加入到sys.path中
sys.path.append(str(Path(__file__).resolve().parents[1].as_posix()))

# 模板文件路径集合
templates: list[str] = [
    r"timereasoning/templates/zh/year.json5",
    r"timereasoning/templates/zh/weekday.json5",
    r"timereasoning/templates/en/year.json5",
    r"timereasoning/templates/en/weekday.json5",
]

def template_stat(template_path: Path) -> int:
    """统计单个模板文件的模板数量

    Args:
        template_path (Path): 模板文件路径

    Returns:
        int: 模板数量
    """
    with template_path.open(encoding="utf8") as f:
        templates: dict[str, list[str]] = json5.load(f)
    return sum([len(templates[k]) for k in templates])

def main():
    paths: list[Path] = [Path(__file__).resolve().parents[1] / p for p in templates]
    total: int = sum([template_stat(p) for p in paths])
    print(f"模板总数：{total}")

if __name__ == "__main__":
    main()