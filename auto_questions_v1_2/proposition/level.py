# encoding: utf8
# date: 2024-11-30

"""
用于时间推理题的难度评级
"""

# limits.
# 难度等级上限
# 1-20修改：改为3
level_upper_limit = 3
# 难度等级下限
level_lower_limit = 1

# weights of parameters.
# 链长
chain_length_weight = 0.02
# 命题长度
# 2-5修改：由于记录的难度改为命题难度的平均值，将命题难度参数改为0.2
statement_difficulty_weight = 0.2
# 选项数
# 1-28修改：应测试prompt修改，减小选项数的影响至0.25
option_num_weight = 0.25
# 知识难度参数，改为0.1
knowledge_diff_weight = 0.05
# 命题难度
# 1-29修改：将其改为0.5
question_difficulty_weight = 0.5

# functions.
# 1-15新增：加入问题中命题的难度参数
def ask_level(chain_len: int, statement_difficulty: float, option_num: int, knowledge_diff: int, scene_level: float, question_difficulty: float) -> int:
    """根据题目参数评级

    Args:
        chain_len (int): 链长
        statement_difficulty (float): 已知命题的难度
        option_num (int): 选项数
        knowledge_num (int): 知识数量
        scene_level (float): 场景难度
        question_difficulty (float): 问题中命题的难度

    Returns:
        int: 难度等级
    """
    chain_level = chain_len * chain_length_weight
    statement_level = statement_difficulty * statement_difficulty_weight
    option_level = option_num * option_num_weight
    knowledge_level = knowledge_diff * knowledge_diff_weight
    # 1-15新增：加入命题难度参数
    difficulty_level = question_difficulty * question_difficulty_weight
    # level = chain_level + statement_level + option_level + knowledge_level + scene_level
    level = chain_level + statement_level + option_level + knowledge_level + scene_level + difficulty_level
    level_rank = round(level)
    # 1-20修改：修改难度等级上限
    if level_rank < level_lower_limit:
        return level_lower_limit
    elif level_rank > level_upper_limit:
        return level_upper_limit
    else:
        return level_rank