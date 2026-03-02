# 🪟 Windows Setup & Troubleshooting Guide

This guide provides detailed instructions for setting up the Soul Sense EQ Test environment on Windows. It covers dependencies, environment configuration, and fixes for common issues.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python 3.11**: [Download Python 3.11.x](https://www.python.org/downloads/windows/) (Tested version).
    > [!IMPORTANT]
    > During installation, check the box: **"Add Python to PATH"**.
2.  **Node.js (LTS)**: [Download Node.js](https://nodejs.org/).
3.  **Rust**: [Download Rustup](https://rustup.rs/).
4.  **Microsoft C++ Build Tools**: Required for Rust and some Python packages.
    -   Download the [Visual Studio Installer](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
    -   Select **"Desktop development with C++"** and install.

---

## 🚀 Step-by-Step Installation

### 1. Clone the Repository

```powershell
git clone https://github.com/nupurmadaan04/SOUL_SENSE_EXAM.git
cd SOUL_SENSE_EXAM
```

### 2. Setup Python Environment

```powershell
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Initialize the Database

```powershell
# Run the setup script
python -m scripts.setup_dev

# If that fails, run migrations and seed questions manually:
alembic upgrade head
python scripts/setup/seed_questions_v2.py
```

### 4. Setup Tauri/Web Environment

If you plan to work on the modern web/desktop shell:

```powershell
# Ensure Rust and Tauri CLI are ready
.\scripts\setup_tauri_env.ps1

# Navigate to frontend and install packages
cd frontend-web
npm install
```

---

## 🎮 Running the Application

### Option A: Legacy Tkinter App (Fastest)
```powershell
python -m app.main
```

### Option B: Modern Desktop Shell (Tauri)
```powershell
cd frontend-web
npm run tauri dev
```

### Option C: Backend API & Standalone Web
```powershell
# Terminal 1: Backend
python backend/fastapi/start_server.py

# Terminal 2: Web Frontend
cd frontend-web
npm run dev
```

---

## 🛠️ Troubleshooting

### 1. Missing `tkinter` Error
If you see `ModuleNotFoundError: No module named 'tkinter'`:
-   **Fix**: Re-run the Python installer and ensure "tcl/tk and IDLE" is selected under "Optional Features".

### 2. "DLL load failed" or C++ Errors
If you see errors related to missing DLLs or failed builds:
-   **Fix**: Ensure **Microsoft C++ Build Tools** are installed (see Prerequisites). This is critical for NLTK and Rust dependencies.

### 3. "Command Not Found" (PATH Issues)
If `python`, `npm`, or `rustc` are not recognized:
-   **Fix**:
    1.  Open "Environment Variables" via Windows Search.
    2.  Check if the paths to your Python/Scripts, Nodejs, and .cargo/bin are in your user's `Path` variable.
    3.  Restart your terminal (or computer) after updating PATH.

### 4. Database Locked or Schema Errors
-   **Fix**: If you encounter issues with `soulsense.db`:
    ```powershell
    # Remove existing db and re-initialize
    Remove-Item data/soulsense.db
    alembic upgrade head
    python scripts/setup/seed_questions_v2.py
    ```

### 5. Tauri Sidecar Errors
If Tauri fails to find the backend binary:
-   **Fix**: Run the environment setup script to rebuild and sync the sidecar:
    ```powershell
    .\scripts\setup_tauri_env.ps1
    ```

---

## 📬 Still Having Issues?
If you're stuck, please open an issue on the [GitHub repository](https://github.com/nupurmadaan04/SOUL_SENSE_EXAM/issues) with a screenshot of the error.
