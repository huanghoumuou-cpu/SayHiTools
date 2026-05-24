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
const progressPanel = document.querySelector("#progressPanel");
const progressText = document.querySelector("#progressText");
const progressCount = document.querySelector("#progressCount");
const progressBar = document.querySelector("#progressBar");
const previewGrid = document.querySelector("#previewGrid");
const downloadLink = document.querySelector("#downloadLink");
const processModeInputs = Array.from(document.querySelectorAll('input[name="processMode"]'));

let selectedProductFiles = [];
let generatedPreviews = [];
const PROCESS_CONCURRENCY = 3;
const PRODUCT_AREA_RATIO = 0.75;
const CRC_TABLE = buildCrcTable();

function setStatus(message) {
  statusText.textContent = message;
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function revokeObjectUrl(element) {
  if (element.dataset.objectUrl) {
    URL.revokeObjectURL(element.dataset.objectUrl);
    delete element.dataset.objectUrl;
  }
}

function setProductInputFiles(files) {
  const transfer = new DataTransfer();
  files.forEach((file) => transfer.items.add(file));
  productsInput.files = transfer.files;
}

function clearResultState(message = "等待处理") {
  hideProgress();
  generatedPreviews = [];
  disableDownload();
  previewGrid.className = "preview-grid empty";
  previewGrid.innerHTML = "<span>处理完成后显示预览</span>";
  setStatus(message);
}

function showProgress(total) {
  progressPanel.hidden = false;
  progressText.textContent = "准备处理";
  progressCount.textContent = `0 / ${total}`;
  progressBar.style.width = "0%";
}

function updateProgress(current, total, filename) {
  progressPanel.hidden = false;
  progressText.textContent = `已完成 ${current} 张，正在处理：${filename}`;
  progressCount.textContent = `${current} / ${total}`;
  progressBar.style.width = `${Math.round((current / total) * 100)}%`;
}

function hideProgress() {
  progressPanel.hidden = true;
  progressText.textContent = "准备处理";
  progressCount.textContent = "0 / 0";
  progressBar.style.width = "0%";
}

function updateFileList() {
  const incomingFiles = Array.from(productsInput.files || []);
  if (!incomingFiles.length && selectedProductFiles.length) {
    setProductInputFiles(selectedProductFiles);
    return;
  }

  selectedProductFiles = incomingFiles;
  const files = selectedProductFiles;
  Array.from(fileList.querySelectorAll("img")).forEach(revokeObjectUrl);
  fileCount.textContent = files.length ? `${files.length} 个文件已选择` : "尚未选择文件";
  fileList.innerHTML = "";

  files.slice(0, 50).forEach((file) => {
    const item = document.createElement("div");
    item.className = "file-item product-file-item";

    const image = document.createElement("img");
    image.alt = file.name;
    image.src = URL.createObjectURL(file);
    image.onload = () => revokeObjectUrl(image);
    image.dataset.objectUrl = image.src;

    const meta = document.createElement("div");
    meta.className = "file-meta";
    meta.innerHTML = `<strong title="${file.name}">${file.name}</strong><span>${formatSize(file.size)}</span>`;

    item.append(image, meta);
    fileList.appendChild(item);
  });
  clearResultState(files.length ? "商品图已更新" : "等待处理");
}

function clearProducts() {
  Array.from(fileList.querySelectorAll("img")).forEach(revokeObjectUrl);
  selectedProductFiles = [];
  productsInput.value = "";
  fileCount.textContent = "尚未选择文件";
  fileList.innerHTML = "";
  clearResultState("已清空商品图");
}

async function loadTemplates(selectedId) {
  const response = await fetch("/api/templates");
  if (!response.ok) throw new Error("模板列表加载失败");
  const data = await response.json();
  templateSelect.innerHTML = "";
  data.templates.forEach((template) => {
    const option = document.createElement("option");
    option.value = template.id;
    option.textContent = template.name;
    templateSelect.appendChild(option);
  });
  if (selectedId) {
    templateSelect.value = selectedId;
  }
  updateTemplatePreview();
}

function updateTemplatePreview() {
  const id = templateSelect.value || "default";
  templatePreview.src = `/api/templates/${encodeURIComponent(id)}/preview?ts=${Date.now()}`;
}

async function uploadTemplate() {
  const file = templateInput.files?.[0];
  if (!file) return;
  const formData = new FormData();
  formData.append("template", file);
  setStatus("正在上传模板");
  const response = await fetch("/api/templates", {
    method: "POST",
    body: formData,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "模板上传失败");
  }
  await loadTemplates(data.template.id);
  templateInput.value = "";
  setStatus("模板已上传");
}

function validateForm() {
  const files = Array.from(productsInput.files || []);
  if (!files.length && selectedProductFiles.length) {
    setProductInputFiles(selectedProductFiles);
    return validateForm();
  }
  if (!files.length) throw new Error("请先选择商品主图");
  const width = Number(widthInput.value);
  const height = Number(heightInput.value);
  if (!Number.isInteger(width) || !Number.isInteger(height) || width < 64 || height < 64 || width > 5000 || height > 5000) {
    throw new Error("输出宽高需要在 64 到 5000 之间");
  }
  return { files, width, height };
}

function buildProcessFormData({ preview, outputNames } = { preview: true }) {
  const { files, width, height } = validateForm();
  const formData = new FormData();
  files.forEach((file) => formData.append("products", file));
  formData.append("template_id", templateSelect.value || "default");
  formData.append("width", String(width));
  formData.append("height", String(height));
  formData.append("background_color", backgroundColorInput.value || "#ffffff");
  formData.append("base_name", baseNameInput.value || "product");
  formData.append("preview", preview ? "true" : "false");
  if (outputNames) {
    formData.append("output_names", JSON.stringify(outputNames));
  }
  return formData;
}

function buildSingleProcessFormData(file, index, width, height) {
  const formData = new FormData();
  formData.append("product", file);
  formData.append("template_id", templateSelect.value || "default");
  formData.append("width", String(width));
  formData.append("height", String(height));
  formData.append("background_color", backgroundColorInput.value || "#ffffff");
  formData.append("base_name", baseNameInput.value || "product");
  formData.append("index", String(index));
  return formData;
}

function getProcessMode() {
  return processModeInputs.find((input) => input.checked)?.value || "local";
}

function safeStem(value, fallback = "product") {
  return String(value || fallback)
    .replace(/\.[^.]+$/i, "")
    .trim()
    .replace(/[^\w.-]+/g, "_")
    .replace(/^[._-]+|[._-]+$/g, "")
    .slice(0, 80) || fallback;
}

function outputFilenameForIndex(index) {
  const stem = safeStem(baseNameInput.value, "product");
  return `${stem}_${String(index).padStart(3, "0")}.png`;
}

function loadImage(source) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    let objectUrl = "";
    image.onload = () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      resolve(image);
    };
    image.onerror = () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      reject(new Error("图片读取失败"));
    };
    if (source instanceof Blob) {
      objectUrl = URL.createObjectURL(source);
      image.src = objectUrl;
    } else {
      image.src = source;
    }
  });
}

