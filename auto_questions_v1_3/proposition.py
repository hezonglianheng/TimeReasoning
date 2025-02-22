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
TEMPLATES = "templates" # 模板
REPLACE = re.compile(r"\{(\w*?):(\w*?)\}") # 替换模板中的内容

with config.PROP_FILE.open("r", encoding = "utf8") as f:
    PROP_DATA = json5.load(f)

class Proposition(element.Element):
    """自定义的时间命题
    """

    def translate(self, lang: str) -> str:
        """将时间命题翻译成指定语言的方法

        Args:
            lang (str): 语言

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
                pass
        # 首字母大写
        template = template[0].upper() + template[1:]
        return template

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