# get-biji-export

把 Get 笔记（biji）的笔记数据同步到本地（Mongita），并支持导出为 Markdown。

## 功能

- 一条命令启动：缺少登录态 token 时自动打开浏览器登录；回车后自动抓取并写入本地 `.env`，然后继续爬取。
- 拉取笔记列表：`GET https://get-notes.luojilab.com/voicenotes/web/notes`
- （默认开启）对 `note_type=link` 的笔记追加拉取详情：`GET /voicenotes/web/notes/{id}/links/detail`
- 本地存储：默认写入 Mongita（可选从旧 JSONL 迁移）
- 导出：从 Mongita 导出到 Markdown（YAML front matter + 正文内容）

## 环境要求

- Python 3.11+
- `uv`（依赖管理与运行）
- Chrome / Chromium（用于首次登录抓取 token）

## 安装

```bash
uv sync --extra dev
```

## 运行爬虫（推荐）

```bash
uv run run_biji_notes_spider.py
```

首次运行流程：

1. 尝试从当前目录 `.env` 读取 `BIJI_BEARER_TOKEN` / `BIJI_REFRESH_TOKEN`。
2. 若缺少，会自动打开浏览器进入登录页（默认 `https://www.biji.com/note`），你手动完成登录。
3. 回到终端按回车，脚本会从页面 `localStorage` 抓取 `token/refresh_token` 写入 `.env`，随后自动关闭浏览器并继续爬取。

> 建议优先使用 `BIJI_REFRESH_TOKEN`，脚本会自动换取/刷新 access token。

## 数据存储（默认 Mongita）

默认写入本地 Mongita 数据库（嵌入式、无需启动服务）：

- 数据目录：`data/mongita/`（可用 `BIJI_MONGITA_DIR` 修改）
- 数据库名：`biji`（可用 `BIJI_MONGITA_DB` 修改）
- 集合（相当于“三张表”）：
  - `notes`：列表接口返回的笔记（可用 `BIJI_MONGITA_NOTES_COLLECTION` 修改）
  - `details`：仅 `note_type=link` 的详情（可用 `BIJI_MONGITA_DETAILS_COLLECTION` 修改）
  - `misc`：迁移/其它杂项记录（可用 `BIJI_MONGITA_MISC_COLLECTION` 修改）

> 说明：`details` 只对应 link 类型笔记，所以数量通常会小于 `notes`。

## 导出 Markdown

```bash
uv run scripts/export_mongita_to_markdown.py --out data/markdown
```

导出规则：

- 每条笔记一个 `.md`
- 头部为 YAML front matter（title / note_id / url / tags / created_at / updated_at 等）
- 正文优先使用 `details.raw.content`，没有 detail 时回退到 `notes.raw.content/body_text/json_content`
- tag 处理：任意空白会被替换为 `_`（确保 tag 无空格）
- 文件名默认使用 `title`，如重名会自动追加 `note_id` 避免覆盖

只导出有详情的笔记（通常是 link）：

```bash
uv run scripts/export_mongita_to_markdown.py --only-details
```

## 迁移旧 JSONL 到 Mongita

```bash
uv run scripts/migrate_jsonl_to_mongita.py --jsonl data/notes.jsonl --mongita-dir data/mongita
```

## 单独抓取登录态（可选）

如果你只想先把 token 写入 `.env`：

```bash
uv run scripts/capture_biji_env.py --env .env
```

## 常用配置（`.env`）

以下键均可写入 `.env`（已在 `.gitignore` 忽略，避免误提交）：

- `BIJI_REFRESH_TOKEN`：优先使用 refresh_token 自动换取 access token
- `BIJI_BEARER_TOKEN`：直接使用 access token
- `BIJI_LIMIT`：列表分页大小，默认 `100`
- `BIJI_SINCE_ID`：起始 `since_id`，默认空
- `BIJI_SORT`：默认 `create_desc`
- `BIJI_FETCH_DETAIL`：是否拉取 link detail，默认 `1`；设为 `0` 关闭
- `BIJI_MONGITA_DIR`：默认 `data/mongita`
- `BIJI_MONGITA_DB`：默认 `biji`
- `BIJI_MONGITA_NOTES_COLLECTION`：默认 `notes`
- `BIJI_MONGITA_DETAILS_COLLECTION`：默认 `details`
- `BIJI_MONGITA_MISC_COLLECTION`：默认 `misc`

## 开发与测试

```bash
uv run pytest -q
```

## 安全提示

- 不要把 token/refresh_token 写进代码或提交到 git；只放在本地 `.env`。
- `.env*`、`data/`、`tmp/` 均已在 `.gitignore` 中忽略。
