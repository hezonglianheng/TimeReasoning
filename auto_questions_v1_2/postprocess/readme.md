# 后处理脚本

本目录下文件主要用于试题的后处理。下述的文件顺序也是调用文件的顺序。
- [merge.py](merge.py): 将多个试题文件合并为1个
- [filter.py](filter.py): 按照比例从备选试题中抽取试题
- [separate.py](separate.py): 将试题文件中不同文字的试题进行拆分
- [numbering.py](numbering.py): 给同一文件中的试题编号，给试题中的group字段编号，去除临时字段group
- [simplify.py](simplify.py): 生成简化版数据，从数据中抽取必要的字段用于测试
- [stat.py](stat.py): 生成试题的简要统计报告