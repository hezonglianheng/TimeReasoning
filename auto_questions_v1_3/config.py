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

def set_curr_unit(unit: str):
    """设置当前时间单位

    Args:
        unit (str): 时间单位
    """
    global CURR_UNIT
    CURR_UNIT = unit

# 文件配置
# 知识库文件夹
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"
# 与时间单位相关的文件
TIME_UNIT_FILE = KNOWLEDGE_BASE_DIR / "time_unit.json5"
# 与不同时间单位的命题相关的文件夹和文件
PROP_DIR = KNOWLEDGE_BASE_DIR / "proposition"
# 与推理规则相关的文件
RULE_FILE = KNOWLEDGE_BASE_DIR / "rule.json5"
# 与情景相关的文件夹
SCENARIO_DIR = KNOWLEDGE_BASE_DIR / "scenario"