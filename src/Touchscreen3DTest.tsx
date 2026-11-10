import React from "react";
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from "remotion";

export const Touchscreen3DTest: React.FC<{frameFolder?: string}> = ({frameFolder = "touchscreen-3d-test"}) => {
  const frame = useCurrentFrame();
  const title = frame < 75 ? "Beyond the glass." : frame < 165 ? "A hidden sensing grid." : "Your touch changes the field.";
  const local = frame < 75 ? frame : frame < 165 ? frame - 75 : frame - 165;
  const opacity = interpolate(local, [0, 10], [0, 1], {extrapolateRight: "clamp"});
  return <AbsoluteFill style={{background: "#090d14", color: "#f3f2ef", fontFamily: "Arial, sans-serif"}}>
    <Img src={staticFile(`${frameFolder}/${String(frame + 1).padStart(4, "0")}.png`)} style={{width: "100%", height: "100%"}}/>
    <div style={{position: "absolute", top: 145, left: 90, right: 90, textAlign: "center", fontSize: 47, lineHeight: 1.25, fontWeight: 700,
      opacity, textShadow: "0 2px 15px #000"}}>{title}</div>
    <div style={{position: "absolute", bottom: 115, left: 80, right: 80, textAlign: "center", fontSize: 25, color: "#e0e5ec", letterSpacing: .7,
      background: "rgba(5, 10, 17, 0.78)", padding: "10px 14px", borderRadius: 8,
      textShadow: "0 2px 12px #000"}}>Magnified layer separation · Illustrative fields</div>
  </AbsoluteFill>;
};
