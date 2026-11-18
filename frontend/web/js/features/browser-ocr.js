// Self-hosted OCR. No image is sent to a paid or external AI service.
let receiptWorkerPromise;
let receiptOcrProgress = () => {};

// Score readability, not financial correctness; every amount still requires review.
function receiptOcrScore(data) {
  const text = data.text || '';
  const words = text.match(/[a-záéíóúñ]+/gi) || [];
  const fragments = words.filter(word => word.length === 1).length;
  const prices = (text.match(/\d[\d.,]*[.,]\d{2}(?!\d)/g) || []).length;
  return Number(data.confidence || 0) + Math.min(prices, 30) - 30 * fragments / Math.max(words.length, 1);
}

function prepareReceiptPixels(context, width, height, adaptive) {
  const pixels = context.getImageData(0, 0, width, height);
  const gray = new Uint8Array(width * height);
  const histogram = new Uint32Array(256);
  for (let i = 0; i < gray.length; i++) {
    gray[i] = Math.round(.299 * pixels.data[i*4] + .587 * pixels.data[i*4+1] + .114 * pixels.data[i*4+2]);
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
      const x0 = Math.max(0, x-20), x1 = Math.min(width, x+21);
      const y0 = Math.max(0, y-20), y1 = Math.min(height, y+21), stride = width+1;
      const mean = (integral[y1*stride+x1]-integral[y0*stride+x1]-integral[y1*stride+x0]+integral[y0*stride+x0]) / ((x1-x0)*(y1-y0));
      value = gray[i] < mean - 12 ? 0 : 255;
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
  context.drawImage(bitmap,0,0,canvas.width,canvas.height); bitmap.close();
  const image = await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.9));
  if (!image || image.size > 3500000) throw new Error('La imagen preparada supera 3,5 MB. Elegí una foto más pequeña.');
  // Read a separate, enlarged copy; the complete color archive remains unchanged.
  const ocrScale = Math.min(3, Math.max(1, 1600 / canvas.width), Math.sqrt(8000000 / (canvas.width * canvas.height)));
  const reading = document.createElement('canvas');
  const border = 32;
  reading.width = Math.round(canvas.width * ocrScale) + border * 2;
  reading.height = Math.round(canvas.height * ocrScale) + border * 2;
  const readingContext = reading.getContext('2d', {willReadFrequently:true});
  readingContext.fillStyle = '#fff'; readingContext.fillRect(0,0,reading.width,reading.height);
  readingContext.imageSmoothingEnabled = true; readingContext.imageSmoothingQuality = 'high';
  readingContext.drawImage(canvas,border,border,reading.width-border*2,reading.height-border*2);
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
  let result=await worker.recognize(reading, {rotateAuto:true});
  if (result.data.confidence < 85 || !(result.data.text || '').match(/\d[.,]\d{2}/)) {
    progress('Revisando la distribución de las líneas…');
    await worker.setParameters({tessedit_pageseg_mode:'6'});
    const alternative=await worker.recognize(reading, {rotateAuto:true});
    if (receiptOcrScore(alternative.data) > receiptOcrScore(result.data)) result=alternative;
  }
  const text=result.data.text.trim();
  if (!text) throw new Error('No se reconoció texto. Probá una foto completa y más nítida o pegá el texto manualmente.');
  return {text,image};
}
