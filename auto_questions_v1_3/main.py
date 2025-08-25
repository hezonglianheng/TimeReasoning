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
# 05-02新增：引入level文件计算试题难度等级
import level
# 05-03新增：引入外部知识
import knowledge
import json5
import json
import random
import argparse
from pathlib import Path
from typing import Any, Literal
from itertools import combinations
from collections.abc import Iterator, Sequence
from functools import reduce
# 05-03新增：引入time库计算程序运行时间
import time
# 05-03新增：引入defaultdict类记录选项设置情况
from collections import defaultdict
# 05-04新增：引入statistics库以计算平均值
import statistics

# constants.
CONSTRAINT_MACHINE: constraint.ConstraintMachine
SCENARIO: scenario.Scenario
GRAPH: graph.ReasoningGraph
PROP_CHOOSE_MACHINE: machine.PropChooseMachine
OPTION_GENERATOR: machine.OptionGenerator
KNOWLEDGE_BASE: list[knowledge.Knowledge]
"""外部知识列表"""

# settings.json5文件中的键
GUIDE_KEY = "guide"
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
# 05-03新增：外部知识数量的键
KNOWLEDGE_NUM_KEY = "knowledge_num"
"""设置知识数量的键"""

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

# 05-03新增：外部知识的初始化
# 该函数会根据配置文件中的外部知识设置，初始化外部知识
def external_knowledge_setup(time_unit: str, num: int = 5):
    """初始化外部知识，更新程序的知识库

    Args:
        time_unit (str): 当前的时间单位，决定调用的知识库类型
        num (int, optional): 调用外部知识的数量，默认为5.
    """
    global KNOWLEDGE_BASE
    knowledge_list = knowledge.get_selected_knowledge(time_unit, num)
    KNOWLEDGE_BASE = knowledge_list

def graph_setup(events: Sequence[event.Event]):
    """初始化推理图

    Args:
        events (Sequence[event.Event]): 事件序列
    """
    global GRAPH, KNOWLEDGE_BASE, CONSTRAINT_MACHINE
    initial_props = CONSTRAINT_MACHINE.get_time_props(events)
    for t, e in CONSTRAINT_MACHINE.event_order:
        print(f"{e.translate(config.CHINESE)}: {t.translate(config.CHINESE)}")
    scenario_rules = SCENARIO.get_rules()
    knowledge_props = []
    knowledge_props.extend(SCENARIO.get_props()) # 将情景中的独有命题加入知识命题中
    # 05-03新增：将外部知识添加到推理图中
    if KNOWLEDGE_BASE:
        for k in KNOWLEDGE_BASE:
            knowledge_props.extend(k[knowledge.PROPOSITIONS])
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

def set_option_generator():
    """初始化选项生成器，设置选项可以随机的范围
    提问器会根据选项生成器随机生成选项
    """
    print("初始化选项生成器...")
    global OPTION_GENERATOR, GRAPH, CONSTRAINT_MACHINE
    OPTION_GENERATOR = machine.OptionGenerator(GRAPH)
    upper_time, lower_time = CONSTRAINT_MACHINE.upper_bound, CONSTRAINT_MACHINE.lower_bound
    time_range = represent.get_time_range(upper_time, lower_time)
    time_delta_range = represent.get_time_delta_range(upper_time, lower_time)
    # 05-03新增：记录已经查找过的项，避免重复设置
    # TODO：这个位置可以做进一步优化
    be_set_attrs = defaultdict(list)
    for p in GRAPH.get_reachable_props():
        for attr in p.main_attrs():
            if attr in be_set_attrs[p.kind]:
                continue
            be_set_attrs[p.kind].append(attr)
            if type(p[attr]) == represent.CustomTime:
                OPTION_GENERATOR.set_attr_range(p.kind, attr, time_range)
            elif type(p[attr]) == represent.CustomTimeDelta:
                OPTION_GENERATOR.set_attr_range(p.kind, attr, time_delta_range)
    print("选项生成器初始化完成")

