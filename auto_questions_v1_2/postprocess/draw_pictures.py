# encoding: utf8

import matplotlib.pyplot as plt
import numpy as np
import sys
import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

# 将父目录加入到sys.path中
sys.path.append(str(Path(__file__).resolve().parent.parent))

import proposition.config as config

# 设置中文字体以支持中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False

USE_MODELS = [
    "deepseek-reasoner", 
    "qwen-max", 
    "o3-mini", 
    "claude-3-5-sonnet-20241022", 
]

def cope_with_key(key: str) -> tuple[str, str, str]:
    """处理字典的键

    Args:
        key (str): 键

    Returns:
        tuple[str, str, str]: 属性、语言、模型
    """
    attr, lang, model = key.split('_', maxsplit=2)
    return attr, lang, model

def draw_accuracy(acc_dict: dict[str, float], save_path: str):
    info_tuple = [cope_with_key(key) for key in acc_dict.keys()]
    selected_info_tuple = [1 if info[2] in USE_MODELS else 0 for info in info_tuple]
    
    cn_acc = defaultdict(float)
    en_acc = defaultdict(float)
    total_acc = defaultdict(float)
    
    for key, info, flag in zip(acc_dict.keys(), info_tuple, selected_info_tuple):
        if flag == 0:
            continue
        attr, lang, model = info
        accuracy = acc_dict[key]
        if lang == 'cn':
            cn_acc[model] = accuracy
        elif lang == 'en':
            en_acc[model] = accuracy
        total_acc[model] += accuracy

    models = USE_MODELS
    x = range(len(models))
    cn_values = [cn_acc[model] for model in models]
    en_values = [en_acc[model] for model in models]
    total_values = [total_acc[model] / 2 for model in models]
    
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 7))

    bars_cn = ax.bar([i - width for i in x], cn_values, width=width, label='Chinese', color='b')
    bars_en = ax.bar(x,                       en_values, width=width, label='English', color='g')
    bars_total = ax.bar([i + width for i in x], total_values, width=width, label='Total', color='r')

    ax.set_xticks(list(x))
    ax.set_xticklabels(models, rotation=15)
    ax.set_ylabel('Accuracy')
    ax.set_xlabel('Models')
    ax.set_title('Accuracy by Language and Model')
    ax.legend(ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.18))

    # 在柱顶添加标签
    ax.bar_label(bars_cn, fmt='%.2f', padding=2)
    ax.bar_label(bars_en, fmt='%.2f', padding=2)
    ax.bar_label(bars_total, fmt='%.2f', padding=2)

    plt.tight_layout()
    fig_path = Path(save_path) / 'accuracy_in_language.png'
    plt.savefig(fig_path, dpi=300)
    plt.close()

    print(f"Figure saved to {fig_path}.")

