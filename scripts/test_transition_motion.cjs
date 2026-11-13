const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const file = path.resolve(__dirname, '../src/transitionMotion.ts');
const mod = new Module(file);
mod._compile(ts.transpileModule(fs.readFileSync(file, 'utf8'), {
  compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
}).outputText, file);
const {transitionAt} = mod.exports;
const presets = [
  ['inversion-flicker', 0.13, 'invert'],
  ['bw-inverted-shock', 0.17, 'grayscale'],
  ['blu-ray-scanning', 0.24, 'blur'],
  ['retro-exposure', 0.17, 'brightness'],
];
for (const fps of [25, 30000 / 1001]) {
  for (const [preset, duration, filter] of presets) {
    const frame = Math.round(1.75 * fps);
    const cues = [{frame, preset}];
    assert.equal(transitionAt(cues, frame - 1, fps), undefined);
    assert.ok(transitionAt(cues, frame, fps).filter.startsWith(filter));
    assert.notDeepEqual(transitionAt(cues, frame, fps), transitionAt(cues, frame + 1, fps));
    assert.equal(transitionAt(cues, frame + Math.round(duration * fps), fps), undefined);
    assert.deepEqual(transitionAt(cues, frame, fps), transitionAt(cues, frame, fps));
  }
}
assert.equal(transitionAt([], 0, 25), undefined);
console.log('Transition frame bounds and deterministic motion passed at 25 and 29.97 FPS.');
