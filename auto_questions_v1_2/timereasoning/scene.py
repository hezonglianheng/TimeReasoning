# encoding: utf8
# date: 2024-08-27
# author: Qin Yuhang

import abc
from copy import deepcopy
import random
from typing import Union, Any
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from timereasoning import timeprop, timerule, timerelation, event
from timereasoning import timescale as ts
from proposition.machines import ReasonMachine as RM
from proposition.machines import SearchMachine as SM
from timereasoning.machines import TimeAnswerMachine as TAM

class TimeScene(metaclass = abc.ABCMeta):
    def __init__(self, scale: ts.TimeScale | int, guide: str = "") -> None:
        """初始化时间场景

        Args:
            scale (ts.TimeScale | int): 时间尺度
            guide (str, optional): 引导语. 默认为"".
        """
        # 需要使用的属性
        self.guide = guide # 引导语
        self.scale = scale if isinstance(scale, ts.TimeScale) else ts.TimeScale(scale) # 时间尺度
        self.event_list: list[event.Event] = [] # 事件列表
        self.relation_list = deepcopy(timerelation.RELATIONS) # 关系列表
        self.rule_list = deepcopy(timerule.RULES) # 规则列表
        self.temps = ts.choose_templates(scale)
        # 命题收集变量
        self._init_props: list[timeprop.SingleTimeP] = [] # 初始时间命题列表
        self._all_props: list[timeprop.TimeP] = [] # 全部命题总表
        self._all_groups: list[list[int]] = [] # 全部命题组合索引表
        self._statements: list[str] = [] # 一个命题组合的陈述
        self._question: dict[str, Any] = [] # 问题和答案

    def add_events(self, *events: event.Event) -> None:
        """添加事件

        Args:
            events (Event): 待添加的事件
        """
        assert all([isinstance(i, event.Event) for i in events]), "事件列表必须为事件"
        assert all([not isinstance(i, (event.SubEvent, event.Duration)) for i in events]), "事件列表不能为子事件或持续时间"
        self.event_list.extend(events) # 将事件加入到事件列表中
        self._init_props.extend([timeprop.SingleTimeP.build(i) for i in events]) # 将事件转化为初始时间命题

    def get_all_props(self) -> None:
        """获得场景的全部命题"""
        assert len(self.event_list) >= 2, "事件数量必须大于等于2"
        print("开始生成全部命题！")
        curr_props = deepcopy(self._init_props) # 将初始时间命题加入到总表中
        # curr_props.extend(reduce(lambda x, y: x + y, [i.get_child_props() for i in self._init_props])) # 将初始命题的子命题加入到总表中
        rm = RM(curr_props, self.relation_list, self.rule_list) # 利用推理机做推理
        self._all_props = rm.run()
        print(f"全部命题生成完毕！共获得命题{len(self._all_props)}个")
    
    def get_all_groups(self) -> None:
        """调用搜索机，扩圈以发现可行的陈述命题组合"""
        assert len(self._all_props) > 0, "必须先生成全部命题"
        print("开始扩圈！")
        sm = SM(self._init_props, self._all_props, self.relation_list, self.rule_list)
        self._all_groups = sm.run()
        print(f"扩圈完毕！共获得命题组合{len(self._all_groups)}个")

    def get_statements(self, seed: Union[int, float, None] = None) -> list[str]:
        """获取一组命题组合的全部陈述

        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.

        Returns:
            list[str]: 一组命题组合的全部陈述
        """
        assert len(self._all_groups) > 0, "必须先获取可以表述全部情形的命题组合"
        random.seed(seed)
        idxs = random.choice(self._all_groups) # 选择一组命题
        self._statements = [self._all_props[i].state(self.temps) for i in idxs]
        print("随机选择一组命题，得到其陈述.")
        return self._statements

    def get_question(self, seed: Union[int, float, None] = None) -> None | dict[str, Any]:
        """获取问题和答案

        Args:
            seed (Union[int, float, None], optional): 随机种子. 默认为None.

        Returns:
            None | dict[str, Any]: 问题和答案
        """
        assert len(self._all_groups) > 0, "必须先获取可以表述全部情形的命题组合"
        random.seed(seed)
        print("开始获取题目！")
        answer_machine = TAM(self._all_props, self.temps, seed)
        print("获取题目完成！")
        return answer_machine.run()

    def run(self, execute: int = 10, seed: Union[int, float, None] = None) -> list[dict[str, Any]]:
        self.get_all_props()
        self.get_all_groups()
        self.get_statements(seed)
        question_list = []
        for _ in range(execute):
            if (info := self.get_question(seed)) is not None:
                question_list.append(info)
        print(f"获取题目{execute}次，获得题目{len(question_list)}个.")
        return [{"guide": self.guide, "statement": "\n".join(self._statements)} | i for i in question_list]

class LineScene(TimeScene):
    def __init__(self, scale: ts.TimeScale, guide: str = "") -> None:
        super().__init__(scale, guide)

class LoopScene(TimeScene):
    pass