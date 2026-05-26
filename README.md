# SayHiTools

SayHiTools 是一个面向商品主图批量处理的图片模板融合工具。它支持上传多张商品图，选择或上传透明 PNG 模板，设置输出尺寸、背景色和文件名，并生成可预览、可下载的 PNG/ZIP 结果。

项目包含两种使用方式：

- **Web 服务版**：基于 FastAPI + Pillow，适合部署到服务器并通过域名访问。
- **离线 HTML 版**：单个 `standalone.html` 文件即可使用，适合发给别人本地处理图片。

## 功能特性

- 批量上传商品主图，支持 `PNG`、`JPG`、`JPEG`、`WebP`。
- 默认内置 SayHi 透明模板，也可以上传新的 PNG 模板。
- 商品图自动等比缩放，不裁切、不拉伸。
- 默认输出画布为 `1440 x 1440`。
- 商品图默认只占画布中心 `75%` 区域，即 `1440 x 1440` 画布中商品最大放入中心 `1080 x 1080`。
- 支持选择背景色，默认白色。
- 支持处理前预览商品图，处理后预览生成结果。
- 支持为每张输出图片单独编辑文件名。
- 支持批量处理进度提示，展示当前处理第几张、总共多少张。
- 支持三种处理方式：本机处理、服务器处理、混合加速。
- 支持浏览器端打包 ZIP 下载，避免下载时重复处理图片。
- 支持无数据库单管理员登录，登录状态在同一浏览器保留 7 天。
- 前端包含轻量动效：页面进入、面板错落、结果卡片 reveal 和交互反馈。

## 图片合成规则

处理流程固定为三层：

1. 创建指定尺寸的 RGBA 画布。
2. 使用用户选择的背景色填充画布，默认 `#ffffff`。
3. 将商品图等比缩放到画布中心 75% 区域内，居中放置。
4. 将透明 PNG 模板按输出尺寸等比适配并覆盖到最上层。
5. 输出 PNG 图片。

默认情况下：

- 输出尺寸：`1440 x 1440`
- 商品图最大显示区域：`1080 x 1080`
- 商品图位置：画布中心
- 输出格式：`PNG`

## 处理方式

Web 版支持在“开始处理”按钮旁边选择处理方式：

| 模式 | 说明 | 适合场景 |
| --- | --- | --- |
| 本机处理 | 使用浏览器 Canvas 在用户电脑上合成图片，商品图不上传到服务器 | 减轻服务器压力，适合大多数电脑用户 |
| 服务器处理 | 上传商品图到服务器，由 FastAPI + Pillow 处理 | 适合用户设备性能较弱或浏览器兼容性异常时 |
| 混合加速 | 本机和服务器同时处理同一批任务，不同图片分配给不同 worker | 适合批量较多、希望尽量加快处理速度时 |

不论选择哪种模式，输出规则保持一致：商品图居中等比缩放，模板透明叠加，最终导出 PNG。

## 技术栈

- 后端：Python、FastAPI、Pillow
- 前端：HTML、CSS、原生 JavaScript
- 图片处理：Pillow 后端处理，Canvas 离线版处理
- 登录保护：HMAC 签名 HttpOnly Cookie
- 部署：Docker、docker-compose、Nginx 反向代理

## 项目结构

```text
.
├── app/
│   ├── main.py                 # FastAPI 入口与 API 路由
│   ├── auth.py                 # 单管理员登录与签名 Cookie
│   ├── image_tools.py          # 图片合成核心逻辑
│   ├── assets/
│   │   └── default-template.png
│   └── static/
│       ├── index.html          # Web 页面
│       ├── styles.css          # 页面样式
│       └── app.js              # 前端交互与批量处理逻辑
├── data/
│   └── templates/
│       └── default.png         # 默认模板
├── scripts/
│   └── build_standalone.py     # 生成离线单文件 HTML
├── tests/
│   └── test_image_tools.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── standalone.html             # 离线版
└── README.md
```

## 本地运行

### 1. 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 启动服务

先配置管理员账号。Windows PowerShell：

```powershell
$env:SAYHI_ADMIN_USERNAME="admin"
$env:SAYHI_ADMIN_PASSWORD="your-password"
$env:SAYHI_SESSION_SECRET="replace-with-a-long-random-secret"
$env:SAYHI_COOKIE_SECURE="false"
```

macOS / Linux：

```bash
export SAYHI_ADMIN_USERNAME=admin
export SAYHI_ADMIN_PASSWORD=your-password
export SAYHI_SESSION_SECRET=replace-with-a-long-random-secret
export SAYHI_COOKIE_SECURE=false
```

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

浏览器打开：

```text
http://127.0.0.1:8000
```

## Docker 部署

复制环境变量模板并修改真实值：

```bash
cp .env.example .env
```

生产环境建议：

- `SAYHI_ADMIN_PASSWORD` 使用强密码。
- `SAYHI_SESSION_SECRET` 使用长随机字符串。
- HTTPS 域名访问时将 `SAYHI_COOKIE_SECURE=true`。

### 1. 构建并启动

