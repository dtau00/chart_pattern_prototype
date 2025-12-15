  # Project Description
  
  
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
  - For all relevant user fields and selections, persistently save the state, so it will be the same when the user returns.
  - Use Streamlit's st.session_state

  ### Implementation Pattern for Persistent Fields
  To avoid conflicts between widget keys and session state, use **separate keys** for the widget and the persisted value:

  ```python
  # CORRECT - Use different keys for widget and persistence
  window_size = st.number_input(
      "Pattern Window Size (bars)",
      min_value=10,
      max_value=200,
      value=st.session_state.get('scanner_window_size', 50),  # Read from persistence key
      key="scanner_window_size_widget"  # Widget key (different from persistence key)
  )
  st.session_state['scanner_window_size'] = window_size  # Save to persistence key

  # For selectbox with index-based persistence:
  selected_file = st.selectbox(
      "Select data file",
      parquet_files,
      index=st.session_state.get('scanner_file_index', 0),
      key="scanner_file_select_widget"
  )
  if selected_file in parquet_files:
      st.session_state['scanner_file_index'] = parquet_files.index(selected_file)

  # For multiselect:
  filter_labels = st.multiselect(
      "Filter by Pattern Labels",
      options=library.get_all_labels(),
      default=st.session_state.get('scanner_filter_labels', []),
      key="scanner_filter_labels_widget"
  )
  st.session_state['scanner_filter_labels'] = filter_labels
  ```

  **Key Rules:**
  - Widget `key` parameter should end with `_widget` to distinguish it
  - `value` or `default` reads from a separate session state key (without `_widget`)
  - After widget creation, manually save the value back to the persistence key
  - This avoids the "widget was created with a default value but also had its value set via Session State" warning

  # Code Generation Guideline
  - Don't include sections for "instructions" and "how to use".  Keep the pages focused.

  # Documentation
  - Don't create unnecessary documentation unless explicitly asked to.  Such as test results and summary documentation.
