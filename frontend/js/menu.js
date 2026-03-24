/* ═══════════════════════════════════════════════════════════
   menu.js v2.0 — 主菜单逻辑
   ═══════════════════════════════════════════════════════════ */

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
    if (textSpeedSlider) {
      textSpeedSlider.addEventListener('input', (e) => {
        document.getElementById('text-speed-value').textContent = e.target.value;
      });
    }
  }

  async checkGameState() {
    try {
      const data = await API.get('/api/menu/status');
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
    showLoading('加载游戏存档……');
    try {
      const state = await API.get('/api/world/state');

      showScreen('screen-court');
      loadStateToUI(state);

      document.getElementById('chat-messages').innerHTML = '';
      appendSystem(`已恢复存档：第${state.turn}/${state.max_turns}轮，${state.date}`);
    } catch (error) {
      alert('无法继续游戏，可能没有存档。请开始新游戏。');
      console.error(error);
    } finally {
      hideLoading();
    }
  }

  async newGame() {
    // 重置服务端状态
    try {
      await API.post('/api/setup/reset');
    } catch (_) { /* 可能没有活跃游戏 */ }

    showScreen('screen-setup');
    if (app.setupScreen && typeof app.setupScreen.init === 'function') {
      app.setupScreen.init();
    }
  }

  async showSaveList() {
    try {
      const data = await API.get('/api/setup/saves');
      const saveListContent = document.getElementById('save-list-content');
      saveListContent.innerHTML = '';

      if (!data.saves || data.saves.length === 0) {
        saveListContent.innerHTML = '<p class="no-saves">暂无存档</p>';
      } else {
        data.saves.forEach(save => {
          const saveItem = document.createElement('div');
          saveItem.className = 'save-item';
          saveItem.innerHTML = `
            <div class="save-info">
              <h4>${save.ruler_name || '未知'}</h4>
              <p>第${save.turn || '?'}轮</p>
              <p class="save-time">${save.save_time || ''}</p>
            </div>
            <div class="save-actions">
              <button class="btn-load" data-filename="${save.filename}">读取</button>
              <button class="btn-del-save" data-filename="${save.filename}">删除</button>
            </div>
          `;
          saveListContent.appendChild(saveItem);
        });

        // 读取按钮
        saveListContent.querySelectorAll('.btn-load').forEach(btn => {
          btn.addEventListener('click', (e) => {
            this.loadSave(e.target.dataset.filename);
          });
        });

        // 删除按钮
        saveListContent.querySelectorAll('.btn-del-save').forEach(btn => {
          btn.addEventListener('click', async (e) => {
            const fn = e.target.dataset.filename;
            if (confirm(`确认删除存档 ${fn}？`)) {
              try {
                await API.del(`/api/setup/saves/${fn}`);
                this.showSaveList(); // 刷新列表
              } catch (err) {
                alert(`删除失败：${err.message}`);
              }
            }
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
    showLoading('加载存档……');
    try {
      const state = await API.post(`/api/setup/saves/${filename}`);

      this.hideSaveList();
      showScreen('screen-court');

      // v2.0: 需要重新获取格式化后的状态
      const worldState = await API.get('/api/world/state');
      loadStateToUI(worldState);

      document.getElementById('chat-messages').innerHTML = '';
      appendSystem(`已加载存档：第${worldState.turn}/${worldState.max_turns}轮，${worldState.date}`);
    } catch (error) {
      alert(`读取存档失败：${error.message}`);
      console.error(error);
    } finally {
      hideLoading();
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
      const settings = await API.get('/api/menu/settings');
      const textSpeedEl = document.getElementById('setting-text-speed');
      const textSpeedVal = document.getElementById('text-speed-value');
      const autoSaveEl = document.getElementById('setting-auto-save');
      const soundEl = document.getElementById('setting-sound');

      if (textSpeedEl) textSpeedEl.value = settings.text_speed;
      if (textSpeedVal) textSpeedVal.textContent = settings.text_speed;
      if (autoSaveEl) autoSaveEl.checked = settings.auto_save;
      if (soundEl) soundEl.checked = settings.sound_enabled;
    } catch (error) {
      console.error('加载设置失败:', error);
    }
  }

  async saveSettings() {
    try {
      const settings = {
        text_speed: parseInt(document.getElementById('setting-text-speed').value),
        auto_save: document.getElementById('setting-auto-save').checked,
        sound_enabled: document.getElementById('setting-sound').checked,
      };

      await API.post('/api/menu/settings', settings);
      alert('设置已保存');
      this.hideSettings();
    } catch (error) {
      alert('保存设置失败');
      console.error(error);
    }
  }
}
