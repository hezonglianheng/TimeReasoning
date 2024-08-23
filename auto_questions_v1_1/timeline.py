# encoding: utf8
# version: 1.1
# date: 2024-08-18
# author: Qin Yuhang

import timescale as scale
import statements as stmt
import knowledge as know
import random
from fractions import Fraction
import time # 引入计时功能

# 结果的键
GUIDE = "guide"
STATEMENTS = "statements"
PROCESS = "process"
KNOWLEDGE = "knowledge"
QUESTION = "question"
OPTIONS = "options"
ANSWERS = "answers"

# 选择题选项数量
MUITIPLE_CHOICE_NUM = 4
ALL_WRONG_PROB = 0.1 # 全部选项均不正确的概率

class TimeLine:
    """时间轴类，用于描述一个时间轴及其上的事件关系"""
    def __init__(self, scale: scale.TimeScale, guide: str = "") -> None:
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
        self.__described_statements: list[stmt.Statement] = [] # 已经表述过的事件
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
    
    @property
    def sorted_temporal_events(self) -> list[stmt.TemporalEvent]:
        """获取按时间排序的瞬时事件

        Returns:
            list[statements.TemporalEvent]: 按时间排序的瞬时事件
        """
        temporal_events: list[stmt.TemporalEvent] = []
        for event in self.events:
            if isinstance(event, stmt.TemporalEvent):
                temporal_events.append(event)
            elif isinstance(event, stmt.LastingEvent):
                temporal_events.append(event.start_event)
                temporal_events.append(event.end_event)
        return sorted(temporal_events, key=lambda x: x.time)
    
    @property
    def timeline_range(self) -> tuple[int, int]:
        """获取时间轴的时间范围

        Returns:
            tuple[int, int]: 时间轴的时间范围
        """
        return self.sorted_temporal_events[0].time, self.sorted_temporal_events[-1].time
    
    @property
    def timeline_duration(self) -> int:
        """获取时间轴的时间跨度

        Returns:
            int: 时间轴的时间跨度
        """
        return self.timeline_range[1] - self.timeline_range[0]
    
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
        stmt.get_templates_knowledge(self.scale) # 获取时间轴的模板
        stmt.VERBOSE = verbose # 设置输出强度
        know.VERBOSE = verbose # 设置输出强度
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
                self.__described_statements.append(curr_event) # 记录已经表述过的事件
                if verbose >= 2: # 记录生成过程
                    self.__processes_texts.append(f"生成事件描述：{curr_event}")
            else: # 生成事件关系描述
                prev_event = random.choice(self.__described_events) # 随机选择一个已经表述过的事件
                # 根据prev_event和curr_event类型生成事件关系
                relation: stmt.Relation = stmt.events2relation(prev_event, curr_event)
                curr_statement = relation.statement()
                self.__described_statements.append(relation) # 记录已经表述过的事件关系
                if verbose >= 2:
                    self.__processes_texts.append(f"生成事件关系描述：{prev_event} -> {curr_event}")
            self.__stmts.append(curr_statement[stmt._STATEMENT])
            self.__described_events.append(curr_event) # 记录已经表述过的事件
        return {GUIDE: self.guide, STATEMENTS: "\n".join(self.__stmts), PROCESS: "\n".join(self.__processes_texts), KNOWLEDGE: "\n".join(know.KNOWLEDGE_LIST)}
    
    def run_question(self, verbose: int = 0) -> dict[str, str|list[str]|dict[str, str]]:
        """生成时间轴的问题

        Args:
            verbose (int, optional): 详细信息输出强度，0为不输出，1为输出到控制台，2为输出到最终结果. 默认为0.

        Returns:
            dict[str, str|list[str]|dict[str, str]]: 问题，包括问题描述、选项、答案等
        """

        def options_and_answers(correct_answers: str | list[str], candidates: list[str]) -> tuple[dict[str, str], list[str]]:
            """生成选择题的选项和答案

            Args:
                correct_answers (str | list[str]): 正确答案
                candidates (list[str]): 候选答案

            Returns:
                tuple[dict[str, str], list[str]]: 选项和答案
            """            
            global MUITIPLE_CHOICE_NUM, ALL_WRONG_PROB
            if isinstance(correct_answers, str): # 将正确答案转换为列表
                correct_answers = [correct_answers]
            distractors = [i for i in candidates if i not in correct_answers] # 生成干扰项
            if len(correct_answers) < MUITIPLE_CHOICE_NUM: # 若正确答案数量小于选项数量，则从干扰项中补充
                distractors = random.sample(distractors, MUITIPLE_CHOICE_NUM - len(correct_answers)) # 随机选择干扰项
            else: # 若干扰项数量足够，则不需要补充
                distractors = [] # 若干扰项数量足够，则不需要补充
                correct_answers = random.sample(correct_answers, MUITIPLE_CHOICE_NUM) # 随机选择正确答案
            options_list = correct_answers + distractors # 生成选项列表
            random.shuffle(options_list) # 打乱选项顺序
            options = {chr(ord("A")+i): options_list[i] for i in range(MUITIPLE_CHOICE_NUM)} # 生成选项
            answers = [k for k, v in options.items() if v in correct_answers] # 生成答案
            last = chr(ord("A") + MUITIPLE_CHOICE_NUM - 1) # 最后一个选项
            # 若最后一个选项是错误答案，则以一个小概率将其替换为“以上选项均不正确”
            if last not in answers and random.random() < ALL_WRONG_PROB:
                options[last] = "以上选项均不正确"
            # 若只有最后一个选项是正确答案，则以一个小概率将其替换为“以上选项均不正确”
            if len(answers) == 1 and last in answers and random.random() < ALL_WRONG_PROB:
                options[last] = "以上选项均不正确"
            return {OPTIONS: options, ANSWERS: answers}

        assert len(self.events) == len(self.__described_events), "请先执行run_stmt方法生成时间轴描述"
        stmt.VERBOSE = verbose # 设置输出强度
        # 检查未表述过的单个事件
        if avaliable_events := [event for event in self.events if all([event != i for i in self.__described_statements])]:
            # 随机选择生成事件描述或事件关系描述
            method: str = random.choice(["event", "relation"])
        else:
            method = "relation"
        # 根据生成方法生成试题和标准答案
        if method == "event":
            curr_event = random.choice(avaliable_events)
            question_info = curr_event.statement(question_mode=True)
            if (qtype := question_info[stmt._QUESTION_TYPE]) == "time":
                answer_info = options_and_answers(question_info[stmt._ANSWER], [str(i) for i in range(self.timeline_range[0], self.timeline_range[1]+1)])
            elif qtype == "event":
                # 生成所有事件的描述
                all_events = [event for event in self.sorted_temporal_events] + [event for event in self.events if isinstance(event, stmt.LastingEvent)]
                question_event = curr_event.question_event
                if isinstance(question_event, stmt.TemporalEvent):
                    all_events.remove(question_event)
                    correct_list = [e.event for e in all_events if isinstance(e, stmt.TemporalEvent) and e.time == question_event.time] # 生成正确选项
                    candidate_list = [e.event for e in all_events if e not in correct_list] # 生成干扰项
                elif isinstance(question_event, stmt.LastingEvent):
                    all_events.remove(question_event)
                    correct_list = [e.event for e in all_events if isinstance(e, stmt.LastingEvent) and e.time == question_event.time and e.endtime == question_event.endtime] # 生成正确选项
                    candidate_list = [e.event for e in all_events if e not in correct_list] # 生成干扰项
                answer_info = options_and_answers([question_info[stmt._ANSWER]] + correct_list, candidate_list)
            elif qtype == "duration":
                answer_info = options_and_answers(question_info[stmt._ANSWER], [str(i) for i in range(1, self.timeline_duration+1)])
            else:
                raise ValueError(f"未知的问题类型：{qtype}")
        else:
            while True: # 生成事件关系问题
                event1, event2 = random.sample(self.events, 2)
                curr_relation = stmt.events2relation(event1, event2)
                # 检查是否已经生成过这个事件关系
                if all([curr_relation != i for i in self.__described_statements]):
                    break
            question_info = curr_relation.statement(question_mode=True)
            if (qtype := question_info[stmt._QUESTION_TYPE]) == "diff":
                answer_info = options_and_answers(question_info[stmt._ANSWER], [str(i) for i in range(1, self.timeline_duration+1)])
            elif qtype == "event1":
                all_events = [event.event for event in self.sorted_temporal_events] + [event.event for event in self.events if isinstance(event, stmt.LastingEvent)]
                answer_info = options_and_answers(question_info[stmt._ANSWER], all_events)
            elif qtype == "event2":
                all_events = [event.event for event in self.sorted_temporal_events] + [event.event for event in self.events if isinstance(event, stmt.LastingEvent)]
                answer_info = options_and_answers(question_info[stmt._ANSWER], all_events)
            elif qtype == "times":
                times_candidate = [str(i) for i in range(max(0, int(question_info[stmt._ANSWER])-5), int(question_info[stmt._ANSWER])+6)]
                answer_info = options_and_answers(question_info[stmt._ANSWER], times_candidate)
            elif qtype == "ratio":
                ratio = Fraction(question_info[stmt._ANSWER])
                numerator_range = range(max(1, ratio.numerator-2), ratio.numerator+3)
                denominator_range = range(max(2, ratio.denominator-2), ratio.denominator+3)
                ratio_candidate = [f"{i}/{j}" for i in numerator_range for j in denominator_range]
                answer_info = options_and_answers(question_info[stmt._ANSWER], ratio_candidate)
            else:
                raise ValueError(f"未知的问题类型：{qtype}")
        return {QUESTION: question_info[stmt._QUESTION]} | answer_info
    
    def run(self, random_seed: int | float | None = None, verbose: int = 0) -> dict[str, str]:
        """运行时间线，生成对于时间轴的描述和相关问题

        Args:
            random_seed (int | float | None, optional): 随机种子. 默认为None.
            verbose (int, optional): 详细信息输出强度，0为不输出，1为输出到控制台，2为输出到最终结果. 默认为0.

        Returns:
            dict[str, str]: 运行结果，包括引导语、描述、问题、选项、答案、详细信息等
        """
        start_time = time.time()
        random.seed(random_seed) # 设置随机种子
        part_stmt = self.run_stmt(verbose) # 生成时间轴描述
        part_question = self.run_question(verbose) # 生成时间轴问题
        end_time = time.time()
        if verbose >= 1: # 在控制台输出结束提示信息
            print(f"描述和问题生成完毕！用时: {end_time - start_time}\n")
        self.clear() # 清空时间轴的描述和问题
        return part_stmt | part_question # 合并描述和问题

    def clear(self):
        """清空时间轴的描述和问题"""
        self.__stmts.clear()
        self.__described_events.clear()
        self.__described_statements.clear()
        self.__processes_texts.clear()
    
    def run_multiple(self, times: int = 1, random_seed: int | float | None = None, verbose: int = 0) -> list[dict[str, str]]:
        """运行时间线多次，生成对于时间轴的描述和相关问题

        Args:
            times (int): 运行次数，默认为1
            random_seed (int | float | None, optional): 随机种子. 默认为None.
            verbose (int, optional): 详细信息输出强度，0为不输出，1为输出到控制台，2为输出到最终结果. 默认为0.

        Returns:
            list[dict[str, str]]: 运行结果列表，包括引导语、描述、问题、选项、答案、详细信息等
        """
        return [self.run(random_seed, verbose) for _ in range(times)]