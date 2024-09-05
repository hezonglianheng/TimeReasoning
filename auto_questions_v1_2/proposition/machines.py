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
import multiprocessing as mp
from itertools import product, permutations
from functools import reduce, cache
from typing import List, Sequence, Union, Any
from copy import deepcopy
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition import prop, rule, relation

OPTIONS = "options"
ANSWERS = "answers"

class ReasonMachine:
    """推理机，用于执行推理任务"""
    def __init__(self, init_props: list[prop.Proposition], relations: list[type[relation.Relation]], rules: list[type[rule.Rule]]) -> None:
        """初始化推理机

        Args:
            init_props (list[Proposition]): 初始命题列表
            relations (list[type[Relation]]): 关系列表
            rules (list[type[Rule]]): 规则列表
        """
        self.init_props = init_props # 初始命题列表
        self.relations = relations # 关系列表
        self.rules = rules # 规则列表
        # 中间变量
        self.old_props: list[prop.Proposition] = []
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

class SearchMachine:
    """
    搜索机，用于搜索可以推出原始命题的命题组合\n
    该搜索机使用了扩圈思想、剪枝算法、多进程，可以在一定程度上减少搜索时间
    """
    def __init__(self, init_props: list[prop.Proposition], all_props: list[prop.Proposition], relations: list[type[relation.Relation]], rules: list[type[rule.Rule]], limit: int | None = None) -> None:
        """初始化搜索机

        Args:
            init_props (list[prop.Proposition]): 初始命题列表
            all_props (list[prop.Proposition]): 全部命题列表
            relations (list[type[relation.Relation]]): 关系列表
            rules (list[type[rule.Rule]]): 规则列表
            limit (int | None): 最大搜索长度，None表示以初始命题列表长度的2倍为上限. 默认为None.
        """
        self.init_props = init_props # 初始命题列表
        self.all_props = all_props # 全部命题列表
        self.relations = relations
        self.rules = rules
        self.limit = limit if limit is not None else sum([i.num_of_conditions for i in init_props])
        self.index_list: List[List[int]] = []

    @cache
    def _run(self, indexes: str) -> bool:
        """判断一组命题能否推出全部命题

        Args:
            indexes (str): 命题索引

        Returns:
            bool: 是否可以推出全部命题
        """
        indexes_list: List[int] = [int(i) for i in indexes.split()]
        prop_list: List[prop.Proposition] = [self.all_props[i] for i in indexes_list]
        rm = ReasonMachine(prop_list, self.relations, self.rules)
        res = rm.run()
        if all([i.contained(res) for i in self.init_props]):
            return True
        return False
    
    def _be_contained(self, indexes: Sequence[int]) -> bool:
        """判断当前命题组合是否包含一个已经存在的命题组合

        Args:
            indexes (Sequence[int]): 命题索引

        Returns:
            bool: 当前命题组合是否包含一个已经存在的命题组合
        """
        for lst in self.index_list:
            if all([i in indexes for i in lst]):
                return True # 如果存在一个命题组合是当前命题组合的子集，则返回True
        return False # 否则返回False
    
    def run(self) -> List[List[int]]:
        """运行搜索机，获得所有可以推出原始命题的命题组合索引

        Returns:
            List[List[int]]: 所有可以推出原始命题的命题组合索引
        """
        all_indexes: List[int] = [i for i in range(len(self.all_props))]
        basic_indexes: List[List[int]] = [[i] for i in range(len(self.init_props))]
        for n in range(2, self.limit + 1):
            sub_indexes: List[List[int]] = []
            for lst in basic_indexes:
                sub_indexes.extend([lst + [i] for i in all_indexes if i > lst[-1]])
            # 去除已经为某个已有命题组合包含的命题组合
            if len(flitered_indexes := [i for i in sub_indexes if not self._be_contained(i)]) == 0:
                break
            pool = mp.Pool(mp.cpu_count()) # 多进程池
            judges: list[tuple[list[int], bool]] = []
            with tqdm(total=len(flitered_indexes), desc=f"当前命题组合长度为{n}") as pbar:
                for i in flitered_indexes:
                    judges.append((i, pool.apply(self._run, args=(" ".join([str(j) for j in i]),))))
                    pbar.update(1)
            pool.close()
            pool.join()
            basic_indexes = [i for i, j in judges if not j]
            self.index_list.extend([i for i, j in judges if j])
            print(f"当前命题组合长度为{n}，已经找到命题组合{len(self.index_list)}个")
        else:
            print(f"已经达到最大搜索长度{self.limit}，搜索结束")
        if len(self.index_list) <= 0:
            print(f"未找到任何命题组合!")
        print(f"合计找到命题组合{len(self.index_list)}个")
        return self.index_list

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
        assert getattr(self._ask_prop, qtype), f"被询问的命题中没有属性{qtype}"
        # 挑选候选项
        if (candidates := self._value_range.get(qtype)) is None:
            print(f"未找到属性{qtype}的值域，无法生成选项！")
            return None
        elif len(candidates) < self._options - 1:
            print(f"候选项数量不足，无法生成选项！")
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