async function loadTemplateImageForLocal() {
  const id = templateSelect.value || "default";
  return loadImage(`/api/templates/${encodeURIComponent(id)}/preview?ts=${Date.now()}`);
}

async function canvasToPngDataUrl(canvas) {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    }, "image/png");
  });
}

async function processLocalImage(file, index, width, height, templateImage) {
  const productImage = await loadImage(file);
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;

  const context = canvas.getContext("2d");
  context.fillStyle = backgroundColorInput.value || "#ffffff";
  context.fillRect(0, 0, width, height);

  const areaWidth = Math.max(1, Math.round(width * PRODUCT_AREA_RATIO));
  const areaHeight = Math.max(1, Math.round(height * PRODUCT_AREA_RATIO));
  const scale = Math.min(areaWidth / productImage.naturalWidth, areaHeight / productImage.naturalHeight);
  const drawWidth = Math.round(productImage.naturalWidth * scale);
  const drawHeight = Math.round(productImage.naturalHeight * scale);
  const productX = Math.round((width - drawWidth) / 2);
  const productY = Math.round((height - drawHeight) / 2);

  context.drawImage(productImage, productX, productY, drawWidth, drawHeight);
  context.drawImage(templateImage, 0, 0, width, height);

  return {
    filename: outputFilenameForIndex(index),
    data_url: await canvasToPngDataUrl(canvas),
  };
}

