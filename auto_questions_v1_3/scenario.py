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

# constraints.
ATTR_NAMES = "attr_names"
REF_RULES = "ref_rules"
SCENARIO_PROPS = "scenario_props"
SCENARIO_RULES = "scenario_rules"

class Scenario(element.Element):
    """自定义的时间情景
    """
    def __init__(self, name = "", kind = "", **kwargs):
        super().__init__(name, kind, **kwargs)
        self.path = config.SCENARIO_DIR / f"{kind}.json5"
        with self.path.open("r", encoding = "utf8") as f:
            data: dict = json5.load(f)
            self[ATTR_NAMES] = data.get(ATTR_NAMES, {})
            self[REF_RULES] = data.get(REF_RULES, [])
            self[SCENARIO_PROPS] = data.get(SCENARIO_PROPS, {})
            self[SCENARIO_RULES] = data.get(SCENARIO_RULES, [])
        self._attr_rewrite()

    def _attr_rewrite(self):
        """将属性名称重写到属性中
        """
        attr_names: dict = self[ATTR_NAMES]
        for key, value in attr_names.items():
            sentence = f"self['{key}'] = {value}"
            exec(sentence)
    
    def translate(self, lang, require = None, **kwargs):
        return super().translate(lang, require, **kwargs)

    def get_props(self) -> list[prop.Proposition]:
        """获取情景中的自定义命题
        """
        prop.add_prop_data(self[SCENARIO_PROPS])
        prop_res: list[prop.Proposition] = []
        prop_kinds: dict[str, dict] = self[SCENARIO_PROPS]
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
        ref_names: list[str] = self[REF_RULES]
        rules.extend(rule.get_reasoning_rules(ref_names))
        # 创建场景独有规则
        new_rules: list[dict] = self[SCENARIO_RULES]
        for rule_data in new_rules:
            rules.append(rule.Rule(**rule_data))
        return rules