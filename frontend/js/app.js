/* ═══════════════════════════════════════════════════════════
   app.js v2.0 — 主控制器（全局状态 + 工具函数 + 称霸进度）
   ═══════════════════════════════════════════════════════════ */

const API = {
  base: '',

  async post(path, body = {}) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    return r.json();
  },

  async get(path) {
    const r = await fetch(this.base + path);
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    return r.json();
  },

  async del(path) {
    const r = await fetch(this.base + path, { method: 'DELETE' });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    return r.json();
  },
};


// ── 全局游戏状态缓存 ──────────────────────────────────────
let G = {
  phase: 'idle',
  turn: 1,
  maxTurns: 20,
  date: '公元208年秋',
  rulerName: '主公',
  resources: {},
  ministers: {},       // key = minister_id
  conquestProgress: 0,
  gameOver: false,
};


// ── 加载遮罩 ──────────────────────────────────────────────
function showLoading(text = '稍候……') {
  document.getElementById('loading-text').textContent = text;
  document.getElementById('loading-mask').classList.remove('hidden');
}
function hideLoading() {
  document.getElementById('loading-mask').classList.add('hidden');
}


// ── 界面切换 ──────────────────────────────────────────────
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
}


// ── 消息追加（聊天区）──────────────────────────────────────
function appendMessage(who, content, type = 'minister') {
  const wrap = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `msg-bubble msg-${type}`;
  if (who) {
    const name = document.createElement('div');
    name.className = 'msg-name';
    name.textContent = who;
    div.appendChild(name);
  }
  const text = document.createElement('div');
  text.className = 'msg-text';
  text.textContent = content;
  div.appendChild(text);
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

function appendSystem(text) {
  appendMessage(null, text, 'system');
}

function appendScene(text) {
  appendMessage(null, text, 'scene');
}


// ── 资源面板更新 ─────────────────────────────────────────
function updateResourcePanel(res) {
  if (!res) return;
  G.resources = res;
  // 左侧迷你资源
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = typeof val === 'number' ? val.toLocaleString() : (val ?? '-');
  };
  set('res-troops', res.troops);
  set('res-gold', res.gold);
  set('res-food', res.food);
  set('res-prestige', res.prestige);
  // 右侧详细资源
  set('res-troops-detail', res.troops);
  set('res-gold-detail', res.gold);
  set('res-food-detail', res.food);
  set('res-prestige-detail', res.prestige);
}


// ── 称霸进度条 ──────────────────────────────────────────
function updateConquestBar(percent) {
  G.conquestProgress = percent;
  const fill = document.getElementById('conquest-fill');
  const pct = document.getElementById('conquest-percent');
  if (fill) fill.style.width = `${percent}%`;
  if (pct) pct.textContent = `${percent}%`;
}


// ── 回合/日期/阶段 显示 ──────────────────────────────────
function updateTurnDisplay(turn, maxTurns) {
  G.turn = turn;
  G.maxTurns = maxTurns || G.maxTurns;
  const el = document.getElementById('turn-display');
  if (el) el.textContent = `第${turn}/${G.maxTurns}轮`;
}

function updateDateDisplay(date) {
  G.date = date;
  const el = document.getElementById('date-display');
  if (el) el.textContent = date;
}

const PHASE_ZH = {
  idle: '待机',
  opening: '开朝',
  intel: '情报',
  group_discuss: '群议',
  private_meet: '密谋',
  decision: '决策',
  impact: '结算',
  world_update: '世界推进',
};

function updatePhaseDisplay(phase) {
  G.phase = phase;
  const el = document.getElementById('phase-display');
  if (el) {
    el.textContent = PHASE_ZH[phase] || phase;
    el.style.animation = 'none';
    void el.offsetWidth;
    el.style.animation = '';
  }
  // 控制按钮可见性
  _syncButtonVisibility(phase);
}

function _syncButtonVisibility(phase) {
  const toggle = (id, show) => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('hidden', !show);
  };

  toggle('btn-kai-chao',         phase === 'idle');
  toggle('btn-skip-to-discuss',  phase === 'intel' || phase === 'opening');
  toggle('btn-skip-to-private',  phase === 'group_discuss');
  toggle('btn-skip-to-decree',   phase === 'group_discuss' || phase === 'private_meet');
  toggle('btn-settle-impact',    phase === 'decision');
  toggle('btn-end-turn',         phase === 'impact');

  // 输入区显示
  toggle('group-chat-bar',       phase === 'group_discuss');
  toggle('private-chat-bar',     phase === 'private_meet');
  toggle('decree-area',          phase === 'decision');
}


