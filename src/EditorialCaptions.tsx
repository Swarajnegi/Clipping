import React, {useEffect, useState} from "react";
import {cancelRender, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import type {CaptionLayer, ClipProps} from "./types";
import {captionMotion} from "./captionMotion";
import {resolveCaptionSurface} from "./captionSurface";
import {captionFont} from "./captionFonts";

const fontReady = new Map<string, Promise<void>>();
export const useCaptionFonts = (layers: Pick<CaptionLayer, "font" | "italic">[]) => {
  const faces = [...new Map(layers.map(layer => {
    const face = captionFont(layer); return [face.key, face] as const;
  })).values()];
  const key = faces.map(face => face.key).sort().join(",");
  const [handle] = useState(() => delayRender("Load bundled caption fonts"));
  useEffect(() => {
    const pending = faces.map(face => {
      if (!fontReady.has(face.key)) fontReady.set(face.key, (async () => {
        const font = new FontFace(face.family, `url("${staticFile(`fonts/${face.file}`)}")`,
          {weight: face.weight, style: face.style});
        (document.fonts as FontFaceSet & {add(font: FontFace): void}).add(await font.load());
      })());
      return fontReady.get(face.key)!;
    });
    Promise.all(pending).then(() => continueRender(handle)).catch(cancelRender);
  }, [handle, key]);
};

const TextLayer: React.FC<{layer: CaptionLayer; t: number; depth: "front" | "behind"}> = ({layer, t, depth}) => {
  const motion = captionMotion(t, layer.t, layer.t + layer.dur, layer.motion);
  const perspective = layer.perspective;
  const surface = resolveCaptionSurface(layer);
  const shadow = surface.shadow === "none" ? "" : surface.shadow === "soft"
    ? " drop-shadow(0 2px 3px rgba(0,0,0,.45))"
    : " drop-shadow(0 2px 1px rgba(0,0,0,.9)) drop-shadow(0 5px 7px rgba(0,0,0,.75))";
  const ink: React.CSSProperties = {color: surface.color ?? "#f4f5f7",
    backgroundImage: surface.gradient,
    WebkitBackgroundClip: surface.gradient ? "text" : undefined,
    WebkitTextFillColor: surface.gradient ? "transparent" : undefined};
  return <div style={{position: "absolute", left: layer.x, top: layer.y,
    width: layer.width ?? 900, textAlign: layer.align ?? "center",
    fontFamily: `'${captionFont(layer).family}', ${layer.font === "cormorant" ? "serif" : "sans-serif"}`,
    fontSynthesis: "none", fontWeight: layer.weight ?? 700,
    fontSize: layer.size, fontStyle: layer.italic ? "italic" : "normal",
    lineHeight: layer.lineHeight ?? 0.94, letterSpacing: `${layer.tracking ?? -0.05}em`,
    whiteSpace: "pre-wrap", zIndex: (depth === "behind" ? 100 : 20000) + (layer.z ?? 0), mixBlendMode: surface.blend,
    opacity: surface.fillOpacity * (layer.wordTimes ? 1 : motion.opacity),
    filter: `blur(${layer.wordTimes ? 0 : motion.blur}px)${shadow}${layer.glow ? ` drop-shadow(0 0 ${layer.glow}px rgba(235,240,255,.5))` : ""}`,
    transformOrigin: "center center",
    transform: `${perspective ? `perspective(${perspective.distance}px) rotateX(${perspective.rotateX}deg) rotateY(${perspective.rotateY}deg)` : ""} rotate(${layer.rotate ?? 0}deg) ${layer.wordTimes ? "" : `translateY(${motion.rise}px) scale(${motion.scale})`}`,
    ...(!layer.wordTimes ? ink : {})}}>
    {layer.wordTimes ? layer.text.split(/\s+/).map((word, i) => {
      const wordMotion = captionMotion(t, layer.wordTimes![i], layer.t + layer.dur, layer.motion);
      return <React.Fragment key={i}>{i > 0 ? " " : ""}<span style={{display: "inline-block", ...ink,
        opacity: wordMotion.opacity, filter: `blur(${wordMotion.blur}px)`,
        transform: `translateY(${wordMotion.rise}px) scale(${wordMotion.scale})`}}>{word}</span></React.Fragment>;
    }) : layer.text}
  </div>;
};

export const EditorialCaptions: React.FC<{p: Pick<ClipProps, "referenceEdit">; depth: "front" | "behind"}> = ({p, depth}) => {
  useCaptionFonts(p.referenceEdit?.layers ?? []);
  const t = useCurrentFrame() / useVideoConfig().fps;
  return <>
    {(p.referenceEdit?.layers ?? []).filter(layer => (layer.depth ?? "front") === depth &&
      t >= layer.t && t < layer.t + layer.dur).map((layer, i) => <TextLayer key={`${layer.t}-${i}`} layer={layer} t={t} depth={depth} />)}
  </>;
};
