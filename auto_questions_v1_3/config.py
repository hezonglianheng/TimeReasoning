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

# 文件配置
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"
TIME_UNIT_FILE = KNOWLEDGE_BASE_DIR / "time_unit.json5"
PROP_FILE = KNOWLEDGE_BASE_DIR / "proposition.json5"