// Measure the actual bundled Inter font and settled word boxes in Chromium.
const fs = require('fs');
const path = require('path');
const project = __dirname;
const root = path.resolve(project, '../../../..');
const {openBrowser} = require(path.join(root, 'node_modules/@remotion/renderer'));
if (!process.env.CLIPPING_GUARD_JOB) throw new Error('Run via the clipping guard');
(async () => {
  const decisions = JSON.parse(fs.readFileSync(path.join(project,'edit-decisions.json'),'utf8'));
  const layers = decisions.flatMap(d => {
    const spec=JSON.parse(fs.readFileSync(path.join(project,'authoring',d.slug,'clips.json'),'utf8'));
    return spec.clips[0].referenceEdit.layers.map((layer,index)=>({clip:d.slug,index,...layer}));
  });
  const browser=await openBrowser('chrome',{chromiumOptions:{gl:'angle'},logLevel:'error'});
  try {
    const page=await browser.newPage({context:null,logLevel:'error',indent:false,pageIndex:0,onBrowserLog:null,onLog:()=>{}});
    const fonts=[
      {family:'Inter Caption',file:'InterVariable.woff2',style:'normal',weight:'100 900'},
      {family:'Inter Caption',file:'InterVariable-Italic.woff2',style:'italic',weight:'100 900'},
      {family:'Cormorant Caption',file:'CormorantGaramond-Italic.ttf',style:'italic',weight:'300 700'},
    ].map(f=>({...f,data:fs.readFileSync(path.join(root,'public/fonts',f.file)).toString('base64')}));
    const result=await page.evaluate(async (items,fonts) => {
      for(const font of fonts){
        const face=new FontFace(font.family,`url(data:${font.file.endsWith('.ttf')?'font/ttf':'font/woff2'};base64,${font.data})`,{weight:font.weight,style:font.style});
        document.fonts.add(await face.load());
      }
      document.body.style.margin='0';
      const output=[];
      for(const layer of items){
        const el=document.createElement('div');
        Object.assign(el.style,{position:'absolute',left:`${layer.x}px`,top:`${layer.y}px`,width:`${layer.width}px`,
          textAlign:layer.align,fontFamily:layer.font==='cormorant'?'Cormorant Caption':'Inter Caption',fontStyle:layer.italic?'italic':'normal',fontSynthesis:'none',fontWeight:String(layer.weight),fontSize:`${layer.size}px`,
          lineHeight:String(layer.lineHeight??.94),letterSpacing:`${layer.tracking}em`,whiteSpace:'pre-wrap'});
        for(const [i,word] of layer.text.split(/\s+/).entries()){
          if(i)el.appendChild(document.createTextNode(' '));
          const span=document.createElement('span');span.style.display='inline-block';span.textContent=word;el.appendChild(span);
        }
        document.body.appendChild(el);
        const boxes=Array.from(el.querySelectorAll('span')).map(s=>{const r=s.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};});
        const wrapped=boxes.some(b=>Math.abs(b.y-boxes[0].y)>1);
        const safe=boxes.every(b=>b.x>=72 && b.x+b.w<=968 && b.y>=220 && b.y+b.h+12<=1480);
        output.push({clip:layer.clip,index:layer.index,text:layer.text,t:layer.t,dur:layer.dur,wrapped,safe,boxes});
        el.remove();
      }
      return output;
    },layers,fonts);
    const failures=result.filter(x=>x.wrapped||!x.safe);
    const collisions=[];
    for(let i=0;i<result.length;i++)for(let j=i+1;j<result.length;j++){
      const a=result[i],b=result[j];if(a.clip!==b.clip||Math.max(a.t,b.t)>=Math.min(a.t+a.dur,b.t+b.dur)-.001)continue;
      if(a.boxes.some(x=>b.boxes.some(y=>x.x<y.x+y.w && y.x<x.x+x.w && x.y<y.y+y.h && y.y<x.y+x.h)))collisions.push([a.clip,a.index,b.index]);
    }
    const receipt={checked_layers:result.length,failures,collisions,measurements:result,
      scope:'Actual Chromium settled glyph boxes, with 12px entry-motion allowance; not audio or face detection'};
    fs.writeFileSync(path.join(project,'qa/caption-geometry.json'),JSON.stringify(receipt,null,2));
    console.log(JSON.stringify({checked_layers:result.length,failures,collisions}));
    if(failures.length||collisions.length)process.exitCode=1;
  } finally {await browser.close({silent:true});}
})().catch(e=>{console.error(e);process.exitCode=1});

