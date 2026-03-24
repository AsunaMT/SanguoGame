/* ═══════════════════════════════════════════════════════════
   setup.js v2.1 — 开局流程（赐名 + 择将）
   ═══════════════════════════════════════════════════════════ */

const ROLE_BADGE = {
  internal:  '内政',
  military:  '军事',
  diplomacy: '外交',
};

function showSetupError(msg) {
  document.getElementById('setup-error').textContent = msg;
}
function clearSetupError() {
  document.getElementById('setup-error').textContent = '';
}


// ── 开始游戏 ─────────────────────────────────────────────
async function startGame() {
  const rulerName = document.getElementById('ruler-name').value.trim();
  const selectedMinisters = app.setupScreen.selectedMinisters;

  if (!rulerName) { showSetupError('请输入名号'); return; }
  if (!['internal', 'military', 'diplomacy'].every(r => selectedMinisters[r])) {
    showSetupError('请三个职位各选一位大臣'); return;
  }

  showLoading('正在创建游戏……');
  try {
    const res = await API.post('/api/setup/create', {
      ruler_name: rulerName,
      minister_ids: Object.values(selectedMinisters),
    });

    // 进入朝堂界面
    showScreen('screen-court');

    // 加载完整状态
    const state = await API.get('/api/world/state');
    loadStateToUI(state);

    // 清空聊天区
    document.getElementById('chat-messages').innerHTML = '';
    appendSystem(`欢迎，${rulerName}！${res.message}`);
    appendSystem(`你有${state.max_turns}轮时间统一天下，否则寿命将尽！`);
  } catch (e) {
    showSetupError(`创建失败：${e.message}`);
  } finally {
    hideLoading();
  }
}

function backToMenu() {
  showScreen('screen-main-menu');
}


// ── SetupScreen 类 ───────────────────────────────────────
class SetupScreen {
  constructor() {
    this.selectedMinisters = {};  // role -> minister_id
  }

  async init() {
    this.selectedMinisters = {};

    try {
      const candidatesData = await API.get('/api/setup/candidates');
      this.renderCandidates(candidatesData.candidates);
      this.checkSetupReady();
    } catch (e) {
      showSetupError(`加载开局数据失败：${e.message}`);
    }
  }

  renderCandidates(candidates) {
    const grid = document.getElementById('minister-candidates');
    grid.innerHTML = '';

    // 按角色分组
    const byRole = { internal: [], military: [], diplomacy: [] };
    for (const c of candidates) {
      if (byRole[c.role]) byRole[c.role].push(c);
    }

    for (const [role, list] of Object.entries(byRole)) {
      if (list.length === 0) continue;

      const section = document.createElement('div');
      section.className = 'candidate-section';
      section.innerHTML = `<h3 class="candidate-role-title">${ROLE_BADGE[role] || role}</h3>`;

      const row = document.createElement('div');
      row.className = 'candidate-row';

      for (const c of list) {
        const card = document.createElement('div');
        card.className = 'minister-card';
        card.dataset.id = c.id;
        card.dataset.role = c.role;

        const traits = c.personality?.traits || [];
        const surfaceTrait = c.personality?.surface_trait || '';

        card.innerHTML = `
          <div class="mc-header">
            <span class="m-role-badge badge-${c.role}">${ROLE_BADGE[c.role] || c.role}</span>
            <span class="mc-surface-trait">${surfaceTrait}</span>
          </div>
          <div class="m-name">${c.name} <span class="mc-courtesy">字${c.courtesy_name || ''}</span></div>
          <div class="m-traits">${traits.join(' · ')}</div>
          <div class="m-bg">${c.background || ''}</div>
          <div class="m-ability">⚡ ${c.special_ability || ''}</div>
          ${c.stats ? `
          <div class="mc-stats-mini">
            <span>武${c.stats.wuli||'-'}</span>
            <span>智${c.stats.zhili||'-'}</span>
            <span>统${c.stats.tongshuai||'-'}</span>
            <span>辩${c.stats.koucai||'-'}</span>
          </div>
          ` : ''}
        `;
        card.addEventListener('click', () => this.selectMinister(c.id, c.role, card));
        row.appendChild(card);
      }

      section.appendChild(row);
      grid.appendChild(section);
    }
  }

  selectMinister(id, role, card) {
    // 取消该 role 已选
    if (this.selectedMinisters[role]) {
      const prev = document.querySelector(`.minister-card[data-id="${this.selectedMinisters[role]}"]`);
      if (prev) prev.classList.remove('selected');
    }
    this.selectedMinisters[role] = id;
    card.classList.add('selected');
    clearSetupError();
    this.checkSetupReady();
  }

  checkSetupReady() {
    const rulerName = document.getElementById('ruler-name').value.trim();
    const hasAllRoles = ['internal', 'military', 'diplomacy'].every(r => this.selectedMinisters[r]);
    document.getElementById('btn-start-game').disabled = !(rulerName && hasAllRoles);
  }
}


// ── 事件绑定 ────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  app.setupScreen = new SetupScreen();

  document.getElementById('ruler-name').addEventListener('input', () => {
    if (app.setupScreen) app.setupScreen.checkSetupReady();
  });
  document.getElementById('btn-start-game').addEventListener('click', startGame);
  document.getElementById('btn-back-to-menu').addEventListener('click', backToMenu);
});
