#render.py
from jinja2 import Environment, FileSystemLoader
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os

index_page_name = 'index.html'
template_values = {}
template_values[index_page_name] = {}
template_values['index_browse_tab.html'] = {}
template_values['index_draft_tab.html'] = {}
template_values['index_navbar.html'] = {}
template_values['index_view_tab.html'] = {}
template_values[index_page_name]['title'] = 'Expense Forecast UI'
template_values[index_page_name]['css_links'] = '<link rel="stylesheet" href="/css/index.css">'

# template_values[index_page_name]['header_script_links'] = \
# """
# <script src="https://unpkg.com/tabulator-tables@5.5.0/dist/js/tabulator.min.js"></script>
# <link href="https://unpkg.com/tabulator-tables@5.5.0/dist/css/tabulator.min.css" rel="stylesheet">
# <script src="https://d3js.org/d3.v7.min.js"></script>
# <script src="https://cdn.jsdelivr.net/npm/d3-sankey@0.12.3/dist/d3-sankey.min.js"></script>
# """
template_values[index_page_name]['header_script_links'] = \
"""
<script src="./js/luxon.min.js"></script>
<script src="./js/tabulator.min.js"></script>
<link href="./css/tabulator.min.css" rel="stylesheet">
<script src="./js/d3.v7.min.js"></script>
<script src="./js/d3-sankey.min.js"></script>
"""
template_values[index_page_name]['footer_script_links'] = \
"""
<script type="module" src="/js/index.js" defer></script>
"""


template_values[index_page_name]['favicon_link'] = '<link rel="icon" href="/assets/favicon.png" type="image/png">'
template_values[index_page_name]['page_header'] = \
"""
<header>
    <h1></h1>
</header>
"""
template_values[index_page_name]['page_footer'] = \
"""
<footer>
    <p>Built with ❤️ by hdickie</p>
</footer>
"""




def render_template(template_name: str, context: dict = {}) -> str:
    template = env.get_template(template_name)
    return template.render(**context)

def render_all_templates():
    os.makedirs(served_dir, exist_ok=True)
    for template_path in Path(template_dir).glob("*.html"):
        template_name = template_path.name
        output_path = Path(served_dir) / template_name

        rendered_content = render_template(template_name, context=template_values[template_name])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_content)
        print(f"Rendered: {template_name} → {output_path}")


template_dir = '/home/hdickie/Github/expense_forecast/backend/web/templates/'
templates = Jinja2Templates(directory=template_dir)

served_dir = '/home/hdickie/Github/expense_forecast/frontend/public-html/'


env = Environment(loader=FileSystemLoader(template_dir))

if __name__ == '__main__':
    render_all_templates()