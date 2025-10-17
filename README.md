Create the venv and sync it with uv.

For launching the server:

```bash
uvicorn tile_server:app --reload --port 8000
```

For launching the streamlit app:

```bash
streamlit run main.py
```