const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const file = path.resolve(__dirname, '../src/captionMotion.ts');
const compiled = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
  compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
}).outputText;
const mod = new Module(file); mod._compile(compiled, file);
const {captionMotion, maskPoints} = mod.exports;
assert.equal(captionMotion(0.96, 1, 2).opacity, 0);
assert.ok(captionMotion(1, 1, 2).opacity > 0);
assert.deepEqual(captionMotion(1.4, 1, 2), {opacity:1, rise:0, scale:1, blur:0});
assert.equal(captionMotion(2, 1, 2).opacity, 0);
assert.ok(Math.abs(captionMotion(1.96, 1, 2).opacity - 0.5) < 1e-9);
assert.deepEqual(captionMotion(1.12, 1, 2), captionMotion(28 / 25, 1, 2));
const mask = {keyframes:[{t:1,points:[[10,20],[30,20],[20,50]]},
  {t:2,points:[[20,40],[40,40],[30,70]]}]};
assert.deepEqual(maskPoints(mask,1.5),[[15,30],[35,30],[25,60]]);
assert.deepEqual(maskPoints(mask,0),mask.keyframes[0].points);
assert.deepEqual(maskPoints(mask,3),mask.keyframes[1].points);
console.log('Caption motion and mask interpolation checks passed');
const fontFile=path.resolve(__dirname,'../src/captionFonts.ts');
const fontMod=new Module(fontFile);
fontMod._compile(ts.transpileModule(fs.readFileSync(fontFile,'utf8'),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
}).outputText,fontFile);
const {captionFont}=fontMod.exports;
assert.equal(captionFont({}).file,'InterVariable.woff2');
assert.equal(captionFont({font:'inter',italic:true}).file,'InterVariable-Italic.woff2');
assert.equal(captionFont({font:'cormorant',italic:true}).family,'Cormorant Caption');
assert.equal(captionFont({font:'cormorant',italic:true}).style,'italic');
for(const config of [{},{italic:true},{font:'cormorant',italic:true}]){
  assert.ok(fs.existsSync(path.resolve(__dirname,'../.agents/skills/viral-shorts/assets/fonts',captionFont(config).file)));
}
console.log('Bundled true-italic routing and asset checks passed');
