# Project Setup Guide

## 1. Install Homebrew

Make sure Homebrew is installed on your system.

Verify the installation:

```bash
brew --version
```

## 2. Install PostgreSQL 17

Install PostgreSQL using Homebrew:

```bash
brew install postgresql@17
```

Verify the installation:

```bash
psql --version
```

## 3. Navigate to the Project Directory

Open Terminal and move to your project directory:

```bash
cd /path/to/project
```

## 4. Activate the Virtual Environment

Activate the Python virtual environment:

```bash
source venv/bin/activate
```

## 5. Install Project Dependencies

Install Django and Django REST Framework:

```bash
pip install django djangorestframework
```

Alternatively, if your project contains a `requirements.txt` file, install all dependencies using:

```bash
pip install -r requirements.txt
```

## 6. Install PostgreSQL Driver

For PostgreSQL support, install the Psycopg driver:

```bash
pip install "psycopg[binary]"
```

## 7. Verify Installed Packages

You can verify the installed packages with:

```bash
pip list
```
