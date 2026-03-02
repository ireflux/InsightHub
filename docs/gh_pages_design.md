# InsightHub GitHub Pages 方案设计

## 1. 目标与范围

目标：将 InsightHub 每日运行产出的 Markdown 报告自动发布到 `gh-pages` 分支，形成可访问的静态网站。

范围：
- 产物命名：`posts/YYYY-MM-DD-<run_id>.md`
- 每日无内容时也生成“今日无更新”页面
- 生成 `manifest/index.json` 作为站点索引
- CI 预渲染 HTML（非运行时 Markdown 渲染）
- 站点能力：首页分页、全文搜索、标签筛选、文章页渲染
- SEO 与订阅：canonical、sitemap、RSS
- 安全：LLM 输出基础净化（链接白名单、禁止脚本/危险协议）

非目标：
- 不引入 GitHub Pages 原生 Jekyll 主题/插件体系
- 不依赖服务端动态能力

## 2. 当前状态（基线）

- 目前 Markdown sink 会输出到 `output/InsightHub_YYYY-MM-DD_HH-MM.md`。
- `daily.yml` 仅提交 `history.json` 与 `delivery_state.json`。
- 尚未有面向网站的结构化索引（manifest）与预渲染步骤。

## 3. 架构决策

### 3.1 发布模式

采用“两段式 CI”：
1. `daily` 工作流：运行数据采集/总结，生成 Markdown + manifest + 站点构建输入。
2. `deploy-pages` 工作流：读取输入并预渲染站点，发布到 `gh-pages` 分支。

`main` 保持源码，`gh-pages` 仅保留站点静态文件。

### 3.2 时区与日期口径

- 统一业务时区：`Asia/Shanghai`
- 页面展示与文件命名使用上海时区日期（`YYYY-MM-DD`）
- 所有机器可读时间字段采用 ISO8601（含时区偏移）

### 3.3 站点渲染策略

采用项目内自定义静态生成脚本（Python）进行预渲染，而非 GitHub Pages 内建 Jekyll。

理由：
- 与当前 Python 技术栈一致，依赖少，便于维护
- 不受 Jekyll 插件白名单限制
- 可精确控制净化、安全与输出结构

## 4. 数据契约

### 4.1 Markdown 产物路径

- 路径：`output/posts/YYYY-MM-DD-<run_id>.md`
- 其中 `<run_id>` 来源于当前运行上下文（CLI run_id）

### 4.2 Manifest 路径与结构

- 路径：`output/manifest/index.json`
- 结构（建议）：

```json
{
  "site_timezone": "Asia/Shanghai",
  "generated_at": "2026-03-02T23:30:00+08:00",
  "posts": [
    {
      "id": "2026-03-02-a1b2c3d4e5f6",
      "run_id": "a1b2c3d4e5f6",
      "date": "2026-03-02",
      "title": "InsightHub Daily 2026-03-02",
      "slug": "2026-03-02-a1b2c3d4e5f6",
      "markdown_path": "posts/2026-03-02-a1b2c3d4e5f6.md",
      "html_path": "posts/2026-03-02-a1b2c3d4e5f6/index.html",
      "summary": "当日导读摘要",
      "tags": ["hacker_news", "github_trending"],
      "sources": ["hacker_news", "github_trending"],
      "item_count": 8,
      "is_empty_update": false,
      "canonical_url": "https://<user>.github.io/<repo>/posts/2026-03-02-a1b2c3d4e5f6/",
      "created_at": "2026-03-02T23:30:00+08:00"
    }
  ]
}
```

约束：
- `posts` 按 `created_at` 倒序
- `slug` 全局唯一
- `is_empty_update=true` 时 `item_count=0`

## 5. 页面与信息架构

### 5.1 首页

- 路由：`/index.html`
- 功能：
  - 每页 N 篇（默认 20）分页
  - 标题、日期、摘要、标签、来源、条目数
  - 搜索框（标题/摘要/标签）
  - 标签筛选（可多选或单选）

### 5.2 文章页

- 路由：`/posts/<slug>/index.html`
- 内容：
  - 标题与元信息（日期、来源、条目数）
  - 已净化后的 Markdown HTML
  - 上一篇/下一篇导航
  - canonical 链接

### 5.3 附属文件

- `sitemap.xml`
- `rss.xml`
- `search-index.json`（用于前端静态搜索）

## 6. 安全策略（LLM 输出净化）

在 Markdown 转 HTML 后执行二次净化：
- 删除标签：`script`, `iframe`, `object`, `embed`, `style`, `link`, `meta`（站点模板外）
- 移除所有 `on*` 事件属性
- 链接协议白名单：`http`, `https`, `mailto`
- 拒绝 `javascript:`, `data:`, `vbscript:`
- 外链统一添加 `rel="noopener noreferrer nofollow"` 与 `target="_blank"`

## 7. GitHub Actions 设计

### 7.1 daily.yml（生产内容）

- 触发：`schedule` + `workflow_dispatch`
- 步骤：
  1. 检出代码
  2. 安装依赖
  3. 运行测试
  4. 执行 `insighthub run`
  5. 更新 manifest（追加/去重/排序）
  6. 提交以下产物到 `main`：
     - `output/posts/**`
     - `output/manifest/index.json`
     - `history.json`
     - `delivery_state.json`

### 7.2 deploy-pages.yml（部署站点）

- 触发：
  - `workflow_run`（监听 daily 成功）
  - `workflow_dispatch`
  - 可选 `push` 到 `main` 的 `output/**`
- 步骤：
  1. 检出代码
  2. 构建站点（读取 manifest + markdown，生成 `site/`）
  3. 部署 `site/` 到 `gh-pages`

## 8. 开发任务拆分

### 阶段 A：内容产物标准化
- A1. Markdown sink 支持 `run_id` 与上海时区日期命名
- A2. 无新内容时生成“今日无更新”Markdown
- A3. 生成/维护 `output/manifest/index.json`
- A4. 补充单元测试（命名、空日报、manifest 追加与排序）

### 阶段 B：静态站点生成器
- B1. 实现 Markdown -> 安全 HTML 转换
- B2. 生成文章页
- B3. 生成首页分页
- B4. 生成 `search-index.json` + 前端搜索/标签筛选
- B5. 生成 `rss.xml`、`sitemap.xml`、canonical
- B6. 补充站点生成测试

### 阶段 C：CI/CD
- C1. 拆分并更新 `daily.yml`
- C2. 新增 `deploy-pages.yml`
- C3. 验证 `gh-pages` 分支发布产物结构

### 阶段 D：文档与运维
- D1. README 增加“站点发布”章节
- D2. 故障排查（空产物、重复 slug、部署失败回滚）

## 9. 验收标准

- 每日运行后，`main` 可看到新增 Markdown 与 manifest 更新
- `gh-pages` 站点可访问：
  - 首页分页正常
  - 搜索与标签筛选正常
  - 文章页正确渲染
  - 空日报可访问
- SEO 文件存在且内容有效：`canonical`、`sitemap.xml`、`rss.xml`
- 产物不含脚本注入与危险链接协议

