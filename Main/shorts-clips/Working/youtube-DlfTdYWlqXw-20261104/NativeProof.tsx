// Project-only experiment: same logical composition, native browser video decode.
// No change to the established ViralShort composition or its defaults.
import React from 'react';
import {AbsoluteFill,Composition,Html5Video,registerRoot,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import {EditorialCaptions} from '../../../../src/EditorialCaptions';
import type {ClipProps} from '../../../../src/types';

const NativePicture:React.FC<ClipProps>=(p)=>{
  const t=useCurrentFrame()/useVideoConfig().fps;
  const shot=[...p.shots].reverse().find(s=>s.t<=t)??p.shots[0];
  const width=1080/(shot.w??1);
  const height=width*p.srcHeight/p.srcWidth;
  const visibleHeight=Math.min(height,1920);
  const left=Math.min(0,Math.max(1080-width,540-shot.x*width));
  const top=(1920-visibleHeight)*p.yAnchor;
  return <AbsoluteFill style={{backgroundColor:'#000'}}>
    <div style={{position:'absolute',left:0,top,width:1080,height:visibleHeight,overflow:'hidden',
      boxShadow:visibleHeight<1920?'0 0 60px rgba(0,0,0,0.65)':undefined}}>
      <Html5Video src={staticFile(p.src)} muted acceptableTimeShiftInSeconds={0.0001}
        style={{position:'absolute',left,top:(visibleHeight-height)/2,width,height,
          filter:`brightness(${p.grade.brightness}) contrast(${p.grade.contrast}) saturate(${p.grade.saturate})`}}/>
    </div>
    <EditorialCaptions p={p} depth='front'/>
  </AbsoluteFill>;
};
const Root=()=> <Composition id='Native4K' component={NativePicture as React.FC<any>}
  width={1080} height={1920} fps={25} durationInFrames={800}
  calculateMetadata={({props})=>({fps:props.fps,durationInFrames:Math.round(props.durationSec*props.fps)})}/>;
registerRoot(Root);
