# BrightSmile Dental Clinic

A modern, full-featured dental clinic web application built with Flask, Bootstrap, and SQLAlchemy.

## Features

- Responsive, modern design with Bootstrap and custom CSS
- User registration, login, and authentication (Flask-Login)
- Admin panel with user and appointment management
- Dynamic content: appointments, notifications, analytics, etc.
- WTForms for all user input, with validation
- Real-time updates and notifications (Socket.IO)
- TBC Bank logo in footer, linking to [tbceducation.ge](https://tbceducation.ge)
- All JavaScript consolidated in `main.js`
- Accessible and mobile-friendly

## Pages

- Home
- Services
- About
- Team
- News
- Contact
- Register / Login
- Dashboard (user)
- Admin panel
- Analytics

## Setup

1. **Clone the repository:**
   ```bash
   git clone <your-github-repo-link>
   cd <project-folder>
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Unix/macOS:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database:**
   ```bash
   flask db upgrade
   python setup_admin.py  # To create the admin user
   ```

5. **Run the app:**
   ```bash
   flask run
   ```

6. **Access the site:**  
   Open [http://localhost:5000](http://localhost:5000) in your browser.

## Assignment Requirements Mapping

| Requirement                        | Status      |
|-------------------------------------|-------------|
| 5+ pages, navbar, base.html         | ✅           |
| CSS/Bootstrap, design               | ✅           |
| Dynamic content from DB             | ✅           |
| WTForms, validation, DB save        | ✅           |
| Flask-Login, registration, unique   | ✅           |
| Admin user, special features        | ✅           |
| TBC logo in footer, link            | ✅           |
| All JS in main.js                   | ✅           |

## Author

- Your Name
- [Your Email]

---

**When submitting:**  
Paste your deployed site link and GitHub repo link in the submission comment.

---

**Good luck!** #   n e w - p r o j e c t - f i n a l  
 