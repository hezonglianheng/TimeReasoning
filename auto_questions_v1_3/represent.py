# encoding: utf8
# date: 2024-12-31

"""
时间表示的基本类定义，包括自定义时间和自定义时间间隔
"""

import json5
import lemminflect
import element
import config
from typing import Any, Optional

# 常量
TIME_KINDS = "time_kinds"
TIMEDELTA_KINDS = "timedelta_kinds"
STRATEGY = "strategy" # 策略键
TRANSLATE = "translate" # 翻译

SEPARATE = {
    "cn": "", # 中文不需要分隔符
    "en": " ", # 英文需要空格分隔
}

# 读取时间单位的配置文件
with open(config.TIME_UNIT_FILE, "r", encoding = "utf8") as f:
    TIME_UNIT: dict[str, Any] = json5.load(f)

def unit_convert(time_value: int, unit: str, target_unit: str | None = None) -> int:
    """时间单位转换函数

    Args:
        time_value (int): 起始时间值
        unit (str): 起始时间值的单位
        target_unit (str | None, optional): 目标时间值的单位，默认为None

    Returns:
        int: 目标时间值，单位为target_unit
    """
    pass

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

    def translate(self, lang: str) -> str:
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
                list_name: str = g["list"]
                time_list: list[str] = TIME_UNIT["time_list"][list_name][lang]
                time_value: int = self[g["attr"]]
                res += time_list[time_value - 1]
            else:
                raise ValueError(f"对{self.kind}类型的翻译出现了未知的翻译方法: {g[STRATEGY]}")
        return res
    
    def __sub__(self, other: "CustomTime") -> Optional["CustomTimeDelta"]:
        """时间相减的魔术方法

        Args:
            other (CustomTime): 减去的时间

        Returns:
            CustomTimeDelta | None: 时间间隔
        """
        assert type(self) == type(other), "两个时间对象的class不同不能相减"
        assert self.kind == other.kind, "两个时间对象的kind不同不能相减"
        res = CustomTimeDelta()
        # TODO: 计算时间间隔 比较时间先后

class CustomTimeDelta(element.Element):
    """自定义时间间隔的抽象基类
    """

    def translate(self, lang: str) -> str:
        # 获取时间单位的翻译指南
        trans_guide: list[dict[str, str]] = TIME_UNIT[TIMEDELTA_KINDS][self.kind][TRANSLATE][lang]
        res: str = ""
        for g in trans_guide:
            key: str = g["attr"] # 时间值的键
            unit_name: str = g["unit"] # 时间的单位
            time_value: int = self[key] # 时间值，为整数值
            separate = SEPARATE[lang] # 分隔符
            if lang == config.ENGLISH and time_value > 1:
                # 英文需要将单位名转换为复数形式
                unit_name: str = lemminflect.getInflection(unit_name, tag = config.PLURAL_NOUN)[0]
            res += f"{time_value}{separate}{unit_name}"
        return res

    def __sub__(self, other: "CustomTimeDelta") -> Optional["CustomTimeDelta"]:
        """时间间隔相减的魔术方法

        Args:
            other (CustomTimeDelta): 减去的时间间隔

        Returns:
            CustomTimeDelta: 时间间隔
        """
        assert type(self) == type(other), "两个时间对象的class不同不能相减"
        assert self.kind == other.kind, "两个时间对象的kind不同不能相减"
        res = CustomTimeDelta()
        # TODO: 计算时间间隔 比较时间长短

if __name__ == "__main__":
    time1 = CustomTime(kind="year", year=1949)
    print(time1.translate(config.CHINESE))
    print(time1.translate(config.ENGLISH))
    time2 = CustomTime(kind="week_day", day=3)
    print(time2.translate(config.CHINESE))
    print(time2.translate(config.ENGLISH))
    time3 = CustomTimeDelta(kind="day", day=3)
    print(time3.translate(config.CHINESE))
    print(time3.translate(config.ENGLISH))
    time4 = CustomTimeDelta(kind="year", year=2)
    print(time4.translate(config.CHINESE))
    print(time4.translate(config.ENGLISH))