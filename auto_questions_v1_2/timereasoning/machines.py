# encoding: utf8
# author: Qin Yuhang
# date: 2024-11-03

import sys
from pathlib import Path
from tqdm import tqdm
import random
from typing import Any

sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from timereasoning import event, timeprop

class SearchMachine:
    """时间领域专用搜索机
    """
    class SortedEvents:
        """对事件列表进行排序的类"""
        def __init__(self, event_list: list[event.Event]) -> None:
            """初始化排序类

            Args:
                event_list (list[event.Event]): 事件列表
            """
            self.list = event_list

        def sort(self) -> None:
            """对事件列表进行排序"""
            self.list.sort(key = lambda x: x.time)

        def before_events(self, e: event.Event) -> list[event.Event]:
            """返回在事件e之前的事件列表"""
            return [x for x in self.list if x.time < e.time]

        def __call__(self, *args: Any, **kwds: Any) -> list[event.Event]:
            """返回事件列表"""
            return self.list

    def __init__(self, event_list: list[event.Event], prop_list: list[timeprop.TimeP], knowledges: list[timeprop.TimeP] = []) -> None:
        """初始化搜索机

        Args:
            event_list (list[event.Event]): 事件列表
            prop_list (list[timeprop.TimeP]): 命题列表

        Raises:
            TypeError: 未知事件类型
        """
        self.event_list = self.SortedEvents(event_list)
        self.event_list.sort()
        self.prop_list = prop_list
        self.single_prop_list = [p for p in prop_list if isinstance(p, timeprop.SingleTimeP)]
        self.double_prop_list = [p for p in prop_list if isinstance(p, timeprop.DoubleTimeP)]
        # 11-07增加：输入知识
        self.knowledges = knowledges
        self.chosen_props: list[timeprop.TimeP] = []

    @property
    def _temporal_event_sorted(self) -> SortedEvents:
        """将事件列表中的瞬时时间事件按时间排序"""
        lst: list[event.TemporalEvent] = []
        for e in self.event_list():
            if type(e) == event.TemporalEvent:
                lst.append(e)
            elif type(e) == event.DurativeEvent:
                lst.extend((e.start_event, e.end_event))
            elif type(e) == event.FreqEvent:
                lst.extend(e.sub_events)
            else:
                raise TypeError(f"未知事件类型{type(e)}")
        temporals = self.SortedEvents(lst)
        temporals.sort()
        return temporals

    @property
    def _duration_event_sorted(self) -> SortedEvents:
        """将事件列表中的持续时间事件按时间排序"""
        lst: list[event.DurativeEvent] = [e for e in self.event_list() if type(e) == event.DurativeEvent]
        lst.sort(key = lambda x: x.time)
        return self.SortedEvents([e.duration_event for e in lst])
    
    @property
    def _knowledge_events(self) -> list[event.Event]:
        """将知识库中的事件提取出来

        Returns:
            list[event.Event]: 事件列表
        """
        event_list = []
        for k in self.knowledges:
            if isinstance(k, timeprop.SingleTimeP):
                event_list.append(k.element)
            else:
                pass
        return event_list
    
    def _find_all_props(self, e: event.Event) -> list[list[timeprop.TimeP]]:
        """查找事件e对应的全部表述命题

        Args:
            e (event.Event): 事件

        Returns:
            list[list[timeprop.TimeP]]: 表述命题列表
        """
        candidates: list[list[timeprop.TimeP]] = [[p] for p in self.single_prop_list if p.element == e] # 查找单元素命题
        if type(e) == event.TemporalEvent or type(e) == event.SubEvent:
            doubles = [[p] for p in self.double_prop_list if (isinstance(p, (timeprop.AfterTimeP, timeprop.SimultaneousP)) and p.element1 == e and p.element2.got(self._temporal_event_sorted.before_events(e)))]
            candidates.extend(doubles)
            knowledge_related = [[p] for p in self.double_prop_list if (isinstance(p, (timeprop.AfterTimeP, timeprop.BeforeTimeP, timeprop.SimultaneousP)) and p.element1 == e and p.element2.got(self._knowledge_events))]
            candidates.extend(knowledge_related)
        elif type(e) == event.DurativeEvent:
            second = random.choice(("end", "duration"))
            if second == "end":
                double = self._find_all_props(e.start_event) + self._find_all_props(e.end_event)
            else:
                double = self._find_all_props(e.start_event) + self._find_all_props(e.duration_event)
            candidates.extend(double)
        elif type(e) == event.FreqEvent:
            pass
        elif type(e) == event.Duration:
            double = [[p] for p in self.double_prop_list if (isinstance(p, timeprop.DoubleTimeP) and p.element1 == e and p.element2.got(self._duration_event_sorted.before_events(e)))]
            candidates.extend(double)
        else:
            raise TypeError(f"未知事件类型{type(e)}")
        return candidates
    
    def _find_props(self, e: event.Event) -> list[timeprop.TimeP]:
        """随机选择事件e对应的表述命题

        Args:
            e (event.Event): 事件

        Returns:
            list[timeprop.TimeP]: 表述命题
        """
        return random.choice(self._find_all_props(e))

    def run(self) -> list[timeprop.TimeP]:
        """运行推理机，对事件集生成表述命题集

        Returns:
            list[timeprop.TimeP]: 表述命题集
        """
        print("对事件集生成表述命题集...")
        for _, e in tqdm(enumerate(self.event_list()), desc="事件生成表述命题", total=len(self.event_list())):
            props = self._find_props(e)
            self.chosen_props.extend(props)
        print("表述命题集生成完毕.")
        return self.chosen_props