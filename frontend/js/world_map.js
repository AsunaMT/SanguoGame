/* ═══════════════════════════════════════════════════════════
   world_map.js v2.0 — SVG 12州交互地图
   ═══════════════════════════════════════════════════════════ */

const FACTION_COLORS = {
  player:    '#b22222',   // 朱砂红
  cao_cao:   '#555555',   // 铁灰
  liu_bei:   '#1b3a5c',   // 玄青
  sun_quan:  '#2d6a4f',   // 碧绿
  liu_zhang: '#8b4513',   // 棕褐
  yuan_shao: '#6a5acd',   // 紫蓝
  neutral:   '#9e8a5c',   // 沙黄
};

const FACTION_NAMES = {
  player:    '主公',
  cao_cao:   '曹操',
  liu_bei:   '刘备',
  sun_quan:  '孙权',
  liu_zhang: '刘璋',
  yuan_shao: '袁绍',
  neutral:   '中立',
};


async function loadMap() {
  try {
    const data = await API.get('/api/world/map');
    renderMap(data.territories);
  } catch (e) {
    document.getElementById('map-container').textContent = '地图加载失败：' + e.message;
  }
}


function renderMap(territories) {
  const W = 800, H = 620;
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('xmlns', svgNS);
  svg.classList.add('world-map-svg');

  // 背景
  const bg = document.createElementNS(svgNS, 'rect');
  bg.setAttribute('width', W);
  bg.setAttribute('height', H);
  bg.setAttribute('fill', '#e8dcc8');
  svg.appendChild(bg);

  // 标题
  const title = document.createElementNS(svgNS, 'text');
  title.setAttribute('x', W / 2);
  title.setAttribute('y', 36);
  title.setAttribute('text-anchor', 'middle');
  title.setAttribute('font-size', '20');
  title.setAttribute('font-family', 'serif');
  title.setAttribute('fill', '#5c3d11');
  title.setAttribute('font-weight', 'bold');
  title.textContent = `天下舆图 · ${G.date}`;
  svg.appendChild(title);

  // 称霸进度条（地图内）
  renderMapProgressBar(svg, W);

  // 领土
  for (const t of territories) {
    const cx = t.cx || 400;
    const cy = t.cy || 300;
    const rx = t.rx || 48;
    const ry = t.ry || 32;
    const color = FACTION_COLORS[t.owner] || '#aaa';

    const g = document.createElementNS(svgNS, 'g');
    g.style.cursor = 'pointer';
    g.classList.add('territory-group');

    // 阴影椭圆
    const shadow = document.createElementNS(svgNS, 'ellipse');
    shadow.setAttribute('cx', cx + 2);
    shadow.setAttribute('cy', cy + 2);
    shadow.setAttribute('rx', rx);
    shadow.setAttribute('ry', ry);
    shadow.setAttribute('fill', 'rgba(0,0,0,0.15)');
    g.appendChild(shadow);

    // 主椭圆
    const ellipse = document.createElementNS(svgNS, 'ellipse');
    ellipse.setAttribute('cx', cx);
    ellipse.setAttribute('cy', cy);
    ellipse.setAttribute('rx', rx);
    ellipse.setAttribute('ry', ry);
    ellipse.setAttribute('fill', color);
    ellipse.setAttribute('fill-opacity', '0.8');
    ellipse.setAttribute('stroke', t.owner === 'player' ? '#ffd700' : '#2c1a06');
    ellipse.setAttribute('stroke-width', t.owner === 'player' ? '2.5' : '1.5');
    g.appendChild(ellipse);

    // 战争标记
    if (t.at_war) {
      const warIcon = document.createElementNS(svgNS, 'text');
      warIcon.setAttribute('x', cx + rx - 8);
      warIcon.setAttribute('y', cy - ry + 12);
      warIcon.setAttribute('font-size', '14');
      warIcon.setAttribute('pointer-events', 'none');
      warIcon.textContent = '⚔️';
      g.appendChild(warIcon);
    }

    // 领土名称
    const label = document.createElementNS(svgNS, 'text');
    label.setAttribute('x', cx);
    label.setAttribute('y', cy - 3);
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('dominant-baseline', 'middle');
    label.setAttribute('font-size', '13');
    label.setAttribute('font-family', 'serif');
    label.setAttribute('fill', '#f5ead2');
    label.setAttribute('font-weight', 'bold');
    label.setAttribute('pointer-events', 'none');
    label.textContent = t.name;
    g.appendChild(label);

    // 兵力小字
    const troops = document.createElementNS(svgNS, 'text');
    troops.setAttribute('x', cx);
    troops.setAttribute('y', cy + 14);
    troops.setAttribute('text-anchor', 'middle');
    troops.setAttribute('font-size', '10');
    troops.setAttribute('fill', '#f5ead2');
    troops.setAttribute('fill-opacity', '0.8');
    troops.setAttribute('pointer-events', 'none');
    troops.textContent = `兵${(t.troops || 0).toLocaleString()}`;
    g.appendChild(troops);

    // 点击显示详情
    g.addEventListener('click', () => showTerritoryTooltip(t, g, svg));

    svg.appendChild(g);
  }

  // 图例
  renderMapLegend(svg, W, H, territories);

  const container = document.getElementById('map-container');
  container.innerHTML = '';
  container.appendChild(svg);

  // 迷你地图也渲染一份
  renderMiniMap(territories);
}