def draw_difficulty(difficulty_dict: dict[str, float], save_path: str, lang: Optional[str] = None):
    info_tuple = [cope_with_key(key) for key in difficulty_dict.keys()]
    selected_info_tuple = [1 if info[2] in USE_MODELS else 0 for info in info_tuple]

    level1 = defaultdict(float)
    level2 = defaultdict(float)
    level3 = defaultdict(float)

    for key, info, flag in zip(difficulty_dict.keys(), info_tuple, selected_info_tuple):
        if flag == 0:
            continue
        attr, lang_in_key, model = info
        if lang is not None and lang_in_key != lang:
            continue
        difficulty = difficulty_dict[key]
        if attr == '1':
            if lang is None:
                level1[model] += difficulty / 2
            else:
                level1[model] += difficulty
        elif attr == '2':
            if lang is None:
                level2[model] += difficulty / 2
            else:
                level2[model] += difficulty
        elif attr == '3':
            if lang is None:
                level3[model] += difficulty / 2
            else:
                level3[model] += difficulty

    models = USE_MODELS
    x = range(len(models))
    level1_values = [level1[model] for model in models]
    level2_values = [level2[model] for model in models]
    level3_values = [level3[model] for model in models]
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 7))
    bars_level1 = ax.bar([i - width for i in x], level1_values, width=width, label='Level 1', color='b')
    bars_level2 = ax.bar(x,                       level2_values, width=width, label='Level 2', color='g')
    bars_level3 = ax.bar([i + width for i in x], level3_values, width=width, label='Level 3', color='r')
    ax.set_xticks(list(x))
    ax.set_xticklabels(models, rotation=15)
    ax.set_ylabel('Accuracy')
    ax.set_xlabel('Models')
    ax.set_title(f'Average Accuracy by Level in ({lang})' if lang else 'Average Accuracy by Level')
    ax.legend(ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.18))
    # 在柱顶添加标签
    ax.bar_label(bars_level1, fmt='%.2f', padding=2)
    ax.bar_label(bars_level2, fmt='%.2f', padding=2)
    ax.bar_label(bars_level3, fmt='%.2f', padding=2)
    plt.tight_layout()
    fig_path = Path(save_path) / (f'difficulty_in_{lang}.png' if lang else 'difficulty.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

    print(f"Figure saved to {fig_path}.")

def draw_scene_type(scene_type_dict: dict[str, float], save_path: str, lang: Optional[str] = None):
    info_tuple = [cope_with_key(key) for key in scene_type_dict.keys()]
    selected_info_tuple = [1 if info[2] in USE_MODELS else 0 for info in info_tuple]

    linear_level = defaultdict(float)
    cyclic_level = defaultdict(float)

    for key, info, flag in zip(scene_type_dict.keys(), info_tuple, selected_info_tuple):
        if flag == 0:
            continue
        attr, lang_in_key, model = info
        if lang is not None and lang_in_key != lang:
            continue
        difficulty = scene_type_dict[key]
        if attr == 'Linear Scenario':
            if lang is None:
                linear_level[model] += difficulty / 2
            else:
                linear_level[model] += difficulty
        elif attr == 'Cyclic Scenario':
            if lang is None:
                cyclic_level[model] += difficulty / 2
            else:
                cyclic_level[model] += difficulty

    models = USE_MODELS
    x = range(len(models))
    level1_values = [linear_level[model] for model in models]
    level2_values = [cyclic_level[model] for model in models]
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 7))
    bars_level1 = ax.bar([i - width/2 for i in x], level1_values, width=width, label='Linear Scenario', color='b')
    bars_level2 = ax.bar([i + width/2 for i in x], level2_values, width=width, label='Cyclic Scenario', color='g')
    ax.set_xticks(list(x))
    ax.set_xticklabels(models, rotation=15)
    ax.set_ylabel('Accuracy')
    ax.set_xlabel('Models')
    ax.set_title(f'Average Accuracy by Scenario in ({lang})' if lang else 'Average Accuracy by Scenario')
    ax.legend(ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.18))
    # 在柱顶添加标签
    ax.bar_label(bars_level1, fmt='%.2f', padding=2)
    ax.bar_label(bars_level2, fmt='%.2f', padding=2)
    plt.tight_layout()
    fig_path = Path(save_path) / (f'scenario_in_{lang}.png' if lang else 'scenario.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

    print(f"Figure saved to {fig_path}.")

def draw_question_data(question_data: dict[str, dict[str, float]], save_path: str, lang: Optional[str] = None):
    info_tuple = [cope_with_key(key) for key in question_data.keys()]
    selected_info_tuple = [1 if info[2] in USE_MODELS else 0 for info in info_tuple]

    precise = defaultdict(float)
    correct = defaultdict(float)
    incorrect = defaultdict(float)

    for key, info, flag in zip(question_data.keys(), info_tuple, selected_info_tuple):
        if flag == 0:
            continue
        attr, lang_in_key, model = info
        if lang is not None and lang_in_key != lang:
            continue
        acc = question_data[key]
        if attr == 'Precise Event':
            if lang is None:
                precise[model] += acc / 2
            else:
                precise[model] += acc
        elif attr == 'Correct Statements':
            if lang is None:
                correct[model] += acc / 2
            else:
                correct[model] += acc
        elif attr == 'Incorrect Statements':
            if lang is None:
                incorrect[model] += acc / 2
            else:
                incorrect[model] += acc

    models = USE_MODELS
    x = range(len(models))
    precise_values = [precise[model] for model in models]
    correct_values = [correct[model] for model in models]
    incorrect_values = [incorrect[model] for model in models]
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 7))
    bars_precise = ax.bar([i - width for i in x], precise_values, width=width, label='Precise Event', color='b')
    bars_correct = ax.bar(x,                       correct_values, width=width, label='Correct Statements', color='g')
    bars_incorrect = ax.bar([i + width for i in x], incorrect_values, width=width, label='Incorrect Statements', color='r')
    ax.set_xticks(list(x))
    ax.set_xticklabels(models, rotation=15)
    ax.set_ylabel('Accuracy')
    ax.set_xlabel('Models')
    ax.set_title(f'Average Accuracy by Question Type in ({lang})' if lang else 'Average Accuracy by Question Type')
    ax.legend(ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.18))
    # 在柱顶添加标签
    ax.bar_label(bars_precise, fmt='%.2f', padding=2)
    ax.bar_label(bars_correct, fmt='%.2f', padding=2)
    ax.bar_label(bars_incorrect, fmt='%.2f', padding=2)
    plt.tight_layout()
    fig_path = Path(save_path) / (f'question_type_in_{lang}.png' if lang else 'question_type.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()

    print(f"Figure saved to {fig_path}.")

def draw_question_tags(question_data: dict[str, dict[str, float]], save_path: str, lang: Optional[str] = None):
    info_tuple = [cope_with_key(key) for key in question_data.keys()]
    selected_info_tuple = [1 if info[2] in USE_MODELS else 0 for info in info_tuple]

    question_tags_set = set([i[0] for i, j in zip(info_tuple, selected_info_tuple) if j == 1])
    acc_matrix = np.zeros((len(USE_MODELS), len(question_tags_set)), dtype=float)

    for key, info, flag in zip(question_data.keys(), info_tuple, selected_info_tuple):
        if flag == 0:
            continue
        attr, lang_in_key, model = info
        if lang is not None and lang_in_key != lang:
            continue
        # acc = question_data[key]
        acc = float(question_data[key].split('(')[0])
        tag_index = list(question_tags_set).index(attr)
        model_index = USE_MODELS.index(model)
        acc_matrix[model_index][tag_index] += acc

    if lang is None:
        acc_matrix /= 2

    # 绘制雷达图
    labels = list(question_tags_set)
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    acc_matrix = np.concatenate((acc_matrix, acc_matrix[:, [0]]), axis=1)
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    for i, model in enumerate(USE_MODELS):
        values = acc_matrix[i].tolist()
        ax.plot(angles, values, label=model)
        ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_yticklabels([f'{i:.1f}' for i in np.linspace(0, 1, 6)])
    ax.set_ylim(0, 1)
    ax.set_title(f'Accuracy by Question Tags in ({lang})' if lang else 'Accuracy by Question Tags')
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.3))
    plt.tight_layout()
    fig_path = Path(save_path) / (f'question_tags_in_{lang}.png' if lang else 'question_tags.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"Figure saved to {fig_path}.")

def draw_statement_tags(statement_data: dict[str, dict[int, float]], save_path: str, lang: Optional[str] = None):
    info_tuple = [cope_with_key(key) for key in statement_data.keys()]
    selected_info_tuple = [1 if info[2] in USE_MODELS else 0 for info in info_tuple]

    statement_tags_set = set([i[0] for i, j in zip(info_tuple, selected_info_tuple) if j == 1])
    acc_matrix = np.zeros((len(USE_MODELS), len(statement_tags_set)), dtype=float)

    for key, info, flag in zip(statement_data.keys(), info_tuple, selected_info_tuple):
        if flag == 0:
            continue
        attr, lang_in_key, model = info
        if lang is not None and lang_in_key != lang:
            continue
        # acc = statement_data[key]
        acc = float(statement_data[key].split('(')[0])
        tag_index = list(statement_tags_set).index(attr)
        model_index = USE_MODELS.index(model)
        acc_matrix[model_index][tag_index] += acc

    if lang is None:
        acc_matrix /= 2

    # 绘制雷达图
    labels = list(statement_tags_set)
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    acc_matrix = np.concatenate((acc_matrix, acc_matrix[:, [0]]), axis=1)
    angles += angles[:1]
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    for i, model in enumerate(USE_MODELS):
        values = acc_matrix[i].tolist()
        ax.plot(angles, values, label=model)
        ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_yticklabels([f'{i:.1f}' for i in np.linspace(0, 1, 6)])
    ax.set_ylim(0, 1)
    ax.set_title(f'Accuracy by Statement Tags in ({lang})' if lang else 'Accuracy by Statement Tags')
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.3))
    plt.tight_layout()
    fig_path = Path(save_path) / (f'statement_tags_in_{lang}.png' if lang else 'statement_tags.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"Figure saved to {fig_path}.")

def draw_chain_length(chain_len_data: dict[str, dict[int, float]], save_path: str, lang: Optional[str] = None):
    info_tuple = [cope_with_key(key) for key in chain_len_data.keys()]
    selected_info_tuple = [1 if info[2] in USE_MODELS else 0 for info in info_tuple]

    chain_len_set = set([i[0] for i, j in zip(info_tuple, selected_info_tuple) if j == 1])
    acc_matrix = np.zeros((len(USE_MODELS), len(chain_len_set)), dtype=float)

    for key, info, flag in zip(chain_len_data.keys(), info_tuple, selected_info_tuple):
        if flag == 0:
            continue
        attr, lang_in_key, model = info
        if lang is not None and lang_in_key != lang:
            continue
        acc = chain_len_data[key]
        len_index = list(chain_len_set).index(attr)
        model_index = USE_MODELS.index(model)
        acc_matrix[model_index][len_index] += acc

    if lang is None:
        acc_matrix /= 2

    # 绘制柱状图
    models = USE_MODELS
    x = range(len(models))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8, 7))
    bars_list = []
    for i, chain_len in enumerate(chain_len_set):
        values = [acc_matrix[j][i] for j in range(len(USE_MODELS))]
        bars = ax.bar([j + (i - len(chain_len_set)/2) * width for j in x], values, width=width, label=f'{chain_len.rsplit("(", 1)[0]}')
        bars_list.append(bars)
    ax.set_xticks(list(x))
    ax.set_xticklabels(models, rotation=15)
    ax.set_ylabel('Accuracy')
    ax.set_xlabel('Models')
    ax.set_title(f'Average Accuracy by Chain Length in ({lang})' if lang else 'Average Accuracy by Chain Length')
    ax.legend(ncol=len(chain_len_set), loc='upper center', bbox_to_anchor=(0.5, -0.18))
    # 在柱顶添加标签
    for bars in bars_list:
        ax.bar_label(bars, fmt='%.2f', padding=2)
    plt.tight_layout()
    fig_path = Path(save_path) / (f'chain_length_in_{lang}.png' if lang else 'chain_length.png')
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"Figure saved to {fig_path}.")

