// Declarative vector drawing. Environments and props are stored as JSON shape
// lists (editable source files), never as executable code.
//
// Shape: {type, ...geometry, fill?, stroke?, lineWidth?, alpha?, blend?, blur?,
//         rotate?, origin?:{x,y}, children? (type "group")}
// type: rect | roundRect | ellipse | circle | path (SVG "d") | line | polyline |
//       polygon | group | image
// fill: "#hex" | {linear:[x0,y0,x1,y1], stops:[[0,"#hex"],[1,"#hex"]]}
//              | {radial:[x0,y0,r0,x1,y1,r1], stops:[...]}
import { Path2D } from '@napi-rs/canvas';

function paint(ctx, spec) {
  if (!spec || typeof spec === 'string') return spec;
  let g;
  if (spec.linear) g = ctx.createLinearGradient(...spec.linear);
  else if (spec.radial) g = ctx.createRadialGradient(...spec.radial);
  else throw new Error('Gradient needs "linear" or "radial"');
  for (const [o, c] of spec.stops) g.addColorStop(o, c);
  return g;
}

function buildPath(s) {
  const p = new Path2D();
  switch (s.type) {
    case 'rect': p.rect(s.x, s.y, s.w, s.h); break;
    case 'roundRect': p.roundRect(s.x, s.y, s.w, s.h, s.r ?? 12); break;
    case 'ellipse': p.ellipse(s.x, s.y, s.rx, s.ry, 0, 0, Math.PI * 2); break;
    case 'circle': p.arc(s.x, s.y, s.r, 0, Math.PI * 2); break;
    case 'path': return new Path2D(s.d);
    case 'line': p.moveTo(s.x1, s.y1); p.lineTo(s.x2, s.y2); break;
    case 'polyline':
    case 'polygon': {
      const pts = s.points;
      p.moveTo(pts[0], pts[1]);
      for (let i = 2; i < pts.length; i += 2) p.lineTo(pts[i], pts[i + 1]);
      if (s.type === 'polygon') p.closePath();
      break;
    }
    default: throw new Error(`Unknown shape type "${s.type}"`);
  }
  return p;
}

/**
 * Draw shapes. `images` resolves image shape paths to loaded Image objects.
 * `vars` optionally provides time-varying values: a shape with
 * `sway: {amp, speed, origin}` rotates gently (leaves, curtains, steam).
 */
export function drawShapes(ctx, shapes, { images = {}, time = 0 } = {}) {
  for (const s of shapes) {
    if (s.hidden) continue;
    ctx.save();
    if (s.alpha !== undefined) ctx.globalAlpha *= s.alpha;
    if (s.blend) ctx.globalCompositeOperation = s.blend;
    if (s.blur) ctx.filter = `blur(${s.blur}px)`;
    const o = s.origin || { x: 0, y: 0 };
    let rot = s.rotate || 0;
    if (s.sway) rot += Math.sin(time * (s.sway.speed || 1) * Math.PI * 2 + (s.sway.phase || 0)) * (s.sway.amp || 0.03);
    let dy = 0;
    if (s.bob) dy = Math.sin(time * (s.bob.speed || 1) * Math.PI * 2 + (s.bob.phase || 0)) * (s.bob.amp || 4);
    if (rot || s.scale || dy) {
      ctx.translate(o.x, o.y + dy);
      if (rot) ctx.rotate(rot);
      if (s.scale) ctx.scale(s.scale, s.scale);
      ctx.translate(-o.x, -o.y);
    }
    if (s.type === 'group') {
      if (s.translate) ctx.translate(s.translate.x || 0, s.translate.y || 0);
      drawShapes(ctx, s.children || [], { images, time });
    } else if (s.type === 'image') {
      const img = images[s.path];
      if (!img) throw new Error(`Image not loaded: ${s.path}`);
      ctx.drawImage(img, s.x, s.y, s.w ?? img.width, s.h ?? img.height);
    } else {
      const p = buildPath(s);
      if (s.fill) { ctx.fillStyle = paint(ctx, s.fill); ctx.fill(p, s.fillRule || 'nonzero'); }
      if (s.stroke) {
        ctx.strokeStyle = paint(ctx, s.stroke);
        ctx.lineWidth = s.lineWidth ?? 4;
        ctx.lineCap = s.lineCap || 'round';
        ctx.lineJoin = s.lineJoin || 'round';
        ctx.stroke(p);
      }
    }
    ctx.restore();
  }
}

/** Collect image paths referenced by shapes (for preloading). */
export function shapeImages(shapes, out = new Set()) {
  for (const s of shapes || []) {
    if (s.type === 'image') out.add(s.path);
    if (s.children) shapeImages(s.children, out);
  }
  return out;
}
