from __future__ import annotations

import base64
import io
import re
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError


Image.MAX_IMAGE_PIXELS = 60_000_000

SUPPORTED_INPUT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 25 * 1024 * 1024
MAX_BATCH_SIZE = 50
MIN_OUTPUT_SIZE = 64
MAX_OUTPUT_SIZE = 5000
PRODUCT_AREA_RATIO = 0.75


@dataclass(frozen=True)
class TemplateInfo:
    id: str
    name: str
    is_default: bool
    preview_url: str


def safe_stem(value: str, fallback: str = "output") -> str:
    stem = Path(value).stem.strip()
    stem = re.sub(r"[^\w.-]+", "_", stem, flags=re.UNICODE).strip("._-")
    return stem[:80] or fallback


def safe_png_filename(value: str, fallback: str) -> str:
    stem = safe_stem(value, fallback=fallback)
    return f"{stem}.png"


def output_filename_for_index(base_name: str, index: int) -> str:
    return f"{safe_stem(base_name, fallback='product')}_{index:03d}.png"


def make_unique_filename(filename: str, used: set[str]) -> str:
    stem = safe_stem(filename, fallback="product")
    candidate = f"{stem}.png"
    suffix = 2
    while candidate.lower() in used:
        candidate = f"{stem}_{suffix}.png"
        suffix += 1
    used.add(candidate.lower())
    return candidate


def build_output_filenames(base_name: str, count: int, output_names: list[str] | None = None) -> list[str]:
    used: set[str] = set()
    filenames: list[str] = []
    for index in range(1, count + 1):
        fallback = output_filename_for_index(base_name, index)
        requested = output_names[index - 1] if output_names and index <= len(output_names) else fallback
        filenames.append(make_unique_filename(requested or fallback, used))
    return filenames


def ensure_default_template(data_templates_dir: Path, bundled_template: Path) -> None:
    data_templates_dir.mkdir(parents=True, exist_ok=True)
    target = data_templates_dir / "default.png"
    if not target.exists() and bundled_template.exists():
        shutil.copyfile(bundled_template, target)


def list_templates(data_templates_dir: Path) -> list[TemplateInfo]:
    data_templates_dir.mkdir(parents=True, exist_ok=True)
    templates: list[TemplateInfo] = []
    for path in sorted(data_templates_dir.glob("*.png")):
        template_id = path.stem
        templates.append(
            TemplateInfo(
                id=template_id,
                name="默认模板" if template_id == "default" else template_id,
                is_default=template_id == "default",
                preview_url=f"/api/templates/{template_id}/preview",
            )
        )
    templates.sort(key=lambda item: (not item.is_default, item.name.lower()))
    return templates


def resolve_template_path(data_templates_dir: Path, template_id: str) -> Path:
    clean_id = safe_stem(template_id, fallback="default")
    path = (data_templates_dir / f"{clean_id}.png").resolve()
    root = data_templates_dir.resolve()
    if root not in path.parents or not path.exists():
        raise HTTPException(status_code=404, detail="模板不存在")
    return path


async def save_uploaded_template(data_templates_dir: Path, upload: UploadFile) -> TemplateInfo:
    raw = await read_upload_bytes(upload, allowed_extensions={".png"})
    image = open_image(raw, upload.filename or "template.png").convert("RGBA")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    stem = safe_stem(upload.filename or "template", fallback="template")
    template_id = f"{stem}_{timestamp}"
    target = data_templates_dir / f"{template_id}.png"
    image.save(target, format="PNG")
    return TemplateInfo(
        id=template_id,
        name=template_id,
        is_default=False,
        preview_url=f"/api/templates/{template_id}/preview",
    )


async def read_upload_bytes(
    upload: UploadFile,
    allowed_extensions: set[str] = SUPPORTED_INPUT_EXTENSIONS,
) -> bytes:
    filename = upload.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise HTTPException(status_code=400, detail=f"不支持的文件格式：{filename or '未命名文件'}，仅支持 {allowed}")
    raw = await upload.read()
    if not raw:
        raise HTTPException(status_code=400, detail=f"文件为空：{filename or '未命名文件'}")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail=f"文件过大：{filename}，单张最大 25MB")
    return raw


def open_image(raw: bytes, filename: str) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
        return image
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail=f"无法读取图片：{filename}") from exc


