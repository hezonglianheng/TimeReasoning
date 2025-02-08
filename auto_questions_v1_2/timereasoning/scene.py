# encoding: utf8
# date: 2024-08-27
# author: Qin Yuhang

from pycnnum import num2cn # 引入中文数字转换库
import re
from copy import deepcopy
from typing import Any, Dict, Optional, Union, Literal
import sys
from pathlib import Path
import random
import calendar
from itertools import product

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition import prop, relation, machines
from timereasoning import timeprop, timerule, timerelation, event
from timereasoning import timescale as ts
from proposition.scene import Scene
from timereasoning import timeknoledge # 10-30修改：开始引入时间常识库
from timereasoning.machines import SearchMachine as SM # 11-03修改：引入时间领域专用搜索机
from proposition.machines import ReasonMachine as RM # 11-03修改：引入推理机构建推理图
from timereasoning.machines import TimeGetRangeMachine as TGRM # 11-26修改：引入时间领域专用取值范围机
from timereasoning.machines import TimeAskAllMachine as TAAM # 11-27修改：引入时间领域专用询问机
# 1-22新增：引入时间领域config文件
import timereasoning.config

LOOP_LIMIT = 1 # 循环时间场景的循环长度上限

class TimeScene(Scene):
    """
    时间场景
    """
    def __init__(self, scale: ts.TimeScale | int, guide: str = "", *, ask_mode: Literal['random', 'deepest', 'tag'] = 'random', tag: Optional[list[str]] = None, lang: str = "zh") -> None:
        """初始化时间场景

        Args:
            scale (ts.TimeScale | int): 时间尺度
            guide (str, optional): 引导语. 默认为"".
            ask_mode (Literal['random', 'deepest'], optional): 提问模式. 默认为'random'.可选的值有：
                - 'random'，即随机提问. 
                - 'deepest'，优先提问最深层的命题.
                - 'tag'，根据命题的标签进行提问，该模式需要传入tag参数(一个标签列表).
            tag (Optional[list[str]], optional): 提问标签. 默认为None.
            lang (str, optional): 语言. 默认为"zh"(简体中文).
        """
        # 需要使用的属性
        super().__init__(guide, ask_mode=ask_mode, tag=tag, lang=lang)
        self.scale = scale if isinstance(scale, ts.TimeScale) else ts.TimeScale(scale) # 时间尺度
        self.events: list[event.Event] = [] # 事件列表
        self.relations = deepcopy(timerelation.RELATIONS) # 关系列表
        self.rules = deepcopy(timerule.RULES) # 规则列表
        # 11-25修改：增加语言变量
        self.temps = ts.choose_templates(scale, lang=lang) # 模板字典
        # 命题收集变量（为了安全性需要重新定义）
        self._init_props: list[timeprop.TimeP] = []
        self._all_props: list[timeprop.TimeP] = []
        self._all_groups: list[list[int]] = []
        self._statements: list[str] = []
        self._asked_prop: timeprop.TimeP = None
        self._ask_info: dict[str, Any] = {}
        self._value_range: dict[str, list[Any]] = dict()

    def add_events(self, *events: event.Event) -> None:
        """添加事件

        Args:
            events (Event): 待添加的事件
        """
        assert all([isinstance(i, event.Event) for i in events]), "事件列表必须为事件"
        assert all([not isinstance(i, (event.SubEvent, event.Duration)) for i in events]), "事件列表不能为子事件或持续时间"
        self.events.extend(events) # 将事件加入到事件列表中
        self._init_props.extend([timeprop.SingleTimeP.build(i) for i in events]) # 将事件转化为初始时间命题

    def add_knowledge(self, number: int = 5, seed: Union[int, float, None] = None, file_path: Union[str, Path, None] = None) -> None:
        """添加时间常识

        Args:
            number (int, optional): 添加的常识数量. 默认为5.
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            file_path (Union[str, Path, None], optional): 常识文件路径. 默认为None(按照时间尺度抽取默认知识).
        """
        super().add_knowledge(number, seed)
        # 11-07修改：增加传入独有时间常识的接口
        if file_path is not None:
            know_list = timeknoledge.read_knowledge_base(file_path)
        else:
            know_list = timeknoledge.get_knowledge_base(self.scale)
        chosen_know = random.sample(know_list, number) if number < len(know_list) else know_list
        print(f"实际添加时间常识{len(chosen_know)}个.")
        for k in chosen_know: # 遍历所有的时间常识
            if isinstance(k, timeknoledge.EventKnowledge): # 如果是事件常识
                self._knowledges.append(k.use()) # 将事件转化为时间命题
                # 1-20新增：记录知识难度
                self._knowledge_difficulties += k.difficulty
            else:
                pass # 其他类型的常识暂不处理，后续可以添加
    
    def reset(self):
        """清空场景中的事件、初始化命题和知识命题"""
        self.events.clear()
        # 12-24修改：调用父类的reset方法
        super().reset()
    
    def _exp_trans(self, exp: str) -> str:
        """调整时间表达方式

        Args:
            exp (str): 时间表达

        Returns:
            str: 调整后的时间表达
        """
        if self.scale == ts.TimeScale.Weekday and self.lang == "zh": # 如果是星期尺度，可以做一些特殊的处理
            search1 = re.search(r"星期[0-9]", exp)
            if search1 is not None:
                ch_num = num2cn(search1.group()[-1])
                ch_num = "天" if (ch_num == "零" or ch_num == "七") else ch_num # 将0转化为“天”
                exp = exp.replace(search1.group(), "星期" + ch_num)
            search2 = re.search(r"周[0-9]", exp)
            if search2 is not None:
                ch_num = num2cn(search2.group()[-1])
                ch_num = "日" if (ch_num == "零" or ch_num == "七") else ch_num
                exp = exp.replace(search2.group(), "周" + ch_num)
        elif self.scale == ts.TimeScale.Weekday and self.lang == "en":
            search = re.search(r"(weekday) ([0-9])", exp)
            if search is not None:
                num = int(search.group()[-1])
                exp = exp.replace(search.group(), calendar.day_name[num-1])
            # 将问题中的weekday_中的weekday去掉
            exp = exp.replace("weekday ", " ")
        elif self.scale == ts.TimeScale.Month and self.lang == "en":
            search = re.findall(r"(month) ([0-9]{1,2})", exp)
            if search is not None:
                # 获取月份数字
                for result in search:
                    num = int(result[-1])
                    # 获取月份名称
                    exp = exp.replace(result[-1], calendar.month_name[num])
            exp = exp.replace("month ", "")
        return exp
    
    def _statement_trans(self):
        """
        调整语句中的时间表达方式\n
        例如，将星期几的数字转化为中文
        """
        if self.scale == ts.TimeScale.Weekday: # 如果是星期尺度，可以做一些特殊的处理
            for n in range(len(self._statements)):
                self._statements[n] = self._exp_trans(self._statements[n])
        elif self.scale == ts.TimeScale.Month: # 月份的转换处理
            for n in range(len(self._statements)):
                self._statements[n] = self._exp_trans(self._statements[n])
        else:
            pass

    # 11-03修改：在时间领域重载获取全部命题的方法
    def get_all_groups(self) -> None:
        assert len(self._all_props) > 0, "必须先生成全部命题"
        print("开始搜索一组可行的命题组合.")
        sm = SM(self.events, self._all_props, self._knowledges)
        self._chosen_group = sm.run()
        print(f"命题组合搜索结束.")
        print(f"获取推理图.")
        rm = RM(deepcopy(self._chosen_group), self.relations, self.rules, deepcopy(self._knowledges), graph_construct=True)
        self._reachables = rm.run() # 11-12修改: 将建立推理图得到的命题加入可达命题列表
        self.graph = rm.graph
        print(f"推理图获取完毕.")
        
    # 12-14新增：将初始化范围获取机和询问机和获取可及命题的函数分开
    def get_preparations(self):
        # 以可及命题中的单元素时间命题为基础，构建时间领域专用取值范围机
        self._range_machine = TGRM([i.element for i in self._reachables if isinstance(i, timeprop.SingleTimeP)])
        print("初始化选取干扰项的范围获取机.")
        # 1-22新增：调整正确选项数量
        nums: list[int] = list(timereasoning.config.ANSWER_NUM_WEIGHT.keys())
        weights: list[float] = list(timereasoning.config.ANSWER_NUM_WEIGHT.values())
        correct_num = random.choices(nums, weights=weights, k=1)[0]
        self._ask_all_machine = TAAM(deepcopy(self._reachables), deepcopy(self._chosen_group), self.temps, self.graph, self._range_machine, ask_correct=self._ask_correct, lang=self.lang, ask_mode=self.ask_mode, tag=self.tag, correct=correct_num)
        print("初始化询问机.")

    def get_statements(self) -> list[str]:
        super().get_statements()
        self._statement_trans()
        return self._statements
    
    def ask_one(self, seed: int | float | None = None) -> Dict[str, Any]:
        info = super().ask_one(seed)
        if info is None:
            return None
        info[prop.SENTENCE] = self._exp_trans(info[prop.SENTENCE]) # 调整问题中的时间表达方式
        # all_elements = [i.element for i in self._all_props if isinstance(i, timeprop.SingleTimeP)]
        """
        all_elements = [i.element for i in self._reachables if isinstance(i, timeprop.SingleTimeP)]
        if "element" in (typ := info.get(prop.TYPE)):
            ans = info.get(prop.ANSWER)
            if isinstance(ans, (event.TemporalEvent, event.DurativeEvent, event.FreqEvent)):
                self._value_range[typ] = [i for i in all_elements if isinstance(i, (event.TemporalEvent, event.DurativeEvent, event.FreqEvent))]
            elif isinstance(ans, event.Duration):
                self._value_range[typ] = [i for i in all_elements if isinstance(i, (event.Duration, event.TemporalEvent, event.FreqEvent))]
            else:
                raise ValueError(f"未知类型{type(ans)}")
        elif "time" in typ:
            all_temp = sorted([i.time for i in all_elements if isinstance(i, (event.TemporalEvent))], key=lambda x: x)
            self._value_range[typ] = list(range(all_temp[0], all_temp[-1] + 1))
        elif typ == "duration":
            all_temp = sorted([i.time for i in all_elements if isinstance(i, (event.TemporalEvent))], key=lambda x: x)
            self._value_range[typ] = list(range(all_temp[-1] - all_temp[0] + 1))
        elif typ == "diff":
            all_temp = sorted([i.time for i in all_elements if isinstance(i, (event.TemporalEvent))], key=lambda x: x)
            self._value_range[typ] = list(range(all_temp[-1] - all_temp[0] + 1))
        """
        return info

    def get_answers(self, seed: int | float | None = None, options: int = 4, all_wrong_prob: float = 0.1) -> Dict[str, Any] | None:
        answer_info = super().get_answers(seed, options, all_wrong_prob)
        # 12-16新增：如果answer_info是None，则返回None
        if answer_info is None:
            return None
        if "time" in (typ := self._ask_info.get(prop.TYPE)):
            if self.scale == ts.TimeScale.Weekday and self.lang == "zh":
                for k, v in answer_info[machines.OPTIONS].items():
                    # 11-30更新：为防止“以上选项均不正确”报错，加入try-except结构排错
                    try:
                        num = int(v)
                    except ValueError:
                        continue
                    zh_num = num2cn(v)
                    zh_num = "日" if zh_num == "零" else zh_num
                    answer_info[machines.OPTIONS][k] = zh_num
            elif self.scale == ts.TimeScale.Weekday and self.lang == "en":
                for k, v in answer_info[machines.OPTIONS].items():
                    # 11-30更新：为防止“以上选项均不正确”报错，加入try-except结构排错
                    try:
                        num = int(v)
                    except ValueError:
                        continue
                    answer_info[machines.OPTIONS][k] = calendar.day_name[int(v)-1]
            elif self.scale == ts.TimeScale.Month and self.lang == "en":
                for k, v in answer_info[machines.OPTIONS].items():
                    # 11-30更新：为防止“以上选项均不正确”报错，加入try-except结构排错
                    try:
                        num = int(v)
                    except ValueError:
                        continue
                    answer_info[machines.OPTIONS][k] = calendar.month_name[int(v)]
        return answer_info

    def ask_all(self, seed: int | float | None = None) -> Dict[str, Any]:
        info = super().ask_all(seed)
        if info is None:
            return None
        info[machines.QUESTION] = self._exp_trans(info[machines.QUESTION]) # 调整问题中的时间表达方式
        info[machines.CHOICES] = {k: self._exp_trans(v) for k, v in info[machines.CHOICES].items()} # 调整选项中的时间表达方式
        return info

