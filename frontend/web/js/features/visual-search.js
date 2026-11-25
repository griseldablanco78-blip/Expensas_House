// Pretrained CLIP runs in the browser. The uploaded photo is never sent to Hugging Face.
let productVisionPipelinePromise;
const productImageClasses = [
  {label:'a can of Quilmes Clásica beer', query:'cerveza quilmes clasica', title:'lata de cerveza Quilmes clásica'},
  {label:'an aluminum can of beer', query:'cerveza', title:'lata de cerveza'},
  {label:'a bottle of beer', query:'cerveza', title:'cerveza'},
  {label:'a bag of Molinos Ala long grain fine rice', query:'arroz molinos ala largo fino', title:'arroz Molinos Ala largo fino'},
  {label:'a bag of uncooked rice', query:'arroz', title:'paquete de arroz'},
  {label:'a pouch of La Serenísima protein milk', query:'leche serenisima protein', title:'leche Protein La Serenísima'},
  {label:'a carton or pouch of milk', query:'leche', title:'envase de leche'},
  {label:'a package of pasta noodles', query:'fideos', title:'paquete de fideos'},
  {label:'a bag of flour', query:'harina', title:'paquete de harina'},
  {label:'a bag of sugar', query:'azucar', title:'paquete de azúcar'},
  {label:'a bottle of cooking oil', query:'aceite', title:'botella de aceite'},
  {label:'a package of yerba mate', query:'yerba', title:'paquete de yerba'},
  {label:'a jar of coffee', query:'cafe', title:'paquete de café'},
  {label:'a can of tuna', query:'atun', title:'lata de atún'},
  {label:'a can of tomatoes', query:'tomate', title:'lata de tomate'},
  {label:'a package of cookies', query:'galletitas', title:'paquete de galletitas'},
  {label:'a bottle of dish soap', query:'detergente', title:'botella de detergente'},
  {label:'a bar of soap', query:'jabon', title:'jabón'},
  {label:'a package of toilet paper rolls', query:'papel higienico', title:'paquete de papel higiénico'},
  {label:'a bottle of shampoo', query:'shampoo', title:'botella de shampoo'},
  {label:'a bottle of soda', query:'gaseosa', title:'botella de gaseosa'},
  {label:'a bottle of water', query:'agua', title:'botella de agua'},
  {label:'a bottle of wine', query:'vino', title:'botella de vino'},
  {label:'a package of yogurt', query:'yogur', title:'envase de yogur'},
  {label:'a package of cheese', query:'queso', title:'paquete de queso'},
  {label:'a book', query:null, title:'libro'},
  {label:'a chair', query:null, title:'silla'},
];

async function getProductVisionPipeline(progress) {
  if (!productVisionPipelinePromise) productVisionPipelinePromise=(async()=>{
    progress('Cargando el modelo visual CLIP (primera vez, se guarda en este navegador)…');
    const {pipeline}=await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1');
    return pipeline('zero-shot-image-classification','Xenova/clip-vit-base-patch32',{
      revision:'main',
      progress_callback:event=>{
        if(event.status==='progress' && event.file) progress(`Descargando modelo visual: ${event.file} ${Math.round(event.progress||0)}%`);
      }
    });
  })().catch(error=>{productVisionPipelinePromise=null;throw error;});
  return productVisionPipelinePromise;
}

async function classifyProductImage(file, progress=()=>{}) {
  const model=await getProductVisionPipeline(progress);
  const source=URL.createObjectURL(file);
  try {
    progress('Reconociendo visualmente el tipo de producto…');
    const result=await model(source, productImageClasses.map(item=>item.label), {hypothesis_template:'A close-up product photo of {}.'});
    const best=result && result[0];
    const match=productImageClasses.find(item=>item.label===best?.label);
    if(!match || !match.query || Number(best.score)<0.12) return null;
    return {...match,score:Number(best.score)};
  } finally { URL.revokeObjectURL(source); }
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
