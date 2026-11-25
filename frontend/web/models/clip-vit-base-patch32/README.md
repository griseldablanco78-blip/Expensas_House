# CLIP image-search assets

- Model family: OpenAI CLIP ViT-B/32 (`openai/clip-vit-base-patch32`).
- Browser artifact: quantized CLIP vision encoder in ONNX format, converted for Transformers.js by Xenova.
- License reported by the converted model: MIT.
- Runtime: Transformers.js 3.8.1 with ONNX Runtime Web 1.22.0-dev.
- Runtime location: static files bundled and served by this Vercel project; remote model downloads are disabled.
- `labels.json` contains normalized text embeddings generated locally from `labels.source.json` with the matching pretrained CLIP text encoder. The temporary text encoder is not included in the deployed site.
- Vision weight SHA-256: `583fd1110a514667812fee7d684952aaf82a99b959760c8d7dca7e0ab9839299`.

The project does not train or fine-tune CLIP. It uses pretrained weights and compares the uploaded image embedding with a fixed set of product-description embeddings.
