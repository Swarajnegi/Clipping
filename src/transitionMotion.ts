export type TransitionPreset = "inversion-flicker" | "bw-inverted-shock" | "blu-ray-scanning" | "retro-exposure";
export type TransitionCue = {frame: number; preset: TransitionPreset; soundId?: string};

const durationSec: Record<TransitionPreset, number> = {
  "inversion-flicker": 0.13,
  "bw-inverted-shock": 0.17,
  "blu-ray-scanning": 0.24,
  "retro-exposure": 0.17,
};

export function transitionAt(cues: readonly TransitionCue[], frame: number, fps: number) {
  const cue = cues.find(({frame: start, preset}) =>
    frame >= start && frame - start < Math.max(2, Math.round(durationSec[preset] * fps)));
  if (!cue) return undefined;

  const progress = (frame - cue.frame) / Math.max(1, Math.round(durationSec[cue.preset] * fps) - 1);
  const strength = (1 - progress) ** 2;
  switch (cue.preset) {
    case "inversion-flicker":
      return {filter: `invert(${0.64 * strength}) brightness(${1 + 0.18 * strength})`};
    case "bw-inverted-shock":
      return {filter: `grayscale(${strength}) invert(${0.76 * strength}) contrast(${1 + 0.28 * strength}) blur(${1.5 * strength}px)`};
    case "blu-ray-scanning":
      return {
        filter: `blur(${3 * strength}px)`,
        overlay: `linear-gradient(115deg, transparent ${125 * progress - 25}%, rgba(65,146,255,${0.47 * (1 - progress)}) ${125 * progress}%, transparent ${125 * progress + 22}%)`,
      };
    case "retro-exposure":
      return {
        filter: `brightness(${1 + 0.53 * strength}) sepia(${0.22 * strength})`,
        overlay: `radial-gradient(ellipse at 14% 20%, rgba(255,195,104,${0.28 * strength}), transparent 62%)`,
      };
  }
}
