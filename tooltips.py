# tooltips.py
# -*- coding: utf-8 -*-

tooltips = {
    "api_key": "在这里填写你的 API Key。\n\n- OpenAI 官方： https://platform.openai.com/account/api-keys\n- DeepSeek/Gemini 等：请到对应平台获取\n- Ollama 本地：可留空（会自动使用 'ollama' 作为占位 key）",
    "base_url": "模型的接口地址。\n\n- OpenAI 官方：https://api.openai.com/v1\n- Ollama 本地：http://localhost:11434/v1\n- ML Studio：http://localhost:1234/v1\n\n提示：如果你的地址末尾不是 /v1，程序会自动补全（除非你在地址末尾加 # 表示不自动处理）。",
    "interface_format": "指定 LLM 接口兼容格式，可选 OpenAI / Azure OpenAI / Ollama / ML Studio / Gemini 等。\n\n注意：OpenAI 兼容指的是“遵循 OpenAI API 的请求格式”，并非只能使用 api.openai.com。\n例如：Ollama 与 ML Studio 通常也可直接按 OpenAI 兼容方式调用。",
    "model_name": "要使用的模型名称，例如：gpt-4o、gpt-4o-mini、deepseek-chat 等。\n\n如果使用 Ollama，请填写你已在本地下载的模型名称（例如 qwen2.5:7b）。",
    "temperature": "温度控制模型的创意程度：\n\n- 0.3-0.5：稳定保守（推荐用于逻辑推理/一致性审校）\n- 0.6-0.7：平衡（推荐用于一般创作）\n- 0.8-1.0：创意十足（推荐用于脑洞大开）\n\n对于网文创作，推荐 0.75-0.85。",
    "max_tokens": "限制单次生成的最大 Token 数。\n\n请根据模型上下文及需求填写合适值。部分模型上限示例：\n- o1：100,000\n- o1-mini：65,536\n- gpt-4o：16,384\n- gpt-4o-mini：16,384\n- deepseek-reasoner：8,192\n- deepseek-chat：4,096",
    "timeout": "请求超时时间（秒）。网络不稳定时可以适当调大。",
    "embedding_api_key": "调用 Embedding 模型时所需的 API Key。",
    "embedding_interface_format": "Embedding 模型接口风格，比如 OpenAI 或 Ollama。",
    "embedding_url": "Embedding 模型接口地址。",
    "embedding_model_name": "Embedding 模型名称，如 text-embedding-ada-002。",
    "embedding_retrieval_k": "向量检索时返回的 Top-K 结果数量。",
    "topic": "小说的大致主题或主要故事背景描述。",
    "genre": "小说的题材类型，如玄幻、都市、科幻等。",
    "num_chapters": "小说期望的章节总数。",
    "word_number": "每章的目标字数。",
    "filepath": "生成文件存储的根目录路径。所有 txt 文件、向量库等放在该目录下。",
    "chapter_num": "当前正在处理的章节号，用于生成草稿或定稿操作。",
    "user_guidance": "为本章提供的一些额外指令或写作引导。",
    "characters_involved": "本章需要重点描写或影响剧情的角色名单。",
    "key_items": "在本章中出现的重要道具、线索或物品。",
    "scene_location": "本章主要发生的地点或场景描述。",
    "time_constraint": "本章剧情中涉及的时间压力或时限设置。",
    "interface_config": "选择你要编辑/使用的 LLM 接口配置（可新增/重命名/删除）。",

    "novel_name": "小说名称会用于创建项目文件夹，并写入 project.json。建议简短、可识别。",
    "author_name": "作者名将写入 project.json，仅用于项目记录（不会影响生成逻辑）。",
    "synopsis": "简介用于帮助模型理解作品方向。建议 3-8 句话包含：主角、目标、冲突、基调。",
    "planned_total_words": "计划总字数（50k - 500k）。向导会根据每章字数给出一个估算章数。",
    "planned_chapters": "根据计划总字数与每章字数估算的章节数。你可以之后在主界面修改。",
    "project_location": "选择项目保存位置。向导会在该目录下自动创建一个与小说名称同名的项目文件夹。",

    "webdav_url": "WebDAV 服务地址（例如：https://example.com/dav/）。用于备份/恢复配置文件。",
    "webdav_username": "WebDAV 账号用户名。",
    "webdav_password": "WebDAV 账号密码。"
}
