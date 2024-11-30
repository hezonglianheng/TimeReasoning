# encoding: utf8
# date: 2024-11-30

"""
用于时间推理题的难度评级
"""

# weights of parameters.
# 链长
chain_length_weight = 0.01
# 命题长度
statement_length_weight = 0.01
# 选项数
option_num_weight = 0.2
# 知识数量
knowledge_num_weight = 0.1

# functions.
def ask_level(chain_len: int, statement_len: int, option_num: int, knowledge_num: int, scene_level: float) -> int:
    """根据题目参数评级

    Args:
        chain_len (int): 链长
        statement_len (int): 命题长度
        option_num (int): 选项数
        knowledge_num (int): 知识数量
        scene_level (float): 场景难度

    Returns:
        int: 难度等级
    """
    chain_level = chain_len * chain_length_weight
    statement_level = statement_len * statement_length_weight
    option_level = option_num * option_num_weight
    knowledge_level = knowledge_num * knowledge_num_weight
    level = chain_level + statement_level + option_level + knowledge_level + scene_level
    level_rank =  round(level)
    if level_rank < 1:
        return 1
    elif level_rank > 4:
        return 4
    else:
        return level_rank