function renderMapProgressBar(svg, W) {
  const svgNS = 'http://www.w3.org/2000/svg';
  const barX = W / 2 - 150;
  const barY = 50;
  const barW = 300;
  const barH = 14;
  const pct = G.conquestProgress || 0;

  // 背景
  const barBg = document.createElementNS(svgNS, 'rect');
  barBg.setAttribute('x', barX);
  barBg.setAttribute('y', barY);
  barBg.setAttribute('width', barW);
  barBg.setAttribute('height', barH);
  barBg.setAttribute('rx', 7);
  barBg.setAttribute('fill', '#3a2e1a');
  svg.appendChild(barBg);

  // 填充
  const barFill = document.createElementNS(svgNS, 'rect');
  barFill.setAttribute('x', barX);
  barFill.setAttribute('y', barY);
  barFill.setAttribute('width', barW * pct / 100);
  barFill.setAttribute('height', barH);
  barFill.setAttribute('rx', 7);
  barFill.setAttribute('fill', '#b22222');
  svg.appendChild(barFill);

  // 文字
  const barText = document.createElementNS(svgNS, 'text');
  barText.setAttribute('x', W / 2);
  barText.setAttribute('y', barY + 11);
  barText.setAttribute('text-anchor', 'middle');
  barText.setAttribute('font-size', '10');
  barText.setAttribute('fill', '#f5ead2');
  barText.textContent = `称霸 ${pct}%`;
  svg.appendChild(barText);
}


function renderMapLegend(svg, W, H, territories) {
  const svgNS = 'http://www.w3.org/2000/svg';
  // 收集出现的势力
  const factions = new Set(territories.map(t => t.owner));
  let legendX = 20, legendY = H - 35;

  const legendTitle = document.createElementNS(svgNS, 'text');
  legendTitle.setAttribute('x', legendX);
  legendTitle.setAttribute('y', legendY - 4);
  legendTitle.setAttribute('font-size', '11');
  legendTitle.setAttribute('fill', '#5c3d11');
  legendTitle.textContent = '势力：';
  svg.appendChild(legendTitle);
  legendX += 40;

  for (const faction of factions) {
    const color = FACTION_COLORS[faction] || '#aaa';
    const name = FACTION_NAMES[faction] || faction;

    const rect = document.createElementNS(svgNS, 'rect');
    rect.setAttribute('x', legendX);
    rect.setAttribute('y', legendY - 10);
    rect.setAttribute('width', 14);
    rect.setAttribute('height', 14);
    rect.setAttribute('rx', 3);
    rect.setAttribute('fill', color);
    rect.setAttribute('fill-opacity', '0.8');
    svg.appendChild(rect);

    const lbl = document.createElementNS(svgNS, 'text');
    lbl.setAttribute('x', legendX + 18);
    lbl.setAttribute('y', legendY + 2);
    lbl.setAttribute('font-size', '11');
    lbl.setAttribute('fill', '#5c3d11');
    lbl.textContent = name;
    svg.appendChild(lbl);

    legendX += 55;
  }
}


