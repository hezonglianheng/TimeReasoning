# 时间推理器程序1.1版

For User | [For Developer](readme4developer.md)

秦宇航 <hezonglianheng@stu.pku.edu.cn>

## 目录
- [时间推理器程序1.1版](#时间推理器程序11版)
  - [目录](#目录)
  - [程序文件结构及主要功能](#程序文件结构及主要功能)
    - [文件](#文件)
    - [文件夹](#文件夹)
  - [使用指南](#使用指南)
    - [编写模板库](#编写模板库)
    - [编写知识库](#编写知识库)
    - [利用程序编写Python脚本](#利用程序编写python脚本)

## 程序文件结构及主要功能
### 文件
- [timescale.py](timescale.py): 包含决定时间轴尺度的类(class)
- [statement.py](statement.py): 包含表示对时间线上的事件及事件之间关系的陈述的类
- [timeline.py](timeline.py): 包含表示时间线的类，是推理的主要类
- [knowledge.py](knowledge.py): 包含表示时间常识库中常识和常识库本身的类
- [year_example.py](year_example.py): 作者写的一个时间推理器使用示例

### 文件夹
- [knowledge](knowledge): 包含不同时间轴尺度下的时间常识库文件, 程序利用文件将时间常识导入试题制作过程中
- [templates](templates): 包含不同时间轴尺度下的陈述模板, 程序利用文件将不同的事件及事件间关系转换为自然语言文本
- [outputs](outputs): 时间推理器使用示例生成的示例结果

## 使用指南

本程序使用的Python版本为3.12.1.请在目录下创建Python虚拟环境后执行`pip install -r requirements.txt`后使用此程序。

### 编写模板库

### 编写知识库

### 利用程序编写Python脚本
编写可以生成试题的脚本可以参考[year_example.py](year_example.py).
编写脚本主要分成如下步骤: