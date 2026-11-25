// Self-hosted OCR. No image is sent to a paid or external AI service.
let receiptWorkerPromise;
let receiptOcrProgress = () => {};

// Score readability, not financial correctness; every amount still requires review.
function receiptOcrScore(data) {
  const text = data.text || '';
  const words = text.match(/[a-záéíóúñ]+/gi) || [];
  const fragments = words.filter(word => word.length === 1).length;
  const prices = (text.match(/\d[\d.,]*[.,]\d{2}(?!\d)/g) || []).length;
  const lines = text.split(/\r?\n/);
  const metadata = /cuit|iva|subtotal|total|descuento|factura|consumidor|efectivo|pagos?|vuelto|tributos|cajera|cae|telefono|fecha|importe|regimen/i;
  const namedPrices = lines.filter(line => /[a-záéíóúñ]{3}/i.test(line) && /\d[.,]\d{2}/.test(line) && !metadata.test(line)).length;
  const quantities = lines.filter(line => /^\s*\d+(?:[.,]\d+)?\s*[x×]\s*\d/i.test(line)).length;
  // A confident footer without any product is less useful than a legible product row.
  return Number(data.confidence || 0) + namedPrices * 40 + quantities * 15 + Math.min(prices, 15) - 30 * fragments / Math.max(words.length, 1);
}

function receiptOcrHasProductEvidence(data) {
  const metadata = /cuit|iva|subtotal|total|descuento|factura|consumidor|efectivo|pagos?|vuelto|tributos|cae|fecha|importe/i;
  const productLines = (data.text || '').split(/\r?\n/).filter(line =>
    /[a-záéíóúñ]{3}/i.test(line) && /\d[\d.,]*[.,]\d{2}/.test(line) && !metadata.test(line)
  );
  return productLines.length >= 2;
}

function rotateCanvas(source, degrees) {
  const swapDimensions = degrees % 180 !== 0;
  const rotated = document.createElement('canvas');
  rotated.width = swapDimensions ? source.height : source.width;
  rotated.height = swapDimensions ? source.width : source.height;
  const context = rotated.getContext('2d', {willReadFrequently:true});
  context.fillStyle = '#fff';
  context.fillRect(0, 0, rotated.width, rotated.height);
  context.translate(rotated.width / 2, rotated.height / 2);
  context.rotate(degrees * Math.PI / 180);
  context.drawImage(source, -source.width / 2, -source.height / 2);
  return rotated;
}

