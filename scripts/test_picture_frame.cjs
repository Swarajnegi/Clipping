const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');
const file = path.resolve(__dirname, '../src/pictureFrame.ts');
const mod = new Module(file);
mod._compile(ts.transpileModule(fs.readFileSync(file, 'utf8'), {
  compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022},
}).outputText, file);
const {referencePictureBox, frameSourceWidth, SQUARE_PICTURE_FRAME} = mod.exports;
const square = referencePictureBox({frame: SQUARE_PICTURE_FRAME});
assert.deepEqual(square, {x: 50, y: 470, w: 980, h: 980, radius: 48});
assert.equal(square.x * 2 + square.w, 1080);
assert.equal(square.y * 2 + square.h, 1920);
assert.equal(frameSourceWidth(3840, 2160, square), 0.5625);
assert.equal(frameSourceWidth(3840, 2160, square, 1), 0.5625);
assert.equal(frameSourceWidth(3840, 2160, square, 0.4), 0.4);
assert.equal(frameSourceWidth(2160, 3840, square), 1);
assert.deepEqual(referencePictureBox({bandHeight: 1920}), {x: 0, y: 0, w: 1080, h: 1920, radius: 0});
assert.deepEqual(referencePictureBox({}), {x: 0, y: 656, w: 1080, h: 608, radius: 0});
console.log('Picture frame geometry and native-source cover checks passed.');
