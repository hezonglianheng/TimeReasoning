# encoding: utf8
# date: 2025-01-16

"""定义时间推理的事件元素，及与事件相关的事物元素
"""

import lemminflect
import element
import config
from typing import Any

# 常量
NAME_INFO = "name_info" # 名称信息
NAME = "name" # 名称
PRONOUN = "pronoun" # 代词
USE_PRONOUN = "use_pronoun" # 使用代词
PARENT_EVENT = "parent_event" # 父事件

# 事件的类型的枚举
TEMPORAL = "temporal" # 时点事件
DURATIVE = "durative" # 持续事件
FREQUENT = "frequent" # 频率事件
DURATION = "duration" # 时长事件，作为持续事件的子事件

# 持续事件的子事件类型枚举
START_EVENT = "start_event" # 开始事件
END_EVENT = "end_event" # 结束事件
DURATION_EVENT = "duration_event" # 持续时间事件

# 事件的基本元素
SUBJECT = "subject" # 主语
PREDICATE = "predicate" # 谓语
OBJECT = "object" # 宾语
# 事件的时态和数
TENSE = "tense" # 时态
PAST = "past" # 过去时
PRESENT = "present" # 现在时
FUTURE = "future" # 将来时
IS_THIRD_SINGULAR = "is_third_singular" # 是否第三人称单数

class MyObject(element.Element):
    """自定义的事件中的事物元素，一般作为事件的主语
    """

    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        self[USE_PRONOUN] = False # 是否使用代词

    def translate(self, lang: str, require: str|None = None, **kwargs) -> str:
        """将事物元素翻译成指定语言的方法

        Args:
            lang (str): 语言
            require (str, optional): 翻译的要求，默认为None.
            **kwargs: 翻译的其他参数

        Returns:
            str: 翻译结果
        """
        curr_info: dict = self[NAME_INFO][lang]
        if self[USE_PRONOUN]:
            return curr_info[PRONOUN]
        else:
            return curr_info[NAME]

class Event(element.Element):
    """自定义的事件元素
    """

    @classmethod
    def build(cls, attr_dict: dict[str, Any], myobject_list: list[MyObject]) -> list["Event"]:
        """构建事件元素的工厂方法
        
        Raises:
            ValueError: 不支持的事件类型

        Returns:
            list[Event]: 事件元素列表
        """
        kind: str = attr_dict["kind"]
        if kind == TEMPORAL:
            subject_name: str = attr_dict[SUBJECT]
            subject: MyObject = next(filter(lambda x: x.name == subject_name, myobject_list))
            attr_dict[SUBJECT] = subject
            return [cls(**attr_dict)]
        elif kind == DURATIVE:
            children_event: list["Event"] = []
            for member in [START_EVENT, END_EVENT, DURATION_EVENT]:
                child = cls.build(attr_dict[member], myobject_list)
                children_event.extend(child)
                attr_dict[member] = child[0]
            curr_event = cls(**attr_dict)
            return [curr_event]
        elif kind == FREQUENT:
            pass
        elif kind == DURATION:
            subject_name: str = attr_dict[SUBJECT]
            subject: MyObject = next(filter(lambda x: x.name == subject_name, myobject_list))
            attr_dict[SUBJECT] = subject
            return [cls(**attr_dict)]
        else:
            raise ValueError(f"不支持的事件类型: {kind}")

    def translate(self, lang: str, require: str|None = None, **kwargs) -> str:
        subject_element: MyObject = self[SUBJECT]
        subject: str = subject_element.translate(lang)
        predicate: str = lemminflect.getInflection(self[PREDICATE][lang], tag = config.VERB_BASE_FORM)[0]
        obj: str = self[OBJECT][lang]
        if lang == config.CHINESE:
            return config.SEPARATE[lang].join([subject, predicate, obj])
        elif lang == config.ENGLISH:
            if self[TENSE] == PAST:
                predicate = lemminflect.getInflection(predicate, tag = config.PAST_TENSE)[0]
            elif self[TENSE] == FUTURE:
                predicate = "will " + predicate
            else:
                if subject_element[IS_THIRD_SINGULAR]:
                    predicate = lemminflect.getInflection(predicate, tag = config.THIRD_PERSON_SINGULAR_PRESENT)[0]
            return config.SEPARATE[lang].join([subject, predicate, obj])
        else:
            raise ValueError(f"不支持的翻译语言: {lang}")

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
    subject = MyObject(name = "Tom", kind = "person", is_third_singular = True, name_info = nameinfo, )
    print(subject.translate(config.CHINESE))
    print(subject.translate(config.ENGLISH))
    subject[USE_PRONOUN] = True
    print(subject.translate(config.CHINESE))
    print(subject.translate(config.ENGLISH))
    subject[USE_PRONOUN] = False
    event = {"cn": "打", "en": "play"}
    obj = {"cn": "羽毛球", "en": "badminton"}
    e = Event(subject = subject, predicate = event, object = obj, tense = PRESENT)
    print(e.translate(config.CHINESE))
    print(e.translate(config.ENGLISH))