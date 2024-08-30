# encoding: utf8
# date: 2024-08-30
# author: Qin Yuhang

from typing import Union, Any, Optional, Dict
import random
from string import ascii_uppercase
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from timereasoning import timeprop, event, timerelation
from proposition import prop

class TimeAnswerMachine:
    """时间推理答案机，用于生成试题和答案"""
    def __init__(self, all_props: list[timeprop.TimeP], temps: dict[str, list[str]], seed: Union[int, float, None] = None, options: int = 4) -> None:
        self._temps = temps # 模板
        self._askable = [i for i in all_props if i.askable] # 可提问命题
        self._elements = [i.element for i in all_props if isinstance(i, timeprop.SingleTimeP)] # 事件合集
        self._times = [i.time for i in self._elements if not isinstance(i, (event.FreqEvent, event.Duration))] # 事件的时间合集
        self._start = min(self._times) # 时间轴的开始时间
        self._end = max(self._times) # 时间轴的结束时间
        self._seed = seed
        self._options = options if options <= len(ascii_uppercase) else len(ascii_uppercase) # 选项数量

    @staticmethod
    def _compare_singles(event1: event.Event, event2: event.Event) -> bool:
        """比较两个事件在属性上的相等性

        Args:
            event1 (event.Event): 第一个事件
            event2 (event.Event): 第二个事件

        Returns:
            bool: 两个事件在属性上是否相等
        """
        typs: list[type[event.Event]] = [event.TemporalEvent, event.Duration, event.DurativeEvent, event.FreqEvent,]
        for t in typs:
            if isinstance(event1, t) and isinstance(event2, t):
                if t == event.TemporalEvent:
                    return event1.time == event2.time
                elif t == event.Duration:
                    return event1.time == event2.time
                elif t == event.DurativeEvent:
                    return event1.time == event2.time and event1.endtime == event2.endtime
                elif t == event.FreqEvent:
                    return event1.time == event2.time and event1.frequency == event2.frequency and event1.endtime == event2.endtime
        return False
    
    @staticmethod
    def _compare_double(curr_prop: timeprop.TimeP, new_element: event.Event, prev_element: event.Event) -> bool:
        """两个事件能否构成属性相似的命题

        Args:
            curr_prop (timeprop.TimeP): 现有命题
            new_element (event.Event): 构成新命题的新事件
            prev_element (event.Event): 构成新命题的基准事件

        Returns:
            bool: 两个事件能否构成属性相似的命题
        """
        if type(new_element) == type(prev_element):
            new_prop = timeprop.DoubleTimeP.build(new_element, prev_element)
            if isinstance(curr_prop, (timeprop.BeforeTimeP, timeprop.AfterTimeP, timeprop.LongTimeP, timeprop.ShortTimeP)):
                return type(curr_prop) == type(new_prop) and curr_prop.diff == new_prop.diff
            elif isinstance(curr_prop, (timeprop.GapTimeP,)):
                return isinstance(new_prop, (timeprop.BeforeTimeP, timeprop.AfterTimeP, timeprop.LongTimeP, timeprop.ShortTimeP)) and curr_prop.diff == new_prop.diff
            else:
                lst = timerelation.TimeEntailment.reason(new_prop)
                if lst is not None:
                    return any([type(i) == type(curr_prop) for i in lst])
        return False
    
    def run(self) -> Optional[Dict[str, Any]]:
        """运行答案机，生成试题和答案

        Raises:
            ValueError: 未知的问题类型

        Returns:
            Dict[str, Any] | None: 试题和答案
        """
        random.seed(self._seed)
        curr_prop = random.choice(self._askable) # 选择一个命题发问
        question_info = curr_prop.ask(self._temps)
        time_pos: list[str] = ["time", "endtime", ]
        time_len: list[str] = ["diff", "duration", "frequency",]
        correct: tuple[Any, bool] = (question_info[prop.ANSWER], True)
        if "element" == (typ := question_info[prop.TYPE]):
            candidate = [(i, self._compare_singles(i, question_info[prop.ANSWER])) for i in self._elements if i != question_info[prop.ANSWER]]
        elif typ == "prev_element":
            candidate = [(i, self._compare_double(curr_prop, curr_prop.new_element, i)) for i in self._elements if i != question_info[prop.ANSWER]]
        elif typ == "new_element":
            candidate = [(i, self._compare_double(curr_prop, i, curr_prop.prev_element)) for i in self._elements if i != question_info[prop.ANSWER]]
        elif typ in time_pos:
            candidate = [(i, i == question_info[prop.ANSWER]) for i in range(self._start, self._end + 1) if i != question_info[prop.ANSWER]]
        elif typ in time_len:
            candidate = [(i, i == question_info[prop.ANSWER]) for i in range(1, self._end - self._start + 1) if i != question_info[prop.ANSWER]]
        else:
            raise ValueError(f"未知的问题类型: {typ}")
        # 去除名称重复的选项
        _cand = []
        for i in candidate:
            for j in _cand:
                if str(i[0]) == str(j[0]):
                    if i[0] == True and j[0] == False:
                        _cand.remove(j)
                        _cand.append(i)
                    break
            _cand.append(i)
        candidate = _cand
        if len(candidate) < self._options - 1:
            print(f"候选项数量不足，无法生成选项！")
            return None
        others = random.sample(candidate, self._options - 1)
        options = [correct,] + others
        options = [(i[0].event() if isinstance(i[0], event.Event) else str(i[0]), i[1]) for i in options]
        random.shuffle(options)
        solutions: list[str] = []
        opt_dict: dict[str, str] = {}
        for i, (opt, judge) in enumerate(options):
            opt_dict[ascii_uppercase[i]] = opt
            if judge:
                solutions.append(ascii_uppercase[i])
        return {"question": question_info[prop.SENTENCE], "options": opt_dict, prop.ANSWER: solutions}
