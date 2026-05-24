import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def make_png(size=(320, 240), color=(20, 80, 140, 255)):
    buffer = io.BytesIO()
    Image.new("RGBA", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def make_template(size=(1440, 1440)):
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    for x in range(0, size[0], 30):
        for y in range(0, 80):
            image.putpixel((x, y), (255, 0, 0, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "default.png").write_bytes(make_template())
    monkeypatch.setattr("app.main.TEMPLATES_DIR", templates_dir)
    return TestClient(app)


def test_process_single_image_returns_zip(client):
    response = client.post(
        "/api/process",
        data={"template_id": "default", "width": "800", "height": "800", "base_name": "demo"},
        files=[("products", ("toy.png", make_png(), "image/png"))],
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    archive = zipfile.ZipFile(io.BytesIO(response.content))
    assert archive.namelist() == ["demo_001.png"]
    output = Image.open(io.BytesIO(archive.read("demo_001.png")))
    assert output.size == (800, 800)


def test_product_is_scaled_into_center_area_and_background_color_is_used(client):
    response = client.post(
        "/api/process",
        data={
            "template_id": "default",
            "width": "1440",
            "height": "1440",
            "base_name": "area",
            "background_color": "#00ff00",
        },
        files=[("products", ("wide.png", make_png((2000, 1000), (20, 80, 140, 255)), "image/png"))],
    )

    assert response.status_code == 200
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    output = Image.open(io.BytesIO(archive.read("area_001.png"))).convert("RGBA")

    assert output.size == (1440, 1440)
    assert output.getpixel((10, 720)) == (0, 255, 0, 255)
    assert output.getpixel((720, 720)) == (20, 80, 140, 255)


def test_process_preview_returns_images_and_zip(client):
    response = client.post(
        "/api/process",
        data={"template_id": "default", "width": "1440", "height": "1440", "base_name": "batch", "preview": "true"},
        files=[
            ("products", ("one.png", make_png(), "image/png")),
            ("products", ("two.png", make_png((200, 400)), "image/png")),
        ],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["zip_filename"] == "batch.zip"
    assert data["count"] == 2
    assert [item["filename"] for item in data["previews"]] == ["batch_001.png", "batch_002.png"]
    assert data["zip_data_url"].startswith("data:application/zip;base64,")


def test_process_one_returns_single_preview(client):
    response = client.post(
        "/api/process-one",
        data={"template_id": "default", "width": "800", "height": "800", "base_name": "single", "index": "3"},
        files={"product": ("toy.png", make_png(), "image/png")},
    )

    assert response.status_code == 200
    preview = response.json()["preview"]
    assert preview["filename"] == "single_003.png"
    assert preview["data_url"].startswith("data:image/png;base64,")


def test_output_names_can_be_customized(client):
    response = client.post(
        "/api/process",
        data={
            "template_id": "default",
            "width": "800",
            "height": "800",
            "base_name": "batch",
            "output_names": '["front.png", "front.png"]',
        },
        files=[
            ("products", ("one.png", make_png(), "image/png")),
            ("products", ("two.png", make_png(), "image/png")),
        ],
    )

    assert response.status_code == 200
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    assert archive.namelist() == ["front.png", "front_2.png"]


def test_upload_template_adds_template(client):
    response = client.post(
        "/api/templates",
        files={"template": ("new-template.png", make_template(), "image/png")},
    )

    assert response.status_code == 200
    template_id = response.json()["template"]["id"]

    list_response = client.get("/api/templates")
    assert any(item["id"] == template_id for item in list_response.json()["templates"])
