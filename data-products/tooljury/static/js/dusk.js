/* The TechTools365 hero scene: a body rising over a valley at dusk. Each site has its own.
   Use <canvas class="tt-dusk" data-dusk="penny|jury|globe|sun"></canvas>, with data-orb-y to place the body. Generated copies live in each site. */
(function () {
  var SKIES = {
    sun: ['#262839', '#45455F', '#7E6780', '#C98F82', '#EDB994'],
    penny: ['#262839', '#45455F', '#7E6780', '#C98F82', '#EDB994'],
    jury: ['#22243A', '#3C3F68', '#6A6A9C', '#A98FB4', '#E4B6B2'],
    globe: ['#1E2A38', '#35506A', '#5F8596', '#A9A99A', '#E8BE9A'],
  };
  var ORBS = {
    sun: { light: '#FCDCC0', mid: '#EFA67C', dark: '#8F7FD8', glow: '255,205,170' },
    penny: { light: '#FBCBA2', mid: '#E58F55', dark: '#B85C25', glow: '255,196,146' },
    jury: { light: '#D5DBFF', mid: '#8C9BFF', dark: '#4F5BC4', glow: '190,198,255' },
    globe: { light: '#C6F0E4', mid: '#4DB8A4', dark: '#1F6F6E', glow: '170,235,215' },
  };

  function ridge(x, W, seed, rough) {
    var u = x / W;
    return Math.sin(u * 7.3 + seed) * 0.5 * rough + Math.sin(u * 17.9 + seed * 2.1) * 0.28 * rough +
      Math.sin(u * 41.3 + seed * 3.7) * 0.13 * rough + Math.sin(u * 97.1 + seed * 5.3) * 0.05 * rough;
  }

  /* What sets each body apart: a coin's rim, scales, a globe's lines, or the T of the logo. */
  function glyph(g, kind, cx, cy, R) {
    g.save();
    g.lineWidth = Math.max(1.5, R * 0.035);
    g.strokeStyle = 'rgba(255,245,235,0.62)';
    g.fillStyle = 'rgba(255,255,255,0.92)';
    g.lineCap = 'round';
    if (kind === 'penny') {
      g.beginPath(); g.arc(cx, cy, R * 0.82, 0, Math.PI * 2); g.stroke();
    } else if (kind === 'sun') {
      g.beginPath(); g.arc(cx, cy, R * 0.82, 0, Math.PI * 2); g.stroke();
      var u = R / 16;
      g.beginPath();
      g.moveTo(cx - 6.5 * u, cy - 7.4 * u); g.lineTo(cx + 6.5 * u, cy - 7.4 * u); g.lineTo(cx + 6.5 * u, cy - 4.2 * u);
      g.lineTo(cx + 1.6 * u, cy - 4.2 * u); g.lineTo(cx + 1.6 * u, cy + 5.6 * u); g.lineTo(cx - 1.6 * u, cy + 5.6 * u);
      g.lineTo(cx - 1.6 * u, cy - 4.2 * u); g.lineTo(cx - 6.5 * u, cy - 4.2 * u); g.closePath(); g.fill();
    } else if (kind === 'globe') {
      g.save();
      g.beginPath(); g.arc(cx, cy, R, 0, Math.PI * 2); g.clip();
      [-0.5, 0, 0.5].forEach(function (k) {
        g.beginPath(); g.ellipse(cx, cy + k * R, R, R * 0.12 + (0.5 - Math.abs(k)) * R * 0.1, 0, 0, Math.PI * 2); g.stroke();
      });
      g.beginPath(); g.ellipse(cx, cy, R * 0.42, R, 0, 0, Math.PI * 2); g.stroke();
      g.beginPath(); g.moveTo(cx, cy - R); g.lineTo(cx, cy + R); g.stroke();
      g.restore();
    } else if (kind === 'jury') {
      var top = cy - R * 0.5, arm = R * 0.56, drop = R * 0.42, pan = R * 0.25;
      g.beginPath(); g.moveTo(cx, cy - R * 0.68); g.lineTo(cx, cy + R * 0.6); g.moveTo(cx - R * 0.26, cy + R * 0.6); g.lineTo(cx + R * 0.26, cy + R * 0.6);
      g.moveTo(cx - arm, top); g.lineTo(cx + arm, top); g.stroke();
      [-1, 1].forEach(function (side) {
        var sx = cx + side * arm;
        g.beginPath(); g.moveTo(sx, top); g.lineTo(sx - pan, top + drop); g.moveTo(sx, top); g.lineTo(sx + pan, top + drop); g.stroke();
        g.beginPath(); g.arc(sx, top + drop, pan, 0, Math.PI); g.stroke();
      });
    }
    g.restore();
  }

  function paint(canvas) {
    var box = canvas.getBoundingClientRect();
    if (!box.width) return;
    var kind = SKIES[canvas.dataset.dusk] ? canvas.dataset.dusk : 'sun';
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    canvas.width = box.width * dpr;
    canvas.height = box.height * dpr;
    var g = canvas.getContext('2d');
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    var W = box.width, H = box.height;

    var stops = SKIES[kind];
    var sky = g.createLinearGradient(0, 0, 0, H * 0.82);
    [0, 0.32, 0.56, 0.76, 1].forEach(function (at, i) { sky.addColorStop(at, stops[i]); });
    g.fillStyle = sky;
    g.fillRect(0, 0, W, H);

    [[0.14, 0.2, 0.34, 0.1, '150,110,120', 0.26], [0.86, 0.17, 0.36, 0.11, '70,78,112', 0.5], [0.3, 0.5, 0.3, 0.05, '245,205,185', 0.2], [0.74, 0.47, 0.34, 0.05, '245,205,185', 0.16]].forEach(function (c) {
      g.save();
      g.translate(W * c[0], H * c[1]);
      g.scale(W * c[2], H * c[3]);
      var r = g.createRadialGradient(0, 0, 0, 0, 0, 1);
      r.addColorStop(0, 'rgba(' + c[4] + ',' + c[5] + ')');
      r.addColorStop(1, 'rgba(' + c[4] + ',0)');
      g.fillStyle = r;
      g.beginPath(); g.arc(0, 0, 1, 0, Math.PI * 2); g.fill();
      g.restore();
    });

    var orb = ORBS[kind];
    var orbY = W < 640 && canvas.dataset.orbYNarrow ? canvas.dataset.orbYNarrow : canvas.dataset.orbY || '0.725';
    var cx = W * 0.5, cy = H * parseFloat(orbY);
    var R = Math.max(40, Math.min(66, W * 0.05)) * parseFloat(canvas.dataset.orbScale || '1');
    var glow = g.createRadialGradient(cx, cy, R * 0.6, cx, cy, R * 5.4);
    glow.addColorStop(0, 'rgba(' + orb.glow + ',0.6)');
    glow.addColorStop(1, 'rgba(' + orb.glow + ',0)');
    g.fillStyle = glow;
    g.fillRect(cx - R * 6, cy - R * 6, R * 12, R * 12);
    var body = g.createRadialGradient(cx - R * 0.32, cy - R * 0.38, R * 0.1, cx, cy, R * 1.12);
    body.addColorStop(0, orb.light);
    body.addColorStop(0.55, orb.mid);
    body.addColorStop(1, orb.dark);
    g.fillStyle = body;
    g.beginPath(); g.arc(cx, cy, R, 0, Math.PI * 2); g.fill();
    glyph(g, kind, cx, cy, R);

    var land = kind === 'globe'
      ? ['#7E8C8E', '#566D78', '#3B4E5E', '#2A3847', '#1D2430', '#15161E']
      : kind === 'jury'
        ? ['#7F7396', '#5D5A85', '#44446A', '#2F304C', '#1F2031', '#15161E']
        : ['#94788A', '#6D6480', '#494A67', '#30324A', '#1F2130', '#15161E'];
    [[0.76, 0.17, 12, 1.1], [0.8, 0.25, 18, 2.7], [0.85, 0.31, 24, 4.3], [0.9, 0.33, 26, 5.9], [0.95, 0.34, 22, 7.7], [1, 0.22, 14, 9.2]].forEach(function (l, i) {
      g.fillStyle = land[i];
      g.beginPath();
      g.moveTo(0, H);
      for (var x = 0; x <= W + 3; x += 3) {
        var v = Math.pow(Math.abs(x / W - 0.5) * 2, 1.7);
        g.lineTo(x, H * l[0] - v * H * l[1] - ridge(x, W, l[3], l[2]));
      }
      g.lineTo(W, H);
      g.closePath();
      g.fill();
      if (i < 4) {
        var y = H * l[0];
        var mist = g.createRadialGradient(cx, y, 0, cx, y, W * 0.42);
        mist.addColorStop(0, 'rgba(248,214,192,' + (0.26 - i * 0.05) + ')');
        mist.addColorStop(1, 'rgba(248,214,192,0)');
        g.save();
        g.translate(0, y);
        g.scale(1, 0.09);
        g.translate(0, -y);
        g.fillStyle = mist;
        g.fillRect(0, y - H * 6, W, H * 12);
        g.restore();
      }
    });
  }

  function start() {
    Array.prototype.forEach.call(document.querySelectorAll('canvas[data-dusk]'), function (canvas) {
      paint(canvas);
      var w = canvas.getBoundingClientRect().width;
      if ('ResizeObserver' in window) {
        new ResizeObserver(function () {
          var n = canvas.getBoundingClientRect().width;
          if (n && n !== w) { w = n; paint(canvas); }
        }).observe(canvas);
      }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
