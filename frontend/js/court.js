/* ═══════════════════════════════════════════════════════════
   court.js v2.0 — 7步朝堂流程 + 群聊 + 私聊 + 影响结算
   ═══════════════════════════════════════════════════════════ */

// ── 1. 鸣鞭上朝（开朝）──────────────────────────────────
async function kaiChao() {
  showLoading('鸣鞭上朝……');
  try {
    appendSystem('── 鸣鞭三下，百官就位，朝会开始 ──');
    const res = await API.post('/api/court/start');

    updatePhaseDisplay(res.phase);
    updateTurnDisplay(res.turn, res.max_turns);
    updateConquestBar(res.conquest_progress || G.conquestProgress);

    // 随机场景事件
    if (res.scene_event) {
      appendScene(`🎭 ${res.scene_event.description}`);
      if (res.scene_event.hint) {
        appendSystem(`（线索：${res.scene_event.hint}）`);
      }
    }

    appendSystem('── 朝会已开，进入情报汇报 ──');

    // 自动进入情报阶段
    await getIntel();
  } catch (e) {
    appendSystem(`开朝错误：${e.message}`);
  } finally {
    hideLoading();
  }
}


// ── 2. 情报汇报 ─────────────────────────────────────────
async function getIntel() {
  showLoading('大臣汇报情报中……');
  try {
    const res = await API.post('/api/court/intel');
    updatePhaseDisplay(res.phase);

    for (const rpt of res.reports) {
      setMinisterStatus(rpt.minister_id, '汇报中…');
      appendMessage(`${rpt.minister_name}（${rpt.role === 'internal' ? '内政' : rpt.role === 'military' ? '军事' : '外交'}情报）`, rpt.content, 'minister');
      setMinisterStatus(rpt.minister_id, '已汇报');
    }

    appendSystem('── 情报汇报完毕，可进入群议 ──');
  } catch (e) {
    appendSystem(`情报错误：${e.message}`);
  } finally {
    hideLoading();
  }
}


// ── 3. 群议（群聊）──────────────────────────────────────
async function sendGroupChat() {
  const input = document.getElementById('group-chat-input');
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';

  appendMessage('主公', msg, 'player');

  // 标记所有大臣为 "思量中…"
  for (const mid of Object.keys(G.ministers)) {
    setMinisterStatus(mid, '思量中…');
  }

  showLoading('群臣议事中……');
  try {
    const res = await API.post('/api/court/group_chat', { message: msg });
    updatePhaseDisplay(res.phase);

    for (const r of res.responses) {
      setMinisterStatus(r.minister_id, '发言');
      appendMessage(r.minister_name, r.content, 'minister');
      setMinisterStatus(r.minister_id, '已回应');
    }

    // 显示即时影响提示
    if (res.impacts && res.impacts.length > 0) {
      let impactHint = '📊 本次发言影响：';
      for (const imp of res.impacts) {
        const parts = [];
        if (imp.loyalty_delta) parts.push(`忠诚${imp.loyalty_delta > 0 ? '+' : ''}${imp.loyalty_delta}`);
        if (imp.satisfaction_delta) parts.push(`满意${imp.satisfaction_delta > 0 ? '+' : ''}${imp.satisfaction_delta}`);
        if (parts.length > 0) {
          impactHint += ` ${imp.minister_name}(${parts.join(',')})`;
        }
      }
      if (res.impacts.some(i => i.loyalty_delta || i.satisfaction_delta)) {
        appendSystem(impactHint);
      }
    }

    appendSystem('── 可继续群议、进入密谋或直接决策 ──');
  } catch (e) {
    appendSystem(`群议错误：${e.message}`);
    for (const mid of Object.keys(G.ministers)) {
      setMinisterStatus(mid, '就位');
    }
  } finally {
    hideLoading();
  }
}

function enterGroupDiscuss() {
  updatePhaseDisplay('group_discuss');
  appendSystem('── 进入群议，主公可对百官训话 ──');
}


