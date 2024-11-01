# encoding: utf8
# date: 2024-08-28
# author: Qin Yuhang

"""
包含推理机类、搜索机类，用于执行推理任务
"""

from tqdm import tqdm
import random
from string import ascii_uppercase
from warnings import warn
from itertools import product, permutations
from functools import reduce
from typing import List, Union, Any
from copy import deepcopy
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import os

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition import prop, rule, relation
from proposition.config import PRECISE_WEIGHT, NOT_PRECISE_WEIGHT

OPTIONS = "options"
ANSWERS = "answers"

class ReasonMachine:
    """推理机，用于执行推理任务"""
    def __init__(self, init_props: list[prop.Proposition], relations: list[type[relation.Relation]], rules: list[type[rule.Rule]], knowledges: list[prop.Proposition] = []) -> None:
        """初始化推理机

        Args:
            init_props (list[Proposition]): 初始命题列表
            relations (list[type[Relation]]): 关系列表
            rules (list[type[Rule]]): 规则列表
            knowledges (list[Proposition], optional): 已知命题列表. 默认为空.
        """
        self.init_props = init_props # 初始命题列表
        self.relations = relations # 关系列表
        self.rules = rules # 规则列表
        # 中间变量
        self.old_props: list[prop.Proposition] = knowledges
        self.curr_props: list[prop.Proposition] = []
        self.new_props: list[prop.Proposition] = []

    def _reason_by_relation(self) -> list[prop.Proposition]:
        """根据关系，从现有命题推理

        Returns:
            list[Proposition]: 新生成的命题列表
        """
        # 从现有命题推理，得到新命题列表的列表
        prop_lists: List[List[prop.Proposition]] = [new_p for p, r in product(self.curr_props, self.relations) if (new_p := r.reason(p)) is not None]
        # 将新命题列表的列表合并为一个新命题列表
        if len(prop_lists) == 0:
            return []
        else:
            return reduce(lambda x, y: x + y, prop_lists)
    
    def _reason_by_rule(self) -> list[prop.Proposition]:
        """根据规则，从现有命题-(现有命题+旧命题)推理

        Args:
            prop_list (list[Proposition]): 待推理的命题列表

        Returns:
            list[Proposition]: 新生成的命题列表
        """
        return [new_p for (p1, p2), r in product(permutations(self.curr_props + self.old_props, r=2), self.rules) if (new_p := r.reason(p1, p2)) is not None]
    
    def run(self) -> list[prop.Proposition]:
        """运行推理机，获得能够推出的最大命题

        Returns:
            list[prop.Proposition]: 能够推出的最大命题
        """
        assert len(self.init_props) > 0, "初始命题列表不能为空"
        self.curr_props = deepcopy(self.init_props) # 将初始命题列表复制到当前命题列表中
        count = 0
        while True:
            count += 1
            self.new_props.clear() # 清空新命题列表
            by_relations = self._reason_by_relation() # 用关系推理
            by_rules = self._reason_by_rule() # 用规则推理
            # 对新命题的去重和加入
            for p in by_relations + by_rules:
                if all([p != i for i in self.new_props]):
                    self.new_props.append(p)
            # 将当前命题加入旧命题并去重
            self.old_props.extend([i for i in self.curr_props if not i.got(self.old_props)])
            # 检查新命题是否都出现在旧命题中
            if len(new_props := [i for i in self.new_props if not i.got(self.old_props)]) == 0:
                return self.old_props
            # 否则当前命题变更为新命题
            self.curr_props = new_props

