# encoding: utf8
# date: 2024-12-31

"""
时间表示的基本类定义，包括自定义时间和自定义时间间隔
"""

import json5
import lemminflect
import networkx as nx
import element
import config
from typing import Any, Optional, overload
from collections.abc import Iterable
import random
from bisect import bisect

# 常量
BASIC_UNIT = "basic_unit"
TIME_KINDS = "time_kinds"
TIMEDELTA_KINDS = "timedelta_kinds"
STRATEGY = "strategy" # 策略键
TRANSLATE = "translate" # 翻译
CONVERT = "convert" # 转换
BASE = "base" # 基本单位
FROM = "from" # 起始单位
TO = "to" # 目标单位
RATE = "rate" # 单位转换比率
PRECISE = "precise" # 是否精确
UNIT = "unit" # 单位
SUB_RESULT_KIND = "sub_result_kind" # 时间间隔的结果类型

# 读取时间单位的配置文件
with open(config.TIME_UNIT_FILE, "r", encoding = "utf8") as f:
    TIME_UNIT: dict[str, Any] = json5.load(f)

# 构建时间单位转换图
CONVERT_GRAPH = nx.DiGraph()
convert_rules: list[dict[str, Any]] = TIME_UNIT[CONVERT]
for rule in convert_rules:
    CONVERT_GRAPH.add_edge(rule[FROM], rule[TO], **rule)

def convert2lower(time_value: int, from_unit: str, to_unit: str | None = None) -> dict[str, int | bool]:
    """时间单位转换函数，将时间从高单位转换为低单位.\n
    如果没有指定目标单位，则随机选择一个低单位.\n
    如果目标高于起始单位，则返回原值.\n

    Args:
        time_value (int): 起始时间值
        from_unit (str): 起始时间值的单位
        to_unit (str | None, optional): 目标时间值的单位，默认为None

    Returns:
        dict[str, int | bool]: 转换后的字典，value为转换后的时间值，unit为单位，precise为是否精确
    """
    basic_units: list[str] = TIME_UNIT[BASIC_UNIT]
    if to_unit is None:
        unit_index = basic_units.index(from_unit)
        try: 
            to_unit: str = random.choice(basic_units[unit_index + 1:])
        except Exception as e:
            return {"value": time_value, UNIT: from_unit, PRECISE: True}
    # 如果目标高于起始单位，则返回原值.
    from_index = basic_units.index(from_unit)
    to_index = basic_units.index(to_unit)
    if to_index <= from_index:
        return {"value": time_value, UNIT: from_unit, PRECISE: True}
    convert_path = nx.shortest_path(CONVERT_GRAPH, from_unit, to_unit)
    convert_value = time_value
    convert_precise = True
    for i in range(len(convert_path) - 1):
        convert_value = convert_value * CONVERT_GRAPH[convert_path[i]][convert_path[i + 1]][RATE]
        convert_precise = convert_precise and CONVERT_GRAPH[convert_path[i]][convert_path[i + 1]][PRECISE]
    return {"value": convert_value, UNIT: to_unit, PRECISE: convert_precise}

def convert2higher(time_value: int, from_unit: str, to_unit: str) -> dict[str, dict[str, int] | bool]:
    """时间单位转换函数，将时间从低单位转换为高单位.\n
    如果目标低于起始单位，则返回原值.\n

    Args:
        time_value (int): 起始时间值
        from_unit (str): 起始时间值的单位
        to_unit (str): 目标时间值的单位

    Returns:
        dict[str, dict[str, int] | bool]: 转换后的字典，value为转换后的时间值字典，键为单位名称，值为时间值，precise为是否精确
    """
    basic_units: list[str] = TIME_UNIT[BASIC_UNIT]
    # 如果目标低于起始单位，则返回原值.
    from_index = basic_units.index(from_unit)
    to_index = basic_units.index(to_unit)
    if to_index >= from_index:
        return {"value": {from_unit: time_value}, PRECISE: True}
    convert_path = nx.shortest_path(CONVERT_GRAPH, to_unit, from_unit)
    convert_rate: int = 1
    convert_precise: bool = True
    for i in range(len(convert_path) - 1):
        convert_rate *= CONVERT_GRAPH[convert_path[i]][convert_path[i + 1]][RATE]
        convert_precise = convert_precise and CONVERT_GRAPH[convert_path[i]][convert_path[i + 1]][PRECISE]
    convert_value = time_value // convert_rate
    # 求余数
    remainder = time_value % convert_rate
    return {"value": {to_unit: convert_value, from_unit: remainder}, PRECISE: convert_precise}

