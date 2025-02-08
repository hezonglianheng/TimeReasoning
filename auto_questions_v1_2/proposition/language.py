# encoding: utf8
# date: 2024-12-01
# 用于生成语言平行的试题

import sys
import abc
from pathlib import Path
from typing import Union, Any
from copy import deepcopy

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.config
from proposition.config import LANG_CONFIG, ASK_RIGHT, ASK_WRONG, ALL_WRONG
from proposition.scene import Scene, LEVEL, INIT_NUM, KNOWLEDGE_NUM, CHAIN_LENGTH, SCENE_TYPE
from proposition import prop, machines
# 12-24新增：引入句号
from proposition.config import FULL_STOP

class LangParallelScene(metaclass=abc.ABCMeta):
    def __init__(self, original_scene: Scene) -> None:
        self.original_scene = original_scene # 原始场景
        self.lang_temps: dict[str, dict[str, list[str]]] = {} # 语言对应模板
        self.lang_guides: dict[str, str] = {} # 语言对应引导语
        # 12-14新增：记录提问信息的中间变量
        self._ask_info: dict[str, Any] = {}
        # 12-14新增：记录提问的命题的typetag
        self._type_tags: list[str] = []
        # 1-18新增：记录statements的type
        self._statements_type: list[str] = []

    def add_guide(self, lang: str, guide: str) -> None:
        """添加引导语

        Args:
            lang (str): 语言
            guide (str): 引导语
        """
        self.lang_guides[lang] = guide
    
    def add_temp(self, lang: str, temp: dict[str, list[str]]) -> None:
        """添加模板

        Args:
            lang (str): 语言
            temp (dict[str, list[str]]): 模板
        """
        self.lang_temps[lang] = temp
    
    def _first_capitalize(self, lang: str, text: str) -> str:
        """将文本调整为首字母大写，而其他字母不变的形式

        Args:
            lang (str): 语言
            text (str): 文本

        Returns:
            str: 首字母大写而其他字母不变的文本
        """
        if lang == "en":
            return text[0].upper() + text[1:]
        return text
    
    def get_statements(self, lang: str) -> list[str]:
        """获取语言对应的语句

        Args:
            lang (str): 语言

        Returns:
            list[str]: 语句列表
        """
        # 12-17修改：修改试题文本生成形式
        # return [i.state(self.lang_temps[lang]) for i in self.original_scene._chosen_group]
        # 1-18新增：记录statements的type
        self._statements_type = [i.typetag for i in self.original_scene._chosen_group]
        # 12-24修改：移除陈述后的分号
        statements = [i.state(self.lang_temps[lang]) for n, i in enumerate(self.original_scene._chosen_group, start=1)]
        # 12-24新增：语言为英文时将陈述句首字母大写
        statements = [self._first_capitalize(lang, i) for i in statements]
        # 12-24新增：为每个陈述句加上编号
        return [f"({n}){i}" for n, i in enumerate(statements, start=1)]
    
    def get_question(self, lang: str) -> str:
        """获取问题

        Args:
            lang (str): 语言

        Returns:
            str: 问题
        """
        ask_info = self.original_scene._ask_info # 获取问题信息
        self._ask_info = ask_info # 记录提问信息
        ask_prop = self.original_scene._asked_prop # 获取问题命题
        self._type_tags.append(ask_prop.typetag) # 记录提问的命题的typetag
        question = ask_prop.ask(self.lang_temps[lang], ask_info[prop.TYPE]) # 生成问题
        # 12-24新增：添加句号
        # return question[prop.SENTENCE]
        return question[prop.SENTENCE] + proposition.config.LANG_CONFIG[lang][FULL_STOP]
    
    def get_answers(self, lang: str) -> dict[str, Any]:
        """获取答案信息

        Args:
            lang (str): 语言

        Returns:
            dict[str, Any]: 答案信息
        """
        answer_info = self.original_scene.answer_info # 获取答案信息
        answers: dict[str, Any] = deepcopy(answer_info[machines.OPTIONS]) # 深复制答案
        str_answers: dict[str, str] = {k: str(v) for k, v in answers.items()} # 转换为字符串
        # 12-25增加：检查答案文本，如果是“以上选项均不满足要求”，需要替换成对应语言的文本
        for k, v in str_answers.items():
            if v == LANG_CONFIG["zh"][ALL_WRONG] or v == LANG_CONFIG["en"][ALL_WRONG]:
                str_answers[k] = LANG_CONFIG[lang][ALL_WRONG]
        new_info = deepcopy(answer_info) | {machines.OPTIONS: str_answers} # 更新答案信息
        return new_info
        
    def run(self, execute: int = 10, seed: Union[int, float, None] = None) -> list[dict[str, Any]]:
        """运行“提问单个命题”

        Args:
            execute (int, optional): 运行次数. 默认为10.
            seed (Union[int, float, None], optional): 随机种子. 默认为None.

        Returns:
            list[dict[str, Any]]: 数据
        """
        data: list[dict[str, Any]] = [] # 用于存储数据
        for _ in range(execute):
            # 运行原始场景生成原始数据
            origin_result = self.original_scene.run(execute=1, seed=seed)
            for lang in proposition.config.CURR_LANGS:
                proposition.config.set_lang_mode(lang) # 设置全局语言模式
                self.original_scene.lang = lang # 设置原始场景的语言
                guide = self.lang_guides[lang] # 获取引导语
                statements = self.get_statements(lang) # 获取语句
                # 12-17修改：修改试题文本的生成格式
                # text = guide + proposition.config.COLON + proposition.config.SEMICOLON.join(statements) # 生成试题文本
                # 12-24修改：修改试题文本的生成格式
                # text = guide + proposition.config.COLON + "\n" + "\n".join(statements) # 生成试题文本
                text = guide + proposition.config.COLON + "\n" + f"{proposition.config.SEMICOLON}\n".join(statements) + proposition.config.LANG_CONFIG[lang][FULL_STOP] # 生成试题文本
                # 获取问题
                question = self.get_question(lang)
                answer_info = self.get_answers(lang) # 获取答案信息
                level = origin_result[0][LEVEL] # 获取难度等级
                # 12-29修订：调整输出的字段名称
                # infos = {INIT_NUM: origin_result[0][INIT_NUM], CHAIN_LENGTH: origin_result[0][CHAIN_LENGTH], KNOWLEDGE_NUM: origin_result[0][KNOWLEDGE_NUM], SCENE_TYPE: origin_result[0][SCENE_TYPE]}
                # data.append({"guide": guide, "statements": statements, "text": text, "question": question, "choices": answer_info[machines.OPTIONS], "answer": answer_info[machines.ANSWERS], LEVEL: level, "lang": lang} | infos | {"typetags": deepcopy(self._type_tags)}) # 添加数据
                output: dict[str, Any] = {
                    # 1-13修订：将语言信息放置到后方，并改变定义
                    # proposition.config.LANGUAGE: lang,
                    proposition.config.TEXT: text,
                    proposition.config.QUESTION: question,
                    proposition.config.OPTIONS: answer_info[machines.OPTIONS],
                    proposition.config.ANSWER: answer_info[machines.ANSWERS],
                    proposition.config.LEVEL: level,
                    proposition.config.LANGUAGE: proposition.config.LANG_CONFIG[lang][proposition.config.LANG_NAME],
                    proposition.config.QUES_INFO: {
                        proposition.config.CHAIN_LENGTH: origin_result[0][CHAIN_LENGTH],
                        proposition.config.ENTITY_NUM: origin_result[0][INIT_NUM],  # init_num指的是场景中涉及的事件数量
                        proposition.config.KNOWLEDGE_NUM: origin_result[0][KNOWLEDGE_NUM],
                        proposition.config.SCENE_TYPE: origin_result[0][SCENE_TYPE],
                        # 1-11补充：增加QUESTION_TYPE字段
                        proposition.config.QUESTION_TYPE: deepcopy(self._type_tags),
                        # 1-18新增：增加statements_type字段
                        proposition.config.STATEMENTS_TYPE: deepcopy(self._statements_type),
                    },
                }
                data.append(output)
                self._type_tags.clear() # 清空typetags
                self._statements_type.clear() # 清空statements_type
        # 返回数据
        return data

    def get_options(self, lang: str) -> dict[str, str]:
        """获取选项

        Args:
            lang (str): 语言

        Returns:
            dict[str, str]: 选项列表
        """
        option_dict = self.original_scene._ask_all_machine._option_dict # 获取选项信息
        self._type_tags.extend([i.typetag for i in option_dict.values() if isinstance(i, prop.Proposition)]) # 记录选项的命题的typetag
        choices = [i.state(self.lang_temps[lang]) if isinstance(i, prop.Proposition) else str(i) for i in option_dict.values()] # 生成选项
        # 12-24新增：将文本的首字母大写
        choices = [self._first_capitalize(lang, i) for i in choices]
        # 1-3新增：检查选项，如果选项是“以上选项均不正确”，则替换成对应语言的文本
        for i in range(len(choices)):
            # 如果是中文的“以上选项均不正确”或英文的“None of the options above meets the requirements of the question”，则替换成对应语言的文本
            if choices[i] == LANG_CONFIG["zh"][ALL_WRONG]:
                choices[i] = LANG_CONFIG[lang][ALL_WRONG]
            elif choices[i] == LANG_CONFIG["en"][ALL_WRONG]:
                choices[i] = LANG_CONFIG[lang][ALL_WRONG]
        # 12-24新增：为选项加上句号
        choices: list[str] = [i + proposition.config.LANG_CONFIG[lang][FULL_STOP] for i in choices]
        new_dict = {k: v for k, v in zip(option_dict.keys(), choices)} # 生成新的选项字典
        # 检查new_dict的最后一个选项，如果是“以上选项均不正确”，则按照语言寻找ALL_WRONG替换之
        # 12-29修订：修改检查的逻辑，改为检查全部选项
        '''
        if new_dict[list(new_dict.keys())[-1]] == LANG_CONFIG["zh"][ALL_WRONG] or new_dict[list(new_dict.keys())[-1]] == LANG_CONFIG["en"][ALL_WRONG]:
            new_dict[list(new_dict.keys())[-1]] = LANG_CONFIG[lang][ALL_WRONG]
        '''
        # 1-3移除：原有的检查选项的逻辑前移
        '''
        for k, v in new_dict.items():
            if v == LANG_CONFIG["zh"][ALL_WRONG]:
                new_dict[k] = LANG_CONFIG[lang][ALL_WRONG]
            elif v == LANG_CONFIG["en"][ALL_WRONG]:
                new_dict[k] = LANG_CONFIG[lang][ALL_WRONG]
        '''
        return new_dict
    
    def run_ask_all(self, execute: int = 10, seed: Union[int, float, None] = None, ask_correct: bool = True) -> list[dict[str, Any]]:
        """运行场景，获取一组询问多个命题类型的题目
        
        Args:
            execute (int, optional): 生成的题目数量. 默认为10.
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            ask_correct (bool, optional): 询问机的询问模式. 默认为True(询问“以下说法正确的是”). 可选的值有：
                - True，询问“以下说法正确的是”
                - False，询问“以下说法错误的是”

        Returns:
            list[dict[str, Any]]: 一组题目
        """
        data: list[dict[str, Any]] = [] # 用于存储数据
        for _ in range(execute):
            # 运行原始场景生成原始数据
            origin_result = self.original_scene.run_ask_all(execute=1, seed=seed, ask_correct=ask_correct)
            for lang in proposition.config.CURR_LANGS:
                proposition.config.set_lang_mode(lang) # 设置全局语言模式
                self.original_scene.lang = lang # 设置原始场景的语言
                guide = self.lang_guides[lang] # 获取引导语
                statements = self.get_statements(lang) # 获取语句
                # 12-17修改：修改试题文本的生成格式
                # text = guide + proposition.config.COLON + proposition.config.SEMICOLON.join(statements) # 生成试题文本
                # 12-24修改：修改试题文本的生成格式
                # text = guide + proposition.config.COLON + "\n" + "\n".join(statements) # 生成试题文本
                text = guide + proposition.config.COLON + "\n" + f"{proposition.config.SEMICOLON}\n".join(statements) + proposition.config.LANG_CONFIG[lang][FULL_STOP] # 生成试题文本
                origin_question = origin_result[0][machines.QUESTION] # 获取问题
                if origin_question == LANG_CONFIG["zh"][ASK_RIGHT] or origin_question == LANG_CONFIG["en"][ASK_RIGHT]:
                    question = LANG_CONFIG[lang][ASK_RIGHT]
                elif origin_question == LANG_CONFIG["zh"][ASK_WRONG] or origin_question == LANG_CONFIG["en"][ASK_WRONG]:
                    question = LANG_CONFIG[lang][ASK_WRONG]
                else:
                    raise ValueError(f"问题{origin_question}不正确")
                # question = origin_result[0][machines.QUESTION] # 获取问题
                choices = self.get_options(lang) # 获取选项
                answer = origin_result[0][machines.ANSWERS] # 获取答案
                level = origin_result[0][LEVEL]
                # infos = {INIT_NUM: origin_result[0][INIT_NUM], CHAIN_LENGTH: origin_result[0][CHAIN_LENGTH], KNOWLEDGE_NUM: origin_result[0][KNOWLEDGE_NUM], SCENE_TYPE: origin_result[0][SCENE_TYPE]}
                # data.append({"guide": guide, "statements": statements, "text": text, "question": question, "choices": choices, "answer": answer, LEVEL: level, "lang": lang} | infos | {"typetags": deepcopy(self._type_tags)}) # 添加数据
                # 12-29修订：调整输出的字段名称
                output: dict[str, Any] = {
                    # 1-13修订：将语言信息放置到后方，并改变定义
                    # proposition.config.LANGUAGE: lang,
                    proposition.config.TEXT: text,
                    proposition.config.QUESTION: question,
                    proposition.config.OPTIONS: choices,
                    proposition.config.ANSWER: answer,
                    proposition.config.LEVEL: level,
                    proposition.config.LANGUAGE: proposition.config.LANG_CONFIG[lang][proposition.config.LANG_NAME],
                    proposition.config.QUES_INFO: {
                        proposition.config.CHAIN_LENGTH: origin_result[0][CHAIN_LENGTH],
                        proposition.config.ENTITY_NUM: origin_result[0][INIT_NUM],  # init_num指的是场景中涉及的事件数量
                        proposition.config.KNOWLEDGE_NUM: origin_result[0][KNOWLEDGE_NUM],
                        proposition.config.SCENE_TYPE: origin_result[0][SCENE_TYPE],
                        # 1-11补充：增加QUESTION_TYPE字段
                        proposition.config.QUESTION_TYPE: deepcopy(self._type_tags),
                        # 1-18新增：增加statements_type字段
                        proposition.config.STATEMENTS_TYPE: deepcopy(self._statements_type),
                    },
                }
                data.append(output)
                self._type_tags.clear() # 清空typetags
                self._statements_type.clear() # 清空statements_type
        # 返回数据
        return data