import type {CaptionLayer} from "./types";

export const resolveCaptionSurface = (layer: CaptionLayer) => {
  const difference = layer.surface === "difference";
  const color = layer.color ?? (difference ? "#ffffff" : undefined);
  return {
    color,
    gradient: layer.gradient ?? (color ? undefined : "linear-gradient(180deg,#fff 12%,#eceef2 52%,#b6bcc6 100%)"),
    blend: layer.blend ?? (difference ? "difference" : "normal"),
    shadow: layer.shadow ?? (difference ? "none" : "strong"),
    fillOpacity: layer.fillOpacity ?? 1,
  };
};
