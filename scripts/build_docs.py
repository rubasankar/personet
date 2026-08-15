"""
Generate docs/api.html - a fully self-contained ReDoc page that the frontend
team can open in any browser without running the server.

Usage:
    python build_docs.py
"""

import json
import pathlib

# ---------------------------------------------------------------------------
# Load the spec
# ---------------------------------------------------------------------------

with open("openapi.json", encoding="utf-8") as f:  # noqa: PTH123
    spec = json.load(f)

spec_json = json.dumps(spec, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Build the HTML
# ---------------------------------------------------------------------------

HTML = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PerNet API - Documentation</title>
  <style>
    body {{ margin: 0; padding: 0; }}
  </style>
</head>
<body>
  <div id="redoc-container"></div>

  <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.5/bundles/redoc.standalone.js"></script>

  <script>
    Redoc.init(
      {spec_json},
      {{
        theme: {{
          colors: {{ primary: {{ main: "#0066cc" }} }},
          typography: {{
            fontSize: "15px",
            fontFamily:
            "Inter, -apple-system,BlinkMacSystemFont, 'Segoe UI', sans-serif",
            headings: {{ fontFamily: "Inter, sans-serif" }},
            code: {{ fontSize: "13px" }}
          }},
          sidebar: {{ width: "280px", backgroundColor: "#fafafa" }},
          rightPanel: {{ backgroundColor: "#1e2a3a" }}
        }},
        expandResponses: "200,201",
        pathInMiddlePanel: true,
        hideDownloadButton: false,
        sortOperationsAlphabetically: false,
        sortTagsAlphabetically: false
      }},
      document.getElementById("redoc-container")
    );
  </script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------

out = pathlib.Path("../docs/api.html")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(HTML, encoding="utf-8")
