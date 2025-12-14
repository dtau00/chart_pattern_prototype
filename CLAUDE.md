  # Streamlit Multi-Page & Tab Architecture

  ## Directory Structure
  ```
  project_root/
  ├── Main_App.py              # Entrypoint with st.navigation
  ├── pages/                   # Top-level navigation pages
  │   └── analysis_parent.py   # Page with internal tabs
  └── components/              # Component and Tab functions
      ├── init.py              # Required (can be empty)
      ├── header.py           # General reuable component
      ├── tab_overview.py      # A tab "page"
      └── tab_metrics.py       # A tab "page"

  ```

  ## Implementation Pattern

  **Main_App.py** - Router using `st.navigation()`:
  ```python
  import streamlit as st
  st.set_page_config(page_title="App", layout="wide")
  app_pages = [st.Page("pages/analysis_parent.py", title="Analysis", 
  icon=":material/analytics:")]
  pg = st.navigation(app_pages)
  pg.run()

  pages/analysis_parent.py - Lightweight tab container:
  import streamlit as st
  from components.tab_overview import render_overview_tab
  from components.tab_download import render_download

  st.title("Main Analysis View")
  tab1, tab2 = st.tabs(["Overview", "Data Manager"])
  with tab1:
      render_overview_tab()
  with tab2:
      render_download_tab()

  components/tab_*.py - Isolated tab content:
  import streamlit as st
  def render_overview_tab():
      st.header("Overview")
      st.metric("Revenue", "$150K", "3%")
```
  Key Rules:
  - Use /components for tab content (not /subpages)
  - Keep parent pages lightweight (tabs + imports only)
  - One function per component file for isolated logic

  ## Persistent State
  - For all relevant user fields and selections, persistently save the state, so it will be the same whent he user returns.
  - Use Streamlit's st.session_state

  # Code Generation Guideline
  - Don't include sections for "instructions" and "how to use".  Keep the pages focused.
