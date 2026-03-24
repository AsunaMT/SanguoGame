# 游戏更新日志

## 2026-03-24 更新

### 功能1：存档管理系统 ✅

**新增功能：**
- 支持多存档管理，不再局限于单个存档文件
- 可以创建、删除、覆盖存档
- 查看所有存档列表，包括存档时间、君主名、当前回合等信息

**新增 API 端点：**
- `GET /api/setup/saves` - 获取所有存档列表
- `POST /api/setup/saves` - 保存当前游戏到指定槽位
- `DELETE /api/setup/saves/{filename}` - 删除指定存档

**新增 Python 函数（在 game/save_load.py）：**
- `list_saves()` - 列出所有存档及其元数据
- `delete_save(filepath)` - 删除指定存档
- `save_game_with_slot(state, slot_name)` - 保存到指定槽位
- `load_game_from_slot(slot_name)` - 从指定槽位加载

---

### 功能2：游戏主界面和设置系统 ✅

**新增功能：**
- 游戏设置管理（文字速度、自动保存、音效、语言等）
- 游戏状态查询（是否有活跃游戏、当前回合等）
- 返回主菜单功能

**新增 API 端点：**
- `GET /api/menu/settings` - 获取当前游戏设置
- `POST /api/menu/settings` - 更新游戏设置
- `GET /api/menu/status` - 获取游戏状态信息
- `POST /api/menu/exit` - 返回主菜单

**设置选项：**
- `text_speed`: 文字显示速度（1-5）
- `auto_save`: 是否自动保存（true/false）
- `sound_enabled`: 音效开关（true/false）
- `language`: 语言设置（zh/en）

---

### 功能3：角色语言风格调整 ✅

**调整内容：**

#### 大臣角色描述（game/ministers.py）：
将所有大臣的描述语言调整为更直白易懂的风格：

**示例对比：**
- **原描述**："言简意赅，多用数字佐证，偶引古语，语气平稳不失威重"
- **新描述**："说话简单直接，喜欢用数字说明问题，偶尔引用经验，语气稳重"

- **原描述**："口若悬河，善用典故，语中常藏深意，笑里不失算计"
- **新描述**："说话流利，喜欢打比方，话里有话，笑着算计"

#### AI 对话提示词调整（ai/prompts/）：

**minister_base.txt：**
- **原规则**："半文言半白话，称玩家为'主公'，言简意赅不超150字"
- **新规则**："说话要直白易懂，不要太文言，叫玩家'主公'，说清楚意思，不超过150字"

**court_phases.txt：**
- 将"君上"改为"主公"
- 简化指令语言，去掉文言词汇
- 示例：将"不可强谏"改为"要委婉地说"

**narrator.txt：**
- 将"古典叙事风格"改为"描述世界发生的事情"
- 将"语言凝练，兼具史书笔法与小说生动感"改为"说话直接简单，把事情说清楚就行"
- 将"润色为一段优美的周报旁白"改为"整理成一段简短的周报"

---

## 技术细节

### 存档文件结构
```
saves/
├── gamestate.json          # 默认存档（兼容旧版本）
├── slot1.json              # 槽位1存档
├── slot2.json              # 槽位2存档
└── auto-save.json          # 自动存档
```

### 存档元数据格式
```json
{
  "filename": "gamestate.json",
  "filepath": "saves/gamestate.json",
  "ruler_name": "刘备",
  "turn": 5,
  "phase": "议政",
  "save_time": "2026-03-24 14:30:00",
  "timestamp": 1711234200.0
}
```

---

## 使用说明

### 存档管理
```bash
# 列出所有存档
GET /api/setup/saves

# 保存到槽位1
POST /api/setup/saves?slot_name=slot1

# 删除存档
DELETE /api/setup/saves/slot1.json
```

### 设置管理
```bash
# 获取设置
GET /api/menu/settings

# 更新设置
POST /api/menu/settings
Content-Type: application/json
{
  "text_speed": 2,
  "auto_save": true,
  "sound_enabled": false,
  "language": "zh"
}
```

---

## 兼容性说明

- **向后兼容**：保留了 `DEFAULT_SAVE_FILE` 路径（saves/gamestate.json），旧存档仍可正常加载
- **渐进式更新**：新功能不影响现有游戏逻辑
- **API 版本**：所有新增端点使用 `/api/` 前缀，与现有路由保持一致

---

## 后续计划

1. **前端 UI**：为存档管理、设置等功能添加图形界面
2. **自动存档**：实现定期自动存档功能
3. **云存档**：考虑支持云存储同步
4. **存档导入/导出**：支持导出存档文件到本地或从本地导入
