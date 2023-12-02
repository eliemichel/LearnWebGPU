from typing import List, Tuple

def setup(app):
    app.add_css_file("diff-admonition.css")
    app.add_js_file("diff-admonition.js")

    app.add_css_file("translation.css")

    # Each entry is (short language name, emoji, language name, english language name)
    app.add_config_value("translation_languages", [], 'html', List[Tuple[str, str, str, str]])
