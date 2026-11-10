const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const Module=require('node:module');
const ts=require('typescript');
const original=Module._extensions['.ts'];
Module._extensions['.ts']=(mod,file)=>mod._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,file);
try{
  const {sceneAt,sceneMotion,sourceFrameAt}=require(path.resolve(__dirname,'../src/motionEditModel.ts'));
  const scenes=[{kind:'speaker',start:0,end:1},{kind:'illustration',start:1,end:2},{kind:'speaker',start:2,end:3}];
  for(const fps of [25,30000/1001]){
    assert.equal(sceneAt(scenes,Math.round(fps),fps).kind,'illustration');
    assert.equal(sceneAt(scenes,Math.round(2*fps),fps).kind,'speaker');
    for(let frame=0;frame<Math.round(3*fps);frame++)assert.equal(sourceFrameAt(frame),frame);
    assert.deepEqual(sceneMotion(Math.round(1.5*fps),fps,scenes[1]),sceneMotion(Math.round(1.5*fps),fps,scenes[1]));
    assert.equal(sceneMotion(0,fps,scenes[1]).opacity,0);
    assert.equal(sceneMotion(Math.round(1.5*fps),fps,scenes[1]).scale,1);
  }
  console.log('Motion scene boundaries, deterministic easing and uninterrupted source clock passed');
}finally{Module._extensions['.ts']=original;}
