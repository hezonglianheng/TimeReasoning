# encoding: utf8
# date: 2025-02-22

"""时间命题的定义和方法
"""

import element
import config
import json5
import re
import random
from enum import StrEnum

# 常量
ASKABLE = "askable" # 是否可询问
PRECISE = "precise" # 是否精确
TEMPLATES = "templates" # 模板
REPLACE = re.compile(r"\{(\w*?):(\w*?)\}") # 替换模板中的内容
PROP_DATA: dict = {} # 时间命题的数据

# 命题中字段的枚举
class PropField(StrEnum):
    """时间命题中字段的枚举
    """
    TIME = "time" # 时间
    EVENT = "event" # 事件
    KIND = "kind" # 类型
    ENDTIME = "endtime" # 结束时间
    DURATION = "duration" # 持续时间

# 初始化时，读取时间命题的数据
def init():
    """初始化时间命题的数据
    """
    global PROP_DATA
    with config.PROP_FILE.open("r", encoding = "utf8") as f:
        PROP_DATA = json5.load(f)

class Proposition(element.Element):
    """自定义的时间命题
    """

    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        self[ASKABLE] = True # 设置命题是否可询问，默认为True
        self[PRECISE] = True # 设置命题是否为精确命题，默认为True

    def translate(self, lang: str, require: str|None = None, **kwargs) -> str:
        """将时间命题翻译成指定语言的方法

        Args:
            lang (str): 语言
            require (str, optional): 翻译的要求，默认为None.
            **kwargs: 翻译的其他参数

        Returns:
            str: 翻译结果
        """
        # 选择模板
        templates: list[str] = PROP_DATA["prop_kinds"][self.kind][TEMPLATES][lang]
        template = random.choice(templates)
        for match in REPLACE.finditer(template):
            curr_attr: str = match.group(1)
            curr_element: element.Element = self[curr_attr]
            strategy: str = match.group(2)
            # 根据策略选择翻译方法
            if strategy == "":
                template = template.replace(match.group(0), curr_element.translate(lang))
            else:
                template = template.replace(match.group(0), curr_element.translate(lang, require=strategy))
        # 首字母大写
        template = template[0].upper() + template[1:]
        return template

    def __eq__(self, other: "Proposition") -> bool:
        """判断两个时间命题是否相等的方法

        Args:
            other (Proposition): 另一个时间命题

        Returns:
            bool: 两个时间命题是否相等
        """
        if not type(self) == type(other):
            raise TypeError(f"元素{self}和元素{other}类型不同，无法比较")
        if self.kind != other.kind:
            return False
        for key in self.attrs:
            # 忽略ASKABLE和PRECISE属性
            if key == ASKABLE or key == PRECISE:
                continue
            if self[key] != other[key]:
                return False
        return True

if __name__ == "__main__":
    import event
    import represent
    nameinfo = {
        config.CHINESE: {
            event.NAME: "汤姆",
            event.PRONOUN: "他",
        },
        config.ENGLISH: {
            event.NAME: "Tom",
            event.PRONOUN: "he",
        }
    }
    subject = event.MyObject(name = "Tom", kind = "person", is_third_singular = True, name_info = nameinfo, )
    event0 = {"cn": "打", "en": "play"}
    obj = {"cn": "羽毛球", "en": "badminton"}
    e = event.Event(subject = subject, predicate = event0, object = obj, tense = event.PRESENT)
    time = represent.CustomTime(kind="week_day", day=1)
    prop = Proposition(time = time, event = e, kind = "temporal")
    print(prop.translate(config.CHINESE))
    print(prop.translate(config.ENGLISH))