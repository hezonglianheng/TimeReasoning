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
模板库的编写请参照[templates\year.json5](templates\year.json5). 模板是用于将命题翻译为自然语言文本的, 包含占位符的未完成文本. 目前模板的可用字段如下:
|   字段   |                             含义                             |
|:--------:|:------------------------------------------------------------:|
|   verb   |                        事件的谓语动词                        |
|  object  |                          事件的宾语                          |
|   event  |            事件，述宾结构。event1、event2含义相同            |
|   time   | 瞬时事件发生的时间点。start、end表示持续事件的起始、终止时间 |
| duration |                 持续事件的时长，程序自动计算                 |
|   diff   |               两个瞬时事件时点的差值，自动计算               |
|   times  |             两个持续事件时长的倍数，程序自动计算             |
|   ratio  |             两个持续时间时长的比例关系，自动计算             |

### 编写知识库
知识库的编写参照[knowledge\year.json5](knowledge\year.json5). 格式为`{"年份数字": [对于年份的描述列表]}`.

### 利用程序编写Python脚本
编写可以生成试题的脚本可以参考[year_example.py](year_example.py). 主要分成如下步骤:
1. 按照以下代码依次导入所需依赖:
```python
import timescale # 时间尺度及相关对象
import timeline # 时间线及相关对象
import statements # 陈述及相关对象
```
2. 导入需要的其他Python依赖.
3. 创建时间线对象并设置试题的引导语.
4. 设置事件. 目前可以设置的事件主要有瞬时事件和持续事件, 其中可以为持续时间设置特殊的起始事件和终止事件(均为瞬时事件). 请注意, 在设置事件时, 需要将谓词和宾语拆开设置. 
5. 将事件添加到时间线中.
6. 通过时间线的`run()`方法执行推理过程获得试题.