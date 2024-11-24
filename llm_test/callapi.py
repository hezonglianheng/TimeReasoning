# encoding: utf8
# author: Qin Yuhang
# date: 2024-11-15

"""包含调用api的函数的文件
"""

import config
from pathlib import Path
import requests

TEMPERATURE = 0.1 # 固定温度；降低温度，提高生成文本的准确性

def callapi(text: str, model_name: str) -> dict:
    """调用api的函数

    Args:
        text (str): 输入的文本内容
        model_name (str): 模型名称

    Returns:
        dict: 完整的对话过程
    """
    key_file = Path(__file__).parent / "api_key/api.txt"
    with key_file.open(mode="r", encoding="utf-8") as f:
        api = f.read().strip() # 去除前导和后继空格字符的api字符

    headers = {
        'Content-Type': 'application/json', 
        'Accept': 'application/json', 
        'Authorization': f'Bearer {api}', 
    }
    body = {
        "model": model_name, 
        "messages": [
            {
                'role': 'user', 
                'content': text
            }
        ], 
        # 'temperature': config.temperature, # 降低温度，提高生成文本的准确性
        # 'max_tokens': config.max_tokens, # 生成文本的最大长度
    }
    if model_name not in ["o1-preview"]:
        body['temperature'] = config.temperature
    response = requests.post(url=config.url, headers=headers, json=body)
    return response.json()