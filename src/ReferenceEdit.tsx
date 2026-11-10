import React, {useMemo} from "react";
import {OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {createTikTokStyleCaptions} from "@remotion/captions";
import type {ClipProps} from "./types";
import {referencePictureBox} from "./pictureFrame";

export const ReferenceCutaways: React.FC<{p: ClipProps}> = ({p}) => {
  const {fps} = useVideoConfig();
  const box = referencePictureBox(p.referenceEdit!);
  return <>{(p.cutaways ?? []).map((cut, i) =>
    <Sequence key={i} from={Math.round(cut.t * fps)} durationInFrames={Math.max(1, Math.round(cut.dur * fps))} layout="none">
      <div style={{position: "absolute", left: box.x, top: box.y, width: box.w, height: box.h,
        borderRadius: box.radius, overflow: "hidden", background: "black"}}>
        <OffthreadVideo src={staticFile(cut.src)} muted
          style={{width: "100%", height: "100%", objectFit: "cover"}} />
      </div>
    </Sequence>)}</>;
};

export const ReferenceCaptions: React.FC<{p: ClipProps}> = ({p}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const edit = p.referenceEdit!;
  const t = frame / fps;
  const pages = useMemo(() => createTikTokStyleCaptions({captions: p.captions,
    combineTokensWithinMilliseconds: 850, breakOnSilenceAfterMilliseconds: 350}).pages, [p.captions]);
  const page = pages.find(pg => t * 1000 >= pg.startMs && t * 1000 < pg.startMs + pg.durationMs);
  const emphasis = edit.profile === "kinetic" ? edit.emphasis?.find(cue => t >= cue.t && t < cue.t + cue.dur) : undefined;
  const layers = (edit.layers ?? []).filter(layer => t >= layer.t && t < layer.t + layer.dur);
  const suppressBase = edit.layeredOnly || layers.some(layer => layer.suppressBase !== false);
  const entry = emphasis ? Math.min(1, Math.max(0, (t - emphasis.t) / 0.16)) : 1;
  return <>
    {!emphasis && !suppressBase && page ? <div style={{position: "absolute", left: 70, right: 70,
      top: edit.captionY ?? 1000, textAlign: "center", fontFamily: "Arial, sans-serif",
      fontWeight: edit.profile === "restrained" ? 400 : 700, fontSize: edit.captionSize ?? 34,
      color: edit.palette === "silver" ? "#e7e9ed" : "white", textTransform: edit.profile === "restrained" ? "uppercase" : "none",
      textShadow: "0 2px 5px #000", lineHeight: 1.15}}>
      {page.tokens.filter(token => !edit.wordReveal || token.fromMs <= t * 1000).map(token => token.text.trim()).join(" ")}
    </div> : null}
    {emphasis ? <div style={{position: "absolute", left: emphasis.x ?? 540, top: emphasis.y ?? 960,
      maxWidth: 470, fontFamily: emphasis.italic ? "Georgia, serif" : "Arial, sans-serif",
      fontStyle: emphasis.italic ? "italic" : "normal", fontWeight: emphasis.italic ? 400 : 900,
      fontSize: emphasis.size ?? 84, lineHeight: 0.95, color: emphasis.color ?? "white",
      opacity: interpolate(entry, [0, 1], [0, 1]),
      transform: `translateY(${interpolate(entry, [0, 1], [20, 0])}px)`,
      textShadow: "0 2px 6px #000"}}>{emphasis.text}</div> : null}
    {layers.length ? <div style={{position: "absolute", inset: 0, pointerEvents: "none", isolation: "isolate"}}>
      {layers.map((layer, i) => {
        const progress = Math.min(1, Math.max(0, (t - layer.t) / 0.12));
        const eased = 1 - Math.pow(1 - progress, 3);
        const out = Math.min(1, Math.max(0, (layer.t + layer.dur - t) / 0.08));
        const serif = layer.font === "serif";
        const condensed = layer.font === "condensed";
        const text = layer.wordTimes ? layer.text.split(/\s+/).slice(0, layer.wordTimes.filter(at => at <= t).length).join(" ") : layer.text;
        return <div key={`${layer.t}-${layer.text}-${i}`} style={{position: "absolute",
          left: layer.x, top: layer.y, width: layer.width ?? 470,
          fontFamily: serif ? "Georgia, 'Times New Roman', serif" : condensed ? "Impact, 'Arial Narrow', sans-serif" : "Arial, sans-serif",
          fontSize: layer.size, fontWeight: layer.weight ?? (serif || condensed ? 400 : 700),
          fontStyle: layer.italic ? "italic" : "normal", textAlign: layer.align ?? "left",
          whiteSpace: "pre-wrap", lineHeight: 0.94, letterSpacing: condensed ? -0.8 : -0.5,
          color: "#e7e9ed", backgroundImage: edit.palette === "silver" ? "linear-gradient(180deg,#ffffff 8%,#e5e8ed 52%,#c5cbd3 100%)" : undefined,
          WebkitBackgroundClip: edit.palette === "silver" ? "text" : undefined,
          WebkitTextFillColor: edit.palette === "silver" ? "transparent" : undefined,
          filter: "drop-shadow(0 2px 2px rgba(0,0,0,0.38))",
          opacity: eased * out, zIndex: layer.z ?? i,
          transformOrigin: "left center",
          transform: `translateY(${12 * (1 - eased)}px) rotate(${layer.rotate ?? 0}deg) scale(${0.98 + 0.02 * eased})`,
        }}>{text}</div>;
      })}
    </div> : null}
  </>;
};
