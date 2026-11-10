"""Reuse the proven renderer/QA in an isolated caption revision directory."""
from pathlib import Path
P=Path(__file__).resolve().parent
R=P/'caption-v2'
for name in ['audio_master.py','render_prepared.py','qa_clip.py','render_batch.py']:
    text=(P/name).read_text(encoding='utf-8')
    text=text.replace('ROOT=PROJECT.parents[3]','ROOT=PROJECT.parents[4]')
    if name in ['render_prepared.py','qa_clip.py']:
        text=text.replace("ROOT/'work'/work_id/'props/clip_01.json'", "PROJECT/'authoring'/args.slug/'props.json'")
        text=text.replace("'fonts/InterVariable.woff2','fonts/Inter-LICENSE.txt'", "'fonts/InterVariable.woff2','fonts/InterVariable-Italic.woff2','fonts/CormorantGaramond-Italic.ttf','fonts/Cormorant-OFL.txt','fonts/Inter-LICENSE.txt'")
        text=text.replace("'-music-free-DRAFT.mp4'", "'-caption-v2-music-free-DRAFT.mp4'")
    if name=='render_prepared.py':
        text=text.replace("mux_dialogue(pending,ROOT/'public'/props['src'],copied,", "mux_dialogue(pending,PROJECT.parent/'drafts'/(args.slug+'-music-free-DRAFT.mp4'),copied,")
    if name=='render_batch.py':
        text=text.replace("'03-self-reflection','05-three-relationships'", "'03-self-reflection','04-family','05-three-relationships'")
        text=text.replace("    state['current']=slug;", "    if (PROJECT/'qa'/slug/'technical-review.json').exists():\n        state['completed'].append(slug);continue\n    state['current']=slug;")
    (R/name).write_text(text,encoding='utf-8')

text=(P/'check_caption_geometry.cjs').read_text(encoding='utf-8')
text=text.replace("'../../../..'", "'../../../../..'")
text=text.replace("path.join(root,'work',d.work_id,'clips.json')", "path.join(project,'authoring',d.slug,'clips.json')")
text=text.replace("const font=fs.readFileSync(path.join(root,'public/fonts/InterVariable.woff2')).toString('base64');", """const fonts=[
      {family:'Inter Caption',file:'InterVariable.woff2',style:'normal',weight:'100 900'},
      {family:'Inter Caption',file:'InterVariable-Italic.woff2',style:'italic',weight:'100 900'},
      {family:'Cormorant Caption',file:'CormorantGaramond-Italic.ttf',style:'italic',weight:'300 700'},
    ].map(f=>({...f,data:fs.readFileSync(path.join(root,'public/fonts',f.file)).toString('base64')}));""")
text=text.replace('async (items,base64)', 'async (items,fonts)')
text=text.replace("const face=new FontFace('Inter Caption',`url(data:font/woff2;base64,${base64})`,{weight:'100 900'});\n      document.fonts.add(await face.load());", """for(const font of fonts){
        const face=new FontFace(font.family,`url(data:${font.file.endsWith('.ttf')?'font/ttf':'font/woff2'};base64,${font.data})`,{weight:font.weight,style:font.style});
        document.fonts.add(await face.load());
      }""")
text=text.replace("fontFamily:'Inter Caption',fontWeight:", "fontFamily:layer.font==='cormorant'?'Cormorant Caption':'Inter Caption',fontStyle:layer.italic?'italic':'normal',fontSynthesis:'none',fontWeight:")
text=text.replace('},layers,font);','},layers,fonts);')
(R/'check_caption_geometry.cjs').write_text(text,encoding='utf-8')
