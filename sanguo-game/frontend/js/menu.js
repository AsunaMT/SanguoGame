// 主菜单逻辑
class MainMenu {
  constructor() {
    this.initEventListeners();
    this.loadSettings();
    this.checkGameState();
  }

  initEventListeners() {
    document.getElementById('btn-continue-game').addEventListener('click', () => this.continueGame());
    document.getElementById('btn-new-game').addEventListener('click', () => this.newGame());
    document.getElementById('btn-load-save').addEventListener('click', () => this.showSaveList());
    document.getElementById('btn-settings').addEventListener('click', () => this.showSettings());

    // 存档列表模态框
    document.getElementById('btn-close-save-list').addEventListener('click', () => this.hideSaveList());

    // 设置模态框
    document.getElementById('btn-close-settings').addEventListener('click', () => this.hideSettings());
    document.getElementById('btn-save-settings').addEventListener('click', () => this.saveSettings());

    // 文字速度滑块
    const textSpeedSlider = document.getElementById('setting-text-speed');
    textSpeedSlider.addEventListener('input', (e) => {
      document.getElementById('text-speed-value').textContent = e.target.value;
    });
  }

  async checkGameState() {
    try {
      const response = await fetch('/api/menu/status');
      const data = await response.json();

      // 如果没有活跃游戏，禁用"继续游戏"按钮
      const continueBtn = document.getElementById('btn-continue-game');
      if (!data.has_active_game) {
        continueBtn.disabled = true;
        continueBtn.classList.add('disabled');
      } else {
        continueBtn.disabled = false;
        continueBtn.classList.remove('disabled');
      }
    } catch (error) {
      console.error('检查游戏状态失败:', error);
    }
  }

  async continueGame() {
    try {
      const response = await fetch('/api/world/state');
      if (!response.ok) {
        throw new Error('无法加载游戏状态');
      }

      const state = await response.json();

      // 切换到朝堂界面
      this.switchToScreen('screen-court');
      app.loadState(state);
      app.showPhaseTransition();
    } catch (error) {
      alert('无法继续游戏，可能没有存档。请开始新游戏。');
      console.error(error);
    }
  }

  newGame() {
    // 切换到开局界面
    this.switchToScreen('screen-setup');
    // 初始化开局界面（如果setupScreen存在）
    if (app.setupScreen && typeof app.setupScreen.init === 'function') {
      app.setupScreen.init();
    }
  }

  async showSaveList() {
    try {
      const response = await fetch('/api/setup/saves');
      const data = await response.json();

      const saveListContent = document.getElementById('save-list-content');
      saveListContent.innerHTML = '';

      if (data.saves.length === 0) {
        saveListContent.innerHTML = '<p class="no-saves">暂无存档</p>';
      } else {
        data.saves.forEach(save => {
          const saveItem = document.createElement('div');
          saveItem.className = 'save-item';
          saveItem.innerHTML = `
            <div class="save-info">
              <h4>${save.ruler_name}</h4>
              <p>第${save.turn}周 - ${save.phase}</p>
              <p class="save-time">保存时间: ${save.save_time}</p>
            </div>
            <button class="btn-load" data-filename="${save.filename}">读取</button>
          `;
          saveListContent.appendChild(saveItem);
        });

        // 绑定读取按钮事件
        saveListContent.querySelectorAll('.btn-load').forEach(btn => {
          btn.addEventListener('click', (e) => {
            const filename = e.target.dataset.filename;
            this.loadSave(filename);
          });
        });
      }

      document.getElementById('save-list-modal').classList.remove('hidden');
    } catch (error) {
      alert('加载存档列表失败');
      console.error(error);
    }
  }

  hideSaveList() {
    document.getElementById('save-list-modal').classList.add('hidden');
  }

  async loadSave(filename) {
    try {
      const response = await fetch(`/api/setup/saves/${filename}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('读取存档失败');
      }

      this.hideSaveList();
      this.switchToScreen('screen-court');

      const state = await response.json();
      app.loadState(state);
      app.showPhaseTransition();
    } catch (error) {
      alert('读取存档失败');
      console.error(error);
    }
  }

  showSettings() {
    document.getElementById('settings-modal').classList.remove('hidden');
  }

  hideSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
  }

  async loadSettings() {
    try {
      const response = await fetch('/api/menu/settings');
      const settings = await response.json();

      document.getElementById('setting-text-speed').value = settings.text_speed;
      document.getElementById('text-speed-value').textContent = settings.text_speed;
      document.getElementById('setting-auto-save').checked = settings.auto_save;
      document.getElementById('setting-sound').checked = settings.sound_enabled;
    } catch (error) {
      console.error('加载设置失败:', error);
    }
  }

  async saveSettings() {
    try {
      const settings = {
        text_speed: parseInt(document.getElementById('setting-text-speed').value),
        auto_save: document.getElementById('setting-auto-save').checked,
        sound_enabled: document.getElementById('setting-sound').checked
      };

      const response = await fetch('/api/menu/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      });

      if (!response.ok) {
        throw new Error('保存设置失败');
      }

      alert('设置已保存');
      this.hideSettings();
    } catch (error) {
      alert('保存设置失败');
      console.error(error);
    }
  }

  switchToScreen(screenId) {
    // 隐藏所有屏幕
    document.querySelectorAll('.screen').forEach(screen => {
      screen.classList.add('hidden');
    });

    // 显示目标屏幕
    document.getElementById(screenId).classList.remove('hidden');
  }
}