async function processServerImage(file, index, width, height) {
  const response = await fetch("/api/process-one", {
    method: "POST",
    body: buildSingleProcessFormData(file, index, width, height),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || `第 ${index} 张处理失败`);
  }
  return data.preview;
}

function renderResultPreviews(previews) {
  previewGrid.className = "preview-grid";
  previewGrid.innerHTML = "";
  previews.forEach((preview) => {
    const item = document.createElement("figure");
    item.className = "preview-item";

    const image = document.createElement("img");
    image.src = preview.data_url;
    image.alt = preview.filename;

    const input = document.createElement("input");
    input.className = "filename-input";
    input.type = "text";
    input.value = preview.filename.replace(/\.png$/i, "");
    input.setAttribute("aria-label", `${preview.filename} 的输出文件名`);

    item.append(image, input);
    previewGrid.appendChild(item);
  });
}

function getEditedOutputNames() {
  return Array.from(document.querySelectorAll(".filename-input")).map((input) => input.value.trim() || input.placeholder || "product");
}

function makeUniquePngNames(names) {
  const used = new Set();
  return names.map((name, index) => {
    const fallback = `product_${String(index + 1).padStart(3, "0")}`;
    const stem = String(name || fallback)
      .replace(/\.png$/i, "")
      .trim()
      .replace(/[^\w.-]+/g, "_")
      .replace(/^[._-]+|[._-]+$/g, "")
      .slice(0, 80) || fallback;
    let candidate = `${stem}.png`;
    let suffix = 2;
    while (used.has(candidate.toLowerCase())) {
      candidate = `${stem}_${suffix}.png`;
      suffix += 1;
    }
    used.add(candidate.toLowerCase());
    return candidate;
  });
}

function dataUrlToBytes(dataUrl) {
  const base64 = dataUrl.split(",", 2)[1] || "";
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function buildCrcTable() {
  const table = new Uint32Array(256);
  for (let index = 0; index < 256; index += 1) {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) {
      value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
    }
    table[index] = value >>> 0;
  }
  return table;
}

function crc32(bytes) {
  let crc = -1;
  for (let index = 0; index < bytes.length; index += 1) {
    crc = (crc >>> 8) ^ CRC_TABLE[(crc ^ bytes[index]) & 0xff];
  }
  return (crc ^ -1) >>> 0;
}

function writeUint16(output, value) {
  output.push(value & 0xff, (value >>> 8) & 0xff);
}

function writeUint32(output, value) {
  output.push(value & 0xff, (value >>> 8) & 0xff, (value >>> 16) & 0xff, (value >>> 24) & 0xff);
}

function zipDateParts(date = new Date()) {
  const time = (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2);
  const day = date.getDate();
  const month = date.getMonth() + 1;
  const year = Math.max(date.getFullYear() - 1980, 0);
  return { time, date: (year << 9) | (month << 5) | day };
}

function createZip(files) {
  const encoder = new TextEncoder();
  const localParts = [];
  const centralParts = [];
  const { time, date } = zipDateParts();
  let offset = 0;

  files.forEach((file) => {
    const data = file.bytes;
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
  });

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

  return new Blob([...localParts, ...centralParts, new Uint8Array(end)], { type: "application/zip" });
}

function enableDownload() {
  downloadLink.classList.remove("disabled");
  downloadLink.removeAttribute("aria-disabled");
}

function disableDownload() {
  downloadLink.classList.add("disabled");
  downloadLink.setAttribute("aria-disabled", "true");
}

