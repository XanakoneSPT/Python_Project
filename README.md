# 🐍 Python\_project

## 📘 Django Project Setup Guide

Follow the steps below to get your Django project up and running.

---

## 🛠️ Installation

### 1. Install Python

Ensure Python 3.8 or newer is installed.

Check Python version:

```bash
python --version
```

If not installed, download it from the [official Python website](https://www.python.org/downloads/).

---

### 2. Create a Virtual Environment

Create a virtual environment to isolate project dependencies:

```bash
python -m venv venv
```

Activate the environment:

* On Windows:

  ```bash
  venv\Scripts\activate
  ```
* On Mac/Linux:

  ```bash
  source venv/bin/activate
  ```

---

### 3. Install Dependencies

Install all required Python packages using:

```bash
pip install -r requirements.txt
```

---

### 4. Run the Development Server

Start the server:

```bash
python manage.py runserver
```

Visit your app in the browser at: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🧹 Handling Database Errors & Resetting Migrations

If you run into database/migration issues, follow these steps:

### Step 1: Delete Migrations

Remove all migration files (except `__init__.py`):

* On Mac/Linux:

  ```bash
  find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
  find . -path "*/migrations/*.pyc" -delete
  ```

* On Windows: Manually delete files in `your_app/migrations/`, except `__init__.py`.

---

### Step 2: Drop & Recreate the Database

* If using SQLite:

  * Mac/Linux:

    ```bash
    rm db.sqlite3
    ```
  * Windows (Command Prompt):

    ```cmd
    del db.sqlite3
    ```

* For PostgreSQL/MySQL: Drop and recreate the database via your DB tool.

---

### Step 3: Reapply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Step 4: Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

Follow the prompts to set up an admin account.

Or use this preset:

* Username: `xana`
* Password: `xana1234`

---

### Step 5: Run the Server Again

```bash
python manage.py runserver
```

---

🎉 You're all set! Your Django project should now be running smoothly.
