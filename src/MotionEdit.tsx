import React from "react";
import {AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {Framed} from "./ViralShort";
import {EditorialCaptions, useCaptionFonts} from "./EditorialCaptions";
import type {CaptionLayer, ClipProps} from "./types";
import {captionMotion} from "./captionMotion";
import {sceneAt, sceneMotion, sourceFrameAt} from "./motionEditModel";
import type {MotionEditProps, MotionScene, MotionSide} from "./motionEditModel";

const titleStyle: React.CSSProperties = {
  fontFamily: "'Inter Caption', sans-serif", fontWeight: 800, letterSpacing: "-.045em",
  lineHeight: 1.02, overflowWrap: "break-word",
};
const serifStyle: React.CSSProperties = {
  fontFamily: "'Cormorant Caption', serif", fontWeight: 700, fontStyle: "italic",
  fontSynthesis: "none", lineHeight: 1.1,
};
const Asset: React.FC<{src: string; height?: number}> = ({src, height = 570}) =>
  <Img src={staticFile(src)} style={{width: "100%", height, objectFit: "contain"}}/>;

const Side: React.FC<{side: MotionSide; featured: boolean; palette: MotionEditProps["palette"]}> = ({side, featured, palette}) =>
  <div data-motion-box="comparison" style={{width: 430, minHeight: 580, padding: "56px 32px", borderRadius: 34,
    background: featured ? palette.accent : "#ffffff0d", border: "1px solid #ffffff24",
    color: featured ? palette.dark : palette.light, display: "flex", flexDirection: "column", justifyContent: "center", gap: 34}}>
    {side.asset && <Asset src={side.asset} height={250}/>}
    <div style={{...titleStyle, fontSize: 66}}>{side.title}</div>
    {side.detail && <div style={{fontSize: 34, lineHeight: 1.35, opacity: .8}}>{side.detail}</div>}
  </div>;

export const MotionGraphics: React.FC<{scene: MotionScene; p: MotionEditProps}> = ({scene, p}) => {
  const frame = useCurrentFrame(); const {fps} = useVideoConfig();
  const motion = sceneMotion(frame, fps, scene);
  const {palette} = p;
  const entry = {opacity: motion.opacity, transform: `translateY(${motion.rise}px) scale(${motion.scale})`};
  if (scene.kind === "speaker") return null;
  if (scene.kind === "badges") return <AbsoluteFill style={{pointerEvents: "none"}}>
    {(scene.badges ?? []).map((badge, index) => {
      const b = captionMotion(frame / fps, badge.at, scene.end,
        {inSec: .22, outSec: .08, rise: 16, scaleFrom: .96, blur: 0});
      return <div data-motion-box="badge" key={index} style={{position: "absolute", left: badge.x, top: badge.y,
        width: badge.width, padding: "20px 26px", borderRadius: 22, background: palette.dark,
        border: "1px solid #ffffff36", color: palette.light, fontSize: 34, ...titleStyle,
        boxShadow: "0 8px 26px #0007", opacity: b.opacity,
        transform: `translateY(${b.rise}px) scale(${b.scale})`}}>
        <span style={{color: palette.accent, marginRight: 16}}>●</span>{badge.text}
      </div>;
    })}
  </AbsoluteFill>;
  if (scene.kind === "emphasis") return <AbsoluteFill style={{justifyContent: "flex-end", padding: "0 88px 390px",
    background: "linear-gradient(transparent 45%, #000b 100%)", color: palette.light}}>
    <div data-motion-box="emphasis" style={entry}>
      {scene.eyebrow && <div style={{fontSize: 30, letterSpacing: ".12em", marginBottom: 28}}>{scene.eyebrow}</div>}
      <div style={{...titleStyle, fontSize: 108, color: palette.accent}}>{scene.title}</div>
      {scene.subtitle && <div style={{...serifStyle, fontSize: 82, marginTop: 24}}>{scene.subtitle}</div>}
    </div>
  </AbsoluteFill>;
  if (scene.kind === "comparison") return <AbsoluteFill style={{background: palette.dark, color: palette.light,
    justifyContent: "center", padding: "230px 88px 350px", textAlign: "center"}}>
    <div data-motion-box="comparison-title" style={{...entry, marginBottom: 70}}>
      {scene.eyebrow && <div style={{fontSize: 28, letterSpacing: ".13em", marginBottom: 26}}>{scene.eyebrow}</div>}
      <div style={{...titleStyle, fontSize: 76}}>{scene.title}</div>
    </div>
    <div style={{...entry, display: "flex", gap: 44}}>
      <Side side={scene.left!} featured={false} palette={palette}/>
      <Side side={scene.right!} featured={true} palette={palette}/>
    </div>
    {scene.subtitle && <div style={{...serifStyle, ...entry, fontSize: 62, marginTop: 55}}>{scene.subtitle}</div>}
  </AbsoluteFill>;
  return <AbsoluteFill style={{background: palette.light, color: palette.dark,
    padding: "270px 100px 350px", justifyContent: "center", textAlign: "center"}}>
    <div style={{...entry, display: "flex", flexDirection: "column", gap: 42}}>
      {scene.eyebrow && <div style={{fontSize: 27, letterSpacing: ".14em"}}>{scene.eyebrow}</div>}
      <div data-motion-box="illustration-title" style={{...titleStyle, fontSize: 88}}>{scene.title}</div>
      {scene.asset && <Asset src={scene.asset}/>}
      {scene.subtitle && <div data-motion-box="illustration-subtitle" style={{...serifStyle, fontSize: 72}}>{scene.subtitle}</div>}
      <div style={{height: 8, width: 100, background: palette.accent, alignSelf: "center", marginTop: 12}}/>
    </div>
  </AbsoluteFill>;
};

export const MotionEdit: React.FC<MotionEditProps> = p => {
  useCaptionFonts([{font: "inter"}, {font: "cormorant", italic: true}]);
  const frame = useCurrentFrame(); const {fps} = useVideoConfig(); const t = frame / fps;
  const scene = sceneAt(p.scenes, frame, fps);
  const crop = Math.min(1, p.sourceHeight * 1080 / (1920 * p.sourceWidth));
  const framing: ClipProps = {
    src: p.src, srcWidth: p.sourceWidth, srcHeight: p.sourceHeight, bgSrc: null,
    fps, durationSec: p.durationInFrames / fps, widthFrac: crop,
    shots: p.shots.length ? p.shots : [{t: 0, x: .5, w: crop}], track: [], yAnchor: .5,
    hook: "", hookPersist: false, hookDurationSec: 0, captions: [], punchIns: [], watermark: null,
    loopFadeSec: 0, style: "bold", grade: {brightness: 1, contrast: 1, saturate: 1},
    accent: p.palette.accent, intro: null, music: null,
    referenceEdit: {profile: "editorial", bandHeight: 1920, layeredOnly: true},
  };
  const layers: CaptionLayer[] = scene?.captionLayers ?? (
    !scene || scene.kind === "speaker" || scene.kind === "badges" ? p.captionLayers : []);
  return <AbsoluteFill style={{background: p.palette.dark, fontFamily: "'Inter Caption', sans-serif", fontSynthesis: "none"}}>
    <Framed p={framing} t={t} frame={sourceFrameAt(frame)} muted/>
    {p.hasAudio && <Audio src={staticFile(p.src)}/>}
    {scene && <MotionGraphics scene={scene} p={p}/>}
    <EditorialCaptions p={{referenceEdit: {profile: "editorial", layers}}} depth="front"/>
  </AbsoluteFill>;
};
