// bakery.js: AWSAVYA auto-posting reel (vertical 1080x1920, 19 s, 120 BPM).
// One bakery, one continuous camera. Riya the baker is buried in work; Tile (AWSAVYA's helper) hops out of the oven,
// photographs the croissants, paints the ad and flings it into the phone, which fills up day after day.
(() => {
  const C = {
    wall: '#F1D3AE', wallDk: '#E2B98D', tile: '#E9C9A2', wood: '#B8764A', woodDk: '#86502F', woodLt: '#D99C66',
    skin: '#B9784F', skinDk: '#8F5534', hair: '#2E1F26', shirt: '#2F7275', shirtDk: '#235659', apron: '#FFF4E2',
    brick: '#B85B3F', brickDk: '#8A3F2C', metal: '#6F625E', metalLt: '#A6978E', fire: '#F39A3B',
    dough: '#F5E5C6', crust: '#E3A24A', crustDk: '#A9662A', yellow: '#FFC83D', yellowDk: '#E3A21C',
    phone: '#2B2233', screen: '#FFF9EF', screenOff: '#E7DCCB',
  };
  // Story beats (seconds). 120 BPM: a beat every 0.5 s, a bar every 2 s.
  const B = { buzz1: 1.0, glance: 1.25, buzz2: 2.25, whip: 2.85, trays: [3.5, 4.0], jig: 5.25, door: 6.0, hopOut: 6.4,
    land: 7.0, salute: 7.25, look: 7.6, flash: 8.0, paint0: 8.3, paint1: 9.25, proud: 9.5, phoneUp: 10.0, throw0: 10.3,
    throw1: 10.8, days0: 11.25, glowOut: 13.15, morning: 13.4, hop0: 14.25, hop1: 14.75, love: 15.1, end: 16.0 };
  const LOGO = new Image(); LOGO.src = 'assets/awsavya-logo.png';
  (window.PRELOAD = window.PRELOAD || []).push(new Promise(r => { LOGO.onload = r; LOGO.onerror = r; }));

  // colour keyframes: colKf(t, [[t0, '#hex'], ...])
  const colKf = (t, keys) => {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) if (t < keys[i][0]) return mixCol(keys[i - 1][1], keys[i][1], ease(seg(t, keys[i - 1][0], keys[i][0])));
    return keys[keys.length - 1][1];
  };
  const skyAt = t => colKf(t, [[0, '#2E3570'], [6.0, '#3B3D7A'], [9.4, '#EFA466'], [13.3, '#F2B575'], [13.4, '#9FD3F0']]);

  // ---------- props ----------
  function croissant(x, y, s, rot, key) {
    boilSeed('cr ' + key);
    push(); translate(x, y); rotate(rot); scale(s);
    const out = [], inn = [];
    for (let i = 0; i <= 10; i++) { const a = Math.PI * (1.04 + .92 * i / 10); out.push([Math.cos(a) * 46, Math.sin(a) * 32 + 12]); }
    for (let i = 10; i >= 0; i--) { const a = Math.PI * (1.1 + .8 * i / 10); inn.push([Math.cos(a) * 30, Math.sin(a) * 11 + 16]); }
    paint(out.concat(inn), { wash: C.crust, ink: PAL.ink, sw: .9 / Math.max(.6, s), curv: .5 });
    for (const a of [1.33, 1.5, 1.67]) {
      const A = Math.PI * a; inkLine([[Math.cos(A) * 44, Math.sin(A) * 30 + 12], [Math.cos(A) * 31, Math.sin(A) * 11 + 15]], .7, C.crustDk, 'inkfine');
    }
    pop();
  }
  function tray(x, y, w, key) {
    boilSeed('tray ' + key);
    paint(rrPts(x - w / 2, y - 16, w, 16, 6, 1), { wash: C.metalLt, ink: PAL.ink, sw: .9 });
    for (let i = 0; i < 3; i++) croissant(x - w / 3 + i * w / 3, y - 26, .62, (hash(i + key.length) - .5) * .3, key + i);
  }
  function miniPoster(x, y, w, k, key) {   // the little ad in a grid cell or in the air: cream card, yellow label, croissant
    if (k <= .01) return;
    const s = backOut(k); boilSeed('mp ' + key);
    push(); translate(x, y); scale(s);
    paint(rectPts(-w / 2, -w / 2, w, w, 0), { wash: '#FFF6E6', ink: PAL.ink, sw: .5 });
    paint(rectPts(-w / 2, -w / 2, w, w * .24, 0), { wash: C.yellow, ink: null });
    pop();
    croissant(x, y + w * .08 * s, w / 150 * s, -.1, key + 'c');
  }
  function phone(x, y, o = {}) {   // (x, y) = bottom centre
    push(); translate(x + (o.dx || 0), y + (o.dy || 0)); rotate(o.rot || 0); scale(1 + (o.sq || 0) * .5, 1 - (o.sq || 0));
    boilSeed('phone body'); paint(rrPts(-62, -214, 124, 214, 16, .6), { wash: C.phone, ink: PAL.ink, sw: 1.1 });
    boilSeed('phone screen'); paint(rrPts(-53, -202, 106, 182, 8), { wash: o.lit ? C.screen : C.screenOff, ink: null });
    paint(ellPts(-38, -188, 7, 7, 12), { wash: o.lit ? C.yellow : '#CBBFAE', ink: null });
    inkLine([[-26, -188], [10, -188]], .6, '#B8AC9A', 'inkfine');
    for (let i = 0; i < 9; i++) {
      const cx = -34 + (i % 3) * 34, cy = -152 + Math.floor(i / 3) * 34, k = o.cells ? o.cells(i) : 0;
      boilSeed('cell ' + i);
      if (k < 1) paint(rectPts(cx - 15, cy - 15, 30, 30, 0), { wash: '#DCD0BE', washOp: 140, ink: null });
      if (k > 0) miniPoster(cx, cy, 30, k, 'cell' + i);
    }
    if (o.cursor) { boilSeed('cursor'); paint(rectPts(-2, -60, 4, 22), { wash: PAL.ink, washOp: 255 * o.cursor, ink: null }); }
    pop();
    if (o.buzz > .02) {   // vibration marks either side
      boilSeed('buzz');
      for (const sd of [-1, 1]) for (let j = 0; j < 2; j++) {
        const bx = x + sd * (78 + j * 16), by = y - 130 + (o.dy || 0);
        inkLine([[bx, by - 22 + j * 6], [bx + sd * 6, by], [bx, by + 22 - j * 6]], 1.1 * o.buzz, PAL.ink, 'ink', .6);
      }
    }
  }
  function clock(x, y, r, t) {
    boilSeed('clock');
    paint(ellPts(x, y, r, r, 30, .6), { wash: '#FFF6E8', ink: PAL.ink, sw: 1.3 });
    for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; paint(ellPts(x + Math.cos(a) * r * .8, y + Math.sin(a) * r * .8, 3, 3, 8), { wash: PAL.ink, ink: null }); }
    // the minute hand creeps, then spins through the rush
    const m = .25 * t + 9 * Math.max(0, Math.min(t, 5.4) - 3), hA = m / 12 - Math.PI / 2 + 1.2, mA = m - Math.PI / 2;
    inkLine([[x, y], [x + Math.cos(hA) * r * .45, y + Math.sin(hA) * r * .45]], 2, PAL.ink, 'ink', 0);
    inkLine([[x, y], [x + Math.cos(mA) * r * .7, y + Math.sin(mA) * r * .7]], 1.4, C.brickDk, 'ink', 0);
  }
  function oven(t) {
    boilSeed('oven dome');
    const dome = [[640, 1150], [640, 900]]; for (let i = 0; i <= 12; i++) { const a = Math.PI + i / 12 * Math.PI; dome.push([860 + Math.cos(a) * 220, 900 + Math.sin(a) * 190]); } dome.push([1080, 1150]);
    paint(dome, { wash: C.brick, ink: PAL.ink, sw: 1.2, curv: .2 });
    boilSeed('oven bricks');
    for (let r = 0; r < 6; r++) for (let c = 0; c < 5; c++) {
      const bx = 670 + c * 88 + (r % 2) * 44, by = 760 + r * 64; if (bx > 1060 || Math.hypot(bx - 860, (by - 900) * 1.15) > 210 && by < 900) continue;
      inkLine([[bx, by], [bx + 60, by + 2]], .6, C.brickDk, 'inkfine', 0);
    }
    // the mouth, with fire inside
    boilSeed('oven mouth');
    const mouth = [[750, 1120], [750, 980]]; for (let i = 0; i <= 10; i++) { const a = Math.PI + i / 10 * Math.PI; mouth.push([860 + Math.cos(a) * 110, 980 + Math.sin(a) * 100]); } mouth.push([970, 1120]);
    paint(mouth, { wash: '#3B1F1C', ink: PAL.ink, sw: 1.1 });
    const open = ease(seg(t, B.door, B.door + .25));
    glow(860, 1050, 170 + 60 * open + 12 * wob(t, 3), '#FF9A3C', .55 + .45 * open);
    boilSeed('fire');
    for (let i = 0; i < 4; i++) {
      const fx = 800 + i * 40, h = 46 + 20 * Math.sin(t * 9 + i * 1.7) + 30 * open;
      paint(ribbon([[fx, 1118], [fx + 8 * Math.sin(t * 7 + i), 1118 - h * .55], [fx + 4, 1118 - h]], 26, 2), { wash: i % 2 ? C.fire : C.yellow, ink: null });
    }
    // the door: a hinged iron arch that swings open (drawn flat: it narrows towards the hinge)
    const sw = 1 - open; if (sw > .02) {
      boilSeed('oven door');
      const d = []; for (let i = 0; i <= 10; i++) { const a = Math.PI + i / 10 * Math.PI; d.push([750 + (110 + Math.cos(a) * 110) * sw, 980 + Math.sin(a) * 100]); } d.push([750 + 220 * sw, 1122]); d.push([750, 1122]);
      paint(d, { wash: C.metal, ink: PAL.ink, sw: 1.1 });
      paint(rrPts(750 + 150 * sw, 1040, 34 * sw + 2, 14, 6), { wash: C.metalLt, ink: PAL.ink, sw: .8 });
    }
  }
  function room(t) {
    boilSeed('wall'); paint(rectPts(-400, -400, W + 800, 1600), { wash: C.wall, ink: null });
    paint(ellPts(300, 520, 520, 380, 20, 30), { fill: C.wallDk, fillOp: 70, bleed: .25, tex: .5, ink: null });
    boilSeed('tiles'); paint(rectPts(-400, 990, W + 800, 200), { wash: C.tile, ink: null });
    inkLine([[-200, 990], [W + 200, 990]], .9, C.wallDk, 'ink', 0);
    for (let i = 0; i < 12; i++) inkLine([[i * 96 - 20, 994], [i * 96 - 20, 1146]], .5, C.wallDk, 'inkfine', 0);
    // window: the sky outside tells the time of day
    boilSeed('window');
    paint(rrPts(110, 380, 360, 330, 14, 1), { wash: C.woodDk, ink: PAL.ink, sw: 1.2 });
    paint(rectPts(132, 402, 316, 286, 0), { wash: skyAt(t), ink: null });
    const day = t > B.morning;
    if (day) { glow(380, 470, 120, '#FFF1B8', .8); paint(ellPts(380, 470, 34, 34, 20), { wash: '#FFE79A', ink: null }); }
    else paint(ellPts(380, 470, 26, 26, 20), { wash: '#FFF3D6', ink: null });
    inkLine([[290, 402], [290, 688]], 2.2, C.woodDk, 'ink', 0); inkLine([[132, 545], [448, 545]], 2.2, C.woodDk, 'ink', 0);
    paint(rrPts(96, 700, 388, 26, 8), { wash: C.wood, ink: PAL.ink, sw: 1 });
    clock(560, 470, 64, t);
    oven(t);
  }
  function counter(t) {
    boilSeed('counter');
    paint(rectPts(-400, 1150, W + 800, 900), { wash: C.wood, ink: null });
    paint(rectPts(-400, 1132, W + 800, 30, 0), { wash: C.woodLt, ink: null });
    inkLine([[-100, 1132], [W + 100, 1132]], 1.2, PAL.ink, 'ink', 0); inkLine([[-100, 1162], [W + 100, 1162]], 1, PAL.ink, 'ink', 0);
    paint(rectPts(-400, 1162, W + 800, 40, 0), { wash: C.woodDk, washOp: 120, ink: null });
    for (let i = 0; i < 6; i++) inkLine([[i * 210 - 60, 1180], [i * 210 - 30, 1920]], .7, C.woodDk, 'inkfine', 0);
    boilSeed('drawers');
    for (const dx of [150, 590]) { paint(rrPts(dx, 1230, 340, 150, 10, 1), { wash: C.woodLt, washOp: 120, ink: PAL.ink, sw: .9 });
      paint(ellPts(dx + 170, 1305, 16, 12, 14), { wash: C.metalLt, ink: PAL.ink, sw: .8 }); }
  }

  // ---------- Riya: the baker, seen from the waist up behind the counter ----------
  // (x, y) = her waist at the counter top. o: hx/hy head offset, lookX/lookY, eyes, mouth, brows, blush, hL/hR hands
  // (local px), sq, dy, lean, emote/emoteK/emoteAge, holdR(x, y) to draw something in her right hand.
  function riya(x, y, o = {}) {
    const rs = k => boilSeed('riya ' + k), hx = o.hx || 0, hy = (o.hy || 0) - 330, lx = (o.lookX || 0), ly = (o.lookY || 0);
    push(); translate(x, y + (o.dy || 0)); rotate(o.lean || 0); scale(1 + (o.sq || 0) * .5, 1 - (o.sq || 0));
    rs('bun'); paint(ellPts(hx - 6, hy - 92, 38, 34, 18, .8), { wash: C.hair, ink: PAL.ink, sw: 1.1 });
    rs('torso'); paint([[-106, -252], [106, -252], [122, -196], [104, 6], [-104, 6], [-122, -196]], { wash: C.shirt, ink: PAL.ink, sw: 1.2, curv: .35 });
    rs('apron'); paint([[-70, -206], [70, -206], [80, 6], [-80, 6]], { wash: C.apron, ink: PAL.ink, sw: 1 });
    inkLine([[-58, -206], [-34, -258]], 3, C.apron, 'ink', .2); inkLine([[58, -206], [34, -258]], 3, C.apron, 'ink', .2);
    paint(rrPts(-34, -120, 68, 46, 10), { wash: '#F6E4CC', ink: PAL.ink, sw: .7 });
    rs('neck'); paint(rectPts(hx * .4 - 22, -282, 44, 40, 0), { wash: C.skinDk, ink: null });
    rs('head'); paint(ellPts(hx, hy, 84, 88, 26, .7), { wash: C.skin, ink: PAL.ink, sw: 1.2 });
    rs('hair'); const cap = []; for (let i = 0; i <= 12; i++) { const a = Math.PI * (1 + i / 12); cap.push([hx + Math.cos(a) * 90, hy - 6 + Math.sin(a) * 92]); }
    cap.push([hx + 80, hy - 18], [hx + 40, hy - 46], [hx + 6, hy - 30], [hx - 34, hy - 50], [hx - 80, hy - 20]);
    paint(cap, { wash: C.hair, ink: PAL.ink, sw: 1.1, curv: .3 });
    // face
    rs('face');
    const ex = 30, ey = hy + 4 + ly * 5, mx = hx + lx * 8;
    if (o.blush) for (const sd of [-1, 1]) paint(ellPts(mx + sd * 50, hy + 34, 16, 9, 12), { wash: '#F2D9C4', washOp: 210 * o.blush, ink: null });
    for (const sd of [-1, 1]) {
      const cx = mx + sd * ex, e = o.eyes || 'dot';
      if (e === 'dot') paint(ellPts(cx + lx * 6, ey, 7, 10, 12), { wash: PAL.ink, ink: null });
      else if (e === 'wide') { paint(ellPts(cx, ey, 15, 18, 16), { wash: '#FFFDF6', ink: PAL.ink, sw: .9 }); paint(ellPts(cx + lx * 6, ey + ly * 5, 6, 7, 10), { wash: PAL.ink, ink: null }); }
      else if (e === 'happy') inkLine([[cx - 12, ey + 5], [cx, ey - 7], [cx + 12, ey + 5]], 1.4, PAL.ink, 'ink', .8);
      else if (e === 'closed') inkLine([[cx - 12, ey - 2], [cx, ey + 7], [cx + 12, ey - 2]], 1.4, PAL.ink, 'ink', .8);
      else if (e === 'squint') inkLine([[cx - 12, ey], [cx + 12, ey]], 1.4, PAL.ink, 'ink', 0);
      else if (e === 'swirl') { const P = []; for (let i = 0; i < 22; i++) { const a = i * .55 + T * 9 * sd, r = 1.5 + i * .65; P.push([cx + Math.cos(a) * r, ey + Math.sin(a) * r]); } inkLine(P, .9, PAL.ink, 'inkfine', .5); }
      if (o.brows === 'worried') inkLine([[cx - sd * 14, ey - 31], [cx + sd * 13, ey - 22]], 1.2, PAL.ink, 'ink', 0);
      if (o.brows === 'up') inkLine([[cx - 12, ey - 30], [cx + 12, ey - 33]], 1.2, PAL.ink, 'ink', 0);
    }
    const my = hy + 44, m = o.mouth || 'flat';
    if (m === 'flat') inkLine([[mx - 12, my], [mx + 12, my]], 1.2, PAL.ink, 'ink', 0);
    else if (m === 'smile') inkLine([[mx - 18, my - 4], [mx, my + 8], [mx + 18, my - 4]], 1.3, PAL.ink, 'ink', .8);
    else if (m === 'O') paint(ellPts(mx, my + 2, 11, 14, 14), { wash: '#5A2B2B', ink: PAL.ink, sw: .9 });
    else if (m === 'wobble') inkLine([[mx - 16, my], [mx - 8, my - 4], [mx, my + 1], [mx + 8, my - 4], [mx + 16, my]], 1.1, PAL.ink, 'ink', .4);
    else if (m === 'grin') paint([[mx - 22, my - 6], [mx + 22, my - 6], [mx + 12, my + 12], [mx - 12, my + 12]], { wash: '#5A2B2B', ink: PAL.ink, sw: .9, curv: .6 });
    else if (m === 'chew') paint(ellPts(mx, my + 2, 10, 5 + 4 * Math.abs(Math.sin(T * 14)), 12), { wash: '#5A2B2B', ink: PAL.ink, sw: .8 });
    if (o.flour !== false) for (const [fx, fy] of [[-46, 30], [52, 18]]) paint(ellPts(mx + fx, hy + fy, 9, 6, 10, 1), { wash: '#FFFFFF', washOp: 200, ink: null });
    // arms: sleeve to the elbow, then forearm and hand
    for (const sd of [-1, 1]) {
      rs('arm' + sd);
      const sh = [sd * 104, -236], h = sd < 0 ? (o.hL || [-60, -18]) : (o.hR || [60, -18]);
      const el = [(sh[0] + h[0]) / 2 + sd * 34, (sh[1] + h[1]) / 2 + 26];
      paint(ribbon([sh, el], 50, 42), { wash: C.shirt, ink: PAL.ink, sw: 1 });
      paint(ribbon([el, h], 36, 30), { wash: C.skin, ink: PAL.ink, sw: 1 });
      paint(ellPts(h[0], h[1], 23, 21, 14, .5), { wash: C.skin, ink: PAL.ink, sw: 1 });
      if (sd > 0 && o.holdR) o.holdR(h[0], h[1]);
    }
    pop();
    if (o.emote) emote(o.emote, x + hx + 110, y + hy - 70 + (o.dy || 0), 20, o.emoteK ?? 1, o.emoteAge ?? T);
  }

  // ---------- Tile: AWSAVYA's helper (a cream photo tile with a yellow corner) ----------
  function tile(x, y, u, o = {}) {
    const extra = o.draw;
    clawd(x, y, u, { sx: .66, boilKey: 'tile', ...o, col: '#FFFCF3', dk: '#E6D7BD', lt: '#FFFFFF', tint: null,
      draw: (uu, sw) => { paint([[2.3 * uu, -8 * uu], [5 * uu, -8 * uu], [5 * uu, -5.3 * uu]], { wash: C.yellow, ink: PAL.ink, sw }); if (extra) extra(uu, sw); } });
  }
  function checkBadge(x, y, r, k) {
    if (k <= .01) return; const s = backOut(k); boilSeed('check');
    paint(ellPts(x, y, r * s, r * s, 18), { wash: C.yellow, ink: PAL.ink, sw: 1 });
    inkLine([[x - r * .45 * s, y], [x - r * .1 * s, y + r * .35 * s], [x + r * .5 * s, y - r * .4 * s]], 2.2, PAL.ink, 'ink', 0);
  }

  // ---------- the pile of croissants that buries the phone ----------
  const PILE = Array.from({ length: 16 }, (_, i) => {
    const row = Math.floor(i / 5), col = i % 5;
    return { x: 470 + col * 66 + (row % 2) * 30 + (hash(i * 3) - .5) * 20, y: 1128 - row * 40 - hash(i * 7) * 10,
      rot: (hash(i * 11) - .5) * 1.2, t: 4.35 + i * .05, from: [220 + hash(i) * 120, 1040] };
  });
  function pile(t) {
    for (let i = 0; i < PILE.length; i++) {
      const p = PILE[i], k = seg(t, p.t, p.t + .32); if (k <= 0) continue;
      const [px, py] = k < 1 ? arcPt(p.from, [p.x, p.y], 180, easeIn(k) * .4 + k * .6) : [p.x, p.y];
      const jig = t > B.jig && t < B.jig + .4 ? spring(t, B.jig, 8, 40) * 6 : 0;
      croissant(px, py - Math.abs(jig), .78, p.rot * k + (k < 1 ? (1 - k) * 4 : 0), 'p' + i);
    }
  }

  // ---------- camera ----------
  function camAt(t) {
    const K = (keys, e = ease) => kf(t, keys, e);
    if (t < 3.0) {
      let c = K([[0, [480, 960, 1.55]], [2.85, [478, 968, 1.66]]]);
      if (t > B.whip) c = [c[0] + 520 * easeIn(seg(t, B.whip, 3.0)), c[1], c[2]];          // whip pan out
      return c;
    }
    if (t < 5.25) {
      const c = K([[3.0, [450, 975, 1.55]], [5.25, [500, 972, 1.6]]]);
      const hit = Math.max(spring(t, 3.5, 9, 30), spring(t, 4.0, 9, 30)) * 14;
      const sh = shakeXY(t, Math.abs(hit));
      return [c[0] - 520 * (1 - easeOut(seg(t, 3.0, 3.18))) + sh[0], c[1] + sh[1], c[2]];  // whip pan in
    }
    if (t < 6.0) return K([[5.25, [500, 972, 1.6]], [5.5, [855, 1010, 1.95]]]);            // push into the oven, then hold still
    if (t < 10.0) {
      const c = K([[6.0, [855, 1010, 1.9]], [6.18, [855, 1000, 1.78]], [7.0, [720, 975, 1.45]], [8.0, [680, 950, 1.5]], [9.6, [640, 900, 1.45]], [10.0, [630, 910, 1.45]]]);
      const sh = shakeXY(t, 16 * Math.max(0, 1 - (t - B.door) * 4) * (t >= B.door ? 1 : 0));
      return [c[0] + sh[0], c[1] + sh[1], c[2]];
    }
    if (t < B.morning) return K([[10.0, [630, 910, 1.45]], [10.85, [625, 925, 1.5]], [11.25, [660, 900, 2.5]], [13.3, [660, 895, 2.65]]]);
    return K([[B.morning, [500, 975, 1.5]], [B.end, [505, 960, 1.4]]]);
  }

  // ---------- the film ----------
  function bakery(t, lt, dur) {
    const [cx, cy, z] = camAt(t);
    camBegin(cx, cy, z);
    room(t);
    // Riya
    const kneading = t < 3.0 || (t > 1.9 && t < 3.0);
    const bp = bpOf(t), push1 = Math.max(0, Math.sin(bp * Math.PI * 2)) * (t < B.glance || t > 1.9 ? 1 : .2);
    const R = { hL: [-62, -20 - 18 * push1], hR: [62, -20 - 18 * Math.max(0, Math.sin(bp * Math.PI * 2 + Math.PI))], lookY: .6, eyes: 'dot', mouth: 'flat', brows: null, dy: -6 * pulse(t, 8) };
    if (t < 3.0) {
      if (t > B.glance && t < 1.9) { R.lookX = 1; R.lookY = 0; R.hx = 10; R.brows = 'worried'; R.mouth = 'wobble'; R.emote = 'sweat'; R.emoteK = seg(t, 1.4, 1.6); R.emoteAge = t - 1.4; }
      if (t > 1.9) { R.brows = 'worried'; R.mouth = 'wobble'; R.dy -= 4; }
      if (t > B.buzz2 + .1) { R.lookX = .6; R.eyes = 'wide'; R.emote = '!'; R.emoteK = seg(t, B.buzz2 + .1, B.buzz2 + .3); R.emoteAge = t - B.buzz2; }
    } else if (t < 6.0) {
      const look = t < 4.3 ? -1 : (t < 4.6 ? 1 : 0);
      Object.assign(R, { lookX: look, lookY: 0, hx: look * 12, eyes: t > 4.6 ? 'swirl' : 'wide', mouth: t > 4.6 ? 'wobble' : 'O', brows: 'worried',
        hL: [-110, -150 - 20 * pulse(t, 5)], hR: [110, -150 - 20 * pulse(t + .25, 5)], lean: t > 4.6 ? .05 * wob(t, 1.2) : 0 });
    } else if (t < B.morning) {
      const tk = take(t, B.door + .08, 1.2);
      Object.assign(R, { lookX: 1, lookY: 0, hx: 16, eyes: t < B.flash ? 'wide' : (t < B.flash + .3 ? 'squint' : 'wide'), mouth: t < 7.6 ? 'O' : 'smile', brows: 'up',
        hL: [-70, -40], hR: [70, -40], sq: tk.sq, dy: tk.dy * 20 });
    } else {
      const lk = t > B.love ? 1 : 0;
      Object.assign(R, { eyes: 'happy', mouth: t < B.love ? 'chew' : 'smile', lookX: lk, hx: lk * 20, lookY: 0, brows: null, dy: -5 * pulse(t, 6), blush: .8,
        hL: [-64, -24], hR: lk ? [96, -150] : [92, -262],
        holdR: (x, y) => croissant(x - (lk ? 10 : 46), y - (lk ? 30 : 16), .62, lk ? -.3 : .5, 'bite'),
        emote: t > B.love + .1 ? 'heart' : null, emoteK: seg(t, B.love + .1, B.love + .35), emoteAge: t - B.love });
    }
    riya(360, 1150, R);
    counter(t);
    // on the counter
    if (t < 6.0) { boilSeed('dough'); const sq = .06 * push1; paint(ellPts(360, 1128 + 6 * sq, 120 * (1 + sq), 34 * (1 - sq), 22, 1.2), { wash: C.dough, ink: PAL.ink, sw: .9 });
      for (let i = 0; i < 3; i++) { const age = frac(bpOf(t) + i / 3), a = 1 - age; if (t < 3.0 && a > .3) paint(ellPts(330 + i * 30, 1100 - age * 60, 18 + age * 30, 12 + age * 20, 12, 3), { wash: '#FFF8EC', washOp: 160 * a, ink: null }); } }
    if (t >= 3.0 && t < B.morning) for (let i = 0; i < 2; i++) { const k = seg(t, B.trays[i] - .3, B.trays[i]); if (k > 0) tray(lerp(-200, 240 + i * 12, easeOut(k)), 1132 - i * 30, 230, 'tray' + i); }
    // the phone
    const buzz = Math.max(Math.exp(-6 * Math.max(0, t - B.buzz1)) * (t > B.buzz1 ? 1 : 0), Math.exp(-6 * Math.max(0, t - B.buzz2)) * (t > B.buzz2 ? 1 : 0));
    let P = { x: 610, y: 1150, dx: 0, dy: 0, buzz: t < 3.0 ? buzz : 0, lit: false, cursor: t < 3.0 && frac(t * 1.6) < .5 ? 1 : 0, cells: () => 0 };
    if (t < 3.0 && buzz > .05) { P.dx = Math.sin(t * 80) * 5 * buzz; P.dy = -Math.abs(Math.sin(t * 20)) * 16 * buzz; }
    if (t >= B.phoneUp && t < B.morning) {
      const j = jump(t, B.phoneUp, B.phoneUp + .35, 1); P.y = lerp(1150, 990, ease(seg(t, B.phoneUp, B.phoneUp + .35))); P.dy = j.dy * 40; P.sq = j.sq;
      P.lit = true; P.cells = i => i === 0 ? seg(t, B.throw1, B.throw1 + .2) : seg(t, B.days0 + (i - 1) * .25, B.days0 + (i - 1) * .25 + .2);
    }
    if (t >= B.morning) { P = { x: 640, y: 990, lit: true, cells: () => 1 }; boilSeed('stand'); paint(rectPts(595, 990, 90, 160, 0), { wash: C.woodDk, ink: PAL.ink, sw: 1 }); }
    phone(P.x, P.y, P);
    if (t >= 3.0 && t < B.phoneUp + .2) pile(t);
    else if (t >= B.phoneUp + .2 && t < B.morning) pile(9);
    if (t >= B.morning) { tray(190, 1132, 240, 'neat0'); }
    // Tile
    if (t >= B.hopOut && t < B.morning) {
      const k = seg(t, B.hopOut, B.land), [tx, ty] = arcPt([860, 1100], [745, 1150], 200, easeOut(k * .3 + .7 * k));
      const em = emotions(t, [[B.hopOut, 'excited'], [B.salute, 'proud'], [B.look, 'determined', { lookX: -1 }], [B.proud, 'proud'], [B.days0, 'happy']]);
      const jl = t < B.land ? { dy: 0, sq: -.15 } : jump(t, 9, 9.1, 0);
      let aR = em.aR ?? .2;
      if (t > B.salute && t < B.look) aR = 1.3;
      if (t > B.paint0 && t < B.paint1) aR = .9 + .5 * Math.sin(t * 22);
      if (t > B.throw0 - .2 && t < B.throw0) aR = -1; if (t >= B.throw0 && t < B.throw0 + .25) aR = 1.4;
      const landSq = t > B.land ? .3 * Math.exp(-9 * (t - B.land)) * Math.cos(18 * (t - B.land)) : 0;
      const dance = t > B.days0 ? move('bounce', t, 2) : {};
      tile(tx, ty, 17 * (.35 + .65 * easeOut(seg(t, B.hopOut, B.hopOut + .22))), { ...em, ...dance, aR, sq: (em.sq || 0) + landSq + (jl.sq || 0) + (dance.sq || 0), view: t < B.land ? 'q' : (em.view || 'front'), flip: t < B.land });
      if (Math.abs(t - B.flash) < .25) glow(tx - 20, ty - 70, 220 * (1 - Math.abs(t - B.flash) * 4), '#FFF6D8', 1);
    }
    if (t >= B.morning) {   // Tile hops onto Riya's shoulder
      const k = seg(t, B.hop0, B.hop1), [tx, ty] = k <= 0 ? [745, 1150] : (k >= 1 ? [500, 914] : arcPt([745, 1150], [500, 914], 160, ease(k)));
      const j = k > 0 && k < 1 ? { sq: -.15 } : { sq: k >= 1 ? .3 * Math.exp(-9 * (t - B.hop1)) * Math.cos(18 * (t - B.hop1)) : 0 };
      const em = emotions(t, [[B.morning, 'happy'], [B.love, 'love']]);
      tile(tx, ty, 13, { ...em, sq: (em.sq || 0) + j.sq, view: k > 0 && k < 1 ? 'q' : 'front', flip: k > 0 && k < 1 });
    }
    // the painted ad, in the air, then thrown into the phone
    if (t >= B.paint0 && t < B.throw1) {
      const fly = seg(t, B.throw0, B.throw1), at = fly > 0 ? arcPt([600, 800], [612, 880], 120, easeIn(fly)) : [600, 800 + 8 * wob(t, .8)];
      const s = lerp(1, .14, easeIn(fly)), w = 230 * s, frameK = seg(t, B.paint0, B.paint0 + .35);
      boilSeed('ad');
      if (frameK > .99) paint(rectPts(at[0] - w / 2, at[1] - w / 2, w, w, 0), { wash: '#FFF6E6', ink: PAL.ink, sw: .9 });
      else if (frameK > 0) {   // the frame is painted as one stroke around the square
        const per = [[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]], P = [], n = frameK * 4;
        for (let i = 0; i <= Math.floor(n); i++) P.push([at[0] + per[i][0] * w / 2, at[1] + per[i][1] * w / 2]);
        const f = n - Math.floor(n), a = per[Math.floor(n)], b = per[Math.min(4, Math.floor(n) + 1)];
        P.push([at[0] + lerp(a[0], b[0], f) * w / 2, at[1] + lerp(a[1], b[1], f) * w / 2]);
        if (P.length > 1) inkLine(P, 1.6, PAL.ink, 'ink', 0);
      }
      const lab = seg(t, B.paint0 + .65, B.paint0 + .95);
      if (lab > 0) paint(rectPts(at[0] - w / 2, at[1] - w / 2, w * easeOut(lab), w * .24, 0), { wash: C.yellow, ink: null });
      const cr = seg(t, B.paint0 + .35, B.paint0 + .6);
      if (cr > 0) croissant(at[0], at[1] + w * .08, s * 1.5 * backOut(cr), -.1, 'adc');
      checkBadge(at[0] + w * .5, at[1] - w * .5, 26 * s, seg(t, B.proud, B.proud + .25) * (1 - fly));
    }
    // hearts rising from the phone
    if (t > 12.5) for (let i = 0; i < 6; i++) {
      const t0 = 12.5 + i * .28, a = t - t0; if (a < 0 || a > 2.2) continue;
      const hx = (t >= B.morning ? 640 : 612) + (hash(i * 5) - .5) * 140 + 20 * Math.sin(a * 3 + i), hy = (t >= B.morning ? 770 : 760) - a * 110;
      emote('heart', hx, hy, t >= B.morning ? 12 : 9, seg(a, 0, .25) * (1 - seg(a, 1.7, 2.2)), a);
    }
    camEnd();
    // full-frame light and transitions (screen space)
    if (t > B.whip) { const k = Math.sin(seg(t, B.whip, 3.18) * Math.PI); if (k > .05) for (let i = 0; i < 9; i++) { boilSeed('smear' + i); const y = 200 + i * 190 + hash(i) * 80; inkLine([[-50, y], [W + 50, y + 10]], 3 * k, i % 2 ? C.wallDk : C.woodLt, 'dry', 0); } }
    if (t >= B.flash && t < B.flash + .2) flash(.85 * (1 - seg(t, B.flash, B.flash + .2)), '#FFFDF4');
    if (t >= B.door && t < B.door + .25) flash(.6 * (1 - seg(t, B.door, B.door + .25)), '#FFD08A');
    if (t >= B.days0 && t < B.glowOut) {   // days passing: night falls and lifts on every new post
      const d = (t - B.days0) / .44, night = Math.max(0, Math.sin(d * Math.PI)) ** 2;
    }
    if (t >= B.glowOut && t < B.morning + .35) flash(t < B.morning ? seg(t, B.glowOut, B.morning) : 1 - seg(t, B.morning, B.morning + .35), '#FFF8E8');
    // the hook, painted on for the first seconds (Reels are mostly watched muted)
    if (t < 2.9) {
      const a = 1 - seg(t, 2.6, 2.9);
      letter('NO TIME', 540, 300, 128, C.yellow, { screen: true, rot: -.05, stroke: PAL.ink, pop: t < .01 ? 1 : 1, alpha: a });
      letter('TO POST?', 560, 430, 128, C.yellow, { screen: true, rot: -.05, stroke: PAL.ink, pop: 1, alpha: a });
    }
    caption(t);
    if (lt > dur - .3) { flushLetters(); brushWipe((lt - (dur - .3)) / .6, [C.yellowDk, C.yellow]); }
  }

  // ---------- captions: the voiceover, word by word, for people watching muted ----------
  // [start, end, text]: start = when the voice starts the phrase (assets/vo/lines.json), end = when the caption leaves.
  const CAPS = [   // [start, leave, text, seconds of speech]  (timed to the Kokoro voiceover, assets/vo/lines.json)
    [3.05, 3.83, 'And the orders', .78],
    [3.83, 5.3, 'keep piling up.', .78],
    [6.35, 7.24, 'Meet your helper,', .89],
    [7.24, 8.12, 'built by AWSAVYA.', .88],
    [8.12, 9.95, 'It makes your ad for you,', 1.77],
    [10.0, 11.49, 'and posts it on time,', 1.49],
    [11.49, 12.95, 'every single day.', .9],
    [13.6, 15.55, 'You bake. It posts.', 1.32],
  ];
  const mctx = document.createElement('canvas').getContext('2d');
  function caption(t) {
    const c = CAPS.find(([a, b]) => t >= a && t < b); if (!c) return;
    const [a, b, txt, spoken] = c, words = txt.split(' '), font = '800 56px "Archivo"'; mctx.font = font;
    const space = mctx.measureText(' ').width, widths = words.map(w => mctx.measureText(w).width);
    const total = widths.reduce((s, w) => s + w, 0) + space * (words.length - 1), y = 312;
    const inK = seg(t, a, a + .15), outK = seg(t, b - .15, b), s = backOut(inK) * (1 - easeIn(outK));
    boilSeed('cap ' + a);
    if (s > .02) paint(rrPts(540 - (total / 2 + 34) * s, y - 46 * s, (total + 68) * s, 92 * s, 30 * s, 0), { wash: '#FFF8EA', ink: PAL.ink, sw: 1.3 });
    // each word lands as the voice reaches it (spread over the spoken length by its letters)
    const letters = words.reduce((n, w) => n + w.length, 0);
    let x = 540 - total / 2, acc = 0;
    words.forEach((w, i) => {
      const wt = a + spoken * acc / letters; acc += w.length;
      const k = seg(t, wt, wt + .12), now = t >= wt && t < a + spoken * acc / letters + .08;
      if (k > 0 && s > .3) letter(w, x + widths[i] / 2, y + 2, 56, now ? '#C27A00' : PAL.ink, { screen: true, ink: false, font, alpha: k * (1 - outK) });
      x += widths[i] + space;
    });
  }

  function endCard(t, lt, dur) {
    boilSeed('end blob'); paint(ellPts(540, 900, 470, 420, 24, 30), { fill: C.yellow, fillOp: 60, bleed: .3, tex: .5, ink: null });
    const em = emotions(lt, [[0, 'excited'], [.9, 'happy']]);
    tile(540, 660, 27, { ...em, ...move('wave', t, 1), sq: (em.sq || 0) + .3 * Math.exp(-9 * lt) * Math.cos(18 * lt) });
    letter('', 540, 790, 0, null, { img: LOGO, w: 500, screen: true, pop: seg(lt, .25, .55) });
    letter('Your Instagram,', 540, 915, 112, PAL.ink, { screen: true, ink: false, font: '800 112px "Archivo"', pop: seg(lt, .45, .7) });
    letter('on autopilot.', 540, 1035, 112, PAL.ink, { screen: true, ink: false, font: '800 112px "Archivo"', pop: seg(lt, .55, .8) });
    const bk = seg(lt, .9, 1.2);
    if (bk > 0) { boilSeed('button'); const s = backOut(bk); paint(rrPts(540 - 370 * s, 1160 - 56 * s, 740 * s, 112 * s, 56 * s, 0), { wash: C.yellow, ink: PAL.ink, sw: 1.2 }); }
    letter('TALK TO US · AWSAVYA.IN', 540, 1161, 40, PAL.ink, { screen: true, ink: false, font: '600 40px "Martian Mono"', pop: seg(lt, 1.0, 1.25) });
    if (lt < .3) brushWipe(.5 + lt / .6, [C.yellowDk, C.yellow]);
  }

  shots([[0, bakery], [B.end, endCard]]);
})();
