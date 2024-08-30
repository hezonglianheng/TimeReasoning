# encoding: utf8
# date: 2024-08-25
# author: Qin Yuhang

"""
关于命题推理规则的基本定义和基本操作
"""

import abc
from typing import Optional
import sys
from pathlib import Path
# 将上级目录加入到sys.path中
sys.path.append(Path(__file__).resolve().parents[1].as_posix())

import proposition.prop as prop

class Rule(metaclass = abc.ABCMeta):
    """命题推理规则的基类"""
    @classmethod
    @abc.abstractmethod
    def reason(cls, *props: prop.Proposition) -> Optional[prop.Proposition]:
        """根据命题推理生成新的命题

        Args:
            *props (Proposition): 输入的命题

        Returns:
            Proposition: 新的命题或者None
        """
        pass
