# Product Fetcher

This is a Python application that fetches product data from the Poizon API and saves it as a JSON file. It uses `requests` for API calls, `python-dotenv` for environment variables, and `tkinter` for a simple GUI.

This guide for macOS

## Prerequisites

- Homebrew (for installing Python and ensuring Tkinter support)

## Setup Instructions

Follow these steps to set up and run the application on macOS:

1. **Install Homebrew (if not already installed):**
   - Open the Terminal app.
   - Run this command to install Homebrew:
     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```
   - Follow the on-screen instructions to complete the installation.

2. **Install Python 3.13 with Tkinter support:**
   - As of now, Homebrew’s `python-tk` formula installs the latest stable Python version with Tkinter support. However, if Python 3.13 is not the default, you can use `pyenv` to install a specific version.
   - First, install `pyenv`:
     ```bash
     brew install pyenv
     ```
   - Then, install Python 3.13:
     ```bash
     pyenv install 3.13.0
     ```
   - Set Python 3.13 as the global version:
     ```bash
     pyenv global 3.13.0
     ```
   - Verify the installation:
     ```bash
     python --version
     ```
     It should display `Python 3.13.0`.

3. **Verify Tkinter installation:**
   - Tkinter should be included with Python 3.13. Verify it by running:
     ```bash
     python -m tkinter
     ```
   - A small test window should appear, confirming `tkinter` is functional.

4. **Set up a virtual environment:**
   - Navigate to the project directory in the Terminal:
     ```bash
     cd product_fetcher/
     ```
   - Create a virtual environment using Python 3.13:
     ```bash
     python -m venv venv
     ```
   - Activate it:
     ```bash
     source venv/bin/activate
     ```

5. **Install dependencies:**
   - With the virtual environment activated, install the required packages:
     ```bash
     pip install -r requirements.txt
     ```
   - Note: `tkinter` is already included with Python and won’t be installed separately.

6. **Create a `.env` file:**
   - In the project directory, create a file named `.env` from `.env.template`:
     ```bash
     cp .env.template .env
     ```
   - Edit `.env` and add your API keys (replace placeholders with actual values):
     ```
     APP_KEY=your_app_key_here
     APP_SECRET=your_app_secret_here
     ```

7. **Run the application:**
   - With the virtual environment activated, run:
     ```bash
     python product_fetcher.py
     ```
   - A GUI window will appear. Enter a brand name, click "Start," and follow the instructions.

## Notes

- Ensure your API keys in `.env` are valid.
- The app uses multithreading and respects the API’s rate limit of 3 requests per second.
- For large datasets, ensure sufficient memory and disk space.

## Troubleshooting

- If `tkinter` fails, confirm you installed Python with Tkinter support.
- If permissions issues arise, prepend `sudo` to commands (e.g., `sudo brew install pyenv`).
- Check Terminal output for specific error messages if the app doesn’t run.