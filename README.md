# Claude Code 源码解读 · 网站

《Claude Code 源码解读》一书的网页实现。书是对 Claude Code 仓库的一次深读，23 章只讲值得借鉴的工程设计点，每条结论都附 `path/file.ts:line` 级别的源码引用。

🌐 **上线站点**：<https://nayuta403.github.io/claude-code-book/>

![Claude & Code 源码解读](assets/og.png)

## 站点结构

```
/                      书的首页（D 杂志风，带 23 章 TOC、试读、搜索）
/ch01/ ... /ch23/      23 章阅读页
/showcase.html         四个设计备选方向的存档
/a-editorial/          Editorial Monograph  · 编辑部专著风
/b-terminal/           Terminal Logbook     · 日志本风
/c-swiss/              Swiss Archival       · 瑞士档案风
/d-magazine/           → / 的重定向（D 已采用为正文）
/404.html              themed 错误页
/manifest.webmanifest  Web App Manifest
/sitemap.xml           搜索引擎 sitemap
/robots.txt            allow all + sitemap hint
```

## 技术栈

纯静态，零运行时依赖：

| 用途           | 选型                                              |
|----------------|---------------------------------------------------|
| 显示字体       | EB Garamond italic · Albert Sans · JetBrains Mono |
| CJK            | LXGW WenKai（经 jsdelivr CDN）                    |
| 色系           | cream 纸感 + 玫粉色 accent（OKLCH，hue 350）       |
| 构建           | Python 3 stdlib + PIL（只用来生成 OG 图 / favicon） |
| 交互 JS        | 单文件 `assets/book.js`（~3 KB gzip）             |
| 托管           | GitHub Pages（serve from main /）                 |

## 构建 / 重新生成

```bash
# 渲染全部 23 章 + 刷新 sitemap.xml
python3 tools/build.py

# 只渲染某一章（通过 slug 或 chNN）
python3 tools/build.py ch03
python3 tools/build.py ch03-agent-loop

# 重新生成 OG 图 + app icons（需要本地 PIL）
python3 tools/make_og.py
```

渲染器读的 markdown 源在 `/Users/nayuta/ai/claude-code-rev/book/chapters/ch*.md`。

## 阅读体验

- **键盘**：`←` / `[` 上一章 · `→` / `]` 下一章 · `/` 聚焦首页搜索 · `?` 快捷键面板 · `Esc` 关闭面板
- **章内 ¶ 锚点**：每个 h2 / h3 hover 时出现 `¶`，点击复制 deep link
- **本章目录**：折叠的 `<details>`，展开时 scroll-spy 高亮当前小节
- **代码块**：TS / JS / JSON / markdown / xml / bash 预渲染语法高亮 + 复制按钮
- **阅读进度**：顶部 2.5px 玫粉色进度条
- **打印**：章节页有独立的 `@media print` 样式，`⌘P` 能直接存成像样的 PDF，章首有 CONTENTS 段

## 无障碍 / 性能

- `prefers-reduced-motion`：压平所有 transition / animation
- `prefers-color-scheme`：保留 cream 主题（不切暗色，是编辑部语气的一部分）
- `forced-colors: active`（Windows 高对比度）：切系统色 token，描边强制可见
- skip-link、`aria-label`、`lang="zh-Hans"`、canonical + prev/next/up、BreadcrumbList + Article JSON-LD
- fonts preconnect（googleapis / gstatic / jsdelivr），root 预取 `/ch01/` 和 `book.css`

## 书稿源

书稿在另一个仓库（`claude-code-rev/book/chapters/`）。网站只是它的 web front-end。

---

_set in EB Garamond · Albert Sans · JetBrains Mono · LXGW WenKai  ·  volume I · 2026 · ≈ 7.7 hrs 阅读_
