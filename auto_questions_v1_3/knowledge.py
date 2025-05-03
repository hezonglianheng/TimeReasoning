# encoding: utf8
# date: 2025/05/02

"""用于调用外部知识的程序"""

import element
import represent
import config
import event
import proposition as prop
import json5
from tqdm import tqdm
import random
from typing import Any

# 外部知识的字段
PROPOSITIONS = "propositions" # 知识对应的命题
DIFFICULTY = "difficulty" # 知识的难度

class Knowledge(element.Element):
    """外部知识的定义和方法
    """
    def __init__(self, name: str = "", kind: str = "", **kwargs):
        super().__init__(name, kind, **kwargs)

    def translate(self, lang: str, require: str|None = None, **kwargs) -> str:
        """将外部知识翻译成指定语言的方法

        Args:
            lang (str): 语言
            require (str, optional): 翻译的要求，默认为None.
            **kwargs: 翻译的其他参数

        Returns:
            str: 翻译结果
        """
        # 有待后续实现
        return ""

    @classmethod
    def _build_event(cls, attr_dict: dict[str, Any]) -> event.Event:
        """构建外部知识中事件对象的方法

        Args:
            attr_dict (dict[str, Any]): 事件的元素字典

        Returns:
            event.Event: 事件对象
        """
        if (kind := attr_dict["kind"]) == event.TEMPORAL or kind == event.DURATION:
            subject = event.MyObject(**attr_dict[event.SUBJECT])
            event_dict = {
                "name": attr_dict["name"],
                "kind": attr_dict["kind"],
                event.SUBJECT: subject,
                event.PREDICATE: attr_dict[event.PREDICATE],
                event.OBJECT: attr_dict[event.OBJECT],
                event.TENSE: attr_dict[event.TENSE],
            }
            return event.Event(**event_dict)
        elif kind == event.DURATIVE:
            for member in [event.START_EVENT, event.END_EVENT, event.DURATION_EVENT]:
                child = cls._build_event(attr_dict[member])
                attr_dict[member] = child
            subject = event.MyObject(**attr_dict[event.SUBJECT])
            event_dict = {
                "name": attr_dict["name"],
                "kind": attr_dict["kind"],
                event.SUBJECT: subject,
                event.PREDICATE: attr_dict[event.PREDICATE],
                event.OBJECT: attr_dict[event.OBJECT],
                event.TENSE: attr_dict[event.TENSE],
                event.START_EVENT: attr_dict[event.START_EVENT],
                event.END_EVENT: attr_dict[event.END_EVENT],
                event.DURATION_EVENT: attr_dict[event.DURATION_EVENT],
            }
            return event.Event(**event_dict)
        elif kind == event.FREQUENT:
            pass
        else:
            raise ValueError(f"不支持的事件类型: {kind}")

    @classmethod
    def build(cls, attr_dict: dict[str, Any], know_type: str = "") -> "Knowledge":
        """构建外部知识的工厂方法

        Args:
            attr_dict (dict[str, Any]): 外部知识的元素字典
            know_type (str): 知识类型

        Raises:
            ValueError: 字段类型不合法

        Returns:
            Knowledge: 外部知识对象
        """
        difficulty: int = attr_dict.get("difficulty", 1)
        if know_type == "event":
            knowledge_props: list[prop.Proposition] = [] # 与知识相关的命题列表
            if (kind := attr_dict["kind"]) == event.TEMPORAL:
                mytime = represent.CustomTime(**attr_dict["time"])
                myevent = cls._build_event(attr_dict)
                myprop = prop.Proposition(**{prop.TIME: mytime, prop.EVENT: myevent, prop.KIND: kind})
                myprop[prop.ASKABLE] = False
                knowledge_props.append(myprop)
            elif kind == event.DURATIVE:
                start_time = represent.CustomTime(**attr_dict[event.START_EVENT]["time"])
                end_time = represent.CustomTime(**attr_dict[event.END_EVENT]["time"])
                duration_time = end_time - start_time
                myevent = cls._build_event(attr_dict)
                start_prop = prop.Proposition(**{prop.TIME: start_time, prop.EVENT: myevent[event.START_EVENT], prop.KIND: "temporal"})
                end_prop = prop.Proposition(**{prop.TIME: end_time, prop.EVENT: myevent[event.END_EVENT], prop.KIND: "temporal"})
                duration_prop = prop.Proposition(**{prop.TIME: duration_time, prop.EVENT: myevent[event.DURATION_EVENT], prop.KIND: "duration"})
                myprop = prop.Proposition(**{prop.TIME: start_time, prop.END_TIME: end_time, prop.DURATION: duration_time, prop.EVENT: myevent, prop.KIND: kind})
                for p in [start_prop, end_prop, duration_prop, myprop]:
                    p[prop.ASKABLE] = False
                    knowledge_props.append(p)
            elif kind == event.FREQUENT:
                pass
            else:
                raise ValueError(f"不支持的事件类型: {kind}")
            curr_knowledge = cls(kind=know_type, **{PROPOSITIONS: knowledge_props, DIFFICULTY: difficulty})
            return curr_knowledge
        else:
            raise ValueError(f"不支持的知识类型: {know_type}")

def get_selected_knowledge(time_unit: str, num: int = 5) -> list[Knowledge]:
    """获取指定时间单位的知识

    Args:
        time_unit (str): 时间单位
        num (int, optional): 知识数量. 默认为5.

    Returns:
        list[Knowledge]: 知识列表
    """
    assert num > 0, "需要获取的知识数量必须大于0"
    knowledge_file = config.EXTERNAL_KNOWLEDGE_DIR / f"{time_unit}.json5"
    if not knowledge_file.exists():
        print(f"知识文件 {knowledge_file} 不存在")
        return []
    with open(knowledge_file, "r", encoding="utf8") as f:
        knowledge_data: dict[str, list[dict]] = json5.load(f)
    knowledge_items: list[Knowledge] = []
    for key in knowledge_data:
        for d in tqdm(knowledge_data[key], desc=f"构建外部知识 {key}", unit="个"):
            knowledge_items.append(Knowledge.build(d, key))
    if len(knowledge_items) < num:
        print(f"知识数量不足，实际获取的数量为 {len(knowledge_items)}")
        return knowledge_items
    selected_knowledge = random.sample(knowledge_items, num)
    return selected_knowledge

if __name__ == "__main__":
    # 测试代码
    config.CURR_UNIT = "year"
    prop.init()
    knowledge = get_selected_knowledge("year", 5)
    print("测试完成")