// ── 4. 密谋（私聊）──────────────────────────────────────
async function sendPrivateChat() {
  const select = document.getElementById('private-minister-select');
  const input = document.getElementById('private-chat-input');
  const mid = select.value;
  const msg = input.value.trim();
  if (!msg || !mid) return;
  input.value = '';

  const ministerName = G.ministers[mid]?.name || mid;
  appendMessage('主公（密谈）', `[对${ministerName}] ${msg}`, 'player');
  setMinisterStatus(mid, '密谈中…');
  showLoading(`${ministerName}思量中……`);

  try {
    const res = await API.post('/api/court/private_chat', {
      minister_id: mid,
      message: msg,
    });
    updatePhaseDisplay(res.phase);
    appendMessage(`${res.minister_name}（密谈）`, res.content, 'private');
    setMinisterStatus(mid, '密谈完毕');
    appendSystem('── 可继续密谈其他大臣，或进入决策 ──');
  } catch (e) {
    appendSystem(`密谈错误：${e.message}`);
    setMinisterStatus(mid, '就位');
  } finally {
    hideLoading();
  }
}

function enterPrivateMeet() {
  updatePhaseDisplay('private_meet');
  appendSystem('── 进入密谋环节，选择大臣进行私聊 ──');
}


// ── 5. 决策（下旨）──────────────────────────────────────
async function issueDecree() {
  const input = document.getElementById('decree-input');
  const decreeText = input.value.trim();
  if (!decreeText) return;
  input.value = '';

  appendMessage('主公（旨意）', decreeText, 'decree');
  showLoading('群臣接旨……');

  try {
    const res = await API.post('/api/court/decree', { decree_text: decreeText });
    updatePhaseDisplay(res.phase);

    for (const c of res.confirmations) {
      setMinisterStatus(c.minister_id, '接旨');
      appendMessage(`${c.minister_name}（接旨）`, c.content, 'minister');
    }

    appendSystem('── 旨意已下达，可继续下旨或查看结算 ──');
  } catch (e) {
    appendSystem(`下旨错误：${e.message}`);
  } finally {
    hideLoading();
  }
}

function enterDecision() {
  updatePhaseDisplay('decision');
  appendSystem('── 进入决策环节，请下达旨意 ──');
}


// ── 6. 影响结算 ─────────────────────────────────────────
async function settleImpact() {
  showLoading('计算本轮影响……');
  try {
    const res = await API.post('/api/court/impact');
    updatePhaseDisplay(res.phase);

    showImpactModal(res.impacts, res.betrayal_warning, res.undercurrent);

    // 更新大臣面板中的忠诚度显示
    for (const imp of res.impacts) {
      if (imp.current_loyalty !== undefined) {
        const loyalEl = document.querySelector(`#me-${imp.minister_id} .me-loyalty`);
        if (loyalEl) {
          loyalEl.textContent = `忠 ${imp.current_loyalty}`;
          loyalEl.className = `me-loyalty ${imp.current_loyalty >= 70 ? 'loyal-high' : imp.current_loyalty >= 40 ? 'loyal-mid' : 'loyal-low'}`;
        }
      }
    }

    appendSystem('── 影响结算完毕，可退朝结算 ──');
  } catch (e) {
    appendSystem(`结算错误：${e.message}`);
  } finally {
    hideLoading();
  }
}


