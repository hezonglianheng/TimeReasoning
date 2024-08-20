# encoding: utf8
# version: 1.1
# date: 2024-08-18
# author: Qin Yuhang

import statements as stmt
import random

# 结果的键
GUIDE = "guide"
STATEMENTS = "statements"
PROCESS = "process"
QUESTION = "question"
OPTIONS = "options"
ANSWERS = "answers"

class TimeLine:
    """时间轴类，用于描述一个时间轴及其上的事件关系"""
    def __init__(self, scale: stmt.TimeScale, guide: str = "") -> None:
        """时间轴类，用于描述一个时间轴及其上的事件关系

        Args:
            scale (statements.TimeScale): 时间轴的时间尺度
            guide (str, optional): 时间轴的引导语. 默认为空.
        """
        self.scale = scale # 时间轴的时间尺度
        self.guide = guide # 时间轴的引导语
        self.events: list[stmt.Event] = []
        # 运行中间结果
        self.__stmts: list[str] = [] # 时间轴的命题
        self.__described_events: list[stmt.Event] = [] # 已经表述过的事件
        self.__processes_texts: list[str] = [] # 时间轴的过程描述

    def add_events(self, *events: stmt.Event) -> None:
        """添加事件到时间轴中

        Args:
            *events (statements.Event): 事件列表
        """
        self.events.extend(events)
        
    def add_guide(self, guide: str) -> None:
        """添加时间轴的引导语

        Args:
            guide (str): 时间轴的引导语
        """
        self.guide = guide
    
    def run_stmt(self, verbose: int = 0) -> dict[str, str]:
        """生成对于时间轴的描述和相关问题

        Args:
            random_seed (int | float | None, optional): 随机种子. 默认为None.
            verbose (int, optional): 详细信息输出强度，0为不输出，1为输出到控制台，2为输出到最终结果. 默认为0.

        Raises:
            ValueError: 时间轴上少于两个事件时抛出异常

        Returns:
            dict[str, str]: 运行结果，包括引导语、描述、详细信息等
        """
        assert len(self.events) > 1, "时间轴上至少需要两个事件，请通过add_events方法添加事件"
        # random.seed(random_seed) # 设置随机种子
        stmt.get_templates(self.scale) # 获取时间轴的模板
        stmt.VERBOSE = verbose # 设置输出强度
        start_event = random.choice(self.events) # 随机选择一个事件作为起始事件
        self.__stmts.append(start_event.statement()[stmt._STATEMENT]) # 添加起始事件的描述
        self.__described_events.append(start_event) # 记录已经表述过的事件
        # 不断生成表述，直到所有事件都被表述
        while any([event not in self.__described_events for event in self.events]):
            # 随机选取未表述过的事件
            curr_event = random.choice([event for event in self.events if event not in self.__described_events])
            # 随机选择生成事件描述或事件关系描述
            method: str = random.choice(["event", "relation"])
            if method == "event": # 生成单个事件描述
                curr_statement = curr_event.statement()
                if verbose >= 2: # 记录生成过程
                    self.__processes_texts.append(f"生成事件描述：{curr_event}")
            else: # 生成事件关系描述
                prev_event = random.choice(self.__described_events) # 随机选择一个已经表述过的事件
                # 根据prev_event和curr_event类型生成事件关系
                relation: stmt.Relation
                if isinstance(prev_event, stmt.TemporalEvent) and isinstance(curr_event, stmt.TemporalEvent):
                    relation = stmt.TempRelation(prev_event, curr_event)
                elif isinstance(prev_event, stmt.TemporalEvent) and isinstance(curr_event, stmt.LastingEvent):
                    relation = stmt.TempLastingRelation(prev_event, curr_event)
                elif isinstance(prev_event, stmt.LastingEvent) and isinstance(curr_event, stmt.TemporalEvent):
                    relation = stmt.LastingTempRelation(prev_event, curr_event)
                elif isinstance(prev_event, stmt.LastingEvent) and isinstance(curr_event, stmt.LastingEvent):
                    relation = stmt.LastingRelation(prev_event, curr_event)
                else:
                    raise ValueError("事件类型错误")
                curr_statement = relation.statement()
                if verbose >= 2:
                    self.__processes_texts.append(f"生成事件关系描述：{prev_event} -> {curr_event}")
            self.__stmts.append(curr_statement[stmt._STATEMENT])
            self.__described_events.append(curr_event) # 记录已经表述过的事件
        return {GUIDE: self.guide, STATEMENTS: "\n".join(self.__stmts), PROCESS: "\n".join(self.__processes_texts)}
    
    def run_question(self, verbose: int = 0) -> dict[str, str|list[str]|dict[str, str]]:
        """生成时间轴的问题

        Args:
            verbose (int, optional): 详细信息输出强度，0为不输出，1为输出到控制台，2为输出到最终结果. 默认为0.

        Returns:
            dict[str, str|list[str]|dict[str, str]]: 问题，包括问题描述、选项、答案等
        """
        assert self.__described_events, "请先执行run_stmt方法生成时间轴描述"
        return {QUESTION: "", OPTIONS: {}, ANSWERS: []}
    
    def run(self, random_seed: int | float | None = None, verbose: int = 0) -> dict[str, str]:
        """运行时间线，生成对于时间轴的描述和相关问题

        Args:
            random_seed (int | float | None, optional): 随机种子. 默认为None.
            verbose (int, optional): 详细信息输出强度，0为不输出，1为输出到控制台，2为输出到最终结果. 默认为0.

        Returns:
            dict[str, str]: 运行结果，包括引导语、描述、问题、选项、答案、详细信息等
        """
        random.seed(random_seed) # 设置随机种子
        part_stmt = self.run_stmt(verbose) # 生成时间轴描述
        part_question = self.run_question(verbose) # 生成时间轴问题
        return part_stmt | part_question # 合并描述和问题
