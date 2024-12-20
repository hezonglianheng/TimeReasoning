# encoding: utf8
# date: 2024-10-30
# author: Qin Yuhang
# 参数记录文件

# 精确/非精确命题选择权重
PRECISE_WEIGHT = 0.8
NOT_PRECISE_WEIGHT = 0.2

# punctuations
SEMICOLON = "; "
COLON = ": "

# language settings
LANG_MODE = "zh"

ALL_WRONG = 'all_wrong'
BECAUSE = 'because'
ANOTHER = 'another'
SO = 'so'
ASK_RIGHT = "ask_right"
ASK_WRONG = "ask_wrong"

LANG_CONFIG = {
    'zh': {
        ALL_WRONG: "以上选项均不正确",
        BECAUSE: ["因为", "由于", "既然", "根据",],
        ANOTHER: ["另外", "再者", "此外", "而且", "并且",],
        SO: ["所以", "因此", "故", "于是", "因而",],
        ASK_RIGHT: "请问: 以下选项中正确的是____",
        ASK_WRONG: "请问: 以下选项中不正确的是____",
    },
    'en': {
        ALL_WRONG: "none of the above is correct",
        BECAUSE: ["because ", "since ", "as ", "according to ",],
        ANOTHER: ["furthermore ", "moreover ", "besides ", "and ",],
        SO: ["so ", "therefore ", "thus ", "hence ", "consequently ",],
        ASK_RIGHT: "Which of the following is(are) correct?",
        ASK_WRONG: "Which of the following is(are) incorrect?",
    },
}

# functions.

def set_lang_mode(lang_mode: str):
    """设置语言模式

    Args:
        lang_mode (str): 语言模式. 目前支持"zh"或"en".
    """
    global LANG_MODE
    LANG_MODE = lang_mode