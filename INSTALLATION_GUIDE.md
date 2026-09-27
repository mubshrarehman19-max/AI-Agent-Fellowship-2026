# Installation Guide

This guide covers everything needed to set up and run the **AI Workspace** project: VS Code, Git, Python, and the required Python packages (Streamlit, Requests).

---

## 1. Install VS Code

1. Go to [https://code.visualstudio.com](https://code.visualstudio.com)
2. Download the installer for your OS (Windows / macOS / Linux)
3. Run the installer and follow the default setup steps
4. Launch VS Code to confirm it opens correctly

**Recommended extensions:**
- Python (by Microsoft)
- Live Server (for previewing HTML files)

---

## 2. Install Git

1. Go to [https://git-scm.com/downloads](https://git-scm.com/downloads)
2. Download and run the installer for your OS (accept the default options)
3. Verify installation by opening a terminal and running:
   ```bash
   git --version
   ```
4. Set your identity (used for commits):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your@email.com"
   ```

---

## 3. Install Python

1. Go to [https://www.python.org/downloads](https://www.python.org/downloads)
2. Download the latest Python 3.x installer for your OS
3. **Windows:** during install, check the box **"Add Python to PATH"** before clicking Install
4. Verify installation:
   ```bash
   python --version
   ```
   (On macOS/Linux you may need `python3 --version`)

---

## 4. Install Required Python Packages

This project needs **Streamlit** and **Requests**. From the project folder, run:

```bash
pip install -r requirements.txt
```

Or install them individually:

```bash
pip install streamlit requests
```

Verify Streamlit installed correctly:

```bash
streamlit --version
```

---

## 5. Run the App

From the project folder in VS Code's terminal:

```bash
streamlit run app.py
```

This opens the app automatically in your browser (usually at `http://localhost:8501`).

---

## 6. Clone This Repository (optional)

To get this project onto a new machine:

```bash
git clone https://github.com/<your-username>/AI-Agent-Fellowship-2026.git
cd AI-Agent-Fellowship-2026
pip install -r requirements.txt
streamlit run app.py
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `python` not recognized | Reinstall Python and check "Add to PATH" |
| `pip` not recognized | Use `python -m pip install ...` instead |
| `git` not recognized | Restart terminal/VS Code after installing Git |
| Streamlit page won't open | Manually visit `http://localhost:8501` in your browser |
