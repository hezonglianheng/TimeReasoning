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
from proposition.scene import Scene, LEVEL
from proposition import prop, machines

class LangParallelScene(metaclass=abc.ABCMeta):
    def __init__(self, original_scene: Scene) -> None:
        self.original_scene = original_scene # 原始场景
        self.lang_temps: dict[str, dict[str, list[str]]] = {} # 语言对应模板
        self.lang_guides: dict[str, str] = {} # 语言对应引导语
        # 12-14新增：记录提问信息的中间变量
        self._ask_info: dict[str, Any] = {}

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
    
    def get_statements(self, lang: str) -> list[str]:
        """获取语言对应的语句

        Args:
            lang (str): 语言

        Returns:
            list[str]: 语句列表
        """
        return [i.state(self.lang_temps[lang]) for i in self.original_scene._chosen_group]
    
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
        question = ask_prop.ask(self.lang_temps[lang], ask_info[prop.TYPE]) # 生成问题
        return question[prop.SENTENCE]
    
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
        new_info = deepcopy(answer_info) | {machines.OPTIONS: str_answers} # 更新答案信息
        return new_info
        
    def run(self, execute: int = 10, seed: Union[int, float, None] = None) -> list[dict[str, Any]]:
        """运行“提问单个命题”

        Args:
            execute (int, optional): 运行次数. Defaults to 10.
            seed (Union[int, float, None], optional): 随机种子. Defaults to None.

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
                text = guide + proposition.config.COLON + proposition.config.SEMICOLON.join(statements) # 生成试题文本
                # 获取问题
                question = self.get_question(lang)
                answer_info = self.get_answers(lang) # 获取答案信息
                level = origin_result[0][LEVEL] # 获取难度等级
                data.append({"guide": guide, "statements": statements, "text": text, "question": question, "choice": answer_info[machines.OPTIONS], "answer": answer_info[machines.ANSWERS], LEVEL: level, "lang": lang}) # 添加数据
        # 返回数据
        return data

    def get_options(self, lang: str) -> dict[str, Any]:
        """获取选项

        Args:
            lang (str): 语言

        Returns:
            dict[str, Any]: 选项列表
        """
        option_dict = self.original_scene._ask_all_machine._option_dict # 获取选项信息
        choices = [i.state(self.lang_temps[lang]) if isinstance(i, prop.Proposition) else str(i) for i in option_dict.values()] # 生成选项
        new_dict = {k: v for k, v in zip(option_dict.keys(), choices)} # 生成新的选项字典
        # 检查new_dict的最后一个选项，如果是“以上选项均不正确”，则按照语言寻找ALL_WRONG替换之
        if new_dict[list(new_dict.keys())[-1]] == LANG_CONFIG["zh"][ALL_WRONG] or new_dict[list(new_dict.keys())[-1]] == LANG_CONFIG["en"][ALL_WRONG]:
            new_dict[list(new_dict.keys())[-1]] = LANG_CONFIG[lang][ALL_WRONG]
        return new_dict
    
    def run_ask_all(self, execute: int = 10, seed: Union[int, float, None] = None) -> list[dict[str, Any]]:
        data: list[dict[str, Any]] = [] # 用于存储数据
        for _ in range(execute):
            # 运行原始场景生成原始数据
            origin_result = self.original_scene.run_ask_all(execute=1, seed=seed)
            for lang in proposition.config.CURR_LANGS:
                proposition.config.set_lang_mode(lang) # 设置全局语言模式
                self.original_scene.lang = lang # 设置原始场景的语言
                guide = self.lang_guides[lang] # 获取引导语
                statements = self.get_statements(lang) # 获取语句
                text = guide + proposition.config.COLON + proposition.config.SEMICOLON.join(statements) # 生成试题文本
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
                data.append({"guide": guide, "statements": statements, "text": text, "question": question, "choice": choices, "answer": answer, LEVEL: level, "lang": lang})

        return data