// ── 7. 退朝 → 世界结算 ─────────────────────────────────
async function endTurn() {
  showLoading('退朝结算中，天下大势正在演变……');
  try {
    const res = await API.post('/api/court/end');

    // 更新资源
    updateResourcePanel(res.resources);
    updateTurnDisplay(res.new_turn, res.max_turns);
    updateDateDisplay(res.new_date);
    updateConquestBar(res.conquest_progress || G.conquestProgress);
    updatePhaseDisplay('idle');

    // 资源变化浮动
    if (res.resource_delta) {
      floatDelta('res-gold', res.resource_delta.gold);
      floatDelta('res-food', res.resource_delta.food);
      floatDelta('res-troops', res.resource_delta.troops);
    }

    // 重置大臣状态
    for (const mid of Object.keys(G.ministers)) {
      setMinisterStatus(mid, '就位');
    }

    // 检查游戏结束
    if (res.game_over && res.ending) {
      showEnding(res.ending);
    } else {
      // 展示周报
      showWeekReport(res.turn_completed, res.new_date, res.report, res.conquest_progress);
    }

    appendSystem(`── 第${res.turn_completed}轮结算完毕，进入${res.new_date} ──`);

    // 刷新大臣面板数据
    try {
      const worldState = await API.get('/api/world/state');
      updateMinisterPanel(worldState.ministers);
    } catch (_) { /* 非关键 */ }

  } catch (e) {
    appendSystem(`退朝结算错误：${e.message}`);
  } finally {
    hideLoading();
  }
}


// ── 事件绑定 ────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  // 上朝
  document.getElementById('btn-kai-chao').addEventListener('click', kaiChao);

  // 阶段跳转按钮
  document.getElementById('btn-skip-to-discuss').addEventListener('click', enterGroupDiscuss);
  document.getElementById('btn-skip-to-private').addEventListener('click', enterPrivateMeet);
  document.getElementById('btn-skip-to-decree').addEventListener('click', enterDecision);

  // 群聊
  document.getElementById('btn-group-send').addEventListener('click', sendGroupChat);
  document.getElementById('group-chat-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendGroupChat(); }
  });

  // 私聊
  document.getElementById('btn-private-send').addEventListener('click', sendPrivateChat);
  document.getElementById('private-chat-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendPrivateChat(); }
  });

  // 下旨
  document.getElementById('btn-issue-decree').addEventListener('click', issueDecree);

  // 结算
  document.getElementById('btn-settle-impact').addEventListener('click', settleImpact);

  // 退朝
  document.getElementById('btn-end-turn').addEventListener('click', endTurn);

  // 影响弹窗关闭
  document.getElementById('btn-close-impact').addEventListener('click', () => {
    document.getElementById('modal-impact').classList.add('hidden');
  });

  // 周报弹窗关闭
  document.getElementById('btn-close-report').addEventListener('click', () => {
    document.getElementById('modal-report').classList.add('hidden');
  });

  // 地图按钮
  document.getElementById('btn-map-header').addEventListener('click', () => {
    document.getElementById('modal-map').classList.remove('hidden');
    loadMap();
  });
  document.getElementById('btn-fullscreen-map').addEventListener('click', () => {
    document.getElementById('modal-map').classList.remove('hidden');
    loadMap();
  });
  document.getElementById('btn-close-map').addEventListener('click', () => {
    document.getElementById('modal-map').classList.add('hidden');
  });

  // 角色详情弹窗关闭
  document.getElementById('btn-close-character').addEventListener('click', () => {
    document.getElementById('modal-character').classList.add('hidden');
  });

  // 游戏结束弹窗
  document.getElementById('btn-new-game-ending').addEventListener('click', async () => {
    document.getElementById('modal-ending').classList.add('hidden');
    await API.post('/api/setup/reset');
    showScreen('screen-setup');
    if (app.setupScreen) app.setupScreen.init();
  });
  document.getElementById('btn-menu-ending').addEventListener('click', () => {
    document.getElementById('modal-ending').classList.add('hidden');
    showScreen('screen-main-menu');
  });

  // 保存按钮
  document.getElementById('btn-save-header').addEventListener('click', async () => {
    showLoading('保存中……');
    try {
      await API.post('/api/setup/saves?slot_name=manual');
      appendSystem('── 游戏已保存 ──');
    } catch (e) {
      appendSystem(`保存失败：${e.message}`);
    } finally {
      hideLoading();
    }
  });

  // 返回主菜单
  document.getElementById('btn-menu-return').addEventListener('click', () => {
    if (confirm('确认返回主菜单？（当前进度已自动保存）')) {
      showScreen('screen-main-menu');
    }
  });
});
