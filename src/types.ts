import type { Caption } from "@remotion/captions";

// One entry per shot; holds until the next entry. x = horizontal centre of interest (0..1 of
// source width), w = fraction of source width shown (0.316 full-bleed, 1.0 whole frame over blur).
export type Shot = { t: number; x: number; w?: number; track?: boolean };

export type TrackPoint = { t: number; x: number };

export type Punch = { t: number; dur: number; scale: number };

export type Watermark = {
  src: string;
  widthPx: number;
  corner: "tl" | "tr" | "bl" | "br";
  opacity: number;
};

// bold: big word-pop captions (YouTube/IG). clean: small one-line captions below the chin
// (TikTok podcast pages). frame: rounded-corner video card on black. letterbox: the 16:9
// band scaled ~2x on black, the podcast-compilation look.
export type Style = "bold" | "clean" | "frame" | "letterbox";

export type Grade = { brightness: number; contrast: number; saturate: number };

// Optional scripted context voiceover over a still, before the clip rolls.
export type Intro = {
  audio: string;
  still: string;
  durationSec: number;
  captions: Caption[];
};

export type Music = { src: string; db: number; fadeOutSec: number };

export type CaptionMotion = {
  inSec?: number; outSec?: number; rise?: number; scaleFrom?: number;
  blur?: number; easing?: "cubic" | "expo" | "linear";
};
export type CaptionLayer = { t: number; dur: number; text: string; x: number; y: number;
  size: number; width?: number; font?: "condensed" | "serif" | "sans" | "inter" | "cormorant";
  italic?: boolean; weight?: number; z?: number; rotate?: number;
  align?: "left" | "center" | "right"; suppressBase?: boolean; wordTimes?: number[];
  tracking?: number; lineHeight?: number; color?: string; gradient?: string;
  blend?: "normal" | "screen" | "difference" | "color-dodge";
  surface?: "solid" | "difference"; fillOpacity?: number;
  glow?: number; shadow?: "none" | "soft" | "strong"; motion?: CaptionMotion;
  perspective?: {distance: number; rotateX: number; rotateY: number};
  depth?: "front" | "behind";
};
export type ForegroundMask = {t: number; dur: number;
  keyframes: {t: number; points: [number, number][]}[]};

export type ReferenceEdit = {
  profile: "restrained" | "kinetic" | "editorial";
  frame?: {x: number; y: number; width: number; height: number; radius?: number};
  bandHeight?: number;
  captionY?: number;
  captionSize?: number;
  palette?: "silver";
  wordReveal?: boolean;
  layeredOnly?: boolean;
  layers?: CaptionLayer[];
  foregroundMasks?: ForegroundMask[];
  emphasis?: { t: number; dur: number; text: string; x?: number; y?: number;
    size?: number; italic?: boolean; color?: string }[];
};

export type Cutaway = { src: string; t: number; dur: number };

export type ClipProps = {
  src: string;
  // Pre-blurred 9:16 background rendered by ffmpeg (null = blur src live in the browser).
  bgSrc: string | null;
  fps: number;
  // Total composition length: intro + clip.
  durationSec: number;
  srcWidth: number;
  srcHeight: number;
  // Default fraction of source width shown when a shot has no w.
  widthFrac: number;
  shots: Shot[];
  // Face-centre samples (clip seconds); used by shots with track=true, x is the fallback.
  track: TrackPoint[];
  // Vertical placement of the framed video when it does not fill the height (0 top .. 1 bottom).
  yAnchor: number;
  hook: string;
  hookPersist: boolean;
  hookDurationSec: number;
  captions: Caption[];
  punchIns: Punch[];
  watermark: Watermark | null;
  loopFadeSec: number;
  style: Style;
  grade: Grade;
  accent: string;
  intro: Intro | null;
  music: Music | null;
  referenceEdit?: ReferenceEdit;
  cutaways?: Cutaway[];
};
