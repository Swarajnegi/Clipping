import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Caption } from "@remotion/captions";
import { createTikTokStyleCaptions } from "@remotion/captions";
import { loadFont } from "@remotion/google-fonts/Montserrat";
import type { ClipProps, Punch, Shot, TrackPoint } from "./types";
import {ReferenceCaptions, ReferenceCutaways} from "./ReferenceEdit";
import {EditorialCaptions} from "./EditorialCaptions";
import {maskPoints} from "./captionMotion";
import {frameSourceWidth, referencePictureBox} from "./pictureFrame";
import {transitionAt} from "./transitionMotion";

const { fontFamily } = loadFont("normal", { weights: ["700", "800", "900"], subsets: ["latin"] });

const W = 1080;
const H = 1920;
// Shorts UI covers roughly the top 10% and the bottom 15-20%; text stays between.
const HOOK_TOP = 0.115 * H;

type Box = { x: number; y: number; w: number; h: number; radius: number };

// Where the clip is drawn. frame = Alex's rounded card; everything else uses the full canvas.
const canvasBox = (p: ClipProps): Box =>
  p.referenceEdit
    ? referencePictureBox(p.referenceEdit)
    : p.style === "frame"
    ? { x: 48, y: 0.2 * H, w: W - 96, h: 0.62 * H, radius: 44 }
    : { x: 0, y: 0, w: W, h: H, radius: 0 };

const gradeFilter = (p: ClipProps) =>
  `brightness(${p.grade.brightness}) contrast(${p.grade.contrast}) saturate(${p.grade.saturate})`;

const shotAt = (shots: Shot[], t: number): Shot => {
  let cur: Shot = shots[0] ?? { t: 0, x: 0.5 };
  for (const sh of shots) if (sh.t <= t) cur = sh;
  return cur;
};

const shotEnd = (shots: Shot[], shot: Shot): number => {
  const next = shots.find((s) => s.t > shot.t);
  return next ? next.t : Infinity;
};

