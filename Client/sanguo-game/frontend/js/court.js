/* ═══════════════════════════════════════════
   court.js — 朝会界面逻辑
   ═══════════════════════════════════════════ */

// ── 上朝（禀奏）───────────────────────────────────────────
async function kaiChao() {
  showLoading('鸣鞭上朝……');
  try {
    appendSystem('── 鸣鞭三下，百官就位，朝会开始 ──');
    const res = await API.post('/api/court/start');
    updatePhaseDisplay(res.phase);

    for (const msg of res.messages) {
      setMinisterStatus(msg.role, '已禀奏');
      appendMessage(`${msg.minister}（禀奏）`, msg.content, 'minister');
    }
    appendSystem('── 禀奏毕，可进入议事 ──');
  } catch (e) {
    appendSystem(`错误：${e.message}`);
  } finally {
    hideLoading();
  }
}

// ── 进入议事 ──────────────────────────────────────────────
async function enterYishi() {
  try {
    await API.post('/api/court/advance_phase');
    updatePhaseDisplay('yishi');
    appendSystem('── 进入议事，主公可自由问询 ──');
  } catch (e) {
    appendSystem(`错误：${e.message}`);
  }
}

// ── 议事对话 ──────────────────────────────────────────────
async function sendChat() {
  const input = document.getElementById('chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  const role = document.getElementById('minister-select').value;
  const ministerName = G.ministers[role]?.name || role;

  appendMessage(`主公`, msg, 'player');
  setMinisterStatus(role, '发言中…');
  showLoading('大臣思量中……');

  try {
    const res = await API.post('/api/court/chat', {
      minister_id: role,
      message: msg,
    });
    for (const m of res.messages) {
      appendMessage(`${m.minister}`, m.content, 'minister');
      setMinisterStatus(m.role, '已回应');
    }
  } catch (e) {
    appendSystem(`错误：${e.message}`);
    setMinisterStatus(role, '就位');
  } finally {
    hideLoading();
  }
}

// ── 切换拟旨阶段 ──────────────────────────────────────────
async function enterNizhi() {
  try {
    await API.post('/api/court/advance_phase');
    updatePhaseDisplay('nizhi');
    appendSystem('── 进入拟旨，请输入旨意 ──');
  } catch (e) {
    appendSystem(`错误：${e.message}`);
  }
}

// ── 下旨 ──────────────────────────────────────────────────
async function issueDecree() {
  const decreeText = document.getElementById('decree-input').value.trim();
  if (!decreeText) return;
  document.getElementById('decree-input').value = '';

  appendMessage('主公（旨意）', decreeText, 'player');
  showLoading('大臣恭听……');

  try {
    const res = await API.post('/api/court/decree', { decree_text: decreeText });
    for (const m of res.messages) {
      appendMessage(`${m.minister}（拟旨）`, m.content, 'minister');
    }
  } catch (e) {
    appendSystem(`错误：${e.message}`);
  } finally {
    hideLoading();
  }
}

// ── 退朝结算 ──────────────────────────────────────────────
async function tuiChao() {
  if (!confirm('确认退朝并进行本周结算？')) return;
  showLoading('退朝结算中，请稍候……');

  try {
    const res = await API.post('/api/court/end');

    // 更新资源
    updateResourcePanel(res.resources);
    document.getElementById('date-display').textContent = res.new_date;
    updatePhaseDisplay('idle');

    // 显示资源变化浮动
    floatDelta('res-gold',   res.resource_delta?.gold);
    floatDelta('res-food',   res.resource_delta?.food);

    // 展示周报
    showWeekReport(res.turn_completed, res.new_date, res.report);

    // 重置大臣状态
    for (const role of Object.keys(G.ministers)) {
      setMinisterStatus(role, '就位');
    }

    appendSystem(`── 第${res.turn_completed}周结算完毕，进入${res.new_date} ──`);
  } catch (e) {
    appendSystem(`结算错误：${e.message}`);
  } finally {
    hideLoading();
  }
}

// ── 周报弹窗 ──────────────────────────────────────────────
function showWeekReport(turn, date, report) {
  document.getElementById('report-date').textContent = `第${turn}周 · ${date}`;
  document.getElementById('report-content').textContent = report;
  document.getElementById('modal-report').classList.remove('hidden');
}

function closeWeekReport() {
  document.getElementById('modal-report').classList.add('hidden');
}

// ── 事件绑定 ──────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('btn-kai-chao').addEventListener('click', kaiChao);
  document.getElementById('btn-yishi').addEventListener('click', enterYishi);
  document.getElementById('btn-nizhi').addEventListener('click', enterNizhi);
  document.getElementById('btn-tui-chao').addEventListener('click', tuiChao);
  document.getElementById('btn-send').addEventListener('click', sendChat);
  document.getElementById('btn-issue-decree').addEventListener('click', issueDecree);
  document.getElementById('btn-close-report').addEventListener('click', closeWeekReport);

  // 回车发送
  document.getElementById('chat-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
  });

  document.getElementById('btn-map').addEventListener('click', () => {
    document.getElementById('modal-map').classList.remove('hidden');
    loadMap();
  });

  document.getElementById('btn-close-map').addEventListener('click', () => {
    document.getElementById('modal-map').classList.add('hidden');
  });
});
