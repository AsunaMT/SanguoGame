# 主菜单按钮修复说明

## 问题描述
打开游戏后进入主菜单界面，所有按钮（继续游戏、新游戏、读取存档、设置）都无法点击，点击后没有反应。

## 问题原因

### 1. app对象未定义
在`frontend/js/app.js`中，代码试图执行：
```javascript
app.mainMenu = new MainMenu();
```
但是`app`对象从未被定义，导致JavaScript错误。

### 2. 类方法引用错误
在`frontend/js/menu.js`中，代码试图调用：
```javascript
app.courtScreen.loadState(state);
app.courtScreen.showPhaseTransition();
app.setupScreen.init();
```
但这些方法和对象不存在。

### 3. SetupScreen类缺失
`frontend/js/setup.js`中没有`SetupScreen`类的定义，只有全局函数，而`menu.js`期望它是一个类。

## 解决方案

### 1. 修复app.js
添加了全局`app`对象：
```javascript
const app = {
  mainMenu: null,
  setupScreen: null,
  courtScreen: null,

  loadState: function(state) {
    // 更新游戏状态
  },

  showPhaseTransition: function() {
    // 显示阶段转换提示
  }
};
```

### 2. 修复menu.js
将对不存在的`app.courtScreen`方法的调用改为调用`app`对象的方法：
```javascript
app.loadState(state);
app.showPhaseTransition();
```

添加了对`app.setupScreen`存在性的检查：
```javascript
if (app.setupScreen && typeof app.setupScreen.init === 'function') {
  app.setupScreen.init();
}
```

### 3. 重构setup.js
创建了`SetupScreen`类：
```javascript
class SetupScreen {
  constructor() {
    this.selectedBuffs = new Set();
    this.selectedMinisters = {};
  }

  async init() {
    // 初始化开局界面
  }

  renderBuffs(buffs) {
    // 渲染福泽列表
  }

  // ... 其他方法
}
```

在DOMContentLoaded事件中创建实例：
```javascript
window.addEventListener('DOMContentLoaded', () => {
  app.setupScreen = new SetupScreen();
  app.setupScreen.init().catch(console.error);
  // ... 事件绑定
});
```

## 测试方法

### 1. 启动游戏服务器
```bash
cd E:\sanguo-game\sanguo-game
python main.py
```

### 2. 访问游戏
打开浏览器访问：http://localhost:8001

### 3. 测试按钮
- 点击"继续游戏"按钮
- 点击"新游戏"按钮
- 点击"读取存档"按钮
- 点击"设置"按钮

所有按钮都应该能够正常响应点击事件。

## 技术细节

1. **面向对象设计**: 使用类来管理各个界面的状态和方法
2. **全局协调器**: app对象作为全局协调器，管理界面切换和数据共享
3. **错误处理**: 添加了对对象存在性的检查，避免运行时错误
4. **向后兼容**: 保持了现有API和功能的兼容性

## 相关文件

- `frontend/js/app.js`: 应用主控制器
- `frontend/js/menu.js`: 主菜单逻辑
- `frontend/js/setup.js`: 开局界面逻辑
- `frontend/js/court.js`: 朝堂界面逻辑
- `frontend/index.html`: 主HTML文件
