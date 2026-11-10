import type {CaptionMotion, ForegroundMask} from "./types";

const clamp = (v: number) => Math.min(1, Math.max(0, v));

export const captionMotion = (t: number, at: number, end: number, m: CaptionMotion = {}) => {
  const progress = clamp((t - at) / Math.max(0.001, m.inSec ?? 0.2));
  const ease = m.easing === "linear" ? progress : m.easing === "expo"
    ? progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
    : 1 - Math.pow(1 - progress, 3);
  const exit = clamp((end - t) / Math.max(0.001, m.outSec ?? 0.08));
  return {opacity: t < at || t >= end ? 0 : (0.35 + 0.65 * ease) * exit,
    rise: (m.rise ?? 28) * (1 - ease),
    scale: (m.scaleFrom ?? 0.92) + (1 - (m.scaleFrom ?? 0.92)) * ease,
    blur: (m.blur ?? 10) * (1 - ease)};
};

export const maskPoints = (mask: ForegroundMask, t: number): [number, number][] => {
  const frames = mask.keyframes;
  if (t <= frames[0].t) return frames[0].points;
  if (t >= frames[frames.length - 1].t) return frames[frames.length - 1].points;
  const index = frames.findIndex(f => f.t > t);
  const a = frames[index - 1], b = frames[index];
  const mix = (t - a.t) / (b.t - a.t);
  return a.points.map((point, i) => [point[0] + (b.points[i][0] - point[0]) * mix,
    point[1] + (b.points[i][1] - point[1]) * mix]);
};
