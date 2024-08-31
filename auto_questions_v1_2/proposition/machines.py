# encoding: utf8
# date: 2024-08-28
# author: Qin Yuhang

"""
包含推理机类、搜索机类，用于执行推理任务
"""

from itertools import product
from functools import reduce, cache
from typing import List, Sequence
from copy import deepcopy
import sys
from pathlib import Path

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition import prop, rule, relation

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

    def _already_exist(self, prop: prop.Proposition) -> bool:
        """判断这一命题是否已经存在

        Args:
            prop (prop.Proposition): 待判断的命题

        Returns:
            bool: 对这一命题是否已经存在的判断
        """
        return any([i == prop for i in self.old_props])
    
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
        return [new_p for p1, p2, r in product(self.curr_props + self.old_props, self.curr_props + self.old_props, self.rules) if (new_p := r.reason(p1, p2)) is not None]
    
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
            self.old_props.extend([i for i in self.curr_props if not self._already_exist(i)])
            # 检查新命题是否都出现在旧命题中
            if len(new_props := [i for i in self.new_props if not self._already_exist(i)]) == 0:
                return self.old_props
            # 否则当前命题变更为新命题
            self.curr_props = new_props

class SearchMachine:
    """搜索机，用于搜索可以推出原始命题的命题组合\n
    该搜索机使用了扩圈思想和剪枝算法，可以在一定程度上减少搜索时间"""
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
        self.limit = limit if limit is not None else len(init_props) * 2
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
        if all([i.got(res) for i in self.init_props]):
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
            judges = [(i, self._run(" ".join([str(j) for j in i]))) for i in flitered_indexes]
            basic_indexes = [i for i, j in judges if not j]
            self.index_list.extend([i for i, j in judges if j])
            print(f"当前命题组合长度为{n}，已经找到命题组合{len(self.index_list)}个")
        else:
            print(f"已经达到最大搜索长度{self.limit}，搜索结束")
        print(f"合计找到命题组合{len(self.index_list)}个")
        return self.index_list