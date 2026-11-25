// CLIP runs entirely in the browser from static assets served by this Vercel app.
// The uploaded image is not sent to Hugging Face or to the model host.
let productVisionAssetsPromise;

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
        model_file_name:'vision_model_quantized',
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
  const bestIndex=probabilities.indexOf(Math.max(...probabilities));
  const best=labels[bestIndex];
  const score=probabilities[bestIndex]/total;
  if(!best || best.query===null || score<0.12) return null;
  return {query:best.query,title:best.title,score};
}

function enrichVisualProductQuery(visual, textQuery='') {
  const base=visual.query.split(/\s+/);
  const family=base[0];
  const allowed={
    cerveza:'quilmes brahma andes patagonia budweiser heineken stella corona schneider imperial amstel clasica rubia roja ipa negra light',
    arroz:'molinos ala largo fino integral blanco carolina',
    leche:'serenisima sancor protein fresca descremada entera',
  };
  const valid=new Set((allowed[family]||'').split(' '));
  const extras=(textQuery||'').toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g,'').split(/\s+/).filter(word=>valid.has(word));
  return [...new Set([...base,...extras])].join(' ');
}