class LineScene(TimeScene):
    """
    线性时间场景
    """
    def __init__(self, scale: ts.TimeScale | int, guide: str = "", *, ask_mode: Literal['random', 'deepest', 'tag'] = 'random', tag: Optional[list[str]] = None, lang: str = "zh") -> None:
        """初始化线性时间场景

        Args:
            scale (ts.TimeScale | int): 时间尺度
            guide (str, optional): 引导语. 默认为空字符串.
            ask_mode (Literal['random', 'deepest'], optional): 提问模式. 默认为'random'.可选的值有：
                - 'random'，即随机提问. 
                - 'deepest'，优先提问最深层的命题.
                - 'tag'，根据命题的标签进行提问，该模式需要传入tag参数(一个标签列表).
            tag (Optional[list[str]], optional): 提问标签. 默认为None.
            lang (str, optional): 语言. 默认为"zh"(简体中文).
        """
        super().__init__(scale, guide, ask_mode=ask_mode, tag=tag, lang=lang)

    @property
    def scene_type(self) -> str:
        return "线性时间场景"

class LoopScene(TimeScene):
    """
    循环时间场景
    """
    # 11-30新增：场景难度评级
    # 1-29修订：将场景难度评级从0.2增加为0.4
    # 移动到__init__内部
    # scene_level: float = 0.4
    
    def __init__(self, scale: ts.TimeScale | int, guide: str = "", loop: Optional[int] = None, *, ask_mode: Literal['random', 'deepest', 'tag'] = 'random', tag: Optional[list[str]] = None, lang: str = "zh") -> None:
        """初始化循环时间场景

        Args:
            scale (ts.TimeScale | int): 时间尺度
            guide (str, optional): 引导语. 默认为空字符串.
            loop (Optional[int], optional): 循环长度. 默认为None.
            ask_mode (Literal['random', 'deepest'], optional): 提问模式. 默认为'random'.可选的值有：
                - 'random'，即随机提问. 
                - 'deepest'，优先提问最深层的命题.
                - 'tag'，根据命题的标签进行提问，该模式需要传入tag参数(一个标签列表).
            tag (Optional[list[str]], optional): 提问标签. 默认为None.
            lang (str, optional): 语言. 默认为"zh"(简体中文).
        """
        super().__init__(scale, guide, ask_mode=ask_mode, tag=tag, lang=lang)
        self.loop = ts.get_loop_param(scale) if loop is None else loop
        assert self.loop is not None, "未知的循环长度"
        new_relations = list(map(lambda x: x.set_loop(self.loop), [LoopRelation, PeriodRelation, DiffRelation]))
        self.relations.extend(new_relations) # 添加特有的关系
        self.rules.remove(timerule.BeforeandGap)
        self.rules.remove(timerule.AfterandGap) # 移除不适用的规则
        self.scene_level = .5 # 场景难度评级为0.5
    
    def get_all_props(self) -> None:
        super().get_all_props()
        self._arrange_props('all')

    def get_all_groups(self) -> None:
        super().get_all_groups()
        self._arrange_props('reachable')

    def _arrange_props(self, mode: Literal['all', 'reachable']):
        """获得一组命题之后，整理命题

        Args:
            mode (Literal[&#39;all&#39;, &#39;reachable&#39;]): 整理的命题组类型
                - 'all'，整理第一次推理得到的全部命题
                - 'reachable'，整理推理图得到的可达命题

        Raises:
            ValueError: 未知的模式
        """
        if mode == 'all':
            all_props = self._all_props
        elif mode == 'reachable':
            all_props = self._reachables
        else:
            raise ValueError(f"未知的模式{mode}")
        for i in all_props:
            if isinstance(i, timeprop.TemporalP):
                i.time = i.time % self.loop
            elif isinstance(i, (timeprop.BeforeTimeP, timeprop.AfterTimeP, timeprop.GapTimeP)):
                i.diff = i.diff % self.loop
        new_list: list[timeprop.TimeP] = list()
        for i in range(len(all_props)):
            if all_props[i].got(all_props[:i]):
                continue
            elif isinstance(all_props[i], (timeprop.BeforeP, timeprop.AfterP, timeprop.LongP, timeprop.ShortP)):
                continue
            elif isinstance(all_props[i], (timeprop.BeforeTimeP, timeprop.AfterTimeP, timeprop.GapTimeP)) and all_props[i].diff == 0:
                continue
            else:
                new_list.append(all_props[i])
        if mode == 'all':
            self._all_props = new_list
        elif mode == 'reachable':
            self._reachables = new_list
        print(f"调整后有命题{len(new_list)}个.")

    @property
    def scene_type(self) -> str:
        return "循环时间场景"

