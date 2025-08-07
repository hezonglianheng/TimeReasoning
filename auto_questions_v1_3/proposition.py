# encoding: utf8
# date: 2025-02-22

"""时间命题的定义和方法
"""

import element
import config
import json5
import re
import random

# 常量
ASKABLE = "askable" # 是否可询问
PRECISE = "precise" # 是否精确
NO_MAIN_ATTR = [ASKABLE, PRECISE, ] # 非主要属性
TEMPLATES = "templates" # 模板
PROP_KINDS = "prop_kinds" # 命题类型对应的键
REPLACE = re.compile(r"\{(\w*?):(\w*?)\}") # 替换模板中的内容
PROP_DATA: dict = {} # 时间命题的数据
# 05-02新增：与时间命题相关的通用基础信息
BASIC_INFO: dict = {}
"""与时间命题相关的通用基础信息"""

# 命题的字段
TIME = "time" # 时间
EVENT = "event" # 事件
EVENT1 = "event1" # 事件1
EVENT2 = "event2" # 事件2
KIND = "kind" # 类型
END_TIME = "endtime" # 结束时间
DURATION = "duration" # 持续时间
DIFF = "diff" # 时间差

# 初始化时，读取时间命题的数据
def init():
    """读取文件，初始化文件中命题的数据
    """
    global PROP_DATA, BASIC_INFO
    prop_file = config.PROP_DIR / f"{config.CURR_UNIT}.json5"
    with prop_file.open("r", encoding = "utf8") as f:
        PROP_DATA = json5.load(f)
    with config.BASIC_INFO_FILE.open("r", encoding = "utf8") as f:
        BASIC_INFO = json5.load(f)

def add_prop_data(data: dict[str, dict]) -> None:
    """添加自定义命题的数据

    Args:
        data (dict[str, dict]): 自定义命题的数据
    """
    global PROP_DATA
    assert PROP_KINDS in PROP_DATA, "时间命题的数据未初始化"
    PROP_DATA[PROP_KINDS].update(data)

class Proposition(element.Element):
    """自定义的命题
    """

    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        # 若kind不在PropKind中，则抛出异常
        if kind not in PROP_DATA[PROP_KINDS]:
            raise ValueError(f"时间命题的类型{kind}未定义")
        self[ASKABLE] = self.attrs.get(ASKABLE, True) # 设置命题是否可询问，默认为True
        self[PRECISE] = self.attrs.get(PRECISE, True) # 设置命题是否为精确命题，默认为True
        # 05-02新增：在内部记录命题被提问之后得到的文本
        self._translated_questions: dict[str, str] = {}
        """命题被提问之后得到的文本，键为语言，值为文本"""

    def translate(self, lang: str, require: str|None = None, **kwargs) -> str:
        """将时间命题翻译成指定语言的方法

        Args:
            lang (str): 语言
            require (str, optional): 翻译的要求，默认为None.可选值有：
                - "ask": 提问，此时需要提供ask_attr参数，表示提问的属性
            **kwargs: 翻译的其他参数

        Returns:
            str: 翻译结果
        """
        # 选择模板
        templates: list[str] = PROP_DATA[PROP_KINDS][self.kind][TEMPLATES][lang]
        template = random.choice(templates)
        # 如果翻译要求是ask(提问), 则需要从输入中查找提问属性
        if require == "ask":
            ask_attr = kwargs.get("ask_attr", None)
        else:
            ask_attr = None
        for match in REPLACE.finditer(template):
            curr_attr: str = match.group(1)
            curr_element: element.Element = self[curr_attr]
            strategy: str = match.group(2)
            if curr_attr == ask_attr:
                # 当当前属性就是提问属性时，提问点用____替换
                template = template.replace(match.group(0), config.ASK_POINT)
                continue
            # 根据策略选择翻译方法
            if strategy == "":
                template = template.replace(match.group(0), curr_element.translate(lang))
            else:
                template = template.replace(match.group(0), curr_element.translate(lang, require=strategy))
        # 首字母大写
        template = template[0].upper() + template[1:]
        if require == "ask":
            self._translated_questions[lang] = template
        return template

    def __eq__(self, other: "Proposition") -> bool:
        """判断两个命题是否相等的方法

        Args:
            other (Proposition): 另一个时间命题

        Returns:
            bool: 两个时间命题是否相等
        """
        if not type(self) == type(other):
            # 06-20新增：如果类型不同，则返回False
            return False
            # raise TypeError(f"元素{self}和元素{other}类型不同，无法比较")
        if self.kind != other.kind:
            return False
        for key in self.attrs:
            # 忽略ASKABLE、PRECISE属性
            if key in NO_MAIN_ATTR:
                continue
            if self[key] != other[key]:
                return False
        return True

    def main_attrs(self) -> list[str]:
        """返回命题的主要属性

        Returns:
            list[str]: 主要属性列表
        """
        return [key for key in self.attrs if key not in NO_MAIN_ATTR]
    
    # 06-20新增：返回命题的所有主要属性元素
    def all_attr_elements(self) -> list[element.Element]:
        """返回命题的所有属性元素

        Returns:
            list[element.Element]: 属性元素列表
        """
        return [self[key] for key in self.attrs if key not in NO_MAIN_ATTR]
    
    def ask_attr(self) -> str:
        """随机选取命题的一个主要属性，用于提问

        Returns:
            str: 选取的属性
        """
        return random.choice(self.main_attrs())
    
    def get_prop_difficulty(self) -> float:
        """获取命题的难度

        Returns:
            float: 命题的难度参数
        """
        return BASIC_INFO[PROP_KINDS][self.kind]["difficulty"]

    def get_question_difficulty(self, lang: str) -> float:
        """获取问题的难度

        Args:
            lang (str): 提问的语言

        Returns:
            float: 问题的难度参数
        """
        basic_diff = self.get_prop_difficulty()
        """
        lang_question = self._translated_questions.get(lang, None)
        if lang_question is None or config.ASK_POINT not in lang_question:
            # 如果没有提问，或者提问点不在问题中，则返回基本难度
            return basic_diff
        else:
            question_diff = basic_diff + 2 * (1 - (lang_question.index(config.ASK_POINT) + 2) / len(lang_question))
            return question_diff
        """
        # 05-03新增：直接返回命题的难度参数
        return basic_diff

    def get_prop_tag(self) -> str:
        """获取命题的标签

        Returns:
            str: 命题的标签
        """
        return BASIC_INFO[PROP_KINDS][self.kind]["typetag"]

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