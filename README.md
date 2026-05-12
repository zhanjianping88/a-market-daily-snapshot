# A股每日市场快照

一个自动生成 A 股市场日报 HTML 页面的轻量项目。

产物是单文件静态页面，适合直接放在 GitHub 仓库里，也适合配合 GitHub Pages 每天自动更新。

## 功能

- 每日抓取最新市场快照数据
- 实时拉取盘中快讯，生成实时数据面板
- 生成美观的单页 HTML 日报
- 自动保留按交易日归档的历史页面
- 自动更新 `market-snapshot-latest.html`
- 自动更新 `index.html`，方便 GitHub Pages 直接展示
- 采用 A 股习惯配色：上涨红色，下跌绿色

## 本地使用

```bash
python3 generate_market_snapshot.py
```

生成后会更新：

- `index.html`
- `market-snapshot-latest.html`
- `market-snapshot-YYYY-MM-DD.html`

实时面板：

- `realtime.html`

## 自动更新

仓库内置 GitHub Actions：

- 每天定时运行
- 也支持手动触发
- 如果页面有变化，会自动提交回仓库

工作流文件：

- `.github/workflows/daily-update.yml`

## 主要文件

- `generate_market_snapshot.py`：生成日报页面
- `index.html`：GitHub Pages 首页
- `realtime.html`：实时数据面板
- `market-snapshot-latest.html`：最新日报
- `market-snapshot-*.html`：按日期归档

## 说明

页面里已经去掉“数据来源”文案，只保留日报内容和更新时间。
