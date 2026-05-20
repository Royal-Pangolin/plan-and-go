# :partly_sunny: Plan&Go :beach_umbrella:

- [:clipboard: Project Summary](#clipboard-project-summary)
- [:wrench: Installation](#wrench-installation)
  - [:zero: Prerequisites](#zero-prerequisites)
  - [:one: Clone the repository](#one-clone-the-repository)
  - [:two: Setup and install dependencies](#two-setup-and-install-dependencies)
  - [:three: Perform migrations](#three-perform-migrations)
  - [:four: Run the development server](#four-run-the-development-server)

### :busts_in_silhouette: Authors

- Jiménez Flores, Alonso
- Nejeoui Chafiqui, Mariam
- Sánchez Díaz, Ana
- Sánchez Troncoso, Pablo

---

## :clipboard: Project Summary

Plan&Go is a collaborative trip planning and expense-sharing app created for the Technology Integration course in the third year of Computer Engineering at UPO. It helps users create trips, invite members, track shared expenses, and manage trip stops in a simple and organized way.

---

## :wrench: Installation

Follow these steps to set up and run the application locally.

### :zero: Prerequisites

Install the following before proceeding:
- [Git](https://git-scm.com/)
- [Python 3.13](https://www.python.org/downloads/release/python-31313/)

### :one: Clone the repository

Open a terminal and run:

```bash
git clone https://github.com/Royal-Pangolin/plan-and-go.git
cd plan-and-go
```

### :two: Setup and install dependencies

Create a virtual environment in the project root:

```bash
python -m venv .venv
```

Activate the virtual environment:

- Windows PowerShell:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- Windows CMD:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```
- Linux / macOS:
  ```bash
  source .venv/bin/activate
  ```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

### :three: Perform migrations

Run database migrations:

```bash
python manage.py migrate
```

### :four: Run the development server

Start the server:

```bash
python manage.py runserver
```

Press `Ctrl+C` to stop the server.

To exit the Python environment, run:

```bash
deactivate
```

---

