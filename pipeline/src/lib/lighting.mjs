// Screen-space cinematic lighting for A4 warmth: colour grade, drifting light
// shafts, floating dust motes and vignette. Presets live in
// assets/presets/lighting.json so a look is reusable across episodes.
import { hashSeed } from './util.mjs';

export function drawLighting(ctx, preset, { w, h, time, intensity = 1 }) {
  if (!preset) return;
  const k = intensity;
  if (preset.grade) {
    ctx.save();
    ctx.globalCompositeOperation = preset.grade.blend || 'soft-light';
    ctx.globalAlpha = (preset.grade.alpha ?? 0.15) * k;
    ctx.fillStyle = preset.grade.color;
    ctx.fillRect(0, 0, w, h);
    ctx.restore();
  }
  if (preset.gradient) {
    // Directional warm/cool wash, e.g. sunlight entering from one side.
    const g = preset.gradient;
    const [x0, y0, x1, y1] = g.from_to.map((v, i) => v * (i % 2 ? h : w));
    const lg = ctx.createLinearGradient(x0, y0, x1, y1);
    lg.addColorStop(0, g.colors[0]); lg.addColorStop(1, g.colors[1]);
    ctx.save(); ctx.globalCompositeOperation = g.blend || 'soft-light'; ctx.globalAlpha = (g.alpha ?? 0.3) * k;
    ctx.fillStyle = lg; ctx.fillRect(0, 0, w, h); ctx.restore();
  }
  if (preset.rays) {
    const r = preset.rays;
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    ctx.filter = `blur(${(r.blur ?? 28) * (w / 1080)}px)`;
    const ox = (r.origin?.x ?? 0.1) * w, oy = (r.origin?.y ?? -0.1) * h;
    const base = (r.angle ?? 30) * Math.PI / 180;
    for (let i = 0; i < (r.count ?? 4); i++) {
      const s = hashSeed(`ray${i}`);
      const a = base + (i - (r.count ?? 4) / 2) * (r.spread ?? 0.09) + Math.sin(time * 0.35 + s * 9) * 0.015;
      const wdt = (r.width ?? 0.05) * (0.6 + s);
      const len = h * 1.6;
      ctx.globalAlpha = (r.alpha ?? 0.14) * k * (0.6 + 0.4 * Math.sin(time * 0.6 + s * 7) ** 2);
      ctx.fillStyle = r.color || '#FFE6B0';
      ctx.beginPath();
      ctx.moveTo(ox, oy);
      ctx.lineTo(ox + Math.sin(a - wdt) * len, oy + Math.cos(a - wdt) * len);
      ctx.lineTo(ox + Math.sin(a + wdt) * len, oy + Math.cos(a + wdt) * len);
      ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }
  if (preset.motes) {
    const m = preset.motes;
    ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = m.color || '#FFF1CC';
    for (let i = 0; i < (m.count ?? 24); i++) {
      const s = hashSeed(`mote${i}`), s2 = hashSeed(`mote-y${i}`);
      const x = ((s * w + time * 14 * (0.5 + s2)) % w + w) % w;
      const y = ((s2 * h - time * 9 * (0.4 + s)) % h + h) % h;
      ctx.globalAlpha = (m.alpha ?? 0.35) * k * (0.4 + 0.6 * Math.abs(Math.sin(time * (0.6 + s) + i)));
      ctx.beginPath(); ctx.arc(x, y, (1.5 + s * 3) * (w / 1080), 0, Math.PI * 2); ctx.fill();
    }
    ctx.restore();
  }
  if (preset.vignette) {
    const v = preset.vignette;
    const g = ctx.createRadialGradient(w / 2, h * 0.45, Math.min(w, h) * 0.35, w / 2, h / 2, Math.max(w, h) * 0.75);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(1, v.color || '#1C140E');
    ctx.save(); ctx.globalAlpha = (v.alpha ?? 0.3) * k; ctx.globalCompositeOperation = v.blend || 'multiply';
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h); ctx.restore();
  }
}
