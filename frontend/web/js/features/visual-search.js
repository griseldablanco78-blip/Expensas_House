// CLIP runs entirely in the browser from static assets served by this Vercel app.
// The uploaded image is not sent to Hugging Face or to the model host.
let productVisionAssetsPromise;

// Accept browser-decodable image formats and normalize them once for CLIP, OCR,
// and the catalog-image endpoint. GIF uploads use their first decoded frame.
async function normalizeProductSearchImage(file) {
  if (!file || !file.type?.startsWith('image/')) throw new Error('Elegí una imagen de un producto.');
  if (file.size > 10 * 1024 * 1024) throw new Error('La imagen debe pesar menos de 10 MB.');
  let source, width, height, release=()=>{};
  try {
    source=await createImageBitmap(file,{imageOrientation:'from-image'});
    width=source.width; height=source.height; release=()=>source.close();
  } catch {
    const objectUrl=URL.createObjectURL(file);
    try {
      source=new Image(); source.src=objectUrl; await source.decode();
      width=source.naturalWidth; height=source.naturalHeight;
    } catch {
      URL.revokeObjectURL(objectUrl);
      throw new Error('Este formato de imagen no es compatible con el navegador. Probá con JPG, PNG o WebP.');
    }
    release=()=>URL.revokeObjectURL(objectUrl);
  }
  if (!width || !height) { release(); throw new Error('La imagen no tiene dimensiones válidas.'); }
  if (width * height > 25_000_000) { release(); throw new Error('La imagen supera los 25 megapíxeles.'); }
  const scale=Math.min(1,2200/Math.max(width,height));
  const canvas=document.createElement('canvas');
  canvas.width=Math.max(1,Math.round(width*scale));
  canvas.height=Math.max(1,Math.round(height*scale));
  const context=canvas.getContext('2d');
  context.fillStyle='#fff'; context.fillRect(0,0,canvas.width,canvas.height);
  context.drawImage(source,0,0,canvas.width,canvas.height); release();
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',0.9));
  if(!blob) throw new Error('No se pudo preparar la imagen. Probá con JPG o PNG.');
  return new File([blob],'busqueda-producto.jpg',{type:'image/jpeg',lastModified:Date.now()});
}

async function getProductVisionAssets(progress) {
  if (!productVisionAssetsPromise) productVisionAssetsPromise=(async()=>{
    progress('Cargando el reconocedor visual de Expensas House…');
    const {AutoImageProcessor,CLIPVisionModelWithProjection,RawImage,env}=await import('/static/vendor/transformers/transformers.min.js');
    env.allowRemoteModels=false;
    env.allowLocalModels=true;
    env.localModelPath='/static/models/';
    env.backends.onnx.wasm.wasmPaths=new URL('/static/vendor/transformers/',window.location.href).href;

    const modelId='clip-vit-base-patch32';
    const [model,processor,response]=await Promise.all([
      CLIPVisionModelWithProjection.from_pretrained(modelId,{
        // The library appends `_quantized` for dtype q8 on WASM, so keep this as the base name.
        model_file_name:'vision_model',
        dtype:'q8',
        local_files_only:true,
        device:'wasm',
        progress_callback:event=>{
          if(event.status==='progress' && event.file)
            progress(`Descargando el modelo desde Vercel: ${event.file} ${Math.round(event.progress||0)}%`);
        }
      }),
      AutoImageProcessor.from_pretrained(modelId,{local_files_only:true}),
      fetch('/static/models/clip-vit-base-patch32/labels.json',{cache:'force-cache'})
    ]);
    if(!response.ok) throw new Error('No se pudieron cargar las etiquetas visuales.');
    const labels=await response.json();
    return {model,processor,RawImage,labels};
  })().catch(error=>{productVisionAssetsPromise=null;throw error;});
  return productVisionAssetsPromise;
}

async function classifyProductImage(file, progress=()=>{}) {
  const {model,processor,RawImage,labels}=await getProductVisionAssets(progress);
  progress('Comparando la imagen con categorías de productos…');
  const image=await RawImage.read(file);
  const {pixel_values}=await processor(image);
  const {image_embeds}=await model({pixel_values});
  const vector=Array.from(image_embeds.data);
  const norm=Math.sqrt(vector.reduce((sum,value)=>sum+value*value,0))||1;
  const similarities=labels.map(item=>vector.reduce((sum,value,index)=>sum+(value/norm)*item.vector[index],0));
  const logits=similarities.map(value=>value*100);
  const maximum=Math.max(...logits);
  const probabilities=logits.map(value=>Math.exp(value-maximum));
  const total=probabilities.reduce((sum,value)=>sum+value,0)||1;
  let bestIndex=probabilities.indexOf(Math.max(...probabilities));
  // Cans of beer and soft drinks can be nearly tied visually. Prefer a
  // brand-specific beer label when CLIP's cosine scores are effectively equal.
  if(labels[bestIndex]?.query==='gaseosa'){
    const beer=labels.map((item,index)=>({item,index,similarity:similarities[index]}))
      .filter(candidate=>candidate.item.query?.startsWith('cerveza'))
      .sort((left,right)=>right.similarity-left.similarity);
    if(beer.length && similarities[bestIndex]-beer[0].similarity<=0.005){
      const specific=beer.find(candidate=>candidate.item.query.includes('quilmes') && beer[0].similarity-candidate.similarity<=0.005);
      bestIndex=(specific||beer[0]).index;
    }
  }
  const best=labels[bestIndex];
  const score=probabilities[bestIndex]/total;
  if(!best || best.query===null || score<0.12) return null;
  return {query:best.query,title:best.title,score};
}

function enrichVisualProductQuery(visual, textQuery='') {
  const base=visual.query.split(/\s+/);
  let family=base[0];
  const textWords=(textQuery||'').toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'').split(/\s+/);
  const beerBrand=textWords.find(word=>['quilmes','brahma','andes','patagonia','budweiser','heineken','stella','corona','schneider','imperial','amstel'].includes(word));
  if(family==='gaseosa' && beerBrand) { base.splice(0,base.length,'cerveza'); family='cerveza'; }
  const allowed={
    cerveza:'quilmes brahma andes patagonia budweiser heineken stella corona schneider imperial amstel clasica rubia roja ipa negra light',
    arroz:'molinos ala largo fino integral blanco carolina',
    leche:'serenisima sancor protein fresca descremada entera',
    dentifrico:'colgate total fluor menta sensodyne oralb',
  };
  const valid=new Set((allowed[family]||'').split(' '));
  const extras=textWords.filter(word=>valid.has(word));
  return [...new Set([...base,...extras])].join(' ');
}