def get_time_range(time1: "CustomTime", time2: "CustomTime") -> Iterable["CustomTime"]:
    """获得两个时间之间的时间范围，包括上下界

    Returns:
        Iterable[CustomTime]: 两个时间之间的时间范围，包括上下界
    """
    if time1 < time2:
        upper_bound: CustomTime = time2
        lower_bound: CustomTime = time1
    else:
        upper_bound: CustomTime = time1
        lower_bound: CustomTime = time2
    delta: CustomTimeDelta = upper_bound - lower_bound
    # 获得delta的基本单位
    delta_unit: str = TIME_UNIT[TIMEDELTA_KINDS][delta.kind][BASE]
    # 获得delta的值
    delta_value: int = delta[delta_unit]
    # 获得时间范围的上下界
    time_range: Iterable[CustomTime] = (lower_bound + CustomTimeDelta(kind=delta.kind, **{delta_unit: i}) for i in range(delta_value + 1))
    return time_range

class CustomTime(element.Element):
    """自定义时间的抽象基类
    """

    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        # 如果没有指定时间类型，则自动推断
        if kind == "":
            self.kind_infer()

    def kind_infer(self):
        kind_dict: dict[str, Any] = TIME_UNIT[TIME_KINDS]
        for k in kind_dict:
            units = kind_dict[k]["units"]
            # 如果所有的属性都在时间类型的属性中，且时间类型的属性都在属性中，则推断为该时间类型
            if all(u in self.attrs for u in units) and all(u in units for u in self.attrs):
                self.kind = k
                return

    @property
    def convert2base(self) -> dict[str, int]:
        """将时间值转换为基本单位，供进一步比较和计算

        Raises:
            ValueError: 对时间类型的转换出现了未知的转换方法

        Returns:
            dict[str, int]: 转换后的时间值字典，键为单位名称，值为时间值
        """
        base: str = TIME_UNIT[TIME_KINDS][self.kind][BASE]
        convert_result: dict[str, int] = {base: self[base]}
        convert_guide: list[dict] = TIME_UNIT[TIME_KINDS][self.kind][CONVERT]
        for g in convert_guide:
            if g[STRATEGY] == "convert":
                convert_result[base] += convert2lower(self[g[FROM]], g[FROM], base)["value"]
            elif g[STRATEGY] == "list":
                time_list: list[str] = g["list"]
                time_value: int = self[g[FROM]]
                convert_result[base] += time_list[time_value - 1]
            else:
                raise ValueError(f"对{self.kind}类型的转换出现了未知的转换方法: {g[STRATEGY]}")
        return convert_result

    def _convert2standard(self, base_time: dict[str, int]) -> dict[str, int]:
        """将时间值转换为标准形式，供翻译

        Args:
            base_time (dict[str, int]): 基本单位的时间值

        Return:
            dict[str, int]: 转换后的时间值字典，键为单位名称，值为时间值
        """
        base: str = TIME_UNIT[TIME_KINDS][self.kind][BASE]
        convert_guide: list[dict] = TIME_UNIT[TIME_KINDS][self.kind][CONVERT]
        convert_result = base_time.copy()
        for g in convert_guide:
            if g[STRATEGY] == "convert":
                curr_res = convert2higher(base_time[base], base, g[FROM])
                convert_result.update(curr_res["value"])
            elif g[STRATEGY] == "list":
                time_list: list[str] = g["list"]
                time_value: int = base_time[base]
                curr_convert: int = bisect(time_list, time_value)
                convert_result[g[FROM]] = curr_convert
                convert_result[base] = time_value - time_list[curr_convert - 1]
            else:
                raise ValueError(f"对{self.kind}类型的转换出现了未知的转换方法: {g[STRATEGY]}")
        return convert_result
    
    def translate(self, lang: str, require: str|None = None, **kwargs) -> str:
        # 获取翻译指南
        trans_guide: list[dict[str, str]] = TIME_UNIT[TIME_KINDS][self.kind][TRANSLATE][lang]
        res: str = ""
        for g in trans_guide:
            if g[STRATEGY] == "template":
                # 通过模板替换的方法完成翻译
                template: str = g["template"]
                res += template.format(**self.attrs)
            elif g[STRATEGY] == "list":
                # 通过读取列表的方法完成翻译
                time_list: list[str] = g["list"]
                time_value: int = self[g["attr"]]
                res += time_list[time_value - 1]
            else:
                raise ValueError(f"对{self.kind}类型的翻译出现了未知的翻译方法: {g[STRATEGY]}")
        return res
    
    def __lt__(self, other: "CustomTime") -> bool:
        assert type(self) == type(other), "两个时间对象的class不同不能比较"
        assert self.kind == other.kind, "两个时间对象的kind不同不能比较"
        base: str = TIME_UNIT[TIME_KINDS][self.kind][BASE]
        self_base: int = self.convert2base[base]
        other_base: int = other.convert2base[base]
        return self_base < other_base

    def __gt__(self, other: "CustomTime") -> bool:
        return not (self < other)

    @overload
    def __sub__(self, other: "CustomTime") -> Optional["CustomTimeDelta"]: ...

    @overload
    def __sub__(self, other: "CustomTimeDelta") -> "CustomTime": ...
    
    def __sub__(self, other):
        """时间相减的魔术方法

        Args:
            other (CustomTime | CustomTimeDelta): 减去的时间或时间间隔

        Returns:
            CustomTimeDelta | CustomTime | None: 时间间隔、时间或None
        """
        if type(other) == CustomTime:
            assert type(self) == type(other), "两个时间对象的class不同不能相减"
            assert self.kind == other.kind, "两个时间对象的kind不同不能相减"
            if self < other:
                return None
            else:
                base: str = TIME_UNIT[TIME_KINDS][self.kind][BASE]
                self_base: int = self.convert2base[base]
                other_base: int = other.convert2base[base]
                delta_base: int = self_base - other_base
                delta_kind: str = TIME_UNIT[TIME_KINDS][self.kind][SUB_RESULT_KIND]
                delta = CustomTimeDelta(kind=delta_kind, **{base: delta_base})
                return delta
        elif type(other) == CustomTimeDelta:
            left_base: str = TIME_UNIT[TIME_KINDS][self.kind][BASE]
            right_base: str = TIME_UNIT[TIMEDELTA_KINDS][other.kind][BASE]
            assert left_base == right_base, f"时间{self}和时间间隔{other}的基本单位不同，不能相减"
            self_base_value: int = self.convert2base[left_base]
            delta_base_value: int = other[right_base]
            result_base: int = self_base_value - delta_base_value
            time_attr: dict[str, int] = {left_base: result_base}
            time_attr = self._convert2standard(time_attr)
            result = CustomTime(kind=self.kind, **time_attr)
            return result
        else:
            raise ValueError(f"不支持的相减类型: {type(other)}")

    def __add__(self, other: "CustomTimeDelta") -> "CustomTime":
        """时间相加的魔术方法

        Args:
            other (CustomTimeDelta): 加上的时间间隔

        Returns:
            CustomTime: 时间
        """
        left_base: str = TIME_UNIT[TIME_KINDS][self.kind][BASE]
        right_base: str = TIME_UNIT[TIMEDELTA_KINDS][other.kind][BASE]
        assert left_base == right_base, f"时间{self}和时间间隔{other}的基本单位不同，不能相加"
        self_base_value: int = self.convert2base[left_base]
        delta_base_value: int = other[right_base]
        result_base: int = self_base_value + delta_base_value
        time_attr: dict[str, int] = {left_base: result_base}
        time_attr = self._convert2standard(time_attr)
        result = CustomTime(kind=self.kind, **time_attr)
        return result

