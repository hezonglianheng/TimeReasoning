# encoding: utf8
# author: Qin Yuhang
# date: 2024-11-03

import sys
from pathlib import Path
from tqdm import tqdm
import random
from typing import Any, List, Literal
from itertools import product

sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from timereasoning import event, timeprop
from proposition import machines
from proposition import prop
from proposition.graph import Graph

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
                # double = self._find_all_props(e.start_event) + self._find_all_props(e.end_event)
                # 11-12修改：将持续时间事件的结束事件与开始事件的命题组合
                double: list[list[timeprop.TimeP]] = []
                start_props = self._find_all_props(e.start_event) # 开始事件的命题
                end_props = self._find_all_props(e.end_event) # 结束事件的命题
                for startp, endp in product(start_props, end_props):
                    double.append(startp + endp)
            else:
                # double = self._find_all_props(e.start_event) + self._find_all_props(e.duration_event)
                # 11-12修改：将持续时间事件的开始事件与持续时间事件的命题组合
                double: list[list[timeprop.TimeP]] = []
                start_props = self._find_all_props(e.start_event)
                duration_props = self._find_all_props(e.duration_event)
                for startp, durationp in product(start_props, duration_props):
                    double.append(startp + durationp)
            candidates.extend(double)
        elif type(e) == event.FreqEvent:
            pass
        elif type(e) == event.Duration:
            double = [[p] for p in self.double_prop_list if (isinstance(p, (timeprop.LongTimeP, timeprop.ShortTimeP, timeprop.SameLenTimeP)) and p.element1 == e and p.element2.got(self._duration_event_sorted.before_events(e)))]
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

class TimeGetRangeMachine(machines.GetRangeMachine):
    def __init__(self, all_elements: list[event.Event]) -> None:
        """初始化时间领域专用范围获取机

        Args:
            all_elements (list[event.Event]): 全部事件
        """
        super().__init__(all_elements)

    def get_range(self, ask_info: dict[str, Any], *args, **kwargs) -> List[event.Event] | List[int]:
        """获取时间领域的范围

        Args:
            ask_info (dict[str, Any]): 问题信息

        Raises:
            ValueError: 如果回答的答案或者类型是未知的，则抛出此错误

        Returns:
            List[event.Event] | List[int]: 时间领域的范围
        """
        if "element" in (typ := ask_info.get(prop.TYPE)):
            ans = ask_info.get(prop.ANSWER)
            # 12-25修改：对于瞬时事件的值域，只返回瞬时事件
            # 1-13修改：返回的事件不能和已有的事件重复
            # if isinstance(ans, (event.TemporalEvent, event.DurativeEvent, event.FreqEvent)):
            if isinstance(ans, (event.TemporalEvent)):
                # range_list = [i for i in self.all_elements if isinstance(i, (event.TemporalEvent, event.DurativeEvent, event.FreqEvent))]
                # 1-13修改：返回的事件不能和已有的事件重复
                # range_list = [i for i in self.all_elements if isinstance(i, (event.TemporalEvent))]
                range_list = [i for i in self.all_elements if isinstance(i, (event.TemporalEvent)) and i.event() != ans.event()]
            elif isinstance(ans, event.Duration):
                # 12-24修改：对于持续时间的值域，只返回持续时间事件
                # range_list = [i for i in self.all_elements if isinstance(i, (event.Duration, event.TemporalEvent, event.FreqEvent))]
                # 1-13修改：返回的事件不能和已有的事件重复
                # range_list = [i for i in self.all_elements if isinstance(i, (event.Duration))]
                range_list = [i for i in self.all_elements if isinstance(i, (event.Duration)) and i.event() != ans.event()]
            # 12-25新增：其他类型的事件的值域只返回同类型的事件，以避免理解上的困难
            elif isinstance(ans, event.DurativeEvent):
                # 1-13修改：返回的事件不能和已有的事件重复
                # range_list = [i for i in self.all_elements if isinstance(i, (event.DurativeEvent))]
                range_list = [i for i in self.all_elements if isinstance(i, (event.DurativeEvent)) and i.event() != ans.event()]
            elif isinstance(ans, event.FreqEvent):
                # 1-13修改：返回的事件不能和已有的事件重复
                # range_list = [i for i in self.all_elements if isinstance(i, (event.FreqEvent))]
                range_list = [i for i in self.all_elements if isinstance(i, (event.FreqEvent)) and i.event() != ans.event()]
            else:
                raise ValueError(f"未知类型{type(ans)}")
        elif "time" in typ:
            all_temp = sorted([i.time for i in self.all_elements if isinstance(i, (event.TemporalEvent))], key=lambda x: x)
            range_list = list(range(all_temp[0], all_temp[-1] + 1))
        elif typ == "duration":
            all_temp = sorted([i.time for i in self.all_elements if isinstance(i, (event.TemporalEvent))], key=lambda x: x)
            range_list = list(range(all_temp[-1] - all_temp[0] + 1))
        elif typ == "diff":
            all_temp = sorted([i.time for i in self.all_elements if isinstance(i, (event.TemporalEvent))], key=lambda x: x)
            # 12-30修订：diff的值域从1开始
            range_list = list(range(1, all_temp[-1] - all_temp[0] + 1))
        else:
            raise ValueError(f"未知类型{typ}")
        return range_list

class TimeAskAllMachine(machines.AskAllMachine):
    """时间领域专用询问机
    """
    def _get_option_range(self, ask_info: dict[str, Any], curr_prop: timeprop.TimeP) -> List[Any]:
        """获取选项范围

        Args:
            ask_info (dict[str, Any]): 问题信息
            curr_prop (timeprop.TimeP): 当前命题

        Returns:
            List[Any]: 选项范围
        """
        initial_range = super()._get_option_range(ask_info, curr_prop)
        
        if isinstance(curr_prop, timeprop.DurativeP):
            # 如果是持续时间命题且询问endtime，则选项范围为起始时间之后的时间
            if ask_info.get(prop.TYPE) == "endtime":
                initial_range = [i for i in initial_range if i > curr_prop.time]
            # 如果是持续时间命题且询问time，则选项范围为结束时间之前的时间
            elif ask_info.get(prop.TYPE) == "time":
                initial_range = [i for i in initial_range if i < curr_prop.endtime]
        if isinstance(curr_prop, timeprop.DoubleTimeP):
            # 如果是双元素命题，则值域中不包含当前命题的另一个元素
            if ask_info.get(prop.TYPE) == "element1":
                initial_range = [i for i in initial_range if i != curr_prop.element2]
            elif ask_info.get(prop.TYPE) == "element2":
                initial_range = [i for i in initial_range if i != curr_prop.element1]

        return initial_range