import type {CaptionLayer} from "./types";

// Each face is bundled with its licence. Never synthesize an italic from upright.
export const captionFont = (layer: Pick<CaptionLayer, "font" | "italic">) => {
  if (layer.font === "cormorant") return {
    key: "cormorant-italic", family: "Cormorant Caption", file: "CormorantGaramond-Italic.ttf",
    style: "italic", weight: "300 700",
  };
  return {key: layer.italic ? "inter-italic" : "inter-normal", family: "Inter Caption",
    file: layer.italic ? "InterVariable-Italic.woff2" : "InterVariable.woff2",
    style: layer.italic ? "italic" : "normal", weight: "100 900"};
};
