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
    """自定义的事件元素
    """

    def translate(self, lang) -> str:
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
    subject.use_pronoun = True
    print(subject.translate(config.CHINESE))
    print(subject.translate(config.ENGLISH))
    subject.use_pronoun = False
    event = {"cn": "打", "en": "play"}
    obj = {"cn": "羽毛球", "en": "badminton"}
    e = Event(subject = subject, predicate = event, object = obj, tense = PRESENT)
    print(e.translate(config.CHINESE))
    print(e.translate(config.ENGLISH))