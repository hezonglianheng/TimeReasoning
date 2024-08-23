# 时间推理器程序1.1版(For Developer)

[For User](readme.md) | For Developer

秦宇航 <hezonglianheng@stu.pku.edu.cn>

## 程序文件结构及主要功能
### 文件
- [timescale.py](timescale.py): 包含决定时间轴尺度的类(class)
- [statement.py](statement.py): 包含表示对时间线上的事件及事件之间关系的陈述的类
- [timeline.py](timeline.py): 包含表示时间线的类，是推理的主要类
- [knowledge.py](knowledge.py): 包含表示时间常识库中常识和常识库本身的类
- [year_example.py](year_example.py): 作者写的一个时间推理器使用示例

### 目录
- [knowledge](knowledge): 包含不同时间轴尺度下的时间常识库文件, 程序利用文件将时间常识导入试题制作过程中
- [templates](templates): 包含不同时间轴尺度下的陈述模板, 程序利用文件将不同的事件及事件间关系转换为自然语言文本
- [outputs](outputs): 时间推理器使用示例生成的示例结果

## 开发指南