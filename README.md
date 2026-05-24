# SayHi 图片模板融合工具

一个用于批量生成商品主图的 Web 服务：商品图铺底，透明 PNG 模板覆盖，输出 PNG 并打包 ZIP。

## 本地运行

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

打开 `http://127.0.0.1:8000`。

## Docker 部署

```bash
docker compose up -d --build
```

访问 `http://服务器IP:8000`。

## 离线单文件版

项目根目录的 `standalone.html` 是单文件离线版，可以直接发给别人使用。

- 不需要服务器，不需要安装 Python。
- 双击打开，或拖到浏览器里打开即可。
- 默认模板已经内置在 HTML 文件里。
- 商品图合成在浏览器 Canvas 里完成，批量结果会在浏览器端打包成 ZIP 下载。

如果默认模板更新了，重新生成离线版：

```bash
python scripts/build_standalone.py
```

## API

- `GET /`：Web 页面
- `GET /api/templates`：模板列表
- `POST /api/templates`：上传 PNG 模板
- `POST /api/process`：批量处理商品图

`/api/process` 表单字段：

- `products`：商品图文件，可多张
- `template_id`：模板 ID，默认 `default`
- `width`：输出宽度，默认 `1440`
- `height`：输出高度，默认 `1440`
- `background_color`：背景色，默认 `#ffffff`
- `base_name`：输出基础名称，默认 `product`
- `output_names`：可选 JSON 字符串数组，用于自定义每张 PNG 文件名
- `preview`：传 `true` 时返回 JSON 预览和 ZIP data URL；默认返回 ZIP 文件

商品图会等比缩放到输出画布中心 75% 的区域里。默认 `1440x1440` 时，商品图最大占用中心 `1080x1080`，不会裁切或拉伸。