// Tracking is interpolated only inside the current shot so a cut stays a hard cut.
const trackedX = (track: TrackPoint[], shot: Shot, end: number, t: number): number => {
  const pts = track.filter((p) => p.t >= shot.t && p.t < end);
  if (pts.length === 0) return shot.x;
  if (pts.length === 1) return pts[0].x;
  return interpolate(t, pts.map((p) => p.t), pts.map((p) => p.x), {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
};

const punchScale = (punches: Punch[], t: number, fps: number, frame: number): number => {
  let s = 1;
  for (const p of punches) {
    if (t < p.t || t > p.t + p.dur + 0.4) continue;
    const inSpring = spring({ frame: frame - Math.round(p.t * fps), fps, config: { damping: 14, stiffness: 220 } });
    const out = interpolate(t, [p.t + p.dur, p.t + p.dur + 0.4], [1, 0], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    s = Math.max(s, 1 + (p.scale - 1) * inSpring * out);
  }
  return s;
};

// Fraction of source width shown for the current shot, after the style override.
const shownWidth = (p: ClipProps, shot: Shot, box: Box): number => {
  if (p.referenceEdit?.frame) {
    return frameSourceWidth(p.srcWidth, p.srcHeight, box, shot.w);
  }
  if (p.referenceEdit) return shot.w ?? 1;
  // letterbox: 16:9 scaled to ~198% of canvas width (Joe's setting) -> about half the width shows.
  if (p.style === "letterbox") return 0.505;
  const w = shot.w ?? p.widthFrac;
  // Never narrower than what fills the box height; the frame card is shorter than the canvas.
  const fillW = (p.srcHeight * box.w) / box.h / p.srcWidth;
  return Math.max(w, Math.min(fillW, 1));
};

export const Framed: React.FC<{ p: ClipProps; t: number; frame: number; muted?: boolean; pictureFilter?: string }> =
({ p, t, frame, muted, pictureFilter }) => {
  const { fps } = useVideoConfig();
  const box = canvasBox(p);
  const shot = shotAt(p.shots, t);
  const w = shownWidth(p, shot, box);
  const scale = box.w / (w * p.srcWidth);
  const vidW = p.srcWidth * scale;
  const renderH = p.srcHeight * scale;
  const vidH = Math.min(renderH, box.h);
  const cx = shot.track ? trackedX(p.track, shot, shotEnd(p.shots, shot), t) : shot.x;
  const left = Math.min(0, Math.max(box.w - vidW, box.w / 2 - cx * vidW));
  const anchor = p.style === "letterbox" ? 0.5 : p.yAnchor;
  const top = box.y + (box.h - vidH) * anchor;
  const z = punchScale(p.punchIns, t, fps, frame);

  return (
    <div
      style={{
        position: "absolute",
        left: box.x,
        top,
        width: box.w,
        height: vidH,
        overflow: "hidden",
        borderRadius: box.radius,
        transform: p.referenceEdit?.frame ? undefined : `scale(${z})`,
        transformOrigin: "50% 50%",
        boxShadow: vidH < H && p.style === "bold" ? "0 0 60px rgba(0,0,0,0.65)" : undefined,
      }}
    >
      <OffthreadVideo
        src={staticFile(p.src)}
        muted={muted}
        style={{
          position: "absolute",
          left,
          top: (vidH - renderH) / 2,
          width: vidW,
          height: renderH,
          filter: pictureFilter ? `${gradeFilter(p)} ${pictureFilter}` : gradeFilter(p),
          transform: p.referenceEdit?.frame ? `scale(${z})` : undefined,
          transformOrigin: `${box.w / 2 - left}px ${renderH / 2}px`,
        }}
      />
    </div>
  );
};

const needsBlur = (p: ClipProps, t: number): boolean => {
  if (p.referenceEdit) return false;
  if (p.style !== "bold" && p.style !== "clean") return false;
  const box = canvasBox(p);
  const w = shownWidth(p, shotAt(p.shots, t), box);
  return (p.srcHeight * W) / (w * p.srcWidth) < H - 1;
};

// Decoding the same file twice per frame (sharp foreground + blurred background) under
// parallel rendering made Remotion's compositor miss frames at random times, and a 38px CSS
// blur on every 1080x1920 frame is the slowest thing in the render. build.py pre-renders a
// small blurred background with ffmpeg so the browser only scales it.
const Background: React.FC<{ p: ClipProps }> = ({ p }) => (
  <AbsoluteFill style={{ backgroundColor: "#000" }}>
    <OffthreadVideo
      src={staticFile(p.bgSrc ?? p.src)}
      muted
      style={{
        width: "100%",
        height: "100%",
        objectFit: "cover",
        transform: p.bgSrc ? undefined : "scale(1.25)",
        filter: p.bgSrc ? undefined : "blur(38px) brightness(0.55) saturate(1.2)",
      }}
    />
  </AbsoluteFill>
);

const Hook: React.FC<{ p: ClipProps; t: number; frame: number }> = ({ p, t, frame }) => {
  const { fps } = useVideoConfig();
  if (!p.hook) return null;
  const pop = spring({ frame, fps, config: { damping: 12, stiffness: 180 } });
  const fade = p.hookPersist
    ? 1
    : interpolate(t, [p.hookDurationSec - 0.25, p.hookDurationSec], [1, 0], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
  if (fade <= 0) return null;
  const clean = p.style === "clean" || p.style === "letterbox";
  return (
    <div
      style={{
        position: "absolute",
        top: p.style === "frame" ? 0.105 * H : HOOK_TOP,
        left: 60,
        right: 60,
        display: "flex",
        justifyContent: "center",
        opacity: fade,
        transform: `scale(${0.7 + 0.3 * pop})`,
      }}
    >
      <div
        style={{
          fontFamily,
          fontWeight: clean ? 800 : 900,
          fontSize: clean ? (p.hook.length > 28 ? 52 : 60) : p.hook.length > 28 ? 64 : 78,
          lineHeight: 1.08,
          textAlign: "center",
          color: "#fff",
          textTransform: clean ? "none" : "uppercase",
          padding: clean ? "0" : "18px 28px",
          background: clean || p.style === "frame" ? "transparent" : "rgba(0,0,0,0.55)",
          borderRadius: 22,
          WebkitTextStroke: clean ? "0" : "3px #000",
          paintOrder: "stroke fill",
          textShadow: "0 6px 18px rgba(0,0,0,0.6)",
        }}
      >
        {p.hook}
      </div>
    </div>
  );
};

const Captions: React.FC<{ p: ClipProps; captions: Caption[]; t: number }> = ({ p, captions, t }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const clean = p.style === "clean" || p.style === "letterbox";
  const pages = useMemo(
    () =>
      createTikTokStyleCaptions({
        captions,
        combineTokensWithinMilliseconds: clean ? 1400 : 900,
        breakOnSilenceAfterMilliseconds: 500,
      }).pages,
    [captions, clean],
  );
  const ms = t * 1000;
  const page = pages.find((pg) => ms >= pg.startMs && ms < pg.startMs + pg.durationMs);
  if (!page) return null;
  const pageFrame = frame - Math.round((page.startMs / 1000) * fps);
  const enter = spring({ frame: pageFrame, fps, config: { damping: 15, stiffness: 260 } });
  // clean: one small line below the chin; frame: under the card; bold: lower-middle.
  const top = clean ? 0.7 * H : p.style === "frame" ? 0.845 * H : 0.66 * H - 90;

  return (
    <div
      style={{
        position: "absolute",
        left: 50,
        right: 50,
        top,
        display: "flex",
        flexWrap: clean ? "nowrap" : "wrap",
        justifyContent: "center",
        gap: clean ? "0 14px" : "0 34px",
        transform: `scale(${0.85 + 0.15 * enter})`,
      }}
    >
      {page.tokens.map((tok, i) => {
        const active = ms >= tok.fromMs && ms < tok.toMs;
        return (
          <span
            key={i}
            style={{
              fontFamily,
              fontWeight: clean ? 700 : 900,
              fontSize: clean ? 46 : p.style === "frame" ? 70 : 84,
              lineHeight: 1.1,
              textTransform: clean ? "none" : "uppercase",
              color: active && !clean ? p.accent : "#fff",
              WebkitTextStroke: clean ? "0" : "10px #000",
              paintOrder: "stroke fill",
              textShadow: clean ? "0 3px 8px rgba(0,0,0,0.9)" : "0 8px 20px rgba(0,0,0,0.55)",
              transform: active && !clean ? "scale(1.06)" : "scale(1)",
              display: "inline-block",
              whiteSpace: "nowrap",
            }}
          >
            {tok.text.trim()}
          </span>
        );
      })}
    </div>
  );
};

const Mark: React.FC<{ p: ClipProps }> = ({ p }) => {
  if (!p.watermark) return null;
  const m = p.watermark;
  const pad = 48;
  const pos: React.CSSProperties = {
    position: "absolute",
    width: m.widthPx,
    opacity: m.opacity,
    ...(m.corner.includes("t") ? { top: 0.105 * H } : { bottom: 0.2 * H }),
    ...(m.corner.includes("l") ? { left: pad } : { right: pad }),
  };
  return <Img src={staticFile(m.src)} style={pos} />;
};

// The transformative intro: slow push-in on the clip's best frame while the voiceover sets
// up the stakes, so the clip that follows is framed by original narration.
const IntroCard: React.FC<{ p: ClipProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (!p.intro) return null;
  const t = frame / fps;
  const zoom = interpolate(t, [0, p.intro.durationSec], [1.0, 1.1]);
  const box = canvasBox(p);
  return (
    <AbsoluteFill>
      <Img
        src={staticFile(p.intro.still)}
        style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover",
                 filter: "blur(38px) brightness(0.45)", transform: "scale(1.2)" }}
      />
      <div
        style={{ position: "absolute", left: box.x, top: box.y, width: box.w, height: box.h,
                 overflow: "hidden", borderRadius: box.radius }}
      >
        <Img
          src={staticFile(p.intro.still)}
          style={{ width: "100%", height: "100%", objectFit: "cover",
                   transform: `scale(${zoom})`, filter: `${gradeFilter(p)} brightness(0.85)` }}
        />
      </div>
      <Audio src={staticFile(p.intro.audio)} />
      <Captions p={p} captions={p.intro.captions} t={t} />
    </AbsoluteFill>
  );
};

const ClipBody: React.FC<{ p: ClipProps }> = ({ p }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const editorial = p.referenceEdit?.profile === "editorial";
  const transition = p.transitionCues ? transitionAt(p.transitionCues, frame, fps) : undefined;
  const picture = canvasBox(p);
  const mask = p.referenceEdit?.foregroundMasks?.find(m => t >= m.t && t < m.t + m.dur);
  const behind = p.referenceEdit?.layers?.some(l => l.depth === "behind" && t >= l.t && t < l.t + l.dur);
  const introFrames = p.intro ? Math.round(p.intro.durationSec * fps) : 0;
  const clipEnd = (durationInFrames - introFrames) / fps;
  const fadeStart = clipEnd - p.loopFadeSec;
  const loopDim = p.loopFadeSec > 0 ? interpolate(t, [fadeStart, clipEnd], [0, 0.35], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }) : 0;
  return (
    <AbsoluteFill>
      {needsBlur(p, t) ? <Background p={p} /> : null}
      <Framed p={p} t={t} frame={frame} pictureFilter={transition?.filter} />
      {p.referenceEdit ? <ReferenceCutaways p={p} pictureFilter={transition?.filter} /> : null}
      {transition?.overlay ? <div style={{position: "absolute", left: picture.x, top: picture.y,
        width: picture.w, height: picture.h, borderRadius: picture.radius,
        background: transition.overlay, pointerEvents: "none"}} /> : null}
      <AbsoluteFill style={{ backgroundColor: `rgba(0,0,0,${loopDim})` }} />
      {editorial ? <>
        <EditorialCaptions p={p} depth="behind" />
        {mask && behind ? <AbsoluteFill style={{zIndex: 10000, clipPath: `polygon(${maskPoints(mask, t).map(([x,y]) => `${x}px ${y}px`).join(",")})`}}>
          <Framed p={p} t={t} frame={frame} muted pictureFilter={transition?.filter} />
        </AbsoluteFill> : null}
        <EditorialCaptions p={p} depth="front" />
      </> : p.referenceEdit ? <ReferenceCaptions p={p} /> : p.captions.length > 0 ? <Captions p={p} captions={p.captions} t={t} /> : null}
    </AbsoluteFill>
  );
};

const MusicBed: React.FC<{ p: ClipProps }> = ({ p }) => {
  const { fps, durationInFrames } = useVideoConfig();
  if (!p.music) return null;
  const base = Math.pow(10, p.music.db / 20);
  const fadeFrames = Math.round(p.music.fadeOutSec * fps);
  return (
    <Audio
      src={staticFile(p.music.src)}
      loop
      volume={(f) =>
        base * interpolate(f, [durationInFrames - fadeFrames, durationInFrames], [1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      }
    />
  );
};

export const ViralShort: React.FC<ClipProps> = (p) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const introFrames = p.intro ? Math.round(p.intro.durationSec * fps) : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {p.intro ? (
        <Sequence durationInFrames={introFrames} name="Intro">
          <IntroCard p={p} />
        </Sequence>
      ) : null}
      <Sequence from={introFrames} name="Clip">
        <ClipBody p={p} />
      </Sequence>
      <Mark p={p} />
      <Hook p={p} t={frame / fps} frame={frame} />
      <MusicBed p={p} />
    </AbsoluteFill>
  );
};
