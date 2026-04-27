"""Report Compiler node — assembles everything into a self-contained HTML report.

Teaches: final node, Jinja2 templating, END edge.

Optionally generates a PDF via WeasyPrint (wrapped in try/except because
WeasyPrint requires system libraries that not all environments have).
"""

import datetime
import os
from pathlib import Path
import markdown

import jinja2
import pandas as pd

from models.state import ResearchState, State

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent/ "reports"


def _build_summary_table_html(analysis) -> str:
    """Convert the analysis summary_table dict into styled HTML."""
    if not analysis or not analysis.summary_table:
        return ""

    table_data = analysis.summary_table
    columns = table_data.get("columns", [])
    rows = table_data.get("rows", [])
    if not columns or not rows:
        return ""

    df = pd.DataFrame(rows, columns=columns)
    styled = (
        df.style
        .set_table_styles([
            {"selector": "th", "props": [
                ("background-color", "#2c3e50"),
                ("color", "white"),
                ("padding", "10px 14px"),
                ("font-weight", "bold"),
                ("text-align", "left"),
            ]},
            {"selector": "td", "props": [
                ("padding", "8px 14px"),
                ("border-bottom", "1px solid #dee2e6"),
            ]},
            {"selector": "tr:nth-child(even)", "props": [
                ("background-color", "#f8f9fa"),
            ]},
        ])
        .hide(axis="index")
    )
    return styled.to_html()


# def report_compiler(state: ResearchState) -> dict:
def report_compiler(state: State) -> dict:
    """Assemble the final HTML report from all gathered materials."""
    # plan = state["research_plan"]
    # game_stats = state.get("game_stats", [])
    player_stats = state.get("player_stats", [])
    # head_to_head_stats = state.get("head_to_head_stats", [])
    llm_model = state.get("llm_model")
    sections = state.get("report_sections", {})
    charts = state.get("charts", [])
    screenshots = state.get("screenshots", [])
    analysis = state.get("analysis")

    # Group charts by section
    charts_by_section: dict[str, list] = {}
    for chart in charts:
        charts_by_section.setdefault(chart.section, []).append(chart)

    # Build section data for the template
    template_sections = []

    #first game info
    # for game_stat in game_stats:
    #     game_stat_html = markdown.markdown(game_stat.content, extensions=['extra', 'codehilite'])
    #     template_sections.append({
    #         # "title": "Game Info",
    #         "content": game_stat_html,
    #     })

    #individual player stats
    # for title, content in sections.items():
    for player_stat in player_stats:
        player_stat_html = markdown.markdown(player_stat.content, extensions=['extra', 'codehilite'])
        template_sections.append({
            # "title": "Player Stats",
            "content": player_stat_html,
            # "charts": charts_by_section.get(title, []),
        })

    # head-to-head stats
    # for head_to_head_stat in head_to_head_stats:
    #     head_to_head_stat_html = markdown.markdown(head_to_head_stat.content, extensions=['extra', 'codehilite'])
    #     template_sections.append({
    #         # "title": "Head-to-head Info",
    #         "content": head_to_head_stat_html,
    #     })

    # Collect unique sources from search results
    seen_urls: set[str] = set()
    sources = []
    for r in state.get("search_results", []):
        if r.url and r.url not in seen_urls:
            seen_urls.add(r.url)
            sources.append({"title": r.title, "url": r.url})

    # Build summary table HTML
    summary_table_html = _build_summary_table_html(analysis)

    # Render Jinja2 template
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=jinja2.select_autoescape(["html"]),
    )
    template = env.get_template("report.html")

    title = "Matchup Analysis Report"
    generated_datetime = datetime.datetime.now()

    # summary_message = state["messages"][-1].content if state["messages"] else ""
    summary_message = state["summary"] if state["summary"] else ""
    summary_html = markdown.markdown(summary_message, extensions=['extra', 'codehilite'])

    html = template.render(
        # title=plan.title,
        title=title,
        llm_model=state["llm_model"],
        # topic=state["topic"],
        generated_date=generated_datetime.strftime("%m/%d/%Y, %H:%M:%S"),
        # executive_summary=sections.get("Executive Summary", ""),
        executive_summary=summary_html,
        summary_table=summary_table_html,
        sections=template_sections,
        screenshots=screenshots,
        sources=sources,
        key_findings=analysis.key_findings if analysis else [],
    )

    # Save HTML output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in plan.title)
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in title)
    safe_name = safe_name.strip().replace(" ", "-")[:80]
    name_with_timestamp = safe_name + generated_datetime.strftime("_%m_%d_%Y_%H_%M_%S")
    html_path = OUTPUT_DIR / f"{name_with_timestamp}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  ✓ Report saved: {html_path}")

    return {
        # "final_report_html": html,
    }
