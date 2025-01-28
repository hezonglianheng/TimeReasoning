# encoding: utf8
# date: 2024-10-30
# author: Qin Yuhang
# 参数记录文件

# 精确/非精确命题选择权重
PRECISE_WEIGHT = 0.8
NOT_PRECISE_WEIGHT = 0.2

# punctuations.
SEMICOLON = "; "
COLON = ": "
ASK_POINT = "____"

# language settings.
# 当前支持的语言
CURR_LANGS = ["zh", "en",]

LANG_MODE = "zh"

ALL_WRONG = 'all_wrong'
BECAUSE = 'because'
ANOTHER = 'another'
SO = 'so'
ASK_RIGHT = "ask_right"
ASK_WRONG = "ask_wrong"
# 12-24新增：句号
FULL_STOP = "full_stop"
# 1-13新增：语言名称的转换
LANG_NAME = "lang_name"

LANG_CONFIG = {
    'zh': {
        ALL_WRONG: "以上选项均不符合题目要求",
        BECAUSE: ["因为", "由于", "既然", "根据",],
        ANOTHER: ["另外", "再者", "此外", "而且", "并且",],
        SO: ["所以", "因此", "故", "于是", "因而",],
        # 12-29修订：去除“请问”前缀
        # 1-13修订：与其他领域对齐试题表述
        # 1-17修订：修改试题表述，以____作为提问点
        ASK_RIGHT: f"以下选项中正确的是{ASK_POINT}",
        ASK_WRONG: f"以下选项中不正确的是{ASK_POINT}",
        FULL_STOP: "。",
        LANG_NAME: "cn", # 修改LANG_NAME为cn
    },
    'en': {
        ALL_WRONG: "None of the options above meet the requirements of the question",
        BECAUSE: ["because ", "since ", "as ", "according to ",],
        ANOTHER: ["furthermore ", "moreover ", "besides ", "and ",],
        SO: ["so ", "therefore ", "thus ", "hence ", "consequently ",],
        # 12-29修订：修改试题表述
        # ASK_RIGHT: "Which of the following is(are) correct?",
        ASK_RIGHT: f"Select the correct statement(s): {ASK_POINT}",
        # ASK_WRONG: "Which of the following is(are) incorrect?",
        ASK_WRONG: f"Select the incorrect statement(s): {ASK_POINT}",
        FULL_STOP: ".",
        LANG_NAME: "en",
    },
}

# 12-29新增：输出的字段名称
DOMAIN = "domain"
ID = "id"
LANGUAGE = "language"
TEXT = "text"
QUESTION = "question"
OPTIONS = "options"
ANSWER = "answer"
LEVEL = "level"
COT = "CoT"
QUES_INFO = "ques_info"
SCENE_TYPE = "scene_type"
ENTITY_NUM = "entity_num"
CHAIN_LENGTH = "chain_length"
KNOWLEDGE_NUM = "knowledge_num"
QUESTION_TYPE = "question_type"
RELATED_QUESTIONS = "related_questions"
# 1-18新增：增加statements_type字段
STATEMENTS_TYPE = "statements_type"

# functions.

def set_lang_mode(lang_mode: str):
    """设置语言模式

    Args:
        lang_mode (str): 语言模式. 目前支持"zh"或"en".
    """
    global LANG_MODE
    LANG_MODE = lang_mode