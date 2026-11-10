import React from "react";
import { Composition } from "remotion";
import { ViralShort } from "./ViralShort";
import type { ClipProps } from "./types";
import { AIReel, AIReelProps } from "./AIReel";
import { Touchscreen3DTest } from "./Touchscreen3DTest";
import { CaptionSurfaceTest } from "./CaptionSurfaceTest";
import {MotionEdit} from "./MotionEdit";
import type {MotionEditProps} from "./motionEditModel";

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
  <Composition id="MotionEdit" component={MotionEdit as unknown as React.FC<Record<string, unknown>>}
    width={1080} height={1920} fps={25} durationInFrames={75}
    defaultProps={{src: "clips/sample/clip_01.mp4", sourceWidth: 1920, sourceHeight: 1080,
      fps: 25, durationInFrames: 75, hasAudio: false, shots: [], captionLayers: [],
      scenes: [{kind: "speaker", start: 0, end: 3}], palette: {light: "#f5f4f0", dark: "#101114", accent: "#c8f45d"}}}
    calculateMetadata={({props}) => {const p = props as unknown as MotionEditProps;
      return {fps: p.fps, durationInFrames: p.durationInFrames};}}/>
  <Composition id="CaptionSurfaceTest" component={CaptionSurfaceTest} width={1080} height={1920} fps={30} durationInFrames={60}/>
  <Composition id="Touchscreen3DTest" component={Touchscreen3DTest} width={1080} height={1920} fps={30} durationInFrames={240}/>
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