def question_generate(prop_type: Literal["random", "deepest", "certain"] = "random", question_type: Literal["precise", "correct", "incorrect"] = "precise", **kwargs) -> dict[str, Any]:
    """根据指定的参数生成问题

    Args:
        prop_type (Literal[&quot;random&quot;, &quot;deepest&quot;, &quot;certain&quot;], optional): 需要选择的命题类型，默认为"random"。
        question_type (Literal[&quot;precise&quot;, &quot;correct&quot;, &quot;incorrect&quot;], optional): 问题类型，默认为"precise"。
        **kwargs: 其他参数
    
    Returns:
        dict[str, Any]: 问题信息字典，包含问题的命题、选项和答案等信息
    """
    global GRAPH, OPTION_GENERATOR
    ask_machine = machine.AskMachine(GRAPH, OPTION_GENERATOR)
    question_info = ask_machine.run(prop_type, question_type, **kwargs)
    return question_info

def get_level(chosen_props: list[prop.Proposition], question_info: dict[str, Any], question_type: Literal["precise", "correct", "incorrect"] = "precise", lang: str = "cn") -> int:
    """根据问题信息计算问题的难度等级
    
    Args:
        chosen_props (list[prop.Proposition]): 选择的命题列表
        question_info (dict[str, Any]): 问题信息字典，包含问题的命题、选项和答案等信息
        question_type (Literal[&quot;precise&quot;, &quot;correct&quot;, &quot;incorrect&quot;], optional): 问题类型，默认为"precise"。
        lang (str, optional): 语言，默认为"cn"。

    Returns:
        int: 问题的难度等级
    
    Raises:
        ValueError: 问题类型不合法
    """
    global SCENARIO, KNOWLEDGE_BASE
    step_len: int = question_info[machine.COT_LENGTH]
    statements_difficulty = max([p.get_prop_difficulty() for p in chosen_props])
    option_num = len(question_info[machine.ANSWER])
    # 05-03新增：增加知识的难度等级
    knowledge_diff = sum([k[knowledge.DIFFICULTY] for k in KNOWLEDGE_BASE]) if KNOWLEDGE_BASE else 0
    scenario_diff = SCENARIO.get_level()
    if question_type == "precise":
        question_prop: prop.Proposition = question_info[machine.QUESTION]
        question_difficulty = question_prop.get_question_difficulty(lang)
    elif question_type == "correct" or question_type == "incorrect":
        option_props: list[prop.Proposition] = list(question_info[machine.OPTIONS].values())
        question_difficulty = 2.0 * statistics.fmean([p.get_prop_difficulty() for p in option_props])
    else:
        raise ValueError(f"问题类型{question_type}不合法")
    curr_level = level.ask_level(step_len, statements_difficulty, option_num, knowledge_diff, scenario_diff, question_difficulty)
    return curr_level

