# DeepSeek API 迁移指南

## 📋 概述

已将游戏从 Gemini API 迁移到 DeepSeek API，解决了免费额度用完导致游戏卡住的问题。

## ✅ 已完成的修改

### 1. 安装依赖
- ✅ 安装了 `openai` 包（DeepSeek 兼容 OpenAI API 格式）
- ✅ 更新了 `requirements.txt`

### 2. 配置文件
- ✅ 修改 `config.py`：添加 DeepSeek API 配置
- ✅ 更新 `.env`：添加 DEEPSEEK_API_KEY 配置项

### 3. AI 适配器
- ✅ 重写 `ai/minister_agent.py`：使用 DeepSeek API 进行大臣对话
- ✅ 重写 `ai/world_narrator.py`：使用 DeepSeek API 进行旁白生成和命令解析

## 🔑 获取 DeepSeek API Key

### 步骤：

1. **访问 DeepSeek API 平台**
   - 网址：https://platform.deepseek.com

2. **注册/登录账号**
   - 使用手机号或邮箱注册
   - 完成实名认证（如需要）

3. **创建 API Key**
   - 进入控制台或 API Key 管理页面
   - 点击"创建 API Key"
   - 复制生成的 API Key（格式：sk-xxxxxxxxxxxx）

4. **配置到游戏**
   - 打开文件：`E:\sanguo-game\sanguo-game\.env`
   - 将 `DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here` 替换为你的实际 API Key
   - 保存文件

### 免费额度信息

根据 DeepSeek 官网信息：
- 新用户通常有免费额度
- 价格详见：https://api-docs.deepseek.com/quick_start/pricing
- DeepSeek 相比 Gemini 免费额度更充足，中文效果更好

## 🚀 启动游戏

配置完 API Key 后，重启游戏服务器：

```powershell
cd E:\sanguo-game\sanguo-game
python main.py
```

然后在浏览器访问：http://localhost:8000

## 🎮 游戏功能测试

1. **开局设置**：选择君主名号、福泽、大臣
2. **朝堂对话**：测试大臣是否能正常响应
3. **拟旨功能**：测试命令解析是否正常
4. **周报生成**：测试旁白生成是否正常

## 🐛 故障排查

### 问题 1：API Key 无效
**症状**：游戏卡在"大臣思量中"
**解决**：检查 `.env` 文件中的 API Key 是否正确，是否已激活

### 问题 2：网络连接问题
**症状**：API 调用超时
**解决**：检查网络连接，确认能访问 `https://api.deepseek.com`

### 问题 3：额度用完
**症状**：返回 429 错误
**解决**：
- 等待额度重置
- 或升级到付费计划
- DeepSeek 免费额度通常比 Gemini 充足

## 📝 技术细节

### DeepSeek API 配置
```python
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MAX_TOKENS = 2000
DEEPSEEK_TEMPERATURE = 0.8
```

### 使用的模型
- 大臣对话：`deepseek-chat`
- 旁白生成：`deepseek-chat`
- 命令解析：`deepseek-chat`

### 重试机制
- 遇到限流自动等待并重试（最多 2 次）
- 重试延迟：根据 API 返回的 `retry_after` 时间

## 💡 优势对比

| 特性 | Gemini | DeepSeek |
|------|--------|----------|
| 中文效果 | 一般 | 优秀 |
| 免费额度 | 严格 | 充足 |
| 价格 | 较高 | 亲民 |
| 国内访问 | 需要代理 | 无需代理 |
| API 兼容性 | 独立 | OpenAI 兼容 |

## 🔄 回退到 Gemini（可选）

如果需要回退到 Gemini：
1. 恢复 `config.py` 中的 Gemini 配置
2. 恢复 `ai/minister_agent.py` 和 `ai/world_narrator.py` 的旧版本
3. 更新 `requirements.txt` 添加 `google-generativeai`
4. 重新安装依赖