class CustomTimeDelta(element.Element):
    """自定义时间间隔的抽象基类
    """

    def translate(self, lang: str, require: str|None = None, **kwargs) -> str:
        # 获取时间单位的翻译指南
        trans_guide: list[dict[str, str]] = TIME_UNIT[TIMEDELTA_KINDS][self.kind][TRANSLATE][lang]
        res: str = ""
        for g in trans_guide:
            key: str = g["attr"] # 时间值的键
            unit_name: str = g[UNIT] # 时间的单位
            time_value: int = self[key] # 时间值，为整数值
            separate = config.SEPARATE[lang] # 分隔符
            if lang == config.ENGLISH and time_value > 1:
                # 英文需要将单位名转换为复数形式
                unit_name: str = lemminflect.getInflection(unit_name, tag = config.PLURAL_NOUN)[0]
            res += f"{time_value}{separate}{unit_name}"
        return res

    def __lt__(self, other: "CustomTimeDelta") -> bool:
        assert type(self) == type(other), "两个时间对象的class不同不能比较"
        assert self.kind == other.kind, "两个时间对象的kind不同不能比较"
        base: str = TIME_UNIT[TIMEDELTA_KINDS][self.kind][BASE]
        return self[base] < other[base]

    def __gt__(self, other: "CustomTimeDelta") -> bool:
        return not (self < other)

    def __sub__(self, other: "CustomTimeDelta") -> Optional["CustomTimeDelta"]:
        """时间间隔相减的魔术方法

        Args:
            other (CustomTimeDelta): 减去的时间间隔

        Returns:
            CustomTimeDelta: 时间间隔
        """
        assert type(self) == type(other), "两个时间对象的class不同不能相减"
        assert self.kind == other.kind, "两个时间对象的kind不同不能相减"
        if self < other:
            return None
        else:
            base: str = TIME_UNIT[TIMEDELTA_KINDS][self.kind][BASE]
            delta_base: int = self[base] - other[base]
            delta = CustomTimeDelta(kind=self.kind, **{base: delta_base})
            return delta

    @overload
    def __add__(self, other: CustomTime) -> CustomTime: ...

    @overload
    def __add__(self, other: "CustomTimeDelta") -> "CustomTimeDelta": ...

    def __add__(self, other):
        """时间间隔相加的魔术方法

        Args:
            other (CustomTime | CustomTimeDelta): 加上的时间或时间间隔

        Returns:
            CustomTime | CustomTimeDelta: 计算得到的时间或时间间隔
        """
        if type(other) == CustomTime:
            return other + self
        elif type(other) == CustomTimeDelta:
            assert self.kind == other.kind, "两个时间对象的kind不同不能相加"
            base: str = TIME_UNIT[TIMEDELTA_KINDS][self.kind][BASE]
            delta_base: int = self[base] + other[base]
            delta = CustomTimeDelta(kind=self.kind, **{base: delta_base})
            return delta
        else:
            raise ValueError(f"不支持的相加类型: {type(other)}")

if __name__ == "__main__":
    convert_result = convert2lower(1, "year")
    print(convert_result)
    higher_convert = convert2higher(13, "month", "year")
    print(higher_convert)
    year = CustomTime(kind="year", year=2000)
    year0 = CustomTime(kind="year", year=1900)
    year1 = CustomTimeDelta(kind="year", year=1)
    year2 = CustomTimeDelta(kind="year", year=2)
    print(year + year1)
    print(year1 + year2)
    print(year1 + year + year2)
    for y in get_time_range(year, year0):
        print(y)