def read_jsonfile(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def main():
    analysis_path = input("请输入分析结果文件路径：")
    save_path = input("请输入保存图片的文件夹路径：")
    analysis_data = read_jsonfile(analysis_path)
    draw_accuracy(analysis_data['acc'], save_path)
    draw_difficulty(analysis_data['difficulty_level'], save_path)
    draw_difficulty(analysis_data['difficulty_level'], save_path, lang='cn')
    draw_difficulty(analysis_data['difficulty_level'], save_path, lang='en')
    draw_scene_type(analysis_data['scene_type'], save_path)
    draw_scene_type(analysis_data['scene_type'], save_path, lang='cn')
    draw_scene_type(analysis_data['scene_type'], save_path, lang='en')
    draw_question_data(analysis_data['question_type'], save_path)
    draw_question_data(analysis_data['question_type'], save_path, lang='cn')
    draw_question_data(analysis_data['question_type'], save_path, lang='en')
    draw_question_tags(analysis_data['question_tag'], save_path)
    draw_question_tags(analysis_data['question_tag'], save_path, lang='cn')
    draw_question_tags(analysis_data['question_tag'], save_path, lang='en')
    draw_statement_tags(analysis_data['statement_tag'], save_path)
    draw_statement_tags(analysis_data['statement_tag'], save_path, lang='cn')
    draw_statement_tags(analysis_data['statement_tag'], save_path, lang='en')
    draw_chain_length(analysis_data['chain_length'], save_path)
    draw_chain_length(analysis_data['chain_length'], save_path, lang='cn')
    draw_chain_length(analysis_data['chain_length'], save_path, lang='en')

if __name__ == "__main__":
    main()