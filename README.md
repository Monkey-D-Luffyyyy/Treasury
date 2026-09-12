# 🏛️ E.L.I.T.E Treasury Management System

> **Elevating Leaders Innovatively - Training & Excellence**

A centralized, web-based Treasury Management System built for the E.L.I.T.E Organization. It streamlines fund collection, member tracking, expense management, and financial reporting into one intuitive dashboard.

## ✨ Key Features

- **📊 Interactive Dashboard**: Real-time overview of total members, expected funds, collected amounts, and outstanding balances per team.
- **👥 Member Masterlist**: Complete CRUD operations with advanced filtering (Team, Department, Year, Section, Status).
- **💰 Smart Fund Collection**: 
  - Custom Fund Periods (e.g., "September Week 1").
  - Quick "Tap-to-Pay" interface for rapid daily/weekly collections.
  - Supports partial payments (e.g., ₱10/day) with automatic remaining balance tracking.
- **📒 Treasury Ledger**: Unified view of all income (contributions) and expenses with running balance calculations.
- **📝 Notes & Reminders**: Built-in to-do list and deadline tracker for the Treasurer.
- **🎨 Modern UI/UX**: Fully responsive design built with Tailwind CSS, featuring the official E.L.I.T.E branding and color palette.

## 🛠️ Tech Stack

- **Backend**: Python 3.x, Django 5.x
- **Database**: SQLite3 (Development) / MySQL (Production-ready)
- **Frontend**: HTML5, Tailwind CSS (via CDN), Vanilla JavaScript
- **Version Control**: Git & GitHub

---

## 💻 Setup Instructions (For New PC)

Follow these steps to get the project running on a new machine:

### 1. Prerequisites
Make sure you have installed:
- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

### 2. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME


Setup Virtual Environment

# Windows
- python -m venv venv
- venv\Scripts\activate

# Mac/Linux
- python3 -m venv venv
- source venv/bin/activate

#Install Dependencies
- pip install -r requirements.txt

#Database Setup

**# Apply migrations to create the database tables
- python manage.py migrate

# Create a superuser account to access the admin panel
- python manage.py createsuperuser**


#Seed Dummy Data
- python manage.py shell