class PeriodRelation(relation.SingleEntailment):
    """表示时间点的周期性关系，属于单元蕴含关系"""
    loop = 0
    _tp_tuples = [(timeprop.TemporalP, timeprop.TemporalP)]

    @classmethod
    def reason(cls, input_prop: timeprop.TemporalP) -> list[timeprop.TemporalP] | None:
        if not isinstance(input_prop, timeprop.TemporalP):
            return None
        res = super().reason(input_prop)
        if res is None:
            return None
        else:
            for i in res:
                i.time = i.time % cls.loop
            return res

    @classmethod
    def set_loop(cls, loop: int) -> type["PeriodRelation"]:
        """设置周期长度"""
        cls.loop = loop
        return cls

class DiffRelation(relation.DoubleEntailment):
    """表示时间差的周期性关系，属于双元蕴含关系"""
    loop = 0
    _tp_tuples = [(timeprop.BeforeTimeP, timeprop.BeforeTimeP), (timeprop.AfterTimeP, timeprop.AfterTimeP), (timeprop.GapTimeP, timeprop.GapTimeP)]

    @classmethod
    def reason(cls, input_prop: timeprop.DoubleTimeP) -> list[timeprop.DoubleTimeP] | None:
        global LOOP_LIMIT
        if not isinstance(input_prop, (timeprop.BeforeTimeP, timeprop.AfterTimeP, timeprop.GapTimeP)):
            return None
        res = super().reason(input_prop)
        if res is None:
            return None
        else:
            for i in res:
                i.diff = i.diff % cls.loop
            # 1-21移除：移除循环时间场景的循环时间上限决定的命题
            """
            new_res: timeprop.DoubleTimeP = []
            for i, t in product(res, range(1, LOOP_LIMIT)):
                j = deepcopy(i)
                j.diff = i.diff + t * cls.loop
                new_res.append(j)
            """
            return res
            # return res + new_res
        
    @classmethod
    def set_loop(cls, loop: int) -> type["DiffRelation"]:
        """设置周期长度"""
        cls.loop = loop
        return cls
    
class LoopRelation(relation.DoubleEntailment):
    """循环关系，用于处理先后关系的循环性质"""
    loop = 0
    _tp_tuples = [(timeprop.BeforeTimeP, timeprop.AfterTimeP), (timeprop.AfterTimeP, timeprop.BeforeTimeP)]

    @classmethod
    def reason(cls, prop: timeprop.BeforeTimeP | timeprop.AfterTimeP) -> list[timeprop.BeforeTimeP | timeprop.AfterTimeP] | None:
        if not isinstance(prop, (timeprop.BeforeTimeP, timeprop.AfterTimeP)):
            return None
        res = super().reason(prop)
        if res is None:
            return None
        else:
            for i in res:
                i.diff = (cls.loop - prop.diff) % cls.loop
                # 1-25修改：命题难度改为+2.0
                i.difficulty += 2.0
            return res

    @classmethod
    def set_loop(cls, loop: int) -> type["LoopRelation"]:
        """设置周期长度"""
        cls.loop = loop
        return cls