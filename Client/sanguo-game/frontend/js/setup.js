/* ═══════════════════════════════════════════
   setup.js — 开局流程
   ═══════════════════════════════════════════ */

let selectedBuffs = new Set();
let selectedMinisters = {};   // role → id

async function initSetup() {
  const [buffsData, candidatesData] = await Promise.all([
    API.get('/api/setup/buffs'),
    API.get('/api/setup/candidates'),
  ]);

  renderBuffs(buffsData.buffs);
  renderCandidates(candidatesData.candidates);
}

function renderBuffs(buffs) {
  const grid = document.getElementById('buff-list');
  grid.innerHTML = '';
  for (const buff of buffs) {
    const card = document.createElement('div');
    card.className = 'buff-card';
    card.dataset.id = buff.id;
    card.innerHTML = `
      <div class="buff-name">${buff.name}</div>
      <div class="buff-desc">${buff.desc}</div>
    `;
    card.addEventListener('click', () => toggleBuff(buff.id, card));
    grid.appendChild(card);
  }
}

function toggleBuff(id, card) {
  if (selectedBuffs.has(id)) {
    selectedBuffs.delete(id);
    card.classList.remove('selected');
  } else {
    if (selectedBuffs.size >= 2) {
      showSetupError('最多选择2项福泽');
      return;
    }
    selectedBuffs.add(id);
    card.classList.add('selected');
  }
  clearSetupError();
  checkSetupReady();
}

const ROLE_BADGE = {
  internal: '内政',
  military: '军事',
  diplomacy: '外交',
};

function renderCandidates(candidates) {
  const grid = document.getElementById('minister-candidates');
  grid.innerHTML = '';
  for (const c of candidates) {
    const card = document.createElement('div');
    card.className = 'minister-card';
    card.dataset.id = c.id;
    card.dataset.role = c.role;
    card.innerHTML = `
      <div>
        <span class="m-role-badge badge-${c.role}">${ROLE_BADGE[c.role] || c.role}</span>
      </div>
      <div class="m-name">${c.name} <span style="font-size:0.85rem;color:var(--text-muted)">字${c.courtesy_name}</span></div>
      <div class="m-traits">${c.personality.traits.join(' · ')}</div>
      <div class="m-bg">${c.background}</div>
      <div class="m-ability">⚡ ${c.special_ability}</div>
    `;
    card.addEventListener('click', () => selectMinister(c.id, c.role, card));
    grid.appendChild(card);
  }
}

function selectMinister(id, role, card) {
  // 取消该role已选
  if (selectedMinisters[role]) {
    const prev = document.querySelector(`.minister-card[data-id="${selectedMinisters[role]}"]`);
    if (prev) prev.classList.remove('selected');
  }
  selectedMinisters[role] = id;
  card.classList.add('selected');
  clearSetupError();
  checkSetupReady();
}

function checkSetupReady() {
  const rulerName = document.getElementById('ruler-name').value.trim();
  const hasAllRoles = ['internal', 'military', 'diplomacy'].every(r => selectedMinisters[r]);
  const hasBuff = selectedBuffs.size > 0;
  document.getElementById('btn-start-game').disabled = !(rulerName && hasAllRoles && hasBuff);
}

function showSetupError(msg) {
  document.getElementById('setup-error').textContent = msg;
}
function clearSetupError() {
  document.getElementById('setup-error').textContent = '';
}

async function startGame() {
  const rulerName = document.getElementById('ruler-name').value.trim();
  if (!rulerName) { showSetupError('请输入名号'); return; }
  if (!['internal','military','diplomacy'].every(r => selectedMinisters[r])) {
    showSetupError('请三个职位各选一位大臣'); return;
  }
  if (selectedBuffs.size === 0) {
    showSetupError('至少选择一项福泽'); return;
  }

  showLoading('正在创建游戏……');
  try {
    const res = await API.post('/api/setup/create', {
      ruler_name: rulerName,
      buff_ids: [...selectedBuffs],
      minister_ids: Object.values(selectedMinisters),
    });

    // 进入朝堂界面
    showScreen('screen-court');

    // 更新资源 & 大臣面板
    updateResourcePanel(res.state_summary.resources);

    // 加载完整状态
    const state = await API.get('/api/world/state');
    updateMinisterPanel(state.ministers);
    updatePhaseDisplay('idle');
    document.getElementById('date-display').textContent = state.date;

    appendSystem(`欢迎，${rulerName}！${res.message}`);
  } catch (e) {
    showSetupError(`创建失败：${e.message}`);
  } finally {
    hideLoading();
  }
}

// ── 事件绑定 ──────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  // 初始化开局界面数据
  initSetup().catch(console.error);

  document.getElementById('ruler-name').addEventListener('input', checkSetupReady);
  document.getElementById('btn-start-game').addEventListener('click', startGame);
});