# TODO: 优化搜索机，减少搜索时间
class SearchMachine:
    """
    搜索机，用于搜索可以推出原始命题的命题组合\n
    该搜索机使用了多进程，可以在一定程度上减少搜索时间
    """
    def __init__(self, init_props: list[prop.Proposition], all_props: list[prop.Proposition], relations: list[type[relation.Relation]], rules: list[type[rule.Rule]], knowledges: list[prop.Proposition] = []) -> None:
        """初始化搜索机

        Args:
            init_props (list[prop.Proposition]): 初始命题列表
            all_props (list[prop.Proposition]): 全部命题列表
            relations (list[type[relation.Relation]]): 关系列表
            rules (list[type[rule.Rule]]): 规则列表
        """
        self.init_props = init_props # 初始命题列表
        self.all_props = all_props # 全部命题列表
        self.relations = relations
        self.rules = rules
        self.knowledges = knowledges
        self._new_prop: prop.Proposition = None # 选择的新命题
        self.chosen_props: List[prop.Proposition] = [] # 已经选择的命题
        self.contained_props: List[prop.Proposition] = [] # 由已经选择的命题推出的全部命题
        # 新增：命题数量上限，默认值为init_props数量的两倍
        self._upper_limit = len(init_props) * 2

    def _lessen_chosen_props(self) -> None:
        """减少已选命题列表，去除已经包含的命题"""
        warn("函数SearchMachine._lessen_chosen_props()已经弃用", DeprecationWarning)
        reasoned: list[bool] = [False] * len(self.chosen_props)
        for i, prop_ in tqdm(enumerate(self.chosen_props), desc="减少已选命题列表", total=len(self.chosen_props)):
            rest_props = self.chosen_props[:i] + self.chosen_props[i + 1:]
            rm = ReasonMachine(rest_props, self.relations, self.rules)
            res = rm.run()
            reasoned[i] = prop_.got(res)
        if all(reasoned):
            self.chosen_props = self.chosen_props[:-1] # 如果所有命题都已经包含，则去除最后一个
            return None
        self.chosen_props = [i for i, j in zip(self.chosen_props, reasoned) if not j]
    
    def _random_choose(self, candidate: list[prop.Proposition]) -> None:
        """随机选择一个新命题，使用精确/非精确命题权重

        Args:
            candidate (list[prop.Proposition]): 候选命题列表
        """
        weight = [PRECISE_WEIGHT if i.precise else NOT_PRECISE_WEIGHT for i in candidate]
        self._new_prop = random.choices(candidate, weights=weight)[0]
    
    def _check(self) -> None:
        """
        检查函数，用于减少已选命题数量
        """
        self.chosen_props.append(self._new_prop)
        reasoned: list[bool] = [False] * len(self.chosen_props)
        size: list[int] = [0] * len(self.chosen_props) # 记录推理结果范围广度
        
        # 检查命题
        print("运行命题推出性检查...")
        def process_reason(index: int):
            """判断命题能否由其他命题推出

            Args:
                index (int): 待判断命题的索引值
            """
            curr = self.chosen_props[index] # 待检查命题
            excluded = [x for i, x in enumerate(self.chosen_props) if i != index] # 其他命题
            reason_machine = ReasonMachine(excluded, self.relations, self.rules, deepcopy(self.knowledges)) # 建立推理器
            res = reason_machine.run() # 运行推理器
            # 记录广度
            size[index] = len(res)
            # 记录判断
            if curr.got(res):
                reasoned[index] = True

        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            executor.map(process_reason, range(len(self.chosen_props)))
        
        # 更新已选命题
        self.chosen_props = [i for i, j in zip(self.chosen_props, reasoned) if not j] # 去除已经推理的命题
        print(f"检查后已选命题有{len(self.chosen_props)}个")
        if len(self.chosen_props) > self._upper_limit: # 超过上限时以推理最广的组合为基础调整已选命题数量
            print(f"由于已选命题数量超过上限，调整为{self._upper_limit}个.")
            max_num = max(size)
            max_index = size.index(max_num)
            self.chosen_props = [x for i, x in enumerate(self.chosen_props) if i != max_index]
        
    def _reason(self):
        """推理函数，使用增量推理方式增加命题覆盖范围"""
        print("根据已选命题运行推理...")
        reason_machine = ReasonMachine(self.chosen_props, self.relations, self.rules, deepcopy(self.knowledges))
        self.contained_props = reason_machine.run()
    
    def run(self) -> List[prop.Proposition]:
        """运行搜索机，搜索可以推出原始命题的命题组合

        Raises:
            ValueError: 如果检索发现已经没有可选的命题了，则抛出异常

        Returns:
            List[prop.Proposition]: 可以推出原始命题的命题组合
        """
        i = 0
        while True:
            # if len(candidate_props := [i for i in self.all_props if not i.got(self.chosen_props)]) == 0:
            if len(candidate_props := [i for i in self.all_props if not i.got(self.contained_props)]) == 0:
                raise ValueError("已经没有可选的命题了")
            print(f"第{(i := i + 1)}次搜索，已选命题数量为{len(self.chosen_props)}")
            # self._new_prop = random.choice(candidate_props) # 随机选择一个新命题
            self._random_choose(candidate_props) # 随机选择一个新命题
            # self.chosen_props.append(new_prop)
            '''
            if len(self.chosen_props) > 1:
                self._lessen_chosen_props()
            rm = ReasonMachine(self.chosen_props, self.relations, self.rules)
            self.contained_props = rm.run()
            '''
            self._check() # 检查命题，减少可行命题组合中命题数量
            if self._new_prop.got(self.chosen_props): # 新增命题存在于已选命题中
                self._reason() # 增量式推理
                if all([i.contained(self.contained_props) for i in self.init_props]):
                    print(f"已经找到可行的命题组合，共{len(self.chosen_props)}个命题")
                    return self.chosen_props
            else: # 新增命题不存在于已选择命题中
                print("新增命题可以被推出，继续推理.")

