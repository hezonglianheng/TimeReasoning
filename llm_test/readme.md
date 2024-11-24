# 模型测试程序

本程序提供了一个利用OpenAI标准api对大模型进行测试的系统。

工作流：
- 利用[sample.py](sample.py)对试题进行随机抽样，获得抽样后的命题；
- 启动[main.py](main.py)，运行模型测试；
- 使用[postprocess.py](postprocess.py)提取答案并进行评分。

可以通过调整[config](config.py)中的内容对LLM测试过程进行控制。