# encoding: utf8
# date: 2024-08-28
# author: Qin Yuhang

"""
包含推理机类、搜索机类、回答机类、范围获取机类，用于执行推理任务
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
import math
import abc # 增加表示抽象类的模块
from typing import Literal, Optional # 增加表示字面值类型

# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

from proposition import prop, rule, relation, graph
from proposition.config import PRECISE_WEIGHT, NOT_PRECISE_WEIGHT
from proposition import element
from proposition.config import LANG_CONFIG, ALL_WRONG, ASK_RIGHT, ASK_WRONG

OPTIONS = "options"
ANSWERS = "answers"
ANSWERPROP = "answerprop"
# 新增返回字典的键
QUESTION = "question"
CHAIN = "chain"
LENGTH = "length"
CHOICES = "choices"

class ReasonMachine:
    """推理机，用于执行推理任务"""

    def __init__(self, init_props: list[prop.Proposition], relations: list[type[relation.Relation]],
                 rules: list[type[rule.Rule]], knowledges: list[prop.Proposition] = [],
                 graph_construct: bool = False) -> None:
        """初始化推理机

        Args:
            init_props (list[Proposition]): 初始命题列表
            relations (list[type[Relation]]): 关系列表
            rules (list[type[Rule]]): 规则列表
            knowledges (list[Proposition], optional): 已知命题列表. 默认为空.
            graph_construct (bool, optional): 是否构建推理图. 默认为False.
        """
        self.init_props = init_props  # 初始命题列表
        self.relations = relations  # 关系列表
        self.rules = rules  # 规则列表
        # 中间变量
        self.old_props: list[prop.Proposition] = knowledges
        self.curr_props: list[prop.Proposition] = []
        self.new_props: list[prop.Proposition] = []
        # 11-03：增加图构建相关变量
        self.graph_construct = graph_construct
        self.graph = graph.Graph(deepcopy(init_props), deepcopy(knowledges)) if graph_construct else None


    def _reason_by_relation(self, layer: int) -> list[prop.Proposition]:
        """根据关系，从现有命题推理

        Returns:
            list[Proposition]: 新生成的命题列表
            layer(int): 推理层数

        Returns:
            list[Proposition]: 新生成的命题列表
        """
        # 从现有命题推理，得到新命题列表的列表
        prop_lists: List[List[prop.Proposition]] = []
        for p, r in tqdm(product(self.curr_props, self.relations), desc="根据关系推理",
                         total=len(self.curr_props) * len(self.relations)):
            new_p = r.reason(p)
            if new_p is not None:
                prop_lists.append(new_p)
                # 11-03：增加图构建
                if self.graph_construct:
                    for p0 in new_p:
                        self.graph.add_node(graph.Node([p], p0, layer))

        # 将新命题列表的列表合并为一个新命题列表
        if len(prop_lists) == 0:
            return []
        else:
            return reduce(lambda x, y: x + y, prop_lists)

    def _reason_by_rule(self, layer: int) -> list[prop.Proposition]:
        """根据规则，从现有命题-(现有命题+旧命题)推理

        Args:
            prop_list (list[Proposition]): 待推理的命题列表
            layer(int): 推理层数

        Returns:
            list[Proposition]: 新生成的命题列表
        """
        prop_list: list[prop.Proposition] = []
        total_len = math.perm(len(self.curr_props + self.old_props), 2) * len(self.rules)
        for (p1, p2), r in tqdm(product(permutations(self.curr_props + self.old_props, r=2), self.rules),
                                desc="根据规则推理", total=total_len):
            new_p = r.reason(p1, p2)
            if new_p is not None:
                prop_list.append(new_p)
                if self.graph_construct:
                    self.graph.add_node(graph.Node([p1, p2], new_p, layer))
        return prop_list

    def run(self) -> list[prop.Proposition]:
        """运行推理机，获得能够推出的最大命题

        Returns:
            list[prop.Proposition]: 能够推出的最大命题
        """
        assert len(self.init_props) > 0, "初始命题列表不能为空"
        self.curr_props = deepcopy(self.init_props)  # 将初始命题列表复制到当前命题列表中
        count = 0
        while True:
            count += 1
            print(f"执行第{count}次推理...")
            self.new_props.clear()  # 清空新命题列表
            by_relations = self._reason_by_relation(count)  # 用关系推理
            by_rules = self._reason_by_rule(count)  # 用规则推理
            # 对新命题的去重和加入
            for p in tqdm(by_relations + by_rules, desc="去重和加入新命题", total=len(by_relations + by_rules)):
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
# 11-03修订：时间领域可能不需要太复杂的命题组合关系
class SearchMachine:
    """
    搜索机，用于搜索可以推出原始命题的命题组合\n
    该搜索机使用了多进程，可以在一定程度上减少搜索时间
    """

    def __init__(self, init_props: list[prop.Proposition], all_props: list[prop.Proposition],
                 relations: list[type[relation.Relation]], rules: list[type[rule.Rule]],
                 knowledges: list[prop.Proposition] = []) -> None:
        """初始化搜索机

        Args:
            init_props (list[prop.Proposition]): 初始命题列表
            all_props (list[prop.Proposition]): 全部命题列表
            relations (list[type[relation.Relation]]): 关系列表
            rules (list[type[rule.Rule]]): 规则列表
        """
        warn("类SearchMachine已经弃用", DeprecationWarning)
        self.init_props = init_props  # 初始命题列表
        self.all_props = all_props  # 全部命题列表
        self.relations = relations
        self.rules = rules
        self.knowledges = knowledges
        self._new_prop: prop.Proposition = None  # 选择的新命题
        self.chosen_props: List[prop.Proposition] = []  # 已经选择的命题
        self.contained_props: List[prop.Proposition] = []  # 由已经选择的命题推出的全部命题
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
            self.chosen_props = self.chosen_props[:-1]  # 如果所有命题都已经包含，则去除最后一个
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
        size: list[int] = [0] * len(self.chosen_props)  # 记录推理结果范围广度

        # 检查命题
        print("运行命题推出性检查...")

        def process_reason(index: int):
            """判断命题能否由其他命题推出

            Args:
                index (int): 待判断命题的索引值
            """
            curr = self.chosen_props[index]  # 待检查命题
            excluded = [x for i, x in enumerate(self.chosen_props) if i != index]  # 其他命题
            reason_machine = ReasonMachine(excluded, self.relations, self.rules, deepcopy(self.knowledges))  # 建立推理器
            res = reason_machine.run()  # 运行推理器
            # 记录广度
            size[index] = len(res)
            # 记录判断
            if curr.got(res):
                reasoned[index] = True

        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            executor.map(process_reason, range(len(self.chosen_props)))

        # 更新已选命题
        self.chosen_props = [i for i, j in zip(self.chosen_props, reasoned) if not j]  # 去除已经推理的命题
        print(f"检查后已选命题有{len(self.chosen_props)}个")
        if len(self.chosen_props) > self._upper_limit:  # 超过上限时以推理最广的组合为基础调整已选命题数量
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
            self._random_choose(candidate_props)  # 随机选择一个新命题
            # self.chosen_props.append(new_prop)
            '''
            if len(self.chosen_props) > 1:
                self._lessen_chosen_props()
            rm = ReasonMachine(self.chosen_props, self.relations, self.rules)
            self.contained_props = rm.run()
            '''
            self._check()  # 检查命题，减少可行命题组合中命题数量
            if self._new_prop.got(self.chosen_props):  # 新增命题存在于已选命题中
                self._reason()  # 增量式推理
                if all([i.contained(self.contained_props) for i in self.init_props]):
                    print(f"已经找到可行的命题组合，共{len(self.chosen_props)}个命题")
                    return self.chosen_props
            else:  # 新增命题不存在于已选择命题中
                print("新增命题可以被推出，继续推理.")


class AnswerMachine:
    """
    答案机，用于根据询问命题和信息生成选项和答案
    """

    def __init__(self, all_prop: list[prop.Proposition], ask_prop: prop.Proposition, ask_info: dict[str, Any],
                 seed: Union[int, float, None] = None, options: int = 4, all_wrong_prob: float = .1, lang: str = 'zh') -> None:
        """初始化答案机，用于根据询问命题和信息生成选项和答案

        Args:
            all_prop (list[prop.Proposition]): 全部命题
            ask_prop (prop.Proposition): 被询问的命题
            ask_info (dict[str, Any]): 询问后获得的信息
            seed (Union[int, float, None], optional): 随机种子. 默认为None.
            options (int, optional): 选项数量. 默认为4.
            all_wrong_prob (float, optional): 设置“全部错误”的概率. 默认为0.1.
            lang (str, optional): 语言设置. 默认为'zh'(中文).
        """
        self._all_prop = all_prop  # 全部命题
        self._ask_prop = ask_prop  # 被询问的命题
        self._ask_info = ask_info  # 询问信息
        self._value_range: dict[str, list[Any]] = dict()
        self._seed = seed
        if options > len(ascii_uppercase):
            warn(f"选项数量{options}大于26，将被重置为26", UserWarning)
            options = len(ascii_uppercase)
        self._options = options
        self._all_wrong_prob = all_wrong_prob  # 全部错误的概率
        self.options_and_answers: dict[str, Any] = dict()
        self.lang = lang # 语言设置

    def set_value_range(self, key: str, value: list[Any]) -> None:
        """为一个可询问的属性设置值域，值域需要被调用用于生成选项

        Args:
            key (str): 需要询问并设置值域的属性
            value (list[Any]): 值域
        """
        value = [i for i in value if i != self._ask_info[prop.ANSWER]]
        self._value_range[key] = value

    def run(self) -> dict[str, Any] :
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
        # 1-20移除：移除随机种子设置
        # random.seed(self._seed)  # 设置随机种子
        # 1-17修改：修改获得干扰命题的逻辑
        # 洗切candidates
        random.shuffle(candidates)
        # 不再需要采样，直接从candidates中选取
        # chosen_candidate = random.sample(candidates, self._options - 1)

        ans_prop: list[prop.Proposition] = []  # 将选项重新填入空中得到的命题

        # 1-17修改：随机从candidates中抽取元素，生成新的命题
        candidate_index = -1
        while len(option_situation_tuples) < self._options:
            candidate_index += 1 # 从0开始，累加索引值
            new_prop = deepcopy(self._ask_prop)
            setattr(new_prop, qtype, candidates[candidate_index])
            # 理智性检查
            if not new_prop.sancheck():
                continue
            if new_prop.got(self._all_prop):
                ans_prop.append(new_prop)
                option_situation_tuples.append((candidates[candidate_index], True))
            else:
                option_situation_tuples.append((candidates[candidate_index], False))
        """
        # 确定候选项是否正确
        for i in chosen_candidate:
            new_prop = deepcopy(self._ask_prop)
            setattr(new_prop, qtype, i)
            if new_prop.got(self._all_prop):
                ans_prop.append(new_prop)  # 将正确答案重新填入空中得到的命题
                option_situation_tuples.append((i, True))
            else:
                option_situation_tuples.append((i, False))
        """
        # 随机打乱选项，生成选项和答案
        random.shuffle(option_situation_tuples)
        options: dict[str, Any] = dict() # 12-11修订：不再返回字符串，而是返回内部存储对象
        answers: list[str] = list()
        for i, (opt, judge) in enumerate(option_situation_tuples):
            # 12-11修订：不再返回字符串，而是返回内部存储对象
            # options[ascii_uppercase[i]] = str(opt)
            options[ascii_uppercase[i]] = opt
            if judge:
                answers.append(ascii_uppercase[i])
        # 设置“以上选项均不正确”选项
        if random.random() < self._all_wrong_prob:
            options[ascii_uppercase[self._options - 1]] = LANG_CONFIG[self.lang][ALL_WRONG]
            if len(answers) > 1 and ascii_uppercase[self._options - 1] in answers:
                answers.remove(ascii_uppercase[self._options - 1])
        # 返回最终结果

        self.options_and_answers = {OPTIONS: options, ANSWERS: answers, ANSWERPROP: ans_prop}
        return self.options_and_answers

class GetRangeMachine(metaclass = abc.ABCMeta):
    """范围获取机的抽象基类，用于根据输入参数获取特定的范围\n
    该类是一个抽象类，需要在领域中被继承并实现get_range方法
    """
    def __init__(self, all_elements: list[element.Element]) -> None:
        """初始化范围获取机

        Args:
            all_elements (list[element.Element]): 全部元素列表
        """
        self.all_elements = all_elements

    @abc.abstractmethod
    def get_range(self, ask_info: dict[str, Any], *args, **kwargs) -> List[Any]:
        """根据输入参数获取特定的范围
        Args:
            ask_info (dict[str, Any]): 询问信息

        Returns:
            List[Any]: 获得的范围列表
        """
        pass

# TODO
class AskAllMachine:
    """询问机，用于询问“以下选项中正确的是”“以下选项中错误的是”两类试题
    """
    # 题干模板
    ask_correct_questions: str = "请问: 以下选项中正确的是____"
    ask_wrong_questions: str = "请问: 以下选项中错误的是____"

    def __init__(self, all_props: list[prop.Proposition], chosen_props: list[prop.Proposition], temps: dict[str, list[str]], reason_graph: graph.Graph, range_machine: GetRangeMachine, ask_correct: bool = True, lang: str = "zh", *, options: int = 4, correct: int = 1, ask_mode: Literal['random', 'deepest', 'tag'] = 'random', all_wrong_prob: float = .1, tag: Optional[list[str]] = None) -> None:
        """初始化询问机

        Args:
            all_props (list[prop.Proposition]): 全部命题
            chosen_props (list[prop.Proposition]): 已选命题
            temps (dict[str, list[str]]): 模板字典
            reason_graph (graph.Graph): 推理图
            range_machine (GetRangeMachine): 范围获取机
            ask_correct (bool, optional): 是否询问“以上选项中正确的是”. 默认为True. 若为False，则询问“以上选项中错误的是”
            lang (str, optional): 语言设置. 默认为'zh'(中文).
            options (int, optional): 选项数量. 默认为4.(最大26)
            correct (int, optional): 正确选项数量. 默认为1.(大于0且小于等于options)
            ask_mode (Literal[&#39;random&#39;, &#39;deepest&#39;, &#39;tag&#39;], optional): 询问模式. 默认为&#39;random&#39;.
                - random: 随机询问
                - deepest: 从推理图中选择最深的节点询问
                - tag: 从推理图中选择特定标记的节点询问，需要提供tag参数
            all_wrong_prob (float, optional): 设置“全部错误”的概率. 默认为0.1.
            tag (Optional[list[str]], optional): 询问标记. 默认为空.
        """
        self.all_props = all_props # 全部可提问的命题
        self.chosen_group = chosen_props # 已选命题
        self.temps = temps # 模板字典
        self.reason_graph = reason_graph # 推理图
        self.range_machine = range_machine # 范围获取机
        self.ask_correct = ask_correct # 是否询问“以上选项中正确的是”
        self.lang = lang # 语言设置
        if options > len(ascii_uppercase):
            warn(f"选项数量{options}大于26，将被重置为26", UserWarning)
            options = len(ascii_uppercase)
        self.options = options
        assert 0 < correct <= options, f"正确选项数量{correct}不合法"
        self.correct = correct # 正确选项数量
        self.ask_mode = ask_mode # 询问模式
        self.all_wrong_prob = all_wrong_prob # 全部错误的概率
        self.tag = tag # 询问标记
        # 中间变量
        self._candidates: list[prop.Proposition] = [] # 候选命题列表
        self._question = ASK_RIGHT if ask_correct else ASK_WRONG # 问题
        self._option_dict: dict[str, prop.Proposition | str] = dict() # 选项字典
        self._answers: list[str] = [] # 答案列表
        self._chains: list[str] = [] # 询问链
        self._chain_length: int = 0 # 询问链长度

    def _choose_candidates(self) -> list[prop.Proposition]:
        """选择候选命题

        Raises:
            ValueError: 如果询问模式不合法，则抛出异常

        Returns:
            list[prop.Proposition]: 候选命题列表
        """
        if self.ask_mode == 'random':
            candidates: list[prop.Proposition] = [i for i in self.all_props if not i.got(self.chosen_group) and i.askable]
        elif self.ask_mode == 'deepest':
            assert self.reason_graph is not None, "deepest提问模式下，必须先获取推理图"
            deepest_layer: int = -1
            for i in [k for k in self.all_props if not k.got(self.chosen_group) and k.askable]:
                layer = self.reason_graph.layer_query(i)
                if layer > deepest_layer:
                    deepest_layer = layer
            candidates = [i for i in self.all_props if not i.got(self.chosen_group) and i.askable and self.reason_graph.layer_query(i) == deepest_layer]
        elif self.ask_mode == 'tag':
            assert self.tag is not None, "tag提问模式下，提问标签不能为空"
            candidates = [i for i in self.all_props if not i.got(self.chosen_group) and i.askable and i.typetag in self.tag]
        else:
            raise ValueError(f"提问模式错误，不存在{self.ask_mode}模式")
        self._candidates = candidates # 保存候选命题列表
        return candidates

    def _get_option_range(self, ask_info: dict[str, Any], curr_prop: prop.Proposition) -> List[Any]:
        """获取选项可替换的值域范围

        Args:
            ask_info (dict[str, Any]): 询问信息
            curr_prop (prop.Proposition): 当前命题

        Returns:
            List[Any]: 可替换的值域范围
        """
        value_range = self.range_machine.get_range(ask_info) # 获取值域
        value_range = [i for i in value_range if i != ask_info[prop.ANSWER]] # 排除值域中的正确项
        return value_range
    
    # 12-25修订：如果检查值域发现值域为空，则返回None
    def _get_option_prop(self, curr_prop: prop.Proposition, judge: bool) -> prop.Proposition | None:
        """获取选项中需要使用的命题

        Args:
            curr_prop (prop.Proposition): 当前命题
            judge (bool): 是否为正确选项

        Returns:
            prop.Proposition: 选项中需要使用的命题
        """
        if judge:
            return curr_prop
        else:
            ask_info = curr_prop.ask(self.temps) # 询问信息
            value_range = self._get_option_range(ask_info, curr_prop) # 获取值域
            # 12-25新增：如果检查值域发现值域为空，则返回None
            if len(value_range) == 0:
                return None
            new_prop = deepcopy(curr_prop) # 复制当前命题
            # 1-20修改：需要对新的命题进行sancheck
            while True:
                setattr(new_prop, ask_info[prop.TYPE], random.choice(value_range))
                if new_prop.sancheck():
                    break
            # setattr(new_prop, ask_info[prop.TYPE], random.choice(value_range)) # 随机选择一个错误选项，替换当前命题，生成新命题
            return new_prop
    
    def _make_options(self) -> None:
        """生成选项、答案和推理链

        Raises:
            ValueError: 如果候选命题列表为空，则抛出异常
        """
        # candidate为空，则报错
        if len(self._candidates) == 0:
            raise ValueError("候选命题列表为空，无法生成选项")
        # candidate不足，返回None
        if len(self._candidates) < self.options:
            print(f"候选命题数量不足，无法生成选项")
            return None
        # 采样命题
        samples = random.sample(self._candidates, self.options)
        # 随机为每个命题确定一个bool值作为判断值
        if self.ask_correct:
            situation = [True] * self.correct + [False] * (self.options - self.correct)
        else:
            situation = [False] * self.correct + [True] * (self.options - self.correct)
        random.shuffle(situation)
        # 生成选项
        option_props = [self._get_option_prop(i, j) for i, j in zip(samples, situation)]
        # 12-25修订：如果option_props中包含空，则返回，不进行后续的操作
        if None in option_props:
            return None
        # 生成新的判断（旧的判断未必能够成功替换）
        judges = [i.got(self.all_props) for i in option_props]
        # 生成选项字典
        # 12-12修改：输出的选项字典的值不是字符串而是命题
        # self._option_dict = {ascii_uppercase[i]: j.state(self.temps) for i, j in enumerate(option_props)}
        self._option_dict = {ascii_uppercase[i]: j for i, j in enumerate(option_props)}
        # 生成答案
        if self.ask_correct:
            self._answers = [ascii_uppercase[i] for i, j in enumerate(judges) if j]
        else:
            self._answers = [ascii_uppercase[i] for i, j in enumerate(judges) if not j]
        # 获得采样命题的推理链
        chain_nodes = [self.reason_graph.backtrace(i) for i in samples]
        # 11-30更新：计算推理链长度
        self._chain_length = sum([len(i) for i in chain_nodes])
        self._chains = ["\n".join([j.state(self.temps, lang=self.lang) for j in i]) for i in chain_nodes]
        # 检查答案是否为空
        if len(self._answers) == 0:
            # 将最后一个项换成“以上选项均不对”
            self._option_dict[ascii_uppercase[self.options - 1]] = LANG_CONFIG[self.lang][ALL_WRONG]
            self._answers = [ascii_uppercase[self.options - 1]]
            return None
        if random.random() < self.all_wrong_prob:
            # 将最后一个项换成“以上选项均不对”
            self._option_dict[ascii_uppercase[self.options - 1]] = LANG_CONFIG[self.lang][ALL_WRONG]
            if len(self._answers) > 1 and ascii_uppercase[self.options - 1] in self._answers:
                self._answers.remove(ascii_uppercase[self.options - 1])

    def run(self) -> dict[str, Any] | None:
        """运行询问机，生成问题、选项、答案和推理链

        Returns:
            dict[str, Any]: 问题、选项、答案和推理链
        """
        self._choose_candidates() # 选择候选命题
        self._make_options() # 生成选项、答案和推理链
        # 如果选项字典为空，则返回None
        if len(self._option_dict) == 0:
            return None
        # 否则返回问题、选项、答案和推理链
        return {
            QUESTION: LANG_CONFIG[self.lang][self._question],
            # OPTIONS: self._option_dict,
            CHOICES: self._option_dict, # 12-02更新：将选项的键改为CHOICES
            ANSWERS: self._answers,
            # CHOICES: self._answers, # 11-30更新：将答案的键改为CHOICES
            CHAIN: "\n".join(self._chains), 
            LENGTH: self._chain_length, 
        }