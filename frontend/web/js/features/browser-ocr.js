// Self-hosted OCR. No image is sent to a paid or external AI service.
let receiptWorkerPromise;
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
  // The archived color image stays intact; preprocessing affects only the OCR copy.
  if (mode === 'adaptive') {
    const pixels = context.getImageData(0,0,canvas.width,canvas.height);
    for (let i=0;i<pixels.data.length;i+=4) {
      const gray=.299*pixels.data[i]+.587*pixels.data[i+1]+.114*pixels.data[i+2];
      const value=Math.max(0,Math.min(255,(gray-128)*1.5+128));
      pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=value;
    }
    context.putImageData(pixels,0,0);
  }
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
      if(labels[event.status]) progress(labels[event.status]+'… '+Math.round((event.progress||0)*100)+'%');
    }
  }).catch(error=>{receiptWorkerPromise=null;throw error;});
  progress('Preparando el lector en español…');
  const worker=await receiptWorkerPromise;
  await worker.setParameters({tessedit_pageseg_mode:'6',preserve_interword_spaces:'1'});
  const result=await worker.recognize(canvas);
  const text=result.data.text.trim();
  if (!text) throw new Error('No se reconoció texto. Probá una foto completa y más nítida o pegá el texto manualmente.');
  return {text,image};
}
