# encoding: utf8
# date: 2024-08-28
# author: Qin Yuhang

"""
包含推理机类，用于执行推理任务
"""

from itertools import product, permutations
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
        return [new_p for p, r in product(self.curr_props, self.relations) if (new_p := r.reason(p)) is not None]
    
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
            print(f"执行第{count}次推理")
            self.new_props.clear() # 清空新命题列表
            by_relations = self._reason_by_relation() # 用关系推理
            by_rules = self._reason_by_rule() # 用规则推理
            self.new_props.extend(by_relations + by_rules) # 加入新命题
            # 将当前命题加入旧命题并去重
            self.old_props.extend([i for i in self.curr_props if not self._already_exist(i)])
            # 检查新命题是否都出现在旧命题中
            if len(new_props := [i for i in self.new_props if not self._already_exist(i)]) == 0:
                print(f"推理完成，得到命题{len(self.old_props)}条")
                return self.old_props
            # 否则当前命题变更为新命题
            self.curr_props = new_props