const fs=require('fs');
const path=require('path');
const root=path.resolve(__dirname,'..');
const output=path.join(root,'frontend/web/vendor/ocr');
fs.mkdirSync(path.join(output,'core'),{recursive:true});
fs.mkdirSync(path.join(output,'lang'),{recursive:true});
for (const name of ['tesseract.min.js','worker.min.js']) fs.copyFileSync(path.join(root,'node_modules/tesseract.js/dist',name),path.join(output,name));
for (const name of ['tesseract-core-lstm.wasm.js','tesseract-core-lstm.wasm','tesseract-core-simd-lstm.wasm.js','tesseract-core-simd-lstm.wasm'])
  fs.copyFileSync(path.join(root,'node_modules/tesseract.js-core',name),path.join(output,'core',name));
for (const language of ['spa']) fs.copyFileSync(path.join(root,'node_modules/@tesseract.js-data',language,'4.0.0_best_int',language+'.traineddata.gz'),path.join(output,'lang',language+'.traineddata.gz'));
console.log('OCR assets prepared locally: Tesseract.js + LSTM spa.');

// Vercel serves generated assets from its CDN, not through Python function responses.
for (const directory of ['js','css','vendor']) fs.cpSync(path.join(root,'frontend/web',directory),path.join(root,'public/static',directory),{recursive:true});
