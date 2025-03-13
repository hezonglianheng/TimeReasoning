# encoding: utf8
# date: 2025-03-01

"""自动出题的主程序，包括自动出题的全部pipeline
"""

import element
import config
import event
import represent
import proposition as prop
import constraint
import graph
import scenario
import machine
import json5
import json
import random
import argparse
from pathlib import Path
from typing import Any
from itertools import combinations
from collections.abc import Iterator, Sequence
from functools import reduce

# constants.
CONSTRAINT_MACHINE: constraint.ConstraintMachine
SCENARIO: scenario.Scenario
GRAPH: graph.ReasoningGraph
PROP_CHOOSE_MACHINE: machine.PropChooseMachine

# settings.json5文件中的键
SCENARIO_KEY = "scenario"
RANDOM_SEED_KEY = "random_seed"
EVENT_NUM_KEY = "event_num"
OBJECT_KEY = "object"
EVENT_KEY = "event"
CONSTRAINT_KEY = "constraint"
RESET_TIME_KEY = "reset_time"
ASK_TIME_KEY = "ask_time"
TIME_RANGE_KEY = "time_range"
CURR_UNIT_KEY = "curr_unit" # 当前需要引用的单位

def set_random_seed(seed: int | float | None):
    """设置随机种子

    Args:
        seed (int | float | None): 随机种子
    """
    random.seed(seed)

def myobject_setup(myobject_attr_dicts: list[dict]) -> list[event.MyObject]:
    """初始化MyObject对象作为事件的主体

    Args:
        myobject_attr_dicts (list[dict]): MyObject对象的属性字典列表

    Returns:
        list[event.MyObject]: MyObject对象列表

    Raises:
        ValueError: MyObject对象的名称不唯一
    """
    myobject_list = [event.MyObject(**myobject_dict) for myobject_dict in myobject_attr_dicts]
    if element.name_is_unique(myobject_list):
        print(f"MyObject对象列表初始化完成，共{len(myobject_list)}个对象")
        return myobject_list
    else:
        raise ValueError("MyObject对象的名称不唯一")

def event_setup(event_attr_list: list[dict], myobject_list: list[event.MyObject], event_num: int | None) -> Iterator[tuple[event.Event]]:
    """初始化数个Event对象

    Args:
        event_attr_list (list[dict]): Event对象的属性字典列表
        myobject_list (list[event.MyObject]): MyObject对象列表
        event_num (int | None): 事件数量，若为None则为全部事件

    Raises:
        ValueError: Event对象的名称不唯一

    Yields:
        Iterator[tuple[event.Event]]: Event对象的迭代器
    """
    event_num = event_num if event_num is not None else len(event_attr_list)
    event_list: list[event.Event] = reduce(lambda x, y: x + y, [event.Event.build(event_attr, myobject_list) for event_attr in event_attr_list])
    if not element.name_is_unique(event_list):
        raise ValueError("Event对象的名称不唯一")
    print(f"Event对象列表初始化完成，共{len(event_list)}个对象")
    random.shuffle(event_list)
    for chosen_list in combinations(event_list, event_num):
        yield chosen_list

def event_name_setup(event_attr_list: list[dict]) -> list[str]:
    """初始化事件名称列表

    Args:
        event_attr_list (list[dict]): 事件属性字典列表

    Returns:
        list[str]: 事件名称列表
    """
    names: list[str] = []
    for event_attr in event_attr_list:
        if event_attr["kind"] == event.TEMPORAL:
            names.append(event_attr["name"])
        if event_attr["kind"] == event.DURATIVE:
            for member in [event.START_EVENT, event.END_EVENT]:
                names.append(event_attr[member]["name"])
    return names

def constraint_setup(event_names: list[str], constraint_rules: list[dict], upper_bound: dict, lower_bound: dict):
    """初始化约束机器

    Args:
        event_names (list[str]): 事件名称列表
        constraint_rules (list[dict]): 约束规则字典列表
        upper_bound (dict): 约束上界字典
        lower_bound (dict): 约束下界字典
    """
    global CONSTRAINT_MACHINE
    upper_bound = represent.CustomTime(**upper_bound)
    lower_bound = represent.CustomTime(**lower_bound)
    CONSTRAINT_MACHINE = constraint.ConstraintMachine(event_names, constraint_rules, upper_bound, lower_bound)

def scenario_setup(scenario_attr_dict: dict):
    """初始化情景

    Args:
        scenario_attr_dict (dict): 情景属性字典
    """
    global SCENARIO
    SCENARIO = scenario.Scenario(**scenario_attr_dict)

def graph_setup(events: Sequence[event.Event]):
    """初始化推理图

    Args:
        events (Sequence[event.Event]): 事件序列
    """
    global GRAPH
    initial_props = CONSTRAINT_MACHINE.get_time_props(events)
    for t, e in CONSTRAINT_MACHINE.event_order:
        print(f"{e.translate(config.CHINESE)}: {t.translate(config.CHINESE)}")
    scenario_rules = SCENARIO.get_rules()
    knowledge_props = SCENARIO.get_props()
    GRAPH = graph.ReasoningGraph(initial_props, scenario_rules, knowledge_props)
    GRAPH.reason()

def prop_choose() -> list[prop.Proposition]:
    """选择试题中作为已知信息出现的命题

    Returns:
        list[prop.Proposition]: 已知信息命题列表
    """
    global GRAPH, PROP_CHOOSE_MACHINE, CONSTRAINT_MACHINE
    events = [i[1] for i in CONSTRAINT_MACHINE.event_order]
    PROP_CHOOSE_MACHINE = machine.PropChooseMachine(events, GRAPH)
    return PROP_CHOOSE_MACHINE.run()

def second_reason(temp_props: list[prop.Proposition]):
    """执行二次推理，设置推理图上节点的层级

    Args:
        temp_props (list[prop.Proposition]): 二次推理的初始命题列表
    """
    global GRAPH
    GRAPH.set_node_layers(temp_props)

def main(dir_path: str):
    # 读取settings.json5文件
    setting_path = Path(dir_path) / config.SETTINGS_FILE
    # 设置当前配置文件夹
    config.set_curr_setting_dir(dir_path)
    with open(setting_path, "r", encoding="utf8") as f:
        settings: dict[str, Any] = json5.load(f)
    # 设置随机种子
    set_random_seed(settings[RANDOM_SEED_KEY])
    # 初始化MyObject对象
    myobject_list = myobject_setup(settings[OBJECT_KEY])
    # 初始化Event对象
    event_names = event_name_setup(settings[EVENT_KEY])
    event_iter = event_setup(settings[EVENT_KEY], myobject_list, settings[EVENT_NUM_KEY])
    # 初始化约束机器
    constraint_setup(event_names, settings[CONSTRAINT_KEY], settings[TIME_RANGE_KEY]["upper_bound"], settings[TIME_RANGE_KEY]["lower_bound"])
    # 命题文件的初始化
    config.set_curr_unit(settings[CURR_UNIT_KEY])
    prop.init()
    # 初始化场景
    scenario_setup(settings[SCENARIO_KEY])
    for i in range(settings[RESET_TIME_KEY]):
        print(f"第{i+1}次重置")
        curr_events: tuple[event.Event] = next(event_iter)
        graph_setup(curr_events)
        for j in range(settings[ASK_TIME_KEY]):
            print(f"第{j+1}次提问")
            # 选择命题
            chosen_props = prop_choose()
            second_reason(chosen_props)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="时间领域自动出题程序")
    parser.add_argument("dir_path", type=str, help="settings.json5文件所在目录路径")
    args = parser.parse_args()
    main(args.dir_path)