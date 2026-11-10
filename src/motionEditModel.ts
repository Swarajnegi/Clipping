import type {CaptionLayer, Shot} from "./types";
import {captionMotion} from "./captionMotion";

export type MotionBadge = {text: string; at: number; x: number; y: number; width: number};
export type MotionSide = {title: string; detail?: string; asset?: string};
export type MotionScene = {
  kind: "speaker" | "emphasis" | "illustration" | "comparison" | "badges";
  start: number; end: number; title?: string; subtitle?: string; eyebrow?: string;
  asset?: string; left?: MotionSide; right?: MotionSide; badges?: MotionBadge[];
  captionLayers?: CaptionLayer[];
};
export type MotionEditProps = {
  src: string; fps: number; durationInFrames: number; sourceWidth: number; sourceHeight: number;
  hasAudio: boolean; shots: Shot[]; captionLayers: CaptionLayer[]; scenes: MotionScene[];
  palette: {light: string; dark: string; accent: string};
};

export const sceneAt = (scenes: MotionScene[], frame: number, fps: number) =>
  scenes.find(scene => frame >= Math.round(scene.start * fps) && frame < Math.round(scene.end * fps));

export const sceneMotion = (frame: number, fps: number, scene: MotionScene) =>
  captionMotion(frame / fps, scene.start, scene.end,
    {inSec: 0.24, outSec: 0.08, rise: 28, scaleFrom: 0.97, blur: 0});

// Graphic scenes never reset the source clock. Keeping the video mounted preserves seeks.
export const sourceFrameAt = (compositionFrame: number) => compositionFrame;