Docker Compose V2：

```bash
docker compose up -d --build
```

Docker Compose V1：

```bash
docker-compose up -d --build
```

### 2. 查看运行状态

```bash
docker ps
```

正常情况下可以看到服务监听：

```text
0.0.0.0:8000->8000/tcp
```

### 3. 本机验证

```bash
curl -I http://127.0.0.1:8000/
curl http://127.0.0.1:8000/login | head
```

未登录访问 `/` 会返回跳转到 `/login`，登录页能返回 HTML 内容即说明服务已经启动成功。

## 服务器更新流程

如果项目已经部署在服务器 `/opt/sayhitool`，更新新版代码后可以执行：

```bash
cd /opt/sayhitool
docker-compose build
docker-compose down
docker-compose up -d
docker ps
```

如果服务器使用较老的 `docker-compose 1.29.x`，偶尔出现 `KeyError: 'ContainerConfig'`，可以先清理旧容器再启动：

```bash
cd /opt/sayhitool
docker-compose down
docker rm -f sayhi-image-tool 2>/dev/null || true
docker-compose up -d
```

## 国内服务器构建加速

如果服务器在国内，建议 Dockerfile 使用国内 PyPI 源安装依赖：

```dockerfile
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt
```

这样可以避免每次构建时下载 Python 依赖过慢。

## Nginx 反向代理示例

如果希望通过域名访问，例如 `sayhi.example.com`，可以使用 Nginx 反向代理到本地 `8000` 端口：

```nginx
server {
    listen 80;
    server_name sayhi.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

修改后检查并重载 Nginx：

```bash
nginx -t
systemctl reload nginx
```

HTTPS 可以使用 Certbot 配置：

```bash
certbot --nginx -d sayhi.example.com
```

## 登录保护

Web 服务版默认需要登录后使用。登录状态保存在浏览器的 `HttpOnly Cookie` 中，有效期 7 天。

- 不使用数据库、Redis 或 IP 绑定。
- 只有一个管理员账号。
- 支持多个设备同时登录。
- 每个浏览器独立保存登录状态。
- 新设备登录不会让旧设备下线。
- 清除 Cookie、换浏览器、换设备或超过 7 天后需要重新登录。

登录相关接口：

- `GET /login`：登录页面
- `POST /api/login`：管理员登录
- `POST /api/logout`：退出登录
- `GET /api/session`：查询当前登录状态

## 离线 HTML 版

`standalone.html` 是离线单文件版，可以直接发给别人使用：

- 不需要服务器。
- 不需要安装 Python。
- 默认模板已经内置。
- 双击打开，或拖到浏览器中打开即可使用。
- 图片合成和 ZIP 打包都在浏览器本地完成。

如果默认模板或前端逻辑更新了，可以重新生成离线版：

```bash
python scripts/build_standalone.py
```

## API 说明

除 `/api/login` 和 `/api/session` 外，Web 版 API 均需要登录 Cookie。

### `GET /`

已登录时返回 Web 工具页面，未登录时跳转到 `/login`。

### `GET /api/templates`

返回模板列表。

### `GET /api/templates/{template_id}/preview`

返回指定模板的预览图片。

### `POST /api/templates`

上传新的透明 PNG 模板。

表单字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `template` | file | PNG 模板文件 |
| `name` | string | 模板名称，可选 |

### `POST /api/process-one`

处理单张商品图。前端批量处理时会并发调用该接口，以便显示更清晰的进度。

表单字段：

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `product` | file | - | 商品主图 |
| `template_id` | string | `default` | 模板 ID |
| `width` | int | `1440` | 输出宽度 |
| `height` | int | `1440` | 输出高度 |
| `background_color` | string | `#ffffff` | 背景色 |
| `output_name` | string | `product_001` | 输出文件名 |

返回 JSON，包含生成图片的文件名和 Data URL。

### `POST /api/process`

批量处理商品图，保留给兼容场景使用。

表单字段：

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `products` | file[] | - | 商品图文件，可多张 |
| `template_id` | string | `default` | 模板 ID |
| `width` | int | `1440` | 输出宽度 |
| `height` | int | `1440` | 输出高度 |
| `background_color` | string | `#ffffff` | 背景色 |
| `base_name` | string | `product` | 批量输出基础名称 |
| `output_names` | string | - | JSON 字符串数组，用于自定义每张图片名称 |
| `preview` | bool | `false` | 为 `true` 时返回 JSON 预览数据 |

默认返回 ZIP 文件。

## 测试

运行测试：

```bash
pytest
```

测试重点：

- 商品图缩放到中心区域，不裁切。
- 透明模板正确覆盖。
- 输出尺寸符合设置。
- 批量命名按序生成。

## 注意事项

- 首版输出格式固定为 PNG。
- 用户上传的商品图不会作为历史记录长期保存。
- 上传的新模板会保存到 `data/templates/`。
- 如果部署到公网，建议配合 Nginx、HTTPS 和服务器防火墙使用。

## License

未指定开源许可证。公开使用或二次分发前，请先确认项目所有者的授权要求。
