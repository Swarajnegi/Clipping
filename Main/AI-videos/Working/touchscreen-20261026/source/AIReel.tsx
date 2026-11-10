import React from "react";
import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {TouchscreenScene} from "./TouchscreenScene";

export type AIScene = {duration: number; heading: string; body?: string; asset?: string; kind?: "image" | "video"; accent?: string; visual?: "touchscreen"; phase?: number};
export type AIReelProps = {title: string; scenes: AIScene[]; audio?: string; captions?: {w: string; s: number; e: number}[]; fps?: number};

const Diagram: React.FC<{accent: string; frame: number; fps: number}> = ({accent, frame, fps}) => {
  const progress = (frame / fps / 4) % 1;
  return <svg viewBox="0 0 800 640" style={{width: "100%", filter: "drop-shadow(0 22px 28px #0008)"}}>
    <path d="M130 390 L400 540 L670 390 L400 240Z" fill="#202c3c" stroke="#52627a" strokeWidth="3"/>
    {[0, 1, 2].map(i => {const x = 210 + i * 150; const y = 270 - i * 35; return <g key={i} transform={`translate(${x},${y + Math.sin(frame / fps * 1.4 + i) * 7})`}>
      <path d="M-75 0L0 -43L75 0L0 43Z" fill={accent}/><path d="M-75 0L0 43V150L-75 107Z" fill="#42627c"/>
      <path d="M0 43L75 0V107L0 150Z" fill="#283f57"/>
      {[0,1,2].map(j => <path key={j} d={`M-58 ${32+j*29}L-18 ${55+j*29}`} stroke="#c5e5ee" strokeWidth="4"/>)}
    </g>;})}
    <path d="M200 460 L400 570 L630 430" stroke={accent} strokeWidth="6" fill="none" strokeDasharray="12 15"/>
    <circle cx={200 + progress * 430} cy={460 + Math.sin(progress * Math.PI) * 85 - progress * 30} r="12" fill="#fff"/>
  </svg>;
};

const Scene: React.FC<AIScene> = ({heading, body, asset, kind, accent = "#82e6cb", visual, phase = 0, duration}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const rise = interpolate(frame, [0, fps * .55], [34, 0], {extrapolateRight: "clamp"});
  const opacity = interpolate(frame, [0, fps * .35], [0, 1], {extrapolateRight: "clamp"});
  const zoom = interpolate(frame, [0, Math.max(durationInFrames, 1)], [1, 1.04], {extrapolateRight: "clamp"});
  if (visual === "touchscreen") return <TouchscreenScene heading={heading} phase={phase} duration={duration}/>;
  return <AbsoluteFill style={{background: "#0a1420", color: "#f2f5f7", fontFamily: "Arial, sans-serif", padding: "160px 76px 260px"}}>
    <div style={{position: "absolute", inset: 0, background: `radial-gradient(ellipse at 80% 55%, ${accent}18, transparent 60%)`}}/>
    <div style={{height: 8, width: 88, background: accent, marginBottom: 38}}/>
    <div style={{fontSize: 68, fontWeight: 800, lineHeight: 1.12, transform: `translateY(${rise}px)`, opacity}}>{heading}</div>
    <div style={{flex: 1, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden", margin: "40px 0", borderRadius: 30}}>
      {asset ? (kind === "video" ? <OffthreadVideo src={staticFile(asset)} muted style={{width: "100%", height: "100%", objectFit: "cover"}}/> :
        <Img src={staticFile(asset)} style={{maxWidth: "100%", maxHeight: "100%", transform: `scale(${zoom})`}}/>) : <Diagram accent={accent} frame={frame} fps={fps}/>}
    </div>
    {body && <div style={{fontSize: 36, lineHeight: 1.4, color: "#b7c7d4", opacity}}>{body}</div>}
  </AbsoluteFill>;
};

export const AIReel: React.FC<AIReelProps> = ({title, scenes, audio, captions = []}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  let cursor = 0;
  const active = captions.find(word => frame / fps >= word.s && frame / fps < word.e);
  const touchscreen = scenes.every(scene => scene.visual === "touchscreen");
  const activeIndex = captions.findIndex(word => frame / fps >= word.s && frame / fps < word.e);
  const groupStart = Math.floor(Math.max(activeIndex, 0) / 4) * 4;
  return <AbsoluteFill>
    {scenes.map((scene, i) => {const from = cursor; const frames = Math.round(scene.duration * fps); cursor += frames;
      return <Sequence key={i} from={from} durationInFrames={frames}><Scene {...scene}/></Sequence>;})}
    {audio && <Audio src={staticFile(audio)}/>}
    <div style={{position: "absolute", left: 82, right: 82, bottom: touchscreen ? 215 : 162, textAlign: "center", color: touchscreen ? "#172c35" : "#fff", fontFamily: "Arial, sans-serif", fontWeight: 800, fontSize: touchscreen ? 49 : 54,
      textShadow: touchscreen ? "none" : "0 3px 12px #000", minHeight: 70, lineHeight: 1.3}}>{touchscreen ? (activeIndex >= 0 && captions.slice(groupStart, groupStart + 4).map((word, i) =>
        <span key={i} style={{color: groupStart + i === activeIndex ? "#d65334" : "#172c35"}}>{word.w.trim()}{" "}</span>)) : active?.w.trim()}</div>
    {!touchscreen && <div style={{position: "absolute", left: 76, top: 76, font: "22px Arial", color: "#9db2c3", letterSpacing: 3}}>{title.toUpperCase()}</div>}
  </AbsoluteFill>;
};
