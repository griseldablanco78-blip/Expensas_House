import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { AutoTokenizer, CLIPTextModelWithProjection, env } from '@huggingface/transformers';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const modelDir = path.resolve(process.argv[2] || path.join(root, 'frontend/web/models/.clip-build'));
const labelsPath = path.join(root, 'frontend/web/models/clip-vit-base-patch32/labels.source.json');
const outputPath = path.join(root, 'frontend/web/models/clip-vit-base-patch32/labels.json');

env.allowRemoteModels = false;
const labels = JSON.parse(await fs.readFile(labelsPath, 'utf8'));
const tokenizer = await AutoTokenizer.from_pretrained(modelDir, { local_files_only: true });
const model = await CLIPTextModelWithProjection.from_pretrained(modelDir, {
  model_file_name: 'text_model_quantized',
  local_files_only: true,
  device: 'cpu',
});
const tokens = tokenizer(labels.map(({ label }) => `A close-up product photo of ${label}.`), {
  padding: true,
  truncation: true,
});
const { text_embeds: embeddings } = await model(tokens);
const vectors = [];
for (let row = 0; row < labels.length; row++) {
  const start = row * embeddings.dims[1];
  const vector = Array.from(embeddings.data.slice(start, start + embeddings.dims[1]));
  const norm = Math.sqrt(vector.reduce((sum, value) => sum + value * value, 0)) || 1;
  vectors.push(vector.map(value => Number((value / norm).toFixed(7))));
}
await fs.writeFile(outputPath, JSON.stringify(labels.map((item, index) => ({ ...item, vector: vectors[index] }))));
console.log(`Saved ${labels.length} normalized CLIP text vectors to ${outputPath}`);
