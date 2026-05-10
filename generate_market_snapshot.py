#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path


SNAPSHOT_URL = "https://hhxg.top/static/data/assistant/skill_snapshot.json"
OUTPUT_DIR = Path(__file__).resolve().parent
CACHE_FILE = OUTPUT_DIR / "market-snapshot-cache.json"


def fetch_snapshot() -> dict:
    try:
        with urllib.request.urlopen(SNAPSHOT_URL, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return data
    except Exception:
        try:
            result = subprocess.run(
                ["/usr/bin/curl", "-sS", "-L", SNAPSHOT_URL],
                capture_output=True,
                text=True,
                check=True,
                timeout=20,
            )
            data = json.loads(result.stdout)
            CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return data
        except Exception:
            if CACHE_FILE.exists():
                return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            raise


def pct(value: int, total: int) -> str:
    if not total:
        return "0"
    return f"{(value / total) * 100:.1f}".rstrip("0").rstrip(".")


def top_news(items: list[dict], limit: int = 4) -> str:
    blocks = []
    for item in items[:limit]:
        time_text = item.get("t", "").replace("T", " · ")[:16]
        category = item.get("cat", "")
        title = escape_html(item.get("title", ""))
        blocks.append(
            f"""
          <div class="news-item">
            <div class="news-meta">{time_text} · {escape_html(category)}</div>
            {title}
          </div>""".rstrip()
        )
    return "\n".join(blocks)


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render(snapshot: dict) -> str:
    date_text = snapshot.get("date", "")
    update_time = snapshot.get("meta", {}).get("update_time", "")
    summary = snapshot.get("ai_summary", {})
    market = snapshot.get("market", {})
    total = int(market.get("total", 0) or 0)
    sectors = snapshot.get("sectors", [])
    hot_themes = snapshot.get("hot_themes", [])
    ladder = snapshot.get("ladder", {})
    ladder_detail = snapshot.get("ladder_detail", {})
    hotmoney = snapshot.get("hotmoney", {})
    focus_news = snapshot.get("focus_news", [])
    comparison = snapshot.get("comparison", {})
    buckets_html = []
    for bucket in market.get("buckets", []):
        count = int(bucket.get("count", 0) or 0)
        direction = " down" if "跌" in bucket.get("name", "") else ""
        buckets_html.append(
            f'<div class="bar-row"><span>{escape_html(bucket.get("name", ""))}</span>'
            f'<div class="track"><div class="fill{direction}" style="width:{pct(count, total)}%"></div></div>'
            f"<strong>{count}</strong></div>"
        )

    theme_html = []
    for theme in hot_themes[:4]:
        leaders = "、".join(stock.get("name", "") for stock in theme.get("top_stocks", [])[:2])
        related = "、".join(item.get("name", "") for item in theme.get("related_themes", [])[:3])
        theme_html.append(
            f"""
          <div class="heat-item">
            <div class="heat-head"><strong>{escape_html(theme.get("name", ""))}</strong><span class="pill">{theme.get("limitup_count", 0)} 家涨停 · {theme.get("net_yi", 0)} 亿</span></div>
            <div class="tags">龙头：{escape_html(leaders)} · 关联：{escape_html(related)}</div>
          </div>""".rstrip()
        )

    def sector_rows(group_index: int, side: str) -> str:
        rows = []
        items = sectors[group_index].get(side, []) if len(sectors) > group_index else []
        for item in items[:5]:
            amount = float(item.get("net_yi", 0) or 0)
            cls = "pos" if amount >= 0 else "neg"
            rows.append(
                f'<div class="sector-row"><strong>{escape_html(item.get("name", ""))}</strong>'
                f'<span class="{cls}">{amount:+.0f}亿</span><span>{escape_html(item.get("leader", ""))}</span></div>'
            )
        return "\n".join(rows)

    levels_html = []
    for level in ladder_detail.get("levels", [])[:3]:
        stocks = [s.get("name", "") for s in level.get("stocks", []) if s.get("is_success", True)]
        if not stocks:
            stocks = [s.get("name", "") for s in level.get("stocks", [])[:4]]
        levels_html.append(
            f"""
          <div class="ladder-level">
            <div class="board"><strong>{level.get("boards", 0)}</strong><span>{level.get("count", 0)} 只晋级</span></div>
            <div class="board-list">{escape_html(' / '.join(stocks[:8])) or '暂无'}</div>
          </div>""".rstrip()
        )

    hotmoney_rows = []
    for row in hotmoney.get("top_net_buy", [])[:5]:
        hotmoney_rows.append(
            f"<tr><td>{escape_html(row.get('name', ''))}</td><td class=\"pos\">{row.get('net_yi', 0)}亿</td><td>{row.get('ratio_pct', 0)}%</td></tr>"
        )

    sentiment = float(market.get("sentiment_index", 0) or 0)
    limit_up = market.get("limit_up", 0)
    fried = market.get("fried", 0)
    limit_down = market.get("limit_down", 0)
    promotion_rate = market.get("promotion_rate", "")
    struct_diff = market.get("struct_diff", 0)
    trend_label = comparison.get("trend_label", "")
    hero_line = "，".join(
        part for part in [
            summary.get("market_state", ""),
            summary.get("focus_direction", ""),
            summary.get("theme_focus", ""),
            summary.get("hotmoney_state", ""),
        ] if part
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A股每日市场快照 · {date_text}</title>
  <style>
    :root {{
      --bg: #f3efe7;
      --paper: rgba(255,255,255,.72);
      --text: #18222f;
      --muted: #687483;
      --line: rgba(24,34,47,.1);
      --red: #d64b46;
      --green: #1c8c63;
      --gold: #b7822d;
      --teal: #1d6f74;
      --shadow: 0 24px 60px rgba(30, 41, 59, .12);
      --radius: 24px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "SF Pro Display", "PingFang SC", "Noto Sans SC", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(214,75,70,.14), transparent 28%),
        radial-gradient(circle at top right, rgba(29,111,116,.15), transparent 30%),
        linear-gradient(180deg, #f8f3ea 0%, #f2ede4 52%, #ece6dc 100%);
    }}
    .shell {{ max-width: 1380px; margin: 0 auto; padding: 28px; }}
    .hero {{
      overflow: hidden; padding: 34px; border-radius: 30px; color: #f7f8fa;
      background: linear-gradient(135deg, rgba(27,53,87,.96), rgba(19,78,94,.92));
      box-shadow: var(--shadow);
    }}
    .eyebrow {{
      display: inline-flex; gap: 10px; align-items: center; padding: 8px 14px;
      border: 1px solid rgba(255,255,255,.18); border-radius: 999px; font-size: 13px;
      letter-spacing: .08em; text-transform: uppercase; color: rgba(255,255,255,.82);
    }}
    h1 {{ margin: 18px 0 10px; font-size: clamp(36px, 6vw, 68px); line-height: .98; letter-spacing: -.04em; }}
    .hero-grid {{ display: grid; grid-template-columns: 1.45fr .95fr; gap: 26px; margin-top: 18px; align-items: end; }}
    .summary {{ font-size: 20px; line-height: 1.65; color: rgba(247,248,250,.92); }}
    .hero-side, .metric-strip, .grid, .stat-list, .dist, .heat-list, .news-list, .ladder-levels {{ display: grid; gap: 12px; }}
    .metric-strip {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .metric-chip, .hero-note, .card, .stat, .heat-item, .sector-box, .board-list, .news-item {{
      border: 1px solid rgba(255,255,255,.12); border-radius: 18px;
    }}
    .metric-chip, .hero-note {{ padding: 16px 18px; background: rgba(255,255,255,.09); }}
    .metric-chip .label, .hero-note .label {{ display:block; font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:rgba(255,255,255,.7); margin-bottom:8px; }}
    .metric-chip strong {{ font-size: 28px; }}
    .grid {{ grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 18px; margin-top: 22px; }}
    .card {{ background: var(--paper); border-color: rgba(255,255,255,.6); box-shadow: var(--shadow); padding: 24px; }}
    .card h2 {{ margin: 0 0 6px; font-size: 24px; letter-spacing: -.03em; }}
    .card .sub {{ color: var(--muted); font-size: 14px; margin-bottom: 18px; }}
    .span-5 {{ grid-column: span 5; }} .span-6 {{ grid-column: span 6; }} .span-7 {{ grid-column: span 7; }} .span-12 {{ grid-column: span 12; }}
    .gauge-wrap {{ display: grid; grid-template-columns: 220px 1fr; gap: 20px; align-items: center; }}
    .gauge {{
      width: 210px; height: 210px; border-radius: 50%; display: grid; place-items: center;
      background: radial-gradient(closest-side, rgba(255,255,255,.92) 71%, transparent 72% 100%),
                  conic-gradient(from 220deg, var(--teal) 0 calc({sentiment} * 1%), rgba(24,34,47,.08) 0 100%);
      margin: 0 auto;
    }}
    .gauge-value {{ text-align: center; }} .gauge-value strong {{ display:block; font-size:46px; line-height:1; letter-spacing:-.05em; }} .gauge-value span {{ color: var(--muted); font-size:14px; }}
    .stat-list {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .stat {{ padding: 14px 16px; background: rgba(255,255,255,.58); border-color: var(--line); }}
    .stat .k {{ color: var(--muted); font-size: 13px; margin-bottom: 8px; }} .stat .v {{ font-size: 28px; font-weight: 700; letter-spacing: -.03em; }}
    .bar-row {{ display:grid; grid-template-columns:70px 1fr 64px; gap:12px; align-items:center; font-size:14px; }}
    .track {{ height:12px; border-radius:999px; background:rgba(24,34,47,.08); overflow:hidden; }}
    .fill {{ height:100%; border-radius:inherit; background:linear-gradient(90deg, #d17752, #d64b46); }}
    .fill.down {{ background:linear-gradient(90deg, #2f8f68, #1c8c63); }}
    .heat-item, .sector-box, .board-list, .news-item {{ padding: 16px 18px; background: rgba(255,255,255,.58); border-color: var(--line); }}
    .heat-head, .ladder-head {{ display:flex; justify-content:space-between; gap:12px; align-items:baseline; margin-bottom:8px; }}
    .heat-head strong {{ font-size:20px; }} .pill {{ display:inline-flex; align-items:center; padding:6px 10px; border-radius:999px; font-size:12px; background:rgba(183,130,45,.12); color:var(--gold); font-weight:700; }}
    .tags {{ color: var(--muted); font-size: 14px; line-height: 1.6; }}
    .sector-columns {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
    .sector-box h3 {{ margin:0 0 12px; font-size:18px; }}
    .sector-row {{ display:grid; grid-template-columns:1fr 70px 80px; gap:10px; padding:10px 0; border-top:1px solid rgba(24,34,47,.08); font-size:14px; }}
    .sector-row:first-of-type {{ border-top:0; }}
    .pos {{ color: var(--red); font-weight:700; }} .neg {{ color: var(--green); font-weight:700; }}
    .ladder-top {{ font-size:16px; color:var(--muted); }} .ladder-top strong {{ color:var(--text); font-size:34px; letter-spacing:-.04em; margin-right:8px; }}
    .ladder-level {{ display:grid; grid-template-columns:96px 1fr; gap:14px; align-items:start; }}
    .board {{ padding:14px 10px; border-radius:18px; background:linear-gradient(180deg, rgba(27,53,87,.95), rgba(43,90,121,.92)); color:#fff; text-align:center; }}
    .board strong {{ display:block; font-size:30px; line-height:1; }} .board span {{ font-size:12px; color:rgba(255,255,255,.76); }}
    .table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    .table th, .table td {{ text-align:left; padding:12px 10px; border-top:1px solid rgba(24,34,47,.08); }}
    .table th {{ color:var(--muted); font-weight:600; font-size:12px; letter-spacing:.06em; text-transform:uppercase; border-top:0; }}
    .news-meta {{ color:var(--muted); font-size:12px; margin-bottom:8px; text-transform:uppercase; letter-spacing:.06em; }}
    .foot {{ margin-top: 18px; color: var(--muted); font-size: 13px; line-height: 1.7; text-align: center; }}
    @media (max-width: 1080px) {{
      .hero-grid, .gauge-wrap, .sector-columns {{ grid-template-columns: 1fr; }}
      .span-5, .span-6, .span-7 {{ grid-column: span 12; }}
      .metric-strip {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">A股每日市场快照 · 最近交易日 {escape_html(date_text)}</div>
      <h1>{escape_html(summary.get("market_state", "市场快照"))}<br>{escape_html(summary.get("focus_direction", ""))}</h1>
      <div class="hero-grid">
        <div class="summary">{escape_html(hero_line)}</div>
        <div class="hero-side">
          <div class="metric-strip">
            <div class="metric-chip"><span class="label">涨停</span><strong>{limit_up}</strong></div>
            <div class="metric-chip"><span class="label">炸板</span><strong>{fried}</strong></div>
            <div class="metric-chip"><span class="label">跌停</span><strong>{limit_down}</strong></div>
          </div>
          <div class="hero-note"><span class="label">更新</span>{escape_html(update_time.replace("T", " "))}</div>
        </div>
      </div>
    </section>

    <section class="grid">
      <article class="card span-5">
        <h2>市场温度</h2>
        <div class="sub">情绪强度、结构差值与晋级率</div>
        <div class="gauge-wrap">
          <div class="gauge">
            <div class="gauge-value"><strong>{sentiment:.1f}</strong><span>赚钱效应指数</span></div>
          </div>
          <div class="stat-list">
            <div class="stat"><div class="k">情绪标签</div><div class="v">{escape_html(market.get("sentiment_label", ""))}</div></div>
            <div class="stat"><div class="k">结构差值</div><div class="v">{struct_diff}</div></div>
            <div class="stat"><div class="k">晋级率</div><div class="v">{escape_html(str(promotion_rate))}</div></div>
            <div class="stat"><div class="k">情绪区间</div><div class="v">{escape_html(trend_label)}</div></div>
          </div>
        </div>
      </article>

      <article class="card span-7">
        <h2>涨跌分布</h2>
        <div class="sub">{total} 只个股的日内分布结构</div>
        <div class="dist">
          {"".join(buckets_html)}
        </div>
      </article>

      <article class="card span-6">
        <h2>热门题材</h2>
        <div class="sub">按涨停家数与资金净流入排序</div>
        <div class="heat-list">
          {"".join(theme_html)}
        </div>
      </article>

      <article class="card span-6">
        <h2>行业强弱</h2>
        <div class="sub">净流入强势与弱势板块</div>
        <div class="sector-columns">
          <div class="sector-box">
            <h3>强势行业</h3>
            {sector_rows(0, "strong")}
          </div>
          <div class="sector-box">
            <h3>弱势行业</h3>
            {sector_rows(0, "weak")}
          </div>
        </div>
      </article>

      <article class="card span-7">
        <div class="ladder-head">
          <div>
            <h2>连板天梯</h2>
            <div class="sub">最高连板 {ladder.get("max_streak", 0)} 板，龙头为 {escape_html(ladder.get("top_streak", {}).get("name", ""))}</div>
          </div>
          <div class="ladder-top"><strong>{ladder.get("total_limit_up", 0)}</strong> 涨停总数</div>
        </div>
        <div class="ladder-levels">
          {"".join(levels_html)}
        </div>
      </article>

      <article class="card span-5">
        <h2>游资龙虎榜</h2>
        <div class="sub">龙虎榜总净买入 {hotmoney.get("total_net_yi", 0)} 亿</div>
        <table class="table">
          <thead><tr><th>个股</th><th>净买入</th><th>占比</th></tr></thead>
          <tbody>
            {"".join(hotmoney_rows)}
          </tbody>
        </table>
      </article>

      <article class="card span-12">
        <h2>焦点新闻</h2>
        <div class="sub">市场交易叙事与盘后线索</div>
        <div class="news-list">
          {top_news(focus_news)}
        </div>
      </article>
    </section>

    <div class="foot">
      数据日期：{escape_html(date_text)}（最近交易日） · 更新时间：{escape_html(update_time.replace("T", " "))}
    </div>
  </div>
</body>
</html>
"""


def write_files(snapshot: dict) -> tuple[Path, Path]:
    date_text = snapshot.get("date", datetime.now().strftime("%Y-%m-%d"))
    dated = OUTPUT_DIR / f"market-snapshot-{date_text}.html"
    latest = OUTPUT_DIR / "market-snapshot-latest.html"
    index = OUTPUT_DIR / "index.html"
    html = render(snapshot)
    dated.write_text(html, encoding="utf-8")
    latest.write_text(html, encoding="utf-8")
    index.write_text(html, encoding="utf-8")
    return dated, latest


def main() -> int:
    snapshot = fetch_snapshot()
    dated, latest = write_files(snapshot)
    print(dated)
    print(latest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