def question_translate(guide: dict[str, str], chosen_props: list[prop.Proposition], question_info: dict[str, Any], question_type: Literal["precise", "correct", "incorrect"] = "precise") -> list[dict[str, Any]]:
    """将问题信息翻译成不同语言的版本\n
    该函数会根据配置文件中的语言设置，将问题信息翻译成不同语言的版本，并返回一个包含所有语言版本的列表

    Args:
        guide (dict[str, str]): 问题的引导语
        chosen_props (list[prop.Proposition]): 选择的命题列表
        question_info (dict[str, Any]): 问题信息字典，包含问题的命题、选项和答案等信息
        question_type (Literal[&quot;precise&quot;, &quot;correct&quot;, &quot;incorrect&quot;], optional): 问题类型，默认为"precise"。

    Returns:
        list[dict[str, Any]]: 包含所有语言版本的列表，每个元素是一个字典，包含问题、选项和答案等信息
    """
    global SCENARIO
    translate_result: list[dict[str, Any]] = []
    question: element.Element = question_info[machine.QUESTION]
    options: dict[str, element.Element] = question_info[machine.OPTIONS]
    for lang in config.LANG_CONFIG:
        # 06-19新增：翻译命题时的分隔字符串
        chosen_prop_translation = ';\n'.join([f"({i})" + p.translate(lang) for i, p in enumerate(chosen_props, start=1)])
        lang_guide = guide[lang]
        text = f"{lang_guide}:\n{chosen_prop_translation}"
        question_str = question.translate(lang, require='ask', ask_attr=question_info[machine.ASK_ATTR])
        options_str = {k: v.translate(lang) for k, v in options.items()}
        # 05-02新增：计算问题的难度等级
        question_level = get_level(chosen_props, question_info, question_type=question_type, lang=lang)
        # 05-02新增：获得问题相关的tags
        if question_type == "precise":
            question_tags: list[str] = [question.get_prop_tag()]
        elif question_type == "correct" or question_type == "incorrect":
            question_tags: list[str] = [p.get_prop_tag() for p in options.values()]
        else:
            raise ValueError(f"问题类型{question_type}不合法")
        str_info = {
            config.TEXT: text,
            config.QUESTION: question_str,
            config.OPTIONS: options_str,
            config.ANSWER: question_info[machine.ANSWER],
            config.LANGUAGE: lang,
            config.LEVEL: question_level, # 问题的难度等级
            config.QUESTION_INFO: {
                config.SCENE_TYPE: SCENARIO[scenario.TYPE_NAME], 
                config.STEP: question_info[machine.COT_LENGTH], # 推理步骤数
                config.STATEMENT_TYPE: [p.get_prop_tag() for p in chosen_props], # 命题类型
                config.QUESTION_TYPE: question_tags, # 问题类型
            }, 
        }
        translate_result.append(str_info)
    return translate_result

def main(dir_path: str, question_type: Literal["precise", "correct", "incorrect"] = "precise"):
    """程序主函数，负责读取配置文件，初始化各个模块，并执行自动出题的流程

    Args:
        dir_path (str): 配置文件所在目录路径。该目录下应包含settings.json5文件
        question_type (Literal[&quot;precise&quot;, &quot;correct&quot;, &quot;incorrect&quot;], optional): 问题类型，默认为"precise"。
    """
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
    prop.init() # 初始化命题库，加载命题文件。必须初始化！
    # 初始化场景
    scenario_setup(settings[SCENARIO_KEY])
    result = []
    for i in range(settings[RESET_TIME_KEY]):
        print(f"第{i+1}次重置")
        curr_events: tuple[event.Event] = next(event_iter)
        # 05-03新增：外部知识的初始化
        external_knowledge_setup(settings[CURR_UNIT_KEY], settings[KNOWLEDGE_NUM_KEY])
        graph_setup(curr_events)
        group_result = []
        for j in range(settings[ASK_TIME_KEY]):
            print(f"第{j+1}次提问")
            # 选择命题
            chosen_props = prop_choose()
            second_reason(chosen_props)
            set_option_generator()
            question_info = question_generate(question_type=question_type)
            translated_questions = question_translate(settings[GUIDE_KEY], chosen_props, question_info, question_type=question_type)
            # 将问题信息添加到结果列表中
            group_result.extend(translated_questions)
        # 将同一组问题给出group属性名称
        group_result = [n | {config.GROUP: f"{Path(dir_path).stem}-{question_type}-{i}"} for n in group_result]
        result.extend(group_result)
    # 将结果写入文件
    res_file: Path = Path(dir_path) / f"{question_type}.json"
    with open(res_file, "w", encoding="utf8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    print(f"问题生成完成，共生成{len(result)}道题目，已保存至{res_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="时间领域自动出题程序")
    parser.add_argument("dir_path", type=str, help="settings.json5文件所在目录路径")
    parser.add_argument("-q", "--question_type", type=str, help="问题类型", default="precise")
    args = parser.parse_args()
    time1 = time.time()
    main(args.dir_path, args.question_type)
    time2 = time.time()
    print(f"程序运行完成，用时{time2 - time1}s")