function prepareReceiptPixels(context, width, height, adaptive) {
  const pixels = context.getImageData(0, 0, width, height);
  const gray = new Uint8Array(width * height);
  const histogram = new Uint32Array(256);
  for (let i = 0; i < gray.length; i++) {
    const x = i % width, r = pixels.data[i*4], g = pixels.data[i*4+1], b = pixels.data[i*4+2];
    // Colored table edges are background, not monochrome receipt print.
    const coloredEdge = (x < width*.1 || x > width*.9) && r-g > 12 && r-b > 18;
    gray[i] = coloredEdge ? 255 : Math.round(.299*r + .587*g + .114*b);
    histogram[gray[i]]++;
  }
  let low = 0, high = 255, count = 0;
  const tail = gray.length * .01;
  for (; low < 254 && count + histogram[low] < tail; low++) count += histogram[low];
  count = 0;
  for (; high > low + 1 && count + histogram[high] < tail; high--) count += histogram[high];
  let integral;
  if (adaptive) {
    integral = new Float64Array((width + 1) * (height + 1));
    for (let y = 0; y < height; y++) {
      let row = 0;
      for (let x = 0; x < width; x++) {
        row += gray[y * width + x];
        integral[(y+1)*(width+1)+x+1] = integral[y*(width+1)+x+1] + row;
      }
    }
  }
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    const i = y * width + x;
    let value = Math.max(0, Math.min(255, (gray[i] - low) * 255 / Math.max(1, high-low)));
    if (adaptive) {
      const x0 = Math.max(0, x-55), x1 = Math.min(width, x+56);
      const y0 = Math.max(0, y-55), y1 = Math.min(height, y+56), stride = width+1;
      const mean = (integral[y1*stride+x1]-integral[y0*stride+x1]-integral[y1*stride+x0]+integral[y0*stride+x0]) / ((x1-x0)*(y1-y0));
      value = gray[i] < mean - 6 ? 0 : 255;
    }
    pixels.data[i*4] = pixels.data[i*4+1] = pixels.data[i*4+2] = value;
  }
  context.putImageData(pixels, 0, 0);
}
async function browserReceiptOcr(file, mode, progress) {
  if (!file || !/^image\/(jpeg|png|webp)$/.test(file.type)) throw new Error('Elegí una foto JPG, PNG o WebP.');
  if (file.size > 10 * 1024 * 1024) throw new Error('La foto original debe pesar menos de 10 MB.');
  const bitmap = await createImageBitmap(file, {imageOrientation:'from-image'});
  if (bitmap.width * bitmap.height > 25000000) { bitmap.close(); throw new Error('La imagen supera los 25 megapíxeles.'); }
  const factor = Math.min(1, 2000 / bitmap.width, 6000 / bitmap.height);
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(bitmap.width * factor); canvas.height = Math.round(bitmap.height * factor);
  const context = canvas.getContext('2d');
  context.fillStyle = '#fff'; context.fillRect(0,0,canvas.width,canvas.height);
  context.drawImage(bitmap,0,0,canvas.width,canvas.height);
  let image = await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.9));
  if (!image || image.size > 3500000) { bitmap.close(); throw new Error('La imagen preparada supera 3,5 MB. Elegí una foto más pequeña.'); }
  // Read a separate, enlarged copy; the complete color archive remains unchanged.
  const ocrScale = Math.min(3, Math.max(1, 1800 / bitmap.width), Math.sqrt(8000000 / (bitmap.width * bitmap.height)));
  const reading = document.createElement('canvas');
  const border = 32;
  reading.width = Math.round(bitmap.width * ocrScale) + border * 2;
  reading.height = Math.round(bitmap.height * ocrScale) + border * 2;
  const readingContext = reading.getContext('2d', {willReadFrequently:true});
  readingContext.fillStyle = '#fff'; readingContext.fillRect(0,0,reading.width,reading.height);
  readingContext.imageSmoothingEnabled = true; readingContext.imageSmoothingQuality = 'high';
  readingContext.drawImage(bitmap,border,border,reading.width-border*2,reading.height-border*2);
  bitmap.close();
  const originalPixels = mode === 'standard' ? readingContext.getImageData(0,0,reading.width,reading.height) : null;
  prepareReceiptPixels(readingContext, reading.width, reading.height, mode === 'adaptive');
  receiptOcrProgress = progress;
  if (!window.Tesseract) {
    await new Promise((resolve,reject)=>{
      const script=document.createElement('script'); script.src='/static/vendor/ocr/tesseract.min.js';
      script.onload=resolve;script.onerror=()=>reject(new Error('No se pudieron cargar los archivos del lector. Reintentá cuando haya conexión.'));
      document.head.appendChild(script);
    });
  }
  if (!receiptWorkerPromise) receiptWorkerPromise=Tesseract.createWorker('spa',1,{
    workerPath:'/static/vendor/ocr/worker.min.js', corePath:'/static/vendor/ocr/core',
    langPath:'/static/vendor/ocr/lang', workerBlobURL:false,
    logger:event=>{
      const labels={'recognizing text':'Leyendo en el dispositivo','loading language traineddata':'Descargando modelo en español','loading tesseract core':'Preparando motor OCR','initializing tesseract':'Iniciando lector','initializing api':'Preparando idioma'};
      if(labels[event.status]) receiptOcrProgress(labels[event.status]+'… '+Math.round((event.progress||0)*100)+'%');
    }
  }).catch(error=>{receiptWorkerPromise=null;throw error;});
  progress('Preparando el lector en español…');
  const worker=await receiptWorkerPromise;
  await worker.setParameters({tessedit_pageseg_mode:'4',preserve_interword_spaces:'1',user_defined_dpi:'300'});
  let result=await worker.recognize(reading, {});
  // Compare both layouts even when the page average hides a badly read product line.
  progress('Revisando nombres y distribución de las líneas…');
  await worker.setParameters({tessedit_pageseg_mode:'6'});
  const alternative=await worker.recognize(reading, {});
  if (receiptOcrScore(alternative.data) > receiptOcrScore(result.data)) result=alternative;
  if (originalPixels && result.data.confidence < 85) {
    progress('Mejorando sombras y revisando los productos…');
    readingContext.putImageData(originalPixels,0,0);
    prepareReceiptPixels(readingContext,reading.width,reading.height,true);
    const shadowAlternative = await worker.recognize(reading, {});
    if (receiptOcrScore(shadowAlternative.data) > receiptOcrScore(result.data)) result=shadowAlternative;
  }
  let selectedRotation = 0;
  if (!receiptOcrHasProductEvidence(result.data)) {
    let bestScore = receiptOcrScore(result.data);
    for (const degrees of [90, 180, 270]) {
      progress('Comprobando la orientación del ticket (' + degrees + '°)…');
      const rotated = rotateCanvas(reading, degrees);
      await worker.setParameters({tessedit_pageseg_mode:'6',preserve_interword_spaces:'1',user_defined_dpi:'300'});
      const candidate = await worker.recognize(rotated, {});
      const score = receiptOcrScore(candidate.data);
      if (score > bestScore) {
        bestScore = score;
        result = candidate;
        selectedRotation = degrees;
      }
    }
  }
  let outputCanvas = canvas;
  let text=result.data.text.trim();
  if (selectedRotation) {
    outputCanvas = rotateCanvas(canvas, selectedRotation);
    image = await new Promise(resolve=>outputCanvas.toBlob(resolve,'image/jpeg',.9));
    if (!image) throw new Error('No se pudo preparar la imagen orientada del ticket.');
    if (image.size > 3500000) throw new Error('La imagen preparada supera 3,5 MB. Elegí una foto más pequeña.');
  }
  const storePattern = /\b(?:dia|carrefour|jumbo|coto|disco|changomas)\b/i;
  if (!storePattern.test(text.split(/\r?\n/).slice(0,18).join(' ')) && outputCanvas.height > 500) {
    progress('Revisando el nombre del supermercado…');
    const header = await worker.recognize(outputCanvas, {rectangle:{
      left:Math.round(outputCanvas.width*.06), top:Math.round(outputCanvas.height*.04),
      width:Math.round(outputCanvas.width*.87), height:Math.round(outputCanvas.height*.13)
    }});
    if (storePattern.test(header.data.text)) text = header.data.text.trim() + '\n' + text;
  }
  if (!text) throw new Error('No se reconoció texto. Probá una foto completa y más nítida o pegá el texto manualmente.');
  const warnings = [];
  if (selectedRotation) warnings.push('Se corrigió la orientación de la foto. Revisá que productos, cantidades e importes coincidan con el ticket.');
  if (Number(result.data.confidence || 0) < 75) warnings.push('Lectura de baja confianza: revisá los nombres y precios antes de confirmar.');
  return {text,image,warnings};
}

