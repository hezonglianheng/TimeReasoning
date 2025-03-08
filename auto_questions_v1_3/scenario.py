# encoding: utf8
# date: 2025-03-07

"""题目中时间情景的定义和方法
"""

import proposition as prop
import rule
import represent
import config
import element
import json5
from enum import StrEnum

class ScenarioField(StrEnum):
    """情景中字段的枚举
    """
    AttrNames = "attr_names" # 属性名称
    RefRules = "ref_rules" # 参考规则
    ScenarioProps = "scenario_props" # 场景命题
    ScenarioRules = "scenario_rules" # 场景规则

class Scenario(element.Element):
    """自定义的时间情景
    """
    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        self.path = config.SCENARIO_DIR / f"{name}.json5"
        with self.path.open("r", encoding = "utf8") as f:
            data: dict = json5.load(f)
            self[ScenarioField.AttrNames] = data.get(ScenarioField.AttrNames, {})
            self[ScenarioField.RefRules] = data.get(ScenarioField.RefRules, [])
            self[ScenarioField.ScenarioProps] = data.get(ScenarioField.ScenarioProps, {})
            self[ScenarioField.ScenarioRules] = data.get(ScenarioField.ScenarioRules, [])
        self._attr_rewrite()

    def _attr_rewrite(self):
        """将属性名称重写到属性中
        """
        attr_names: dict = self[ScenarioField.AttrNames]
        for key, value in attr_names.items():
            sentence = f"self['{key}'] = {value}"
            exec(sentence)
    
    def translate(self, lang, require = None, **kwargs):
        return super().translate(lang, require, **kwargs)

    def get_props(self) -> list[prop.Proposition]:
        """获取情景中的自定义命题
        """
        prop.add_prop_data(self[ScenarioField.ScenarioProps])
        prop_res: list[prop.Proposition] = []
        prop_kinds: dict[str, dict] = self[ScenarioField.ScenarioProps]
        for k in prop_kinds:
            props_definitions: list[dict[str, str]] = prop_kinds[k]['props']
            for d in props_definitions:
                prop_dic: dict = {"kind": k} | {key: eval(value) for key, value in d.items()}
                prop_res.append(prop.Proposition(**prop_dic))
        return prop_res

    def get_rules(self) -> list[rule.Rule]:
        """获取情景中的规则

        Returns:
            list[rule.Rule]: 根据情景引用和创建的规则
        """
        rules: list[rule.Rule] = []
        # 引用已有规则
        ref_names: list[str] = self[ScenarioField.RefRules]
        rules.extend(rule.get_reasoning_rules(ref_names))
        # 创建场景独有规则
        new_rules: list[dict] = self[ScenarioField.ScenarioRules]
        for rule_data in new_rules:
            rules.append(rule.Rule(**rule_data))
        return rules