async function processImages() {
  try {
    const { files, width, height } = validateForm();
    const processMode = getProcessMode();
    processBtn.disabled = true;
    disableDownload();
    showProgress(files.length);
    previewGrid.className = "preview-grid empty";
    previewGrid.innerHTML = "<span>正在处理，完成后显示预览</span>";
    setStatus(`正在生成 0 / ${files.length}`);

    const previews = new Array(files.length);
    const templateImage = processMode === "server" ? null : await loadTemplateImageForLocal();
    let nextIndex = 0;
    let completed = 0;

    async function runWorker(workerType) {
      while (nextIndex < files.length) {
        const offset = nextIndex;
        nextIndex += 1;
        const current = offset + 1;
        const label = workerType === "local" ? "本机" : "服务器";
        updateProgress(completed, files.length, `${label}：${files[offset].name}`);
        setStatus(`正在生成 ${completed} / ${files.length}`);

        previews[offset] = workerType === "local"
          ? await processLocalImage(files[offset], current, width, height, templateImage)
          : await processServerImage(files[offset], current, width, height);
        completed += 1;
        updateProgress(completed, files.length, `${label}：${files[offset].name}`);
        setStatus(`正在生成 ${completed} / ${files.length}`);
      }
    }

    const workers = [];
    if (processMode === "local") {
      const localCount = Math.min(2, files.length);
      workers.push(...Array.from({ length: localCount }, () => runWorker("local")));
    } else if (processMode === "server") {
      const serverCount = Math.min(PROCESS_CONCURRENCY, files.length);
      workers.push(...Array.from({ length: serverCount }, () => runWorker("server")));
    } else {
      const localCount = Math.min(1, files.length);
      const serverCount = Math.min(2, Math.max(files.length - localCount, 0));
      workers.push(...Array.from({ length: localCount }, () => runWorker("local")));
      workers.push(...Array.from({ length: serverCount }, () => runWorker("server")));
    }
    await Promise.all(workers);

    generatedPreviews = previews;
    renderResultPreviews(previews);
    downloadLink.dataset.zipFilename = `${baseNameInput.value || "product"}.zip`;
    enableDownload();
    setStatus(`已生成 ${files.length} 张图片，可编辑文件名后下载`);
  } catch (error) {
    previewGrid.className = "preview-grid empty";
    previewGrid.innerHTML = `<span>${error.message}</span>`;
    setStatus("处理失败");
  } finally {
    hideProgress();
    processBtn.disabled = false;
  }
}

async function downloadEditedZip(event) {
  event.preventDefault();
  if (downloadLink.classList.contains("disabled")) return;
  try {
    disableDownload();
    setStatus("正在打包下载");
    if (!generatedPreviews.length) {
      throw new Error("请先处理图片");
    }
    const names = makeUniquePngNames(getEditedOutputNames());
    const zipFiles = generatedPreviews.map((preview, index) => ({
      name: names[index],
      bytes: dataUrlToBytes(preview.data_url),
    }));
    const zipBlob = createZip(zipFiles);
    const objectUrl = URL.createObjectURL(zipBlob);
    const temporaryLink = document.createElement("a");
    temporaryLink.href = objectUrl;
    temporaryLink.download = downloadLink.dataset.zipFilename || `${baseNameInput.value || "product"}.zip`;
    document.body.appendChild(temporaryLink);
    temporaryLink.click();
    temporaryLink.remove();
    URL.revokeObjectURL(objectUrl);
    setStatus("ZIP 已下载");
  } catch (error) {
    setStatus(error.message);
  } finally {
    enableDownload();
  }
}

productsInput.addEventListener("change", updateFileList);
clearProductsButton.addEventListener("click", clearProducts);
templateSelect.addEventListener("change", updateTemplatePreview);
templateInput.addEventListener("change", () => uploadTemplate().catch((error) => setStatus(error.message)));
processBtn.addEventListener("click", processImages);
downloadLink.addEventListener("click", downloadEditedZip);

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragover");
  if (event.dataTransfer?.files?.length) {
    productsInput.files = event.dataTransfer.files;
    updateFileList();
  }
});

loadTemplates().catch((error) => setStatus(error.message));
