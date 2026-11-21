// Scene-to-scene transitions composited from two rendered frames A (outgoing)
// and B (incoming). `u` runs 0..1 across the transition window, which is
// centred on the cut point. Durations follow Camera Guide §6 (0.15–0.8 s).
import { ease, clamp } from './util.mjs';

function motionBlurDraw(ctx, img, dx, dy, amount, w, h, steps = 7) {
  if (amount < 0.5) { ctx.drawImage(img, dx, dy, w, h); return; }
  ctx.save();
  ctx.globalAlpha = 1;
  ctx.drawImage(img, dx, dy, w, h);
  for (let i = 1; i <= steps; i++) {
    const o = (i / steps) * amount;
    ctx.globalAlpha = 0.5 / i + 0.08;
    ctx.drawImage(img, dx - o, dy, w, h);
    ctx.drawImage(img, dx + o, dy, w, h);
  }
  ctx.restore();
}

function scaledDraw(ctx, img, s, w, h, cx = 0.5, cy = 0.5, blur = 0) {
  ctx.save();
  if (blur > 0.3) ctx.filter = `blur(${blur}px)`;
  ctx.translate(w * cx, h * cy); ctx.scale(s, s); ctx.translate(-w * cx, -h * cy);
  ctx.drawImage(img, 0, 0, w, h);
  ctx.restore();
}

export const TRANSITION_TYPES = ['cut', 'smash_cut', 'match_cut', 'whip_pan', 'push', 'snap_zoom', 'push_through', 'object_wipe', 'iris', 'dip', 'motion_blur'];

export function composeTransition(ctx, tr, u, A, B, { w, h }) {
  const type = tr.type || 'cut';
  const dir = tr.direction === 'right' ? -1 : tr.direction === 'up' ? 2 : tr.direction === 'down' ? -2 : 1; // default: content moves left
  switch (type) {
    case 'cut': case 'match_cut':
      ctx.drawImage(u < 0.5 ? A : B, 0, 0, w, h); return;
    case 'smash_cut': {
      if (u < 0.5) { ctx.drawImage(A, 0, 0, w, h); return; }
      const k = (u - 0.5) * 2; // punch-in settle on B
      scaledDraw(ctx, B, 1 + (1 - ease('easeOutCubic', k)) * (tr.punch ?? 0.08), w, h);
      if (tr.flash && k < 0.25) { ctx.save(); ctx.globalAlpha = (1 - k / 0.25) * 0.8; ctx.fillStyle = tr.flash === true ? '#FFFFFF' : tr.flash; ctx.fillRect(0, 0, w, h); ctx.restore(); }
      return;
    }
    case 'whip_pan': case 'push': case 'motion_blur': {
      const e = ease(tr.ease || (type === 'push' ? 'easeInOutCubic' : 'easeInOutExpo'), u);
      const vertical = Math.abs(dir) === 2, sgn = Math.sign(dir);
      const span = vertical ? h : w;
      const off = e * span * sgn;
      const blur = type === 'push' ? 0 : Math.sin(u * Math.PI) * (tr.blur ?? 0.09) * w;
      if (vertical) {
        ctx.drawImage(A, 0, -off, w, h); ctx.drawImage(B, 0, span * sgn - off, w, h);
      } else {
        motionBlurDraw(ctx, A, -off, 0, blur, w, h);
        motionBlurDraw(ctx, B, span * sgn - off, 0, blur, w, h);
      }
      return;
    }
    case 'snap_zoom': case 'push_through': {
      const pt = tr.focus || { x: 0.5, y: 0.45 };
      if (u < 0.5) {
        const k = ease('easeInExpo', u * 2);
        scaledDraw(ctx, A, 1 + k * (type === 'push_through' ? 3 : 1.6), w, h, pt.x, pt.y, k * 18 * (w / 1080));
      } else {
        const k = ease('easeOutExpo', (u - 0.5) * 2);
        scaledDraw(ctx, B, (type === 'push_through' ? 0.55 : 1.35) + k * (1 - (type === 'push_through' ? 0.55 : 1.35)), w, h, 0.5, 0.5, (1 - k) * 18 * (w / 1080));
        if (type === 'push_through' && k < 1) { ctx.save(); ctx.globalAlpha = 1 - k; ctx.drawImage(A, 0, 0, w, h); ctx.restore(); }
      }
      return;
    }
    case 'object_wipe': {
      // A dark soft-edged foreground shape (pillar, plant, passer-by) sweeps across.
      ctx.drawImage(u < 0.5 ? A : B, 0, 0, w, h);
      const e = ease('easeInOutSine', u);
      const bw = w * (tr.width ?? 1.25);
      const x = -bw + e * (w + bw);
      ctx.save();
      ctx.fillStyle = tr.color || '#2B2A33';
      ctx.filter = `blur(${10 * (w / 1080)}px)`;
      ctx.beginPath(); ctx.roundRect(sgnX(dir, x, bw, w), -h * 0.1, bw, h * 1.2, bw * 0.2); ctx.fill();
      ctx.restore();
      return;
    }
    case 'iris': {
      const maxR = Math.hypot(w, h) * 0.55;
      if (u < 0.5) { ctx.drawImage(A, 0, 0, w, h); circleMask(ctx, w, h, maxR * (1 - ease('easeInCubic', u * 2)), tr.color); }
      else { ctx.drawImage(B, 0, 0, w, h); circleMask(ctx, w, h, maxR * ease('easeOutCubic', (u - 0.5) * 2), tr.color); }
      return;
    }
    case 'dip': {
      // Only for emotional beats / time jumps (Camera Guide §5).
      ctx.drawImage(u < 0.5 ? A : B, 0, 0, w, h);
      ctx.save(); ctx.globalAlpha = 1 - Math.abs(u - 0.5) * 2; ctx.fillStyle = tr.color || '#1B1712'; ctx.fillRect(0, 0, w, h); ctx.restore();
      return;
    }
    default: throw new Error(`Unknown transition "${type}". Known: ${TRANSITION_TYPES.join(', ')}`);
  }
}
const sgnX = (dir, x, bw, w) => (dir < 0 ? w - x - bw : x);
function circleMask(ctx, w, h, r, color = '#1B1712') {
  ctx.save();
  ctx.beginPath(); ctx.rect(0, 0, w, h); ctx.arc(w / 2, h * 0.45, Math.max(0, r), 0, Math.PI * 2, true);
  ctx.fillStyle = color; ctx.fill('evenodd'); ctx.restore();
}

/** Clamp a transition to the neighbouring scenes so windows never overlap. */
export function transitionWindow(tr, cutTime, prevDur, nextDur) {
  if (!tr || tr.type === 'cut' || tr.type === 'match_cut') return null;
  const d = clamp(tr.duration ?? 0.35, 0.06, Math.min(prevDur, nextDur) * 0.9);
  return { start: cutTime - d / 2, end: cutTime + d / 2, duration: d };
}