function showTerritoryTooltip(t, g, svg) {
  // 移除之前的 tooltip
  const old = svg.querySelector('.map-tooltip');
  if (old) old.remove();

  const svgNS = 'http://www.w3.org/2000/svg';
  const ownerName = FACTION_NAMES[t.owner] || t.owner;

  const info = [
    `【${t.name}】`,
    `归属：${ownerName}`,
    `驻兵：${(t.troops || 0).toLocaleString()}`,
    `人口：${(t.population || 0).toLocaleString()}`,
    `城防：${t.defense || 0}`,
    `税率：${((t.tax_rate || 0) * 100).toFixed(0)}%`,
    t.at_war ? '⚔ 战争中' : '',
  ].filter(Boolean);

  const cx = t.cx || 400;
  const cy = t.cy || 300;

  const tooltip = document.createElementNS(svgNS, 'g');
  tooltip.classList.add('map-tooltip');

  const rectBg = document.createElementNS(svgNS, 'rect');
  rectBg.setAttribute('x', cx + 50);
  rectBg.setAttribute('y', cy - 60);
  rectBg.setAttribute('width', 140);
  rectBg.setAttribute('height', info.length * 18 + 12);
  rectBg.setAttribute('rx', 6);
  rectBg.setAttribute('fill', '#2a1f0d');
  rectBg.setAttribute('fill-opacity', '0.92');
  rectBg.setAttribute('stroke', '#c9a227');
  tooltip.appendChild(rectBg);

  info.forEach((line, i) => {
    const text = document.createElementNS(svgNS, 'text');
    text.setAttribute('x', cx + 58);
    text.setAttribute('y', cy - 42 + i * 18);
    text.setAttribute('font-size', '11');
    text.setAttribute('fill', '#f5ead2');
    text.textContent = line;
    tooltip.appendChild(text);
  });

  svg.appendChild(tooltip);

  // 3秒后自动消失
  setTimeout(() => tooltip.remove(), 4000);

  // 点击其他区域消失
  svg.addEventListener('click', function handler(e) {
    if (!tooltip.contains(e.target) && !g.contains(e.target)) {
      tooltip.remove();
      svg.removeEventListener('click', handler);
    }
  });
}


// ── 迷你地图（右侧面板）──────────────────────────────────
function renderMiniMap(territories) {
  const container = document.getElementById('mini-map-container');
  if (!container) return;

  const W = 240, H = 180;
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.style.width = '100%';
  svg.style.borderRadius = '6px';

  // 背景
  const bg = document.createElementNS(svgNS, 'rect');
  bg.setAttribute('width', W);
  bg.setAttribute('height', H);
  bg.setAttribute('fill', '#e8dcc8');
  svg.appendChild(bg);

  // 缩放领土坐标到迷你地图
  const scale = 0.3;
  const offsetX = 0;
  const offsetY = 0;

  for (const t of territories) {
    const cx = (t.cx || 400) * scale + offsetX;
    const cy = (t.cy || 300) * scale + offsetY;
    const rx = (t.rx || 48) * scale;
    const ry = (t.ry || 32) * scale;
    const color = FACTION_COLORS[t.owner] || '#aaa';

    const ellipse = document.createElementNS(svgNS, 'ellipse');
    ellipse.setAttribute('cx', cx);
    ellipse.setAttribute('cy', cy);
    ellipse.setAttribute('rx', rx);
    ellipse.setAttribute('ry', ry);
    ellipse.setAttribute('fill', color);
    ellipse.setAttribute('fill-opacity', '0.8');
    ellipse.setAttribute('stroke', t.owner === 'player' ? '#ffd700' : '#2c1a06');
    ellipse.setAttribute('stroke-width', '0.8');
    svg.appendChild(ellipse);

    // 只显示名字（迷你版用小字）
    const label = document.createElementNS(svgNS, 'text');
    label.setAttribute('x', cx);
    label.setAttribute('y', cy + 1);
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('dominant-baseline', 'middle');
    label.setAttribute('font-size', '5');
    label.setAttribute('fill', '#f5ead2');
    label.setAttribute('pointer-events', 'none');
    label.textContent = t.name;
    svg.appendChild(label);
  }

  container.innerHTML = '';
  container.appendChild(svg);
}
