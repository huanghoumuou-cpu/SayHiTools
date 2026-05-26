from __future__ import annotations

import base64
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .auth import (
    clear_session_cookie,
    get_session_from_request,
    require_auth,
    set_session_cookie,
    verify_admin_credentials,
)
from .image_tools import (
    build_result_zip,
    build_single_preview,
    ensure_default_template,
    list_templates,
    resolve_template_path,
    save_uploaded_template,
)


APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
DATA_DIR = Path(os.getenv("SAYHI_DATA_DIR", PROJECT_DIR / "data")).resolve()
TEMPLATES_DIR = DATA_DIR / "templates"
BUNDLED_TEMPLATE = APP_DIR / "assets" / "default-template.png"
STATIC_DIR = APP_DIR / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_default_template(TEMPLATES_DIR, BUNDLED_TEMPLATE)
    yield


app = FastAPI(title="SayHi 图片模板融合工具", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_model=None)
def index(request: Request) -> FileResponse | RedirectResponse:
    if get_session_from_request(request) is None:
        return RedirectResponse(url="/login", status_code=303)
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/login", response_model=None)
def login_page(request: Request) -> FileResponse | RedirectResponse:
    if get_session_from_request(request) is not None:
        return RedirectResponse(url="/", status_code=303)
    return FileResponse(STATIC_DIR / "login.html")


@app.post("/api/login")
async def api_login(
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> dict[str, object]:
    config = verify_admin_credentials(username, password)
    set_session_cookie(response, config)
    return {"authenticated": True}


@app.post("/api/logout")
async def api_logout(response: Response) -> dict[str, object]:
    clear_session_cookie(response)
    return {"authenticated": False}


@app.get("/api/session")
def api_session(request: Request) -> dict[str, object]:
    session = get_session_from_request(request)
    return {"authenticated": session is not None, "username": session.username if session else None}


@app.get("/api/templates")
def api_templates(_: Annotated[object, Depends(require_auth)]) -> dict[str, list[dict[str, object]]]:
    return {"templates": [template.__dict__ for template in list_templates(TEMPLATES_DIR)]}


@app.get("/api/templates/{template_id}/preview")
def api_template_preview(template_id: str, _: Annotated[object, Depends(require_auth)]) -> FileResponse:
    path = resolve_template_path(TEMPLATES_DIR, template_id)
    return FileResponse(path, media_type="image/png")


@app.post("/api/templates")
async def api_upload_template(
    template: Annotated[UploadFile, File(description="PNG 模板图片")],
    _: Annotated[object, Depends(require_auth)],
) -> dict[str, object]:
    info = await save_uploaded_template(TEMPLATES_DIR, template)
    return {"template": info.__dict__}


@app.post("/api/process-one")
async def api_process_one(
    product: Annotated[UploadFile, File(description="单张商品主图")],
    template_id: Annotated[str, Form()] = "default",
    width: Annotated[int, Form()] = 1440,
    height: Annotated[int, Form()] = 1440,
    base_name: Annotated[str, Form()] = "product",
    index: Annotated[int, Form()] = 1,
    background_color: Annotated[str, Form()] = "#ffffff",
    _: Annotated[object, Depends(require_auth)] = None,
) -> dict[str, object]:
    template_path = resolve_template_path(TEMPLATES_DIR, template_id)
    preview = await build_single_preview(
        product=product,
        template_path=template_path,
        width=width,
        height=height,
        base_name=base_name,
        index=index,
        background_color=background_color,
    )
    return {"preview": preview}


@app.post("/api/process", response_model=None)
async def api_process(
    products: Annotated[list[UploadFile], File(description="商品主图，可批量上传")],
    template_id: Annotated[str, Form()] = "default",
    width: Annotated[int, Form()] = 1440,
    height: Annotated[int, Form()] = 1440,
    base_name: Annotated[str, Form()] = "product",
    background_color: Annotated[str, Form()] = "#ffffff",
    output_names: Annotated[str | None, Form()] = None,
    preview: Annotated[bool, Form()] = False,
    _: Annotated[object, Depends(require_auth)] = None,
):
    parsed_output_names = None
    if output_names:
        try:
            parsed_output_names = json.loads(output_names)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="output_names must be a JSON array") from exc
        if not isinstance(parsed_output_names, list) or not all(isinstance(item, str) for item in parsed_output_names):
            raise HTTPException(status_code=400, detail="output_names must be a JSON array of strings")

    template_path = resolve_template_path(TEMPLATES_DIR, template_id)
    zip_name, zip_bytes, previews = await build_result_zip(
        products=products,
        template_path=template_path,
        width=width,
        height=height,
        base_name=base_name,
        background_color=background_color,
        output_names=parsed_output_names,
    )
    if preview:
        return JSONResponse(
            {
                "zip_filename": zip_name,
                "zip_data_url": "data:application/zip;base64," + base64.b64encode(zip_bytes).decode("ascii"),
                "previews": previews,
                "count": len(products),
            }
        )
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
