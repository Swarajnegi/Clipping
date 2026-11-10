import React from "react";
import {AbsoluteFill} from "remotion";
import {EditorialCaptions} from "./EditorialCaptions";
import type {ClipProps, CaptionLayer} from "./types";

// Synthetic colour fields make incorrect blend isolation visible and measurable.
export const CaptionSurfaceTest: React.FC = () => {
  const layers: CaptionLayer[] = [
    {t:0,dur:2,text:"LEAVES",x:70,y:320,width:900,size:190,surface:"solid"},
    {t:0,dur:2,text:"LEAVES",x:70,y:820,width:900,size:190,surface:"difference"},
    {t:0,dur:2,text:"LEAVES",x:70,y:1320,width:900,size:190,surface:"difference",fillOpacity:0.65},
  ];
  const p: Pick<ClipProps, "referenceEdit"> = {referenceEdit:{profile:"editorial",layers}};
  return <AbsoluteFill style={{backgroundColor:"#101418"}}>
    {[200,700,1200].map((y,i) => <React.Fragment key={y}>
      <div style={{position:"absolute",top:y-70,left:70,color:"white",fontFamily:"Arial",fontSize:34}}>
        {["SOLID + SHADOW","DIFFERENCE — FOOTAGE COLOUR RESPONSE","DIFFERENCE — 65% MIX"][i]}
      </div>
      <div style={{position:"absolute",left:0,top:y,width:540,height:400,backgroundColor:"#246c38"}} />
      <svg width={540} height={400} style={{position:"absolute",left:0,top:y}}>
        <path d="M10 350 C-30 110 240 25 500 20 C480 220 280 395 10 350Z" fill="#447e35" />
        <path d="M10 350 Q230 180 500 20 M180 225 L140 90 M270 162 L260 50 M180 225 L320 270 M360 100 L420 150" stroke="#7aaa59" strokeWidth={5} fill="none" />
      </svg>
      <div style={{position:"absolute",left:540,top:y,width:540,height:400,backgroundColor:"#eeeeee"}} />
    </React.Fragment>)}
    <EditorialCaptions p={p} depth="front" />
  </AbsoluteFill>;
};
