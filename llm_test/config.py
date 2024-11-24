# encoding: utf8
# author: Qin Yuhang
# date: 2024-11-15

"""配置文件
"""

model_names = [
    "o1-preview", # GPT-o1
    "gpt-3.5-turbo", # GPT-3.5 Turbo
    "gpt-4", # GPT-4
    "claude-3-5-sonnet-20241022", # Claude 3.5
    "ERNIE-Bot-4", # 文心一言
    "glm-4-plus", # ChatGLM
    "qwen-max", # 通义千问
    "moonshot-v1-128k", # 月之暗面
    "llama3.1-405b-instruct", # Llama 3.1
    "mistral-7b-instruct", # Mistral 7B
]

temperature = 0.1 # 固定温度；降低温度，提高生成文本的准确性
max_tokens = 50 # 生成文本的最大长度
url = 'https://api.zhizengzeng.com/v1/chat/completions' # api的url
question_num = 100 # 选择的题目的数量

# system角色的输入
system_text = "你是一位擅长时间推理的学者，你的任务是阅读文本并整理出其中的时间顺序关系，之后只以选项字母回答问题。"

# 少样本使用的文本
few_shot = """
请仿照下述示例回答问题。\n
小明的女儿正在给朋友讲述父亲的一生：在1911年，他开始上初中；他上初中的时间已经长达3年；他在1914年开始上高中；他在初中毕业的3年之后高中毕业；遇见未来的妻子是在开始上高中之后的第3年发生的；在1927年，他结婚；他在遇见未来的妻子的11年之后成为父亲；他退休的时间比成为父亲晚了37年。\n
请问：他____的时间比结婚早。\n
A.遇见未来的妻子 B.退休 C.结婚 D.开始上高中\n
答案：A、D\n\n
小明的女儿正在给朋友讲述父亲的一生：他自1911年起到1914年止上初中；他开始上高中的时候是在1914年；他高中毕业，那是在1917年；在开始上初中之后6年，他才遇见未来的妻子；他结婚的时间比遇见未来的妻子晚了10年；成为父亲是在开始上初中之后的第17年发生的；退休是在初中毕业之后的第51年发生的。\n
请问：他在退休的____年之前结婚。\n
A.18 B.38 C.32 D.9\n
答案：B\n
"""