class AnswerMachine:
    """
    答案机，用于根据询问命题和信息生成选项和答案
    """
    def __init__(self, all_prop: list[prop.Proposition], ask_prop: prop.Proposition, ask_info: dict[str, Any], seed: Union[int, float, None] = None, options: int = 4, all_wrong_prob: float = .1) -> None:
        """初始化答案机，用于根据询问命题和信息生成选项和答案

        Args:
            all_prop (list[prop.Proposition]): 全部命题
            ask_prop (prop.Proposition): 被询问的命题
            ask_info (dict[str, Any]): 询问后获得的信息
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            options (int, optional): 选项数量. 默认为4.
            all_wrong_prob (float, optional): 设置“全部错误”的概率. 默认为.1.
        """
        self._all_prop = all_prop # 全部命题
        self._ask_prop = ask_prop # 被询问的命题
        self._ask_info = ask_info # 询问信息
        self._value_range: dict[str, list[Any]] = dict()
        self._seed = seed
        if options > len(ascii_uppercase):
            warn(f"选项数量{options}大于26，将被重置为26", UserWarning)
            options = len(ascii_uppercase)
        self._options = options
        self._all_wrong_prob = all_wrong_prob # 全部错误的概率
        self.options_and_answers: dict[str, Any] = dict()

    def set_value_range(self, key: str, value: list[Any]) -> None:
        """为一个可询问的属性设置值域，值域需要被调用用于生成选项

        Args:
            key (str): 需要询问并设置值域的属性
            value (list[Any]): 值域
        """
        value = [i for i in value if i != self._ask_info[prop.ANSWER]]
        self._value_range[key] = value

    def run(self) -> dict[str, Any]:
        """运行答案机，生成选项和答案

        Returns:
            dict[str, Any]: 选项和答案
        """
        # 获取询问属性
        qtype = self._ask_info[prop.TYPE]
        option_situation_tuples: list[tuple[Any, bool]] = [(self._ask_info[prop.ANSWER], True)]
        # 10-31修改：改用try-except结构捕捉错误
        try:
            getattr(self._ask_prop, qtype)
        except AttributeError:
            raise AttributeError(f"被询问的命题{type(self._ask_prop)}中没有属性{qtype}")
        else:
            pass
        # assert getattr(self._ask_prop, qtype), f"被询问的命题{type(self._ask_prop)}中没有属性{qtype}"
        # 挑选候选项
        if (candidates := self._value_range.get(qtype)) is None:
            print(f"未找到属性{qtype}的值域，无法生成选项！")
            return None
        elif len(candidates) < self._options - 1:
            print(f"被询问的命题{type(self._ask_prop)}属性{qtype}的候选项数量不足，无法生成选项！")
            return None
        random.seed(self._seed) # 设置随机种子
        chosen_candidate = random.sample(candidates, self._options - 1)
        # 确定候选项是否正确
        for i in chosen_candidate:
            new_prop = deepcopy(self._ask_prop)
            setattr(new_prop, qtype, i)
            if new_prop.got(self._all_prop):
                option_situation_tuples.append((i, True))
            else:
                option_situation_tuples.append((i, False))
        # 随机打乱选项，生成选项和答案
        random.shuffle(option_situation_tuples)
        options: dict[str, str] = dict()
        answers: list[str] = list()
        for i, (opt, judge) in enumerate(option_situation_tuples):
            options[ascii_uppercase[i]] = str(opt)
            if judge:
                answers.append(ascii_uppercase[i])
        # 设置“以上选项均不正确”选项
        if random.random() < self._all_wrong_prob:
            options[ascii_uppercase[self._options - 1]] = "以上选项均不正确"
            if len(answers) > 1 and ascii_uppercase[self._options - 1] in answers:
                answers.remove(ascii_uppercase[self._options - 1])
        # 返回最终结果
        self.options_and_answers = {OPTIONS: options, ANSWERS: answers}
        return self.options_and_answers