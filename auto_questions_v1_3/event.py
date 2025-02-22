# encoding: utf8
# date: 2025-01-16

"""定义时间推理的事件元素，及与事件相关的事物元素
"""

import lemminflect
import element
import config

# 常量
NAME_INFO = "name_info" # 名称信息
NAME = "name" # 名称
PRONOUN = "pronoun" # 代词
SUBJECT = "subject" # 主语
PREDICATE = "predicate" # 谓语
OBJECT = "object" # 宾语

class MyObject(element.Element):
    """自定义的事件中的事物元素，一般作为事件的主语
    """
    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        self.use_pronoun: bool = False # 是否使用代词

    def translate(self, lang: str) -> str:
        """将事物元素翻译成指定语言的方法

        Args:
            lang (str): 语言

        Returns:
            str: 翻译结果
        """
        curr_info: dict = self[NAME_INFO][lang]
        if self.use_pronoun:
            return curr_info[PRONOUN]
        else:
            return curr_info[NAME]

class Event(element.Element):
    pass

if __name__ == "__main__":
    # 测试
    nameinfo = {
        config.CHINESE: {
            NAME: "汤姆",
            PRONOUN: "他",
        },
        config.ENGLISH: {
            NAME: "Tom",
            PRONOUN: "he",
        }
    }
    obj = MyObject(name = "Tom", kind = "person", name_info = nameinfo)
    print(obj.translate(config.CHINESE))
    print(obj.translate(config.ENGLISH))
    obj.use_pronoun = True
    print(obj.translate(config.CHINESE))
    print(obj.translate(config.ENGLISH))