// ── 大臣面板更新（v2.0：key = minister_id）──────────────
function updateMinisterPanel(ministers) {
  if (!ministers) return;
  G.ministers = ministers;
  const list = document.getElementById('minister-list');
  list.innerHTML = '';

  const ROLE_ZH = { internal: '内政', military: '军事', diplomacy: '外交' };

  for (const [mid, m] of Object.entries(ministers)) {
    const div = document.createElement('div');
    div.className = 'minister-entry';
    div.dataset.mid = mid;
    div.id = `me-${mid}`;

    const loyaltyClass = m.loyalty >= 70 ? 'loyal-high' : (m.loyalty >= 40 ? 'loyal-mid' : 'loyal-low');

    div.innerHTML = `
      <div class="me-name">${m.name}</div>
      <div class="me-role">${ROLE_ZH[m.role] || m.role}大臣</div>
      <div class="me-trait">${m.surface_trait || ''}</div>
      <div class="me-loyalty ${loyaltyClass}">忠 ${m.loyalty ?? '-'}</div>
      <div class="me-status" id="me-status-${mid}">就位</div>
    `;

    // 点击打开角色详情
    div.addEventListener('click', () => openCharacterDetail(mid));
    list.appendChild(div);
  }

  // 同步私聊下拉框
  const sel = document.getElementById('private-minister-select');
  if (sel) {
    sel.innerHTML = '';
    for (const [mid, m] of Object.entries(ministers)) {
      const opt = document.createElement('option');
      opt.value = mid;
      opt.textContent = `${m.name}（${ROLE_ZH[m.role] || m.role}）`;
      sel.appendChild(opt);
    }
  }
}

function setMinisterStatus(mid, status) {
  const el = document.getElementById(`me-status-${mid}`);
  if (el) el.textContent = status;
  const entry = document.getElementById(`me-${mid}`);
  if (entry) {
    entry.classList.toggle('speaking', status === '发言中…');
  }
}


// ── 角色详情弹窗 ─────────────────────────────────────────
async function openCharacterDetail(mid) {
  showLoading('加载角色信息……');
  try {
    const data = await API.get(`/api/world/minister/${mid}`);
    const modal = document.getElementById('modal-character');
    const title = document.getElementById('char-modal-title');
    const content = document.getElementById('character-detail-content');

    title.textContent = `${data.name}（${data.courtesy_name}）`;

    const ROLE_ZH = { internal: '内政', military: '军事', diplomacy: '外交' };
    const statsLabels = { wuli: '武力', zhili: '智力', tongshuai: '统率', koucai: '口才' };

    let statsHTML = '';
    if (data.stats) {
      for (const [key, label] of Object.entries(statsLabels)) {
        const val = data.stats[key] || 0;
        statsHTML += `
          <div class="stat-row">
            <span class="stat-label">${label}</span>
            <div class="stat-bar-bg"><div class="stat-bar-fill" style="width:${val}%"></div></div>
            <span class="stat-val">${val}</span>
          </div>
        `;
      }
    }

    const traitTags = (data.personality?.traits || []).map(t => `<span class="trait-tag">${t}</span>`).join('');

    let logHTML = '';
    if (data.action_log && data.action_log.length > 0) {
      logHTML = data.action_log.slice(-8).map(l => `<div class="log-entry">${l}</div>`).join('');
    } else {
      logHTML = '<div class="log-entry">暂无记录</div>';
    }

    content.innerHTML = `
      <div class="char-info-grid">
        <div class="char-section">
          <h3>基本信息</h3>
          <div class="char-field"><span class="field-label">职位</span><span>${ROLE_ZH[data.role] || data.role}大臣 · ${data.position || '-'}</span></div>
          <div class="char-field"><span class="field-label">性格</span><span>${data.personality?.surface_trait || '-'}</span></div>
          <div class="char-field"><span class="field-label">特质</span><span>${traitTags || '-'}</span></div>
          <div class="char-field"><span class="field-label">特殊能力</span><span>${data.special_ability || '-'}</span></div>
          <div class="char-field"><span class="field-label">状态</span><span>${data.status || 'active'}</span></div>
        </div>
        <div class="char-section">
          <h3>能力数值</h3>
          ${statsHTML}
        </div>
        <div class="char-section">
          <h3>情绪状态</h3>
          <div class="emotion-bars">
            <div class="stat-row"><span class="stat-label">忠诚</span><div class="stat-bar-bg"><div class="stat-bar-fill loyalty-bar" style="width:${data.emotion?.loyalty || 0}%"></div></div><span class="stat-val">${data.emotion?.loyalty ?? '-'}</span></div>
            <div class="stat-row"><span class="stat-label">满意</span><div class="stat-bar-bg"><div class="stat-bar-fill satisfaction-bar" style="width:${data.emotion?.satisfaction || 0}%"></div></div><span class="stat-val">${data.emotion?.satisfaction ?? '-'}</span></div>
          </div>
        </div>
        <div class="char-section">
          <h3>背景故事</h3>
          <p class="char-bg-text">${data.background || '未知'}</p>
        </div>
        <div class="char-section">
          <h3>行为记录</h3>
          <div class="action-log-list">${logHTML}</div>
        </div>
      </div>
    `;

    modal.classList.remove('hidden');
  } catch (e) {
    appendSystem(`加载角色信息失败：${e.message}`);
  } finally {
    hideLoading();
  }
}


// ── 影响结算弹窗渲染 ────────────────────────────────────
function showImpactModal(impacts, betrayalWarning, undercurrent) {
  const modal = document.getElementById('modal-impact');
  const content = document.getElementById('impact-content');
  const underArea = document.getElementById('undercurrent-area');

  let html = '';
  for (const imp of impacts) {
    const deltaHTML = (label, val) => {
      if (!val) return '';
      const cls = val > 0 ? 'delta-positive' : 'delta-negative';
      return `<span class="${cls}">${label}${val > 0 ? '+' : ''}${val}</span>`;
    };

    html += `
      <div class="impact-card">
        <div class="impact-name">${imp.minister_name}</div>
        <div class="impact-deltas">
          ${deltaHTML('忠诚', imp.loyalty_delta)}
          ${deltaHTML('满意', imp.satisfaction_delta)}
          ${deltaHTML('恐惧', imp.fear_delta)}
          ${deltaHTML('野心', imp.ambition_delta)}
        </div>
        <div class="impact-bar-row">
          <span>忠诚</span>
          <div class="stat-bar-bg sm"><div class="stat-bar-fill loyalty-bar" style="width:${imp.current_loyalty || 0}%"></div></div>
          <span>${imp.current_loyalty ?? '-'}</span>
        </div>
        <div class="impact-comment">"${imp.comment}"</div>
      </div>
    `;
  }

  if (betrayalWarning) {
    html += `<div class="betrayal-warning">⚠ 暗流涌动：${typeof betrayalWarning === 'string' ? betrayalWarning : '有大臣心存异志……'}</div>`;
  }

  content.innerHTML = html;

  if (undercurrent) {
    underArea.textContent = undercurrent;
    underArea.classList.remove('hidden');
  } else {
    underArea.classList.add('hidden');
  }

  modal.classList.remove('hidden');
}


// ── 周报弹窗 ────────────────────────────────────────────
function showWeekReport(turn, date, report, conquestPercent) {
  document.getElementById('report-date').textContent = `第${turn}轮 · ${date}`;
  document.getElementById('report-content').textContent = report;

  if (conquestPercent !== undefined) {
    const fill = document.getElementById('report-conquest-fill');
    const pct = document.getElementById('report-conquest-percent');
    if (fill) fill.style.width = `${conquestPercent}%`;
    if (pct) pct.textContent = `${conquestPercent}%`;
  }

  document.getElementById('modal-report').classList.remove('hidden');
}


// ── 游戏结束弹窗 ────────────────────────────────────────
function showEnding(ending) {
  if (!ending) return;
  const icons = {
    victory: '🏆',
    death_age: '💀',
    betrayal: '🗡️',
    captured: '⛓️',
    assassinated: '🩸',
  };
  document.getElementById('ending-icon').textContent = icons[ending.type] || '🎌';
  document.getElementById('ending-title').textContent =
    ending.type === 'victory' ? '天下归一！' :
    ending.type === 'death_age' ? '壮志未酬' :
    ending.type === 'betrayal' ? '众叛亲离' :
    ending.type === 'captured' ? '身陷囹圄' :
    '游戏结束';
  document.getElementById('ending-description').textContent = ending.description || '';
  document.getElementById('modal-ending').classList.remove('hidden');
  G.gameOver = true;
}


// ── 资源浮动数字 ────────────────────────────────────────
function floatDelta(elId, delta) {
  if (!delta) return;
  const el = document.getElementById(elId);
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const span = document.createElement('span');
  span.className = `delta-float ${delta > 0 ? 'positive' : 'negative'}`;
  span.textContent = `${delta > 0 ? '+' : ''}${delta}`;
  span.style.left = `${rect.left + rect.width / 2}px`;
  span.style.top = `${rect.top}px`;
  document.body.appendChild(span);
  setTimeout(() => span.remove(), 1300);
}


// ── 加载全局状态到 UI ─────────────────────────────────────
function loadStateToUI(state) {
  updateResourcePanel(state.resources);
  updateMinisterPanel(state.ministers);
  updatePhaseDisplay(state.court_phase || 'idle');
  updateTurnDisplay(state.turn, state.max_turns);
  updateDateDisplay(state.date);
  if (state.conquest) {
    updateConquestBar(state.conquest.progress_percent || 0);
  }
  G.rulerName = state.ruler_name || '主公';
  G.gameOver = state.game_over || false;
}


// ── 全局应用对象 ──────────────────────────────────────────
const app = {
  mainMenu: null,
  setupScreen: null,

  loadState: function(state) {
    loadStateToUI(state);
  },
};


// ── DOMContentLoaded ─────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  // 初始化主菜单
  if (typeof MainMenu !== 'undefined') {
    app.mainMenu = new MainMenu();
  }

  // 默认显示主菜单
  showScreen('screen-main-menu');
});
