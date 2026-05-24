from __future__ import annotations

import base64
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "app" / "assets" / "default-template.png"
OUTPUT_PATH = ROOT / "standalone.html"


def main() -> None:
    template_data_url = "data:image/png;base64," + base64.b64encode(TEMPLATE_PATH.read_bytes()).decode("ascii")
    OUTPUT_PATH.write_text(build_html(template_data_url), encoding="utf-8")


def build_html(template_data_url: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>SayHi 图片融合工具 离线版</title>
    <style>
      :root {{
        --bg: #f6f7f9;
        --panel: #ffffff;
        --line: #d9dee7;
        --text: #141821;
        --muted: #697386;
        --accent: #e53935;
        --accent-dark: #b91f1c;
        --blue: #174bf6;
        --shadow: 0 18px 44px rgba(23, 31, 48, 0.08);
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        background: var(--bg);
        color: var(--text);
        font-family: Inter, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      }}
      button, input, select {{ font: inherit; }}
      .app-shell {{
        width: min(1480px, calc(100vw - 40px));
        margin: 0 auto;
        padding: 28px 0;
      }}
      .topbar {{
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 20px;
        padding: 0 0 22px;
      }}
      .eyebrow {{
        margin: 0 0 6px;
        color: var(--accent);
        font-size: 13px;
        font-weight: 800;
        text-transform: uppercase;
      }}
      h1, h2, p {{ margin: 0; }}
      h1 {{
        font-size: clamp(30px, 4vw, 52px);
        line-height: 1;
        letter-spacing: 0;
      }}
      h2 {{ font-size: 18px; line-height: 1.2; }}
      .workspace {{
        display: grid;
        grid-template-columns: minmax(280px, 0.9fr) minmax(300px, 0.8fr) minmax(360px, 1.2fr);
        gap: 16px;
        align-items: start;
      }}
      .panel {{
        min-width: 0;
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: var(--shadow);
        padding: 18px;
      }}
      .panel-head {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
      }}
      .panel-head-with-action {{ align-items: flex-start; }}
      .panel-head-with-action > div {{ min-width: 0; flex: 1; }}
      .panel-head p {{
        margin-top: 4px;
        color: var(--muted);
        font-size: 13px;
      }}
      .step {{
        display: inline-grid;
        place-items: center;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: #eef2ff;
        color: var(--blue);
        font-weight: 900;
        font-size: 13px;
        flex: 0 0 auto;
      }}
      .primary-button, .download-button {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 44px;
        border: 0;
        border-radius: 8px;
        background: var(--accent);
        color: #fff;
        padding: 0 18px;
        font-weight: 800;
        text-decoration: none;
        cursor: pointer;
        transition: transform 160ms ease, background 160ms ease, opacity 160ms ease;
      }}
      .primary-button:hover, .download-button:hover {{
        background: var(--accent-dark);
        transform: translateY(-1px);
      }}
      .primary-button:disabled {{ opacity: 0.55; cursor: wait; transform: none; }}
      .secondary-button {{
        min-height: 34px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
        color: var(--muted);
        padding: 0 12px;
        font-weight: 800;
        cursor: pointer;
      }}
      .secondary-button:hover {{ border-color: var(--accent); background: #fff5f5; color: var(--accent); }}
      .dropzone {{
        display: grid;
        place-items: center;
        min-height: 210px;
        border: 1.5px dashed #aeb7c7;
        border-radius: 8px;
        background: #fbfcfe;
        cursor: pointer;
        text-align: center;
        transition: border-color 160ms ease, background 160ms ease;
      }}
      .dropzone:hover, .dropzone.dragover {{ border-color: var(--blue); background: #f4f7ff; }}
      .dropzone input {{
        position: absolute;
        width: 1px;
        height: 1px;
        opacity: 0;
        pointer-events: none;
      }}
      .dropzone-title {{
        display: block;
        color: var(--text);
        font-size: 18px;
        font-weight: 900;
      }}
      .dropzone-subtitle {{
        display: block;
        margin-top: 8px;
        color: var(--muted);
        font-size: 13px;
      }}
      .file-list {{
        display: grid;
        gap: 8px;
        max-height: 230px;
        overflow: auto;
        margin-top: 14px;
      }}
      .file-item {{
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 1px solid #eef0f4;
        padding: 8px 0;
        color: var(--muted);
        font-size: 13px;
      }}
      .product-file-item img {{
        width: 54px;
        height: 54px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
        flex: 0 0 auto;
        object-fit: contain;
      }}
      .file-meta {{ display: grid; min-width: 0; gap: 4px; }}
      .file-item strong {{
        min-width: 0;
        overflow: hidden;
        color: var(--text);
        text-overflow: ellipsis;
        white-space: nowrap;
      }}
      .field {{ display: grid; gap: 7px; margin-bottom: 14px; }}
      .field span {{
        color: var(--muted);
        font-size: 13px;
        font-weight: 800;
      }}
      .field input, .field select {{
        width: 100%;
        min-height: 42px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
        color: var(--text);
        padding: 0 12px;
        outline: none;
      }}
      .field input:focus, .field select:focus {{
        border-color: var(--blue);
        box-shadow: 0 0 0 3px rgba(23, 75, 246, 0.12);
      }}
      .color-field input[type="color"] {{ height: 42px; padding: 4px; cursor: pointer; }}
      .grid-2 {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }}
      .template-preview-wrap {{
        display: grid;
        place-items: center;
        aspect-ratio: 1;
        margin-bottom: 14px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background:
          linear-gradient(45deg, #f0f2f6 25%, transparent 25%),
          linear-gradient(-45deg, #f0f2f6 25%, transparent 25%),
          linear-gradient(45deg, transparent 75%, #f0f2f6 75%),
          linear-gradient(-45deg, transparent 75%, #f0f2f6 75%);
        background-color: #fff;
        background-position: 0 0, 0 10px, 10px -10px, -10px 0;
        background-size: 20px 20px;
        overflow: hidden;
      }}
      .template-preview-wrap img {{
        display: block;
        width: 100%;
        height: 100%;
        object-fit: contain;
      }}
      .preview-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        min-height: 360px;
      }}
      .preview-grid.empty {{
        place-items: center;
        grid-template-columns: 1fr;
        border: 1px dashed #c7ceda;
        border-radius: 8px;
        color: var(--muted);
      }}
      .preview-item {{ min-width: 0; margin: 0; }}
      .preview-item img {{
        display: block;
        width: 100%;
        aspect-ratio: 1;
        object-fit: contain;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
      }}
      .filename-input {{
        width: 100%;
        min-height: 36px;
        margin-top: 8px;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0 10px;
        color: var(--text);
        outline: none;
      }}
      .filename-input:focus {{
        border-color: var(--blue);
        box-shadow: 0 0 0 3px rgba(23, 75, 246, 0.12);
      }}
      .download-button {{ width: 100%; margin-top: 14px; }}
      .download-button.disabled {{ pointer-events: none; opacity: 0.45; }}
      @media (max-width: 1120px) {{
        .workspace {{ grid-template-columns: 1fr 1fr; }}
        .result-panel {{ grid-column: 1 / -1; }}
      }}
      @media (max-width: 760px) {{
        .app-shell {{ width: min(100% - 24px, 1480px); padding: 18px 0; }}
        .topbar, .workspace, .grid-2 {{ grid-template-columns: 1fr; }}
        .topbar {{ display: grid; align-items: stretch; }}
        .preview-grid {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main class="app-shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">SayHi Tool Offline</p>
          <h1>图片模板融合</h1>
        </div>
        <button id="processBtn" class="primary-button" type="button">开始处理</button>
      </header>

      <section class="workspace" aria-label="图片处理工作区">
        <form id="toolForm" class="panel upload-panel">
          <div class="panel-head panel-head-with-action">
            <span class="step">01</span>
            <div>
              <h2>商品图</h2>
              <p>商品会缩放到画布中心 75% 区域，不裁切</p>
            </div>
            <button id="clearProductsButton" class="secondary-button" type="button">清空</button>
          </div>

          <label id="dropzone" class="dropzone">
            <input id="productsInput" name="products" type="file" accept="image/png,image/jpeg,image/webp" multiple />
            <span class="dropzone-title">选择或拖入商品主图</span>
            <span id="fileCount" class="dropzone-subtitle">尚未选择文件</span>
          </label>

          <div id="fileList" class="file-list" aria-live="polite"></div>
        </form>

        <section class="panel settings-panel">
          <div class="panel-head">
            <span class="step">02</span>
            <div>
              <h2>模板与输出</h2>
              <p>默认 1440 x 1440，商品区域 1080 x 1080</p>
            </div>
          </div>

          <label class="field">
            <span>模板</span>
            <select id="templateSelect">
              <option value="default">默认模板</option>
              <option value="custom">本次上传模板</option>
            </select>
          </label>

          <div class="template-preview-wrap">
            <img id="templatePreview" alt="当前模板预览" />
          </div>

          <label class="field upload-template">
            <span>上传新模板</span>
            <input id="templateInput" type="file" accept="image/png" />
          </label>

          <div class="grid-2">
            <label class="field">
              <span>宽度</span>
              <input id="widthInput" type="number" min="64" max="5000" value="1440" />
            </label>
            <label class="field">
              <span>高度</span>
              <input id="heightInput" type="number" min="64" max="5000" value="1440" />
            </label>
          </div>

          <label class="field color-field">
            <span>背景色</span>
            <input id="backgroundColorInput" type="color" value="#ffffff" />
          </label>

          <label class="field">
            <span>输出名称</span>
            <input id="baseNameInput" type="text" value="product" maxlength="80" />
          </label>
        </section>

        <section class="panel result-panel">
          <div class="panel-head">
            <span class="step">03</span>
            <div>
              <h2>结果</h2>
              <p id="statusText">等待处理</p>
            </div>
          </div>

          <div id="previewGrid" class="preview-grid empty">
            <span>处理完成后显示预览</span>
          </div>

          <a id="downloadLink" class="download-button disabled" download>下载 ZIP</a>
        </section>
      </section>
    </main>

    <script>
      const DEFAULT_TEMPLATE_DATA_URL = "{template_data_url}";
      const PRODUCT_AREA_RATIO = 0.75;

      const productsInput = document.querySelector("#productsInput");
      const templateInput = document.querySelector("#templateInput");
      const templateSelect = document.querySelector("#templateSelect");
      const templatePreview = document.querySelector("#templatePreview");
      const fileCount = document.querySelector("#fileCount");
      const fileList = document.querySelector("#fileList");
      const dropzone = document.querySelector("#dropzone");
      const clearProductsButton = document.querySelector("#clearProductsButton");
      const widthInput = document.querySelector("#widthInput");
      const heightInput = document.querySelector("#heightInput");
      const backgroundColorInput = document.querySelector("#backgroundColorInput");
      const baseNameInput = document.querySelector("#baseNameInput");
      const processBtn = document.querySelector("#processBtn");
      const statusText = document.querySelector("#statusText");
      const previewGrid = document.querySelector("#previewGrid");
      const downloadLink = document.querySelector("#downloadLink");

      let selectedProductFiles = [];
      let customTemplateFile = null;
      let currentResults = [];

      function setStatus(message) {{
        statusText.textContent = message;
      }}

      function formatSize(bytes) {{
        if (bytes < 1024) return `${{bytes}} B`;
        if (bytes < 1024 * 1024) return `${{(bytes / 1024).toFixed(1)}} KB`;
        return `${{(bytes / 1024 / 1024).toFixed(1)}} MB`;
      }}

      function safeStem(value, fallback = "product") {{
        const stem = String(value || "").replace(/\\.[^.]+$/, "").trim().replace(/[^\\w.-]+/g, "_").replace(/^[._-]+|[._-]+$/g, "");
        return stem.slice(0, 80) || fallback;
      }}

      function revokeObjectUrl(element) {{
        if (element.dataset.objectUrl) {{
          URL.revokeObjectURL(element.dataset.objectUrl);
          delete element.dataset.objectUrl;
        }}
      }}

      function setProductInputFiles(files) {{
        const transfer = new DataTransfer();
        files.forEach((file) => transfer.items.add(file));
        productsInput.files = transfer.files;
      }}

      function disableDownload() {{
        downloadLink.classList.add("disabled");
        downloadLink.setAttribute("aria-disabled", "true");
      }}

      function enableDownload() {{
        downloadLink.classList.remove("disabled");
        downloadLink.removeAttribute("aria-disabled");
      }}

      function clearResultState(message = "等待处理") {{
        currentResults.forEach((item) => URL.revokeObjectURL(item.previewUrl));
        currentResults = [];
        disableDownload();
        previewGrid.className = "preview-grid empty";
        previewGrid.innerHTML = "<span>处理完成后显示预览</span>";
        setStatus(message);
      }}

      function updateFileList() {{
        const incomingFiles = Array.from(productsInput.files || []);
        if (!incomingFiles.length && selectedProductFiles.length) {{
          setProductInputFiles(selectedProductFiles);
          return;
        }}

        selectedProductFiles = incomingFiles;
        const files = selectedProductFiles;
        Array.from(fileList.querySelectorAll("img")).forEach(revokeObjectUrl);
        fileCount.textContent = files.length ? `${{files.length}} 个文件已选择` : "尚未选择文件";
        fileList.innerHTML = "";

        files.slice(0, 50).forEach((file) => {{
          const item = document.createElement("div");
          item.className = "file-item product-file-item";

          const image = document.createElement("img");
          image.alt = file.name;
          image.src = URL.createObjectURL(file);
          image.onload = () => revokeObjectUrl(image);
          image.dataset.objectUrl = image.src;

          const meta = document.createElement("div");
          meta.className = "file-meta";
          meta.innerHTML = `<strong title="${{file.name}}">${{file.name}}</strong><span>${{formatSize(file.size)}}</span>`;

          item.append(image, meta);
          fileList.appendChild(item);
        }});
        clearResultState(files.length ? "商品图已更新" : "等待处理");
      }}

      function clearProducts() {{
        Array.from(fileList.querySelectorAll("img")).forEach(revokeObjectUrl);
        selectedProductFiles = [];
        productsInput.value = "";
        fileCount.textContent = "尚未选择文件";
        fileList.innerHTML = "";
        clearResultState("已清空商品图");
      }}

      function updateTemplatePreview() {{
        if (templateSelect.value === "custom" && customTemplateFile) {{
          const objectUrl = URL.createObjectURL(customTemplateFile);
          templatePreview.onload = () => URL.revokeObjectURL(objectUrl);
          templatePreview.src = objectUrl;
        }} else {{
          templatePreview.src = DEFAULT_TEMPLATE_DATA_URL;
        }}
      }}

      function uploadTemplate() {{
        const file = templateInput.files?.[0];
        if (!file) return;
        customTemplateFile = file;
        templateSelect.value = "custom";
        updateTemplatePreview();
        clearResultState("模板已更新");
      }}

      function validateForm() {{
        const files = Array.from(productsInput.files || []);
        if (!files.length && selectedProductFiles.length) {{
          setProductInputFiles(selectedProductFiles);
          return validateForm();
        }}
        if (!files.length) throw new Error("请先选择商品主图");
        const width = Number(widthInput.value);
        const height = Number(heightInput.value);
        if (!Number.isInteger(width) || !Number.isInteger(height) || width < 64 || height < 64 || width > 5000 || height > 5000) {{
          throw new Error("输出宽高需要在 64 到 5000 之间");
        }}
        return {{ files, width, height }};
      }}

      function loadImage(source) {{
        return new Promise((resolve, reject) => {{
          const image = new Image();
          image.onload = () => resolve(image);
          image.onerror = () => reject(new Error("图片读取失败"));
          image.src = source instanceof Blob ? URL.createObjectURL(source) : source;
          if (source instanceof Blob) {{
            image.dataset.objectUrl = image.src;
          }}
        }});
      }}

      async function getTemplateImage() {{
        const source = templateSelect.value === "custom" && customTemplateFile ? customTemplateFile : DEFAULT_TEMPLATE_DATA_URL;
        const image = await loadImage(source);
        if (image.dataset.objectUrl) URL.revokeObjectURL(image.dataset.objectUrl);
        return image;
      }}

      async function composeImage(productFile, templateImage, width, height, backgroundColor) {{
        const productImage = await loadImage(productFile);
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const context = canvas.getContext("2d");
        context.fillStyle = backgroundColor;
        context.fillRect(0, 0, width, height);

        const areaWidth = Math.round(width * PRODUCT_AREA_RATIO);
        const areaHeight = Math.round(height * PRODUCT_AREA_RATIO);
        const scale = Math.min(areaWidth / productImage.naturalWidth, areaHeight / productImage.naturalHeight);
        const drawWidth = Math.round(productImage.naturalWidth * scale);
        const drawHeight = Math.round(productImage.naturalHeight * scale);
        const productX = Math.round((width - drawWidth) / 2);
        const productY = Math.round((height - drawHeight) / 2);

        context.drawImage(productImage, productX, productY, drawWidth, drawHeight);
        context.drawImage(templateImage, 0, 0, width, height);

        if (productImage.dataset.objectUrl) URL.revokeObjectURL(productImage.dataset.objectUrl);
        return new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
      }}

      function renderResultPreviews(results) {{
        previewGrid.className = "preview-grid";
        previewGrid.innerHTML = "";
        results.forEach((result) => {{
          const item = document.createElement("figure");
          item.className = "preview-item";

          const image = document.createElement("img");
          image.src = result.previewUrl;
          image.alt = result.filename;

          const input = document.createElement("input");
          input.className = "filename-input";
          input.type = "text";
          input.value = result.filename.replace(/\\.png$/i, "");
          input.setAttribute("aria-label", `${{result.filename}} 的输出文件名`);

          item.append(image, input);
          previewGrid.appendChild(item);
        }});
      }}

      function getEditedOutputNames() {{
        return Array.from(document.querySelectorAll(".filename-input")).map((input, index) => {{
          const stem = safeStem(input.value, `product_${{String(index + 1).padStart(3, "0")}}`);
          return `${{stem}}.png`;
        }});
      }}

      async function processImages() {{
        try {{
          const {{ files, width, height }} = validateForm();
          processBtn.disabled = true;
          clearResultState("正在生成图片");
          previewGrid.className = "preview-grid empty";
          previewGrid.innerHTML = "<span>处理中</span>";

          const templateImage = await getTemplateImage();
          const baseName = safeStem(baseNameInput.value, "product");
          const nextResults = [];
          for (let index = 0; index < files.length; index += 1) {{
            const blob = await composeImage(files[index], templateImage, width, height, backgroundColorInput.value || "#ffffff");
            const filename = `${{baseName}}_${{String(index + 1).padStart(3, "0")}}.png`;
            nextResults.push({{ filename, blob, previewUrl: URL.createObjectURL(blob) }});
          }}

          currentResults = nextResults;
          renderResultPreviews(currentResults);
          enableDownload();
          setStatus(`已生成 ${{currentResults.length}} 张图片，可编辑文件名后下载`);
        }} catch (error) {{
          previewGrid.className = "preview-grid empty";
          previewGrid.innerHTML = `<span>${{error.message}}</span>`;
          setStatus("处理失败");
        }} finally {{
          processBtn.disabled = false;
        }}
      }}

      function makeUniqueFilenames(names) {{
        const used = new Set();
        return names.map((name, index) => {{
          const stem = safeStem(name, `product_${{String(index + 1).padStart(3, "0")}}`);
          let candidate = `${{stem}}.png`;
          let suffix = 2;
          while (used.has(candidate.toLowerCase())) {{
            candidate = `${{stem}}_${{suffix}}.png`;
            suffix += 1;
          }}
          used.add(candidate.toLowerCase());
          return candidate;
        }});
      }}

      function crc32(bytes) {{
        let crc = -1;
        for (let index = 0; index < bytes.length; index += 1) {{
          crc = (crc >>> 8) ^ CRC_TABLE[(crc ^ bytes[index]) & 0xff];
        }}
        return (crc ^ -1) >>> 0;
      }}

      function writeUint16(output, value) {{
        output.push(value & 0xff, (value >>> 8) & 0xff);
      }}

      function writeUint32(output, value) {{
        output.push(value & 0xff, (value >>> 8) & 0xff, (value >>> 16) & 0xff, (value >>> 24) & 0xff);
      }}

      function datePartsForZip(date = new Date()) {{
        const time = (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2);
        const day = date.getDate();
        const month = date.getMonth() + 1;
        const year = Math.max(date.getFullYear() - 1980, 0);
        const zipDate = (year << 9) | (month << 5) | day;
        return {{ time, date: zipDate }};
      }}

      async function createZip(files) {{
        const encoder = new TextEncoder();
        const localParts = [];
        const centralParts = [];
        let offset = 0;
        const {{ time, date }} = datePartsForZip();

        for (const file of files) {{
          const data = new Uint8Array(await file.blob.arrayBuffer());
          const name = encoder.encode(file.name);
          const crc = crc32(data);

          const local = [];
          writeUint32(local, 0x04034b50);
          writeUint16(local, 20);
          writeUint16(local, 0x0800);
          writeUint16(local, 0);
          writeUint16(local, time);
          writeUint16(local, date);
          writeUint32(local, crc);
          writeUint32(local, data.length);
          writeUint32(local, data.length);
          writeUint16(local, name.length);
          writeUint16(local, 0);
          localParts.push(new Uint8Array(local), name, data);

          const central = [];
          writeUint32(central, 0x02014b50);
          writeUint16(central, 20);
          writeUint16(central, 20);
          writeUint16(central, 0x0800);
          writeUint16(central, 0);
          writeUint16(central, time);
          writeUint16(central, date);
          writeUint32(central, crc);
          writeUint32(central, data.length);
          writeUint32(central, data.length);
          writeUint16(central, name.length);
          writeUint16(central, 0);
          writeUint16(central, 0);
          writeUint16(central, 0);
          writeUint16(central, 0);
          writeUint32(central, 0);
          writeUint32(central, offset);
          centralParts.push(new Uint8Array(central), name);

          offset += local.length + name.length + data.length;
        }}

        const centralSize = centralParts.reduce((sum, part) => sum + part.length, 0);
        const end = [];
        writeUint32(end, 0x06054b50);
        writeUint16(end, 0);
        writeUint16(end, 0);
        writeUint16(end, files.length);
        writeUint16(end, files.length);
        writeUint32(end, centralSize);
        writeUint32(end, offset);
        writeUint16(end, 0);

        return new Blob([...localParts, ...centralParts, new Uint8Array(end)], {{ type: "application/zip" }});
      }}

      async function downloadEditedZip(event) {{
        event.preventDefault();
        if (downloadLink.classList.contains("disabled") || !currentResults.length) return;

        try {{
          disableDownload();
          setStatus("正在打包下载");
          const names = makeUniqueFilenames(getEditedOutputNames());
          const zipBlob = await createZip(currentResults.map((result, index) => ({{ name: names[index], blob: result.blob }})));
          const objectUrl = URL.createObjectURL(zipBlob);
          const temporaryLink = document.createElement("a");
          temporaryLink.href = objectUrl;
          temporaryLink.download = `${{safeStem(baseNameInput.value, "product")}}.zip`;
          document.body.appendChild(temporaryLink);
          temporaryLink.click();
          temporaryLink.remove();
          URL.revokeObjectURL(objectUrl);
          setStatus("ZIP 已下载");
        }} catch (error) {{
          setStatus(error.message);
        }} finally {{
          enableDownload();
        }}
      }}

      const CRC_TABLE = (() => {{
        const table = new Uint32Array(256);
        for (let index = 0; index < 256; index += 1) {{
          let c = index;
          for (let bit = 0; bit < 8; bit += 1) {{
            c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
          }}
          table[index] = c >>> 0;
        }}
        return table;
      }})();

      productsInput.addEventListener("change", updateFileList);
      clearProductsButton.addEventListener("click", clearProducts);
      templateSelect.addEventListener("change", updateTemplatePreview);
      templateInput.addEventListener("change", uploadTemplate);
      processBtn.addEventListener("click", processImages);
      downloadLink.addEventListener("click", downloadEditedZip);

      dropzone.addEventListener("dragover", (event) => {{
        event.preventDefault();
        dropzone.classList.add("dragover");
      }});

      dropzone.addEventListener("dragleave", () => {{
        dropzone.classList.remove("dragover");
      }});

      dropzone.addEventListener("drop", (event) => {{
        event.preventDefault();
        dropzone.classList.remove("dragover");
        if (event.dataTransfer?.files?.length) {{
          productsInput.files = event.dataTransfer.files;
          updateFileList();
        }}
      }});

      updateTemplatePreview();
    </script>
  </body>
</html>
"""


if __name__ == "__main__":
    main()