// Product package search reuses the locally hosted Spanish Tesseract model.
// The photo stays in the browser; only the extracted query reaches the catalog API.
async function browserProductImageQuery(file, progress = () => {}) {
  if (!file || !/^image\/(jpeg|png|webp)$/.test(file.type)) throw new Error('Elegí una imagen JPG, PNG o WebP.');
  if (file.size > 10 * 1024 * 1024) throw new Error('La imagen debe pesar menos de 10 MB.');
  const bitmap = await createImageBitmap(file, {imageOrientation:'from-image'});
  if (bitmap.width * bitmap.height > 25000000) { bitmap.close(); throw new Error('La imagen supera los 25 megapíxeles.'); }
  const scale = Math.min(1, 1800 / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement('canvas');
  canvas.width = Math.round(bitmap.width * scale); canvas.height = Math.round(bitmap.height * scale);
  const context = canvas.getContext('2d');
  context.fillStyle = '#fff'; context.fillRect(0,0,canvas.width,canvas.height);
  context.drawImage(bitmap,0,0,canvas.width,canvas.height); bitmap.close();
  receiptOcrProgress = progress;
  if (!window.Tesseract) await new Promise((resolve,reject)=>{
    const script=document.createElement('script'); script.src='/static/vendor/ocr/tesseract.min.js';
    script.onload=resolve; script.onerror=()=>reject(new Error('No se pudieron cargar los archivos del lector. Reintentá con conexión.'));
    document.head.appendChild(script);
  });
  if (!receiptWorkerPromise) receiptWorkerPromise=Tesseract.createWorker('spa',1,{
    workerPath:'/static/vendor/ocr/worker.min.js', corePath:'/static/vendor/ocr/core',
    langPath:'/static/vendor/ocr/lang', workerBlobURL:false,
    logger:event=>{ const labels={'recognizing text':'Leyendo el envase','loading language traineddata':'Descargando modelo en español','loading tesseract core':'Preparando motor OCR','initializing tesseract':'Iniciando lector','initializing api':'Preparando idioma'}; if(labels[event.status]) receiptOcrProgress(labels[event.status]+'… '+Math.round((event.progress||0)*100)+'%'); }
  }).catch(error=>{receiptWorkerPromise=null;throw error;});
  progress('Preparando el lector de texto…');
  const worker=await receiptWorkerPromise;
  await worker.setParameters({tessedit_pageseg_mode:'11',preserve_interword_spaces:'1',user_defined_dpi:'300'});
  let result=await worker.recognize(canvas,{});
  if ((result.data.text||'').trim().length < 4) {
    await worker.setParameters({tessedit_pageseg_mode:'6'});
    result=await worker.recognize(canvas,{});
  }
  const stop = new Set('nuestra naturaleza es cuidarte elaborado industria producto informacion nutricional ingredientes contiene conservar mantengase origen argentina contenido neto peso neto alimento calidad premium seleccion especial sin tacc'.split(' '));
  const lines=(result.data.text||'').split(/\r?\n/).map(line=>line.replace(/(\d)\s+(kg|g|gr|mg|l|lt|ml)\b/gi,'$1$2').replace(/[^\p{L}\p{N},. ]/gu,' ').replace(/\s+/g,' ').trim()).filter(Boolean);
  const scored=lines.map((line,index)=>{
    const words=line.toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'').split(/\s+/).filter(word=>word.length>1&&!stop.has(word)&&!['kg','gr','mg','ml','lt'].includes(word));
    const hasSize=/\b\d+(?:[.,]\d+)?\s?(?:kg|g|gr|mg|l|lt|ml)\b/i.test(line);
    const productWord=/\b(arroz|leche|fideos?|azucar|harina|aceite|yerba|cafe|galletitas?|atun|tomate|detergente|jabon|queso|yogur|cereal|lentejas?|porotos?)\b/i.test(line);
    return {line,words,score:(hasSize?8:0)+(productWord?8:0)+Math.min(words.length,5)+(line.length>70?-5:0),index};
  }).filter(item=>item.words.length);
  scored.sort((a,b)=>b.score-a.score||a.index-b.index);
  const selected=[]; let count=0;
  for(const item of scored){
    const fresh=item.words.filter(word=>!selected.includes(word));
    if(!fresh.length) continue;
    for(const word of fresh){selected.push(word);count++;if(count>=9)break;}
    if(count>=9)break;
  }
  const query=selected.join(' ').trim();
  if(query.length<3) throw new Error('No se pudo identificar el producto. Probá una foto más nítida o escribí su nombre.');
  return query;
}
