## get-biji-export

d0ublecl1ck，这是一个用于导出 Get 笔记（biji）数据的本地脚本项目。

### 功能

- 一条命令启动：如果本地没有可用的登录态 token，会自动打开浏览器让你登录；回车后自动抓取 token 写入 `.env`，并继续爬取。
- 拉取笔记列表：`GET https://get-notes.luojilab.com/voicenotes/web/notes`
- （默认开启）对 `note_type=link` 的笔记追加拉取详情：`GET /voicenotes/web/notes/{id}/links/detail`
- 导出到本地：默认写入 Mongita（可选 JSONL）

### 环境要求

- Python 3.11+
- `uv`（用于依赖管理与运行）

### 安装依赖

```bash
uv sync --extra dev
```

### 运行（推荐）

```bash
uv run run_biji_notes_spider.py
```

运行逻辑：

1. 尝试从当前目录 `.env` 读取 `BIJI_BEARER_TOKEN/BIJI_REFRESH_TOKEN`。
2. 如果缺少，会自动弹出浏览器打开 `https://www.biji.com/note`，你手动登录。
3. 回到终端按回车，脚本会从页面 `localStorage` 抓 `token/refresh_token` 并写入 `.env`，随后自动关闭浏览器继续爬取。

### 输出位置

#### Mongita（默认）

默认会写入本地 Mongita 数据库（嵌入式、无需启动服务）：

- 数据目录：`data/mongita/`（可用 `BIJI_MONGITA_DIR` 修改）
- 数据库名：`biji`（可用 `BIJI_MONGITA_DB` 修改）
- 两个集合（你要的“两张表”）：
  - `notes`：列表接口的笔记（可用 `BIJI_MONGITA_NOTES_COLLECTION` 修改）
  - `details`：link 笔记详情（可用 `BIJI_MONGITA_DETAILS_COLLECTION` 修改）
  - （可选）`misc`：其它杂项记录（可用 `BIJI_MONGITA_MISC_COLLECTION` 修改）

快速检查：

```bash
ls -la data/mongita
```

#### JSONL（可选）

如需写回 `data/notes.jsonl`，把 pipeline 切回 `crawler.pipelines.notes_jsonl_pipeline.NotesJsonlPipeline`（当前默认是 Mongita）。

### 常用配置（可选）

这些值可以写入 `.env`（已在 `.gitignore` 忽略，避免误提交）：

- `BIJI_REFRESH_TOKEN`：优先使用 refresh_token 自动换取 access token
- `BIJI_BEARER_TOKEN`：直接使用 access token（不推荐长期用）
- `BIJI_LIMIT`：列表分页大小，默认 `100`
- `BIJI_SINCE_ID`：起始 `since_id`，默认空
- `BIJI_SORT`：默认 `create_desc`
- `BIJI_FETCH_DETAIL`：是否拉取 link detail，默认 `1`；设为 `0` 关闭
- `BIJI_EXPORT_PATH`：仅 JSONL 导出时使用，默认 `data/notes.jsonl`
- `BIJI_MONGITA_DIR`：Mongita 数据目录，默认 `data/mongita`
- `BIJI_MONGITA_DB`：Mongita 数据库名，默认 `biji`
- `BIJI_MONGITA_NOTES_COLLECTION`：默认 `notes`
- `BIJI_MONGITA_DETAILS_COLLECTION`：默认 `details`

### 安全提示

- 不要把 token/refresh_token 写进代码或提交到 git；只放在本地 `.env`。
- `tmp/`、`.env*`、`data/` 都已在 `.gitignore` 中忽略。
