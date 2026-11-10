import React from "react";
import { Composition } from "remotion";
import { ViralShort } from "./ViralShort";
import type { ClipProps } from "./types";
import { AIReel, AIReelProps } from "./AIReel";

const defaults: ClipProps = {
  src: "clips/sample/clip_01.mp4",
  bgSrc: null,
  fps: 30,
  durationSec: 10,
  srcWidth: 1920,
  srcHeight: 1080,
  widthFrac: 0.42,
  shots: [{ t: 0, x: 0.5 }],
  track: [],
  yAnchor: 0.42,
  hook: "WAIT FOR IT",
  hookPersist: true,
  hookDurationSec: 2.5,
  captions: [],
  punchIns: [],
  watermark: null,
  loopFadeSec: 0,
  style: "bold",
  grade: { brightness: 1, contrast: 1, saturate: 1 },
  accent: "#FFE14D",
  intro: null,
  music: null,
};

export const RemotionRoot: React.FC = () => (
  <>
  <Composition
    id="ViralShort"
    component={ViralShort as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={300}
    defaultProps={defaults as unknown as Record<string, unknown>}
    calculateMetadata={({ props }) => {
      const p = props as unknown as ClipProps;
      return { fps: p.fps, durationInFrames: Math.max(1, Math.round(p.durationSec * p.fps)) };
    }}
  />
  <Composition id="AIReel" component={AIReel as unknown as React.FC<Record<string, unknown>>}
    width={1080} height={1920} fps={30} durationInFrames={240}
    defaultProps={{title: "AI video", scenes: [{duration: 8, heading: "A clear idea, brought to life"}]}}
    calculateMetadata={({props}) => {const p = props as unknown as AIReelProps; const fps = p.fps || 30;
      return {fps, durationInFrames: p.scenes.reduce((total, scene) => total + Math.round(scene.duration * fps), 0)};}}/>
  </>
);
