/* ═══════════════════════════════════════════
   world_map.js — SVG 地图渲染
   ═══════════════════════════════════════════ */

const FACTION_COLORS = {
  player:    '#b22222',   // 朱砂红
  cao_cao:   '#555555',   // 铁灰
  liu_bei:   '#1b3a5c',   // 玄青
  sun_quan:  '#2d6a4f',   // 碧绿
  liu_biao:  '#6b4c1e',   // 棕褐
  neutral:   '#9e8a5c',   // 沙黄
};

// 简化地图布局：每个领土的 [cx, cy, rx, ry]（椭圆占位）
const TERRITORY_POSITIONS = {
  player_start: { cx: 340, cy: 380, rx: 52, ry: 36, label_dy: 5 },
  xu_du:        { cx: 460, cy: 120, rx: 60, ry: 38, label_dy: 5 },
  jingzhou_bei: { cx: 360, cy: 170, rx: 55, ry: 34, label_dy: 5 },
  wan_cheng:    { cx: 420, cy: 220, rx: 44, ry: 32, label_dy: 5 },
  ye_cheng:     { cx: 530, cy: 80,  rx: 52, ry: 34, label_dy: 5 },
  xinye:        { cx: 310, cy: 220, rx: 48, ry: 32, label_dy: 5 },
  fangling:     { cx: 370, cy: 255, rx: 44, ry: 30, label_dy: 5 },
  jiankang:     { cx: 580, cy: 310, rx: 58, ry: 36, label_dy: 5 },
  '柴桑':       { cx: 510, cy: 340, rx: 48, ry: 32, label_dy: 5 },
  jiujiang:     { cx: 570, cy: 390, rx: 44, ry: 30, label_dy: 5 },
  xiangyang:    { cx: 300, cy: 280, rx: 52, ry: 34, label_dy: 5 },
  jiangling:    { cx: 350, cy: 320, rx: 48, ry: 32, label_dy: 5 },
  changsha:     { cx: 400, cy: 420, rx: 48, ry: 32, label_dy: 5 },
  guiyang:      { cx: 460, cy: 460, rx: 44, ry: 30, label_dy: 5 },
  wuling:       { cx: 300, cy: 430, rx: 44, ry: 30, label_dy: 5 },
};

let mapLoaded = false;

async function loadMap() {
  if (mapLoaded) return;
  try {
    const data = await API.get('/api/world/map');
    renderMap(data.territories);
    mapLoaded = false;   // 每次打开都刷新
  } catch (e) {
    document.getElementById('map-container').textContent = '地图加载失败：' + e.message;
  }
}

function renderMap(territories) {
  const W = 700, H = 560;
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('xmlns', svgNS);
  svg.style.background = '#e8dcc8';

  // 标题
  const title = document.createElementNS(svgNS, 'text');
  title.setAttribute('x', W / 2);
  title.setAttribute('y', 32);
  title.setAttribute('text-anchor', 'middle');
  title.setAttribute('font-size', '18');
  title.setAttribute('font-family', 'serif');
  title.setAttribute('fill', '#5c3d11');
  title.textContent = '天下舆图（公元208年）';
  svg.appendChild(title);

  for (const t of territories) {
    const pos = TERRITORY_POSITIONS[t.id];
    if (!pos) continue;

    const color = FACTION_COLORS[t.owner] || '#aaa';
    const g = document.createElementNS(svgNS, 'g');
    g.style.cursor = 'pointer';

    // 椭圆
    const ellipse = document.createElementNS(svgNS, 'ellipse');
    ellipse.setAttribute('cx', pos.cx);
    ellipse.setAttribute('cy', pos.cy);
    ellipse.setAttribute('rx', pos.rx);
    ellipse.setAttribute('ry', pos.ry);
    ellipse.setAttribute('fill', color);
    ellipse.setAttribute('fill-opacity', '0.75');
    ellipse.setAttribute('stroke', '#2c1a06');
    ellipse.setAttribute('stroke-width', '1.5');
    g.appendChild(ellipse);

    // 名称
    const label = document.createElementNS(svgNS, 'text');
    label.setAttribute('x', pos.cx);
    label.setAttribute('y', pos.cy + (pos.label_dy || 0));
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('dominant-baseline', 'middle');
    label.setAttribute('font-size', '12');
    label.setAttribute('font-family', 'serif');
    label.setAttribute('fill', '#f5ead2');
    label.setAttribute('pointer-events', 'none');
    label.textContent = t.name;
    g.appendChild(label);

    // 点击显示tooltip
    g.addEventListener('click', () => showTerritoryInfo(t));
    svg.appendChild(g);
  }

  // 图例
  let legendX = 16, legendY = H - 120;
  const legendTitle = document.createElementNS(svgNS, 'text');
  legendTitle.setAttribute('x', legendX);
  legendTitle.setAttribute('y', legendY - 8);
  legendTitle.setAttribute('font-size', '11');
  legendTitle.setAttribute('fill', '#5c3d11');
  legendTitle.textContent = '势力图例：';
  svg.appendChild(legendTitle);

  for (const [faction, color] of Object.entries(FACTION_COLORS)) {
    const rect = document.createElementNS(svgNS, 'rect');
    rect.setAttribute('x', legendX);
    rect.setAttribute('y', legendY);
    rect.setAttribute('width', 16);
    rect.setAttribute('height', 16);
    rect.setAttribute('fill', color);
    rect.setAttribute('fill-opacity', '0.75');
    rect.setAttribute('stroke', '#2c1a06');
    svg.appendChild(rect);

    const factionNames = {
      player: '主公', cao_cao: '曹操', liu_bei: '刘备',
      sun_quan: '孙权', liu_biao: '刘表', neutral: '中立',
    };
    const lbl = document.createElementNS(svgNS, 'text');
    lbl.setAttribute('x', legendX + 20);
    lbl.setAttribute('y', legendY + 12);
    lbl.setAttribute('font-size', '11');
    lbl.setAttribute('fill', '#5c3d11');
    lbl.textContent = factionNames[faction] || faction;
    svg.appendChild(lbl);

    legendX += 60;
  }

  const container = document.getElementById('map-container');
  container.innerHTML = '';
  container.appendChild(svg);
}

function showTerritoryInfo(t) {
  const factionNames = {
    player: '主公', cao_cao: '曹操', liu_bei: '刘备',
    sun_quan: '孙权', liu_biao: '刘表', neutral: '中立',
  };
  alert(
    `【${t.name}】\n` +
    `归属：${factionNames[t.owner] || t.owner}\n` +
    `驻兵：${t.troops?.toLocaleString()}\n` +
    `人口：${t.population?.toLocaleString()}\n` +
    `税率：${((t.tax_rate || 0) * 100).toFixed(0)}%`
  );
}
