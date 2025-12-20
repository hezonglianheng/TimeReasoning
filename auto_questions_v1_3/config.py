# encoding: utf8
# date: 2025-01-16

"""程序的全局配置文件
"""

from pathlib import Path

# 语言设置
CHINESE = "cn"
ENGLISH = "en"

SEPARATE = {
    CHINESE: "", # 中文不需要分隔符
    ENGLISH: " ", # 英文需要空格分隔
}

# Penn-Treebank 词性标签
PAST_TENSE = "VBD"
PAST_PARTICIPLE = "VBN"
PRESENT_PARTICIPLE = "VBG"
THIRD_PERSON_SINGULAR_PRESENT = "VBZ"
VERB_BASE_FORM = "VB"
PLURAL_NOUN = "NNS"

# 当前运行配置，需要在运行时修改
CURR_UNIT = "" # 当前时间单位
CURR_SETTING_DIR = "" # 当前试题配置文件夹

def set_curr_unit(unit: str):
    """设置当前时间单位

    Args:
        unit (str): 时间单位
    """
    global CURR_UNIT
    CURR_UNIT = unit

def set_curr_setting_dir(setting_dir: str):
    """设置当前试题配置文件夹

    Args:
        setting_dir (str): 试题配置文件夹
    """
    global CURR_SETTING_DIR
    CURR_SETTING_DIR = setting_dir

# 文件配置
# 知识库文件夹
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"
# 与时间单位相关的文件
TIME_UNIT_FILE = KNOWLEDGE_BASE_DIR / "time_unit.json5"
# 与不同时间单位的命题相关的文件夹和文件
PROP_DIR = KNOWLEDGE_BASE_DIR / "proposition"
# 时间命题基础信息文件
BASIC_INFO_FILE = PROP_DIR / "basic_info.json5"
"""时间命题基础信息文件"""
# 与推理规则相关的文件
RULE_FILE = KNOWLEDGE_BASE_DIR / "rule.json5"
# 与情景相关的文件夹
SCENARIO_DIR = KNOWLEDGE_BASE_DIR / "scenario"
# 试题配置文件名称
SETTINGS_FILE = "settings.json5"
# 推理节点的文本文件
GRAPH_FILE = "graph.txt"
# 从命题库中选择命题的规则
PROP_CHOOSE_RULE_FILE = KNOWLEDGE_BASE_DIR / "prop_choose_rule.json5"
# 05-02新增：外部知识库文件夹
EXTERNAL_KNOWLEDGE_DIR = KNOWLEDGE_BASE_DIR / "external_knowledge"
"""外部知识库文件夹"""

# 问题配置
ASK_POINT = "____" # 询问点
LANG_CONFIG = {
    "cn": {
        "ask_right": f"以下选项中正确的是{ASK_POINT}",
        "ask_wrong": f"以下选项中不正确的是{ASK_POINT}",
        "full_stop": "。",
        "comma": "，",
        "all_wrong": "以上选项均不符合题目要求",
        "because": ['因为', '由于',],
        "and": ['并且', '且', '同时',],
        "so": ['所以', '因此', '故',],
    }, 
    "en": {
        "ask_right": f"Select the correct statement(s): {ASK_POINT}",
        "ask_wrong": f"Select the incorrect statement(s): {ASK_POINT}",
        "full_stop": ".",
        "comma": ",",
        "all_wrong": "None of the options above meet the requirements of the question",
        "because": ['because', 'as', 'since',],
        "and": ['and', 'also', 'moreover',],
        "so": ['so', 'therefore', 'thus',],
    }, 
}

# 结果字典字段
TEXT = "text"
QUESTION = "question"
ANSWER = "answer"
OPTIONS = "options"
LANGUAGE = "language"
GROUP = "group" # 问题按照命题集合是否相同分组
# 05-02新增：问题中的一些其他统计信息
LEVEL = "level" # 问题的难度等级
"""问题的难度等级"""
QUESTION_INFO = "question_info" # 问题的其他信息
"""问题的其他信息"""
SCENE_TYPE = "scene_type"
"""情景类型"""
STEP = "step" # 推理步骤数
"""推理步骤数"""
STATEMENT_TYPE = "statement_type" # 命题类型
"""命题类型"""
QUESTION_TYPE = "question_type" # 问题类型
"""问题类型"""
# 12-19新增：推理链相关的信息
COT = "cot"
"""推理链"""