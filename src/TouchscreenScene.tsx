import React from "react";
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from "remotion";

const ink = "#172c35";
const teal = "#16847e";
const coral = "#e76443";
const paper = "#f3f0e8";
const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
const ease = Easing.bezier(.2, .8, .2, 1);

const Contact: React.FC<{x: number; y: number; time: number; r?: number}> = ({x, y, time, r = 38}) => <g>
  {[0, 1].map(i => <circle key={i} cx={x} cy={y} r={r + ((time * 22 + i * 24) % 48)} fill="none" stroke={coral}
    strokeWidth={2.5} opacity={.6 * (1 - ((time * 22 + i * 24) % 48) / 48)}/>)}
  <circle cx={x} cy={y} r={r} fill={coral} fillOpacity={.13} stroke={coral} strokeWidth={3}/>
  <circle cx={x} cy={y} r={7} fill={coral}/>
</g>;

const Phone: React.FC<{children?: React.ReactNode; screen?: string}> = ({children, screen = "#e7eee8"}) => <g>
  <rect x="202" y="55" width="506" height="922" rx="83" fill="#a9afab"/>
  <rect x="190" y="40" width="506" height="922" rx="83" fill={ink}/>
  <rect x="202" y="52" width="482" height="898" rx="73" fill="none" stroke="#657579" strokeWidth="2"/>
  <rect x="219" y="71" width="448" height="856" rx="58" fill={screen}/>
  <rect x="370" y="91" width="145" height="32" rx="16" fill={ink}/>
  <circle cx="484" cy="107" r="6" fill="#40585c"/>
  <path d="M190 220v84M190 326v84M696 260v111" stroke="#56666a" strokeWidth="8"/>
  <path d="M382 902h122" stroke="#5e7478" strokeWidth="6" strokeLinecap="round"/>
  {children}
</g>;

const Grid: React.FC<{time: number; active: boolean; touched?: boolean}> = ({time, active, touched = false}) => {
  const row = Math.floor(time * 4) % 11;
  return <g>
    {Array.from({length: 7}, (_, i) => <g key={i}>
      <path d={`M${267 + i * 58} 162V840`} stroke={teal} strokeWidth="4" opacity=".46"/>
      <circle cx={267 + i * 58} cy={840} r="5" fill={teal}/>
    </g>)}
    {Array.from({length: 11}, (_, j) => <g key={j}>
      <path d={`M249 ${190 + j * 59}H637`} stroke={active && row === j ? coral : teal} strokeWidth={active && row === j ? 8 : 4} opacity={active && row === j ? .95 : .46}/>
      <circle cx={249} cy={190 + j * 59} r="5" fill={teal}/>
      {Array.from({length: 7}, (_, i) => {
        const selected = touched && Math.abs(i - 4) <= 1 && Math.abs(j - 4) <= 1;
        return <rect key={i} x={260 + i * 58} y={183 + j * 59} width="14" height="14" rx="3" transform={`rotate(45 ${267 + i * 58} ${190 + j * 59})`}
          fill={selected ? coral : teal} opacity={selected ? .9 : .3}/>;
      })}
    </g>)}
  </g>;
};

type Point = [number, number];
const P = (x: number, y: number, z: number): Point => [450 + .85 * x - .56 * y, 650 + .35 * x + .55 * y - z];
const polygon = (points: Point[]) => points.map(p => p.join(",")).join(" ");
const Plane: React.FC<{z: number; fill: string; opacity?: number; children?: React.ReactNode}> = ({z, fill, opacity = 1, children}) => {
  const a = P(-155, -270, z), b = P(155, -270, z), c = P(155, 270, z), d = P(-155, 270, z);
  return <g opacity={opacity}>
    <polygon points={polygon([d, c, P(155, 270, z - 12), P(-155, 270, z - 12)])} fill="#5f777a"/>
    <polygon points={polygon([b, c, P(155, 270, z - 12), P(155, -270, z - 12)])} fill="#93aaa8"/>
    <polygon points={polygon([a, b, c, d])} fill={fill} stroke="#547779" strokeWidth="2"/>
    {children}
  </g>;
};

const Exploded: React.FC<{time: number}> = ({time}) => {
  const amount = interpolate(time, [0, 1.3], [0, 1], {...clamp, easing: ease});
  return <g>
    <ellipse cx="450" cy="865" rx="260" ry="50" fill={ink} opacity=".07"/>
    <Plane z={0} fill={ink}>
      {Array.from({length: 8}, (_, j) => Array.from({length: 5}, (_, i) => {
        const x = -125 + i * 53, y = -230 + j * 61;
        return <polygon key={`${i}-${j}`} points={polygon([P(x, y, 1), P(x + 40, y, 1), P(x + 40, y + 46, 1), P(x, y + 46, 1)])}
          fill={["#6aaba6", "#c2d6c7", "#d79971"][(i + j) % 3]} opacity=".8"/>;
      }))}
    </Plane>
    <Plane z={100 * amount + 20} fill="#c5e5dc" opacity={.92}>
      {Array.from({length: 7}, (_, i) => <path key={`x${i}`} d={`M${P(-130 + i * 43, -245, 100 * amount + 21).join(" ")}L${P(-130 + i * 43, 245, 100 * amount + 21).join(" ")}`} stroke={teal} strokeWidth="3"/>)}
      {Array.from({length: 12}, (_, i) => <path key={`y${i}`} d={`M${P(-135, -240 + i * 44, 100 * amount + 22).join(" ")}L${P(135, -240 + i * 44, 100 * amount + 22).join(" ")}`} stroke={teal} strokeWidth="3"/>)}
    </Plane>
    <Plane z={230 * amount + 40} fill="#e3f3ef" opacity={.67}/>
    {[[-155, -270], [155, -270], [155, 270], [-155, 270]].map(([x, y], i) => <path key={i}
      d={`M${P(x, y, 0).join(" ")}L${P(x, y, 230 * amount + 40).join(" ")}`} stroke={ink} strokeWidth="1.5" strokeDasharray="5 8" opacity=".3"/>)}
  </g>;
};

const TouchDiagram: React.FC<{phase: number; time: number}> = ({phase, time}) => {
  const touch = {x: 499, y: 426};
  if (phase === 1) return <svg viewBox="0 0 900 1020" style={{width: "100%", height: "100%"}}><Exploded time={time}/>
    {[['GLASS', '#8fb4ae'], ['SENSORS', teal], ['DISPLAY', ink]].map(([label, color], i) => <g key={label} transform={`translate(${135 + i * 220},970)`}>
      <circle r="7" fill={color}/><text x="18" y="9" fontSize="25" fill={ink} fontWeight="700">{label}</text></g>)}
  </svg>;
  return <svg viewBox="0 0 900 1020" style={{width: "100%", height: "100%"}}>
    <ellipse cx="450" cy="980" rx="240" ry="24" fill={ink} opacity=".08"/>
    <Phone screen={phase === 0 || phase === 6 ? "#cee2d9" : "#e8efea"}>
      {(phase === 0 || phase === 6) ? <g>
        <text x="260" y="230" fontSize="29" fill={teal} fontWeight="700">THE SCIENCE OF A TAP</text>
        <rect x="260" y="277" width="366" height="285" rx="30" fill={paper}/>
        <path d="M286 506L369 368L442 474L497 403L600 533H286Z" fill={teal} opacity=".75"/>
        <circle cx="543" cy="328" r="25" fill={coral}/>
        {[0, 1, 2].map(i => <rect key={i} x={260 + i * 126} y="593" width="112" height="113" rx="24" fill={i === 1 ? teal : "#b0cdc1"}/>)}
        <path d="M280 754H580M280 793H510" stroke="#91afa4" strokeWidth="12" strokeLinecap="round"/>
        <Contact x={444} y={649} time={time}/>
        {phase === 6 && <path d="M419 649l18 18 37-42" stroke={paper} strokeWidth="8" fill="none" strokeLinecap="round"/>}
      </g> : <>
        <Grid time={time} active={phase === 2} touched={phase === 3 || phase === 4}/>
        {(phase === 3 || phase === 4) && <g>
          <ellipse cx={touch.x} cy={touch.y} rx="82" ry="74" fill={coral} opacity=".08"/>
          {[0, 1, 2].map(i => <path key={i} d={`M${touch.x - 90} ${touch.y + i * 17}Q${touch.x} ${touch.y - 140 + i * 25} ${touch.x + 90} ${touch.y + i * 17}`}
            stroke={coral} strokeWidth="3" fill="none" opacity=".6"/>)}
          <Contact {...touch} time={time}/>
        </g>}
        {phase === 4 && <>
          <path d={`M${touch.x} 162V840M249 ${touch.y}H637`} stroke={coral} strokeWidth="2" strokeDasharray="7 8"/>
          <rect x="290" y="685" width="310" height="113" rx="22" fill={ink}/>
          <text x="445" y="734" fontSize="24" fill="#b7d6cb" textAnchor="middle">TOUCH POSITION</text>
          <text x="445" y="773" fontSize="32" fill={paper} textAnchor="middle" fontFamily="Consolas, monospace">{`x ${Math.round((touch.x - 219) / 448 * 100)}% · y ${Math.round((touch.y - 71) / 856 * 100)}%`}</text>
        </>}
        {phase === 5 && (() => {const spread = 45 + 45 * (.5 - .5 * Math.cos(time * 1.6)); return <>
          <rect x={323 - spread * .3} y={315 - spread * .4} width={245 + spread * .6} height={270 + spread * .8} rx="22" fill="#d5dfd2" stroke={ink} strokeWidth="2"/>
          <path d="M345 520L415 378L477 465L524 421L585 550H345Z" fill={teal}/>
          <circle cx="540" cy="360" r="21" fill={coral}/>
          <Contact x={444 - spread} y={450 + spread} time={time}/><Contact x={444 + spread} y={450 - spread} time={time + 1}/>
        </>;})()}
      </>}
    </Phone>
    {phase === 2 && <g transform="translate(67,330)">
      <rect width="102" height="310" rx="18" fill={ink}/>
      {Array.from({length: 9}, (_, i) => <path key={i} d={`M102 ${25 + i * 31}H123`} stroke={teal} strokeWidth="5"/>)}
      <text x="51" y="155" fill={paper} fontSize="23" textAnchor="middle" transform="rotate(-90 51 155)">CONTROLLER</text>
    </g>}
  </svg>;
};

export const TouchscreenScene: React.FC<{heading: string; phase: number; duration: number}> = ({heading, phase, duration}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const time = frame / fps;
  const appear = interpolate(frame, [0, 14], [0, 1], {...clamp, easing: ease});
  const labels = ["01 / THE QUESTION", "02 / UNDER THE GLASS", "03 / THE SCAN", "04 / THE ELECTRIC FIELD", "05 / THE TOUCH CONTROLLER", "06 / MULTI-TOUCH", "07 / NOW YOU KNOW"];
  const notes = ["It works through a layer of glass.", "Simplified layers · not to scale", "One grid. Many sensing points.", "Capacitance = electrical charge storage", "The software receives your position.", "Track positions → recognise a pinch", "An electrical change. A software response."];
  return <AbsoluteFill style={{background: paper, color: ink, fontFamily: "Arial, sans-serif"}}>
    <div style={{position: "absolute", top: 82, left: 82, right: 82, display: "flex", justifyContent: "space-between", fontSize: 24, fontWeight: 700, letterSpacing: 3, color: teal}}>
      <span>INSIDE YOUR PHONE</span><span>{String(phase + 1).padStart(2, "0")} / 07</span>
    </div>
    <div style={{position: "absolute", top: 166, left: 82, right: 82, fontWeight: 800, fontSize: 85, lineHeight: 1.08, letterSpacing: -3,
      opacity: appear, transform: `translateY(${(1 - appear) * 20}px)`}}>{heading}</div>
    <div style={{position: "absolute", top: 411, left: 76, width: 928, height: 1052,
      opacity: appear, transform: `translateY(${(1 - appear) * 25}px)`}}><TouchDiagram phase={phase} time={time}/></div>
    <div style={{position: "absolute", top: 1470, left: 82, right: 82, fontSize: phase === 1 ? 31 : 36, color: "#556c6e", lineHeight: 1.3}}>{notes[phase]}</div>
    <div style={{position: "absolute", left: 82, right: 82, top: 1557, height: 2, background: "#c9d3cb"}}/>
    <div style={{position: "absolute", left: 82, top: 1800, color: "#597476", letterSpacing: 2, fontSize: 23}}>{labels[phase]}</div>
    <div style={{position: "absolute", left: 82, right: 82, top: 1773, height: 4, background: "#d8dfd8"}}>
      <div style={{height: "100%", background: teal, width: `${100 * Math.min(time / duration, 1)}%`}}/>
    </div>
  </AbsoluteFill>;
};