def validate_output_size(width: int, height: int) -> None:
    if not (MIN_OUTPUT_SIZE <= width <= MAX_OUTPUT_SIZE and MIN_OUTPUT_SIZE <= height <= MAX_OUTPUT_SIZE):
        raise HTTPException(
            status_code=400,
            detail=f"输出尺寸需在 {MIN_OUTPUT_SIZE}-{MAX_OUTPUT_SIZE}px 之间",
        )


def parse_background_color(value: str) -> tuple[int, int, int, int]:
    color = (value or "#ffffff").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        return (
            int(color[1:3], 16),
            int(color[3:5], 16),
            int(color[5:7], 16),
            255,
        )
    raise HTTPException(status_code=400, detail="背景色必须是 #RRGGBB 格式")


def product_area_size(width: int, height: int) -> tuple[int, int]:
    area_width = max(1, int(round(width * PRODUCT_AREA_RATIO)))
    area_height = max(1, int(round(height * PRODUCT_AREA_RATIO)))
    return area_width, area_height


def fit_product_on_canvas(
    product: Image.Image,
    width: int,
    height: int,
    background_color: tuple[int, int, int, int],
) -> Image.Image:
    canvas = Image.new("RGBA", (width, height), background_color)
    product_rgba = ImageOps.exif_transpose(product).convert("RGBA")
    fitted = ImageOps.contain(product_rgba, product_area_size(width, height), method=Image.Resampling.LANCZOS)
    offset = ((width - fitted.width) // 2, (height - fitted.height) // 2)
    canvas.alpha_composite(fitted, dest=offset)
    return canvas


def resize_template(template: Image.Image, width: int, height: int) -> Image.Image:
    template_rgba = ImageOps.exif_transpose(template).convert("RGBA")
    return template_rgba.resize((width, height), Image.Resampling.LANCZOS)


def compose_product_with_template(
    product_raw: bytes,
    product_filename: str,
    template: Image.Image,
    width: int,
    height: int,
    background_color: tuple[int, int, int, int],
) -> bytes:
    product = open_image(product_raw, product_filename)
    canvas = fit_product_on_canvas(product, width, height, background_color)
    overlay = resize_template(template, width, height)
    canvas.alpha_composite(overlay)
    output = io.BytesIO()
    canvas.save(output, format="PNG", optimize=True)
    return output.getvalue()


async def build_result_zip(
    products: Iterable[UploadFile],
    template_path: Path,
    width: int,
    height: int,
    base_name: str,
    background_color: str = "#ffffff",
    output_names: list[str] | None = None,
) -> tuple[str, bytes, list[dict[str, str]]]:
    product_list = list(products)
    if not product_list:
        raise HTTPException(status_code=400, detail="请至少上传一张商品图")
    if len(product_list) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"一次最多处理 {MAX_BATCH_SIZE} 张商品图")

    validate_output_size(width, height)
    parsed_background = parse_background_color(background_color)
    clean_base = safe_stem(base_name, fallback="product")
    output_filenames = build_output_filenames(clean_base, len(product_list), output_names)
    template = Image.open(template_path)
    template.load()

    zip_buffer = io.BytesIO()
    previews: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for index, product in enumerate(product_list, start=1):
            raw = await read_upload_bytes(product)
            filename = output_filenames[index - 1]
            png_bytes = compose_product_with_template(
                product_raw=raw,
                product_filename=product.filename or filename,
                template=template,
                width=width,
                height=height,
                background_color=parsed_background,
            )
            zip_file.writestr(filename, png_bytes)
            previews.append(
                {
                    "filename": filename,
                    "data_url": "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii"),
                }
            )

    zip_name = f"{clean_base}.zip"
    return zip_name, zip_buffer.getvalue(), previews


async def build_single_preview(
    product: UploadFile,
    template_path: Path,
    width: int,
    height: int,
    base_name: str,
    index: int,
    background_color: str = "#ffffff",
) -> dict[str, str]:
    validate_output_size(width, height)
    parsed_background = parse_background_color(background_color)
    template = Image.open(template_path)
    template.load()
    raw = await read_upload_bytes(product)
    filename = output_filename_for_index(base_name, max(index, 1))
    png_bytes = compose_product_with_template(
        product_raw=raw,
        product_filename=product.filename or filename,
        template=template,
        width=width,
        height=height,
        background_color=parsed_background,
    )
    return {
        "filename": filename,
        "data_url": "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii"),
    }
