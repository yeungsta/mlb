"""Report Compiler node — assembles everything into a self-contained HTML report.

Teaches: final node, Jinja2 templating, END edge.

Optionally generates a PDF via WeasyPrint (wrapped in try/except because
WeasyPrint requires system libraries that not all environments have).
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import markdown
import pytz

import jinja2
import pandas as pd
import pytz

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
    if not state.get("title"):
        return {"final_report_html": ""}
    
    """Assemble the final HTML report from all gathered materials."""
    # all_stats = state.get("all_stats", [])
    stats_summary = state.get("stats_summary", "")
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

    #all stats
    # for title, content in sections.items():
    # for stat in all_stats:
        # stat_html = markdown.markdown(stat.content, extensions=['extra', 'codehilite'])
        # template_sections.append({
        #     # "title": "Player Stats",
        #     "content": stat_html,
        #     # "charts": charts_by_section.get(title, []),
        # })

    # stats summary
    stats_html = markdown.markdown(stats_summary, extensions=['extra', 'codehilite'])
    template_sections.append({
        "content": stats_html,
    })
    
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

    title = state["title"] if state["title"] else "The Vin Scully AI Matchup Analysis"

    # Define the PST/PDT timezone
    pst = pytz.timezone('America/Los_Angeles')
    generated_datetime = datetime.now(pst)

    summary_message = state["summary"] if state["summary"] else ""
    # add quotation marks around the summary if not already present
    if not (summary_message[0] == '"' and summary_message[-1] == '"'):
        summary_message = f'"{summary_message}"'
    summary_html = markdown.markdown(summary_message, extensions=['extra', 'codehilite'])

    html = template.render(
        # title=plan.title,
        title=title,
        llm_model=state["llm_model"],
        # topic=state["topic"],
        generated_date=generated_datetime.strftime("%m/%d/%Y %I:%M %p PST"),
        # executive_summary=sections.get("Executive Summary", ""),
        executive_summary=summary_html,
        summary_table=summary_table_html,
        sections=template_sections,
        screenshots=screenshots,
        sources=sources,
        key_findings=analysis.key_findings if analysis else [],
    )

    # Save HTML output
    # Ensure the report directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Format today's date (e.g., "2026-04-30")
    today_folder_name = datetime.now().strftime("%m-%d-%Y")
    # 2. Define the full path to the new subfolder
    daily_report_dir = OUTPUT_DIR / today_folder_name
    # 3. Create the folder
    # parents=True: creates if it doesn't exist
    # exist_ok=True: prevents an error if the folder is already there
    daily_report_dir.mkdir(parents=True, exist_ok=True)

    # safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in plan.title)
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in title)
    safe_name = safe_name.strip().replace(" ", "-")[:80]
    # name_with_timestamp = safe_name + generated_datetime.strftime("_%m_%d_%Y_%H_%M_%S")
    html_path = daily_report_dir / f"{safe_name}.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"  ✓ Report saved: {html_path}")

    #email
    import smtplib
    from email.message import EmailMessage

    # Configuration
    SENDER_EMAIL = "yeungsta@gmail.com"
    APP_PASSWORD = "pofz xtky kugq lqzn"  # Use the 16-digit App Password
    RECIPIENT_EMAIL = "yeungsta@gmail.com"

    # Create the email container
    msg = EmailMessage()
    msg['Subject'] = f"⚾️ {title}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    # Define the HTML content
    html_content = html

    # Set the email body to HTML
    msg.add_alternative(html_content, subtype='html')

    # Send the email via Gmail's SMTP server
    try:
        # Use SMTP_SSL for port 465 (more secure)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

    return {
        # "final_report_html": html,
    }
