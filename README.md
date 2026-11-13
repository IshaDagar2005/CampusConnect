# CampusConnect: Academic Progress and Communication Portal

CampusConnect is a web-based academic progress and communication portal for faculty members and students, developed as a Minor Project for the Master of Computer Applications (MCA) programme at Vivekananda Institute of Professional Studies - Technical Campus (VIPS-TC), affiliated with Guru Gobind Singh Indraprastha University (GGSIPU), Delhi.

---

## 1. Guiding Principles & Architecture

CampusConnect satisfies all core principles specified in the synopsis:
- **One Academic Workspace (P1):** Coursework, lab practicals, project milestones, deadlines, and circulars are unified into a single portal.
- **Role-Based Access (P2):** Strict server-side role validation for Administrators, Faculty, and Students.
- **Clear Progress Status (P3):** Dynamic calculation of Submitted, Pending, Overdue, and Reviewed academic work.
- **Student Visibility (P4):** Personal dashboard with upcoming deadlines, instructions, and instructor feedback.
- **Timely Communication (P5):** Automated, opt-in Telegram Bot alerts for new tasks, deadlines, and notices.
- **Practical Implementation (P6):** Standard Python (Flask), SQLAlchemy, MySQL / SQLite relational database.
- **Privacy and Accountability (P7):** Passwords hashed using Werkzeug (`scrypt`), single-use tokens for Telegram linking, course-level authorization.
- **Zero Emojis:** Professional academic UI design with no emojis in labels, buttons, messages, or placeholders.

---

## 2. System Modules

1. **Module 1: Authentication & Role Management**
   - Student self-registration (min 8-character password, department tracking).
   - Faculty and administrator accounts provisioned by admin.
   - Server-side role protection decorators (`@roles`).

2. **Module 2: Course & Academic Task Management**
   - Course CRUD with semester, section, and academic year mapping.
   - Task creation across three types: **Assignment**, **Project**, and **Practical**.
   - Lifecycle state machine: `Draft` -> `Published` -> `Closed` -> `Archived`.
   - Search and filtering by Course, Type, Deadline, and Status.

3. **Module 3: Student Submission & Review**
   - File uploads validated for permitted extensions (PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, ZIP, TXT, PNG, JPG) and 12 MB file size limit.
   - Secure server-side file naming preventing collisions and directory traversal.
   - Faculty review workflow with status updates (`Reviewed` / `Resubmission Required`) and written feedback.

4. **Module 4: Notices & Communication**
   - Department-wide or course-targeted notices.
   - Students only see notices relevant to their enrolled courses.

5. **Module 5: Progress Dashboard & Analytics**
   - **Faculty View:** Aggregate metrics, course-wise summaries, and student-by-student completion matrix.
   - **Student View:** Total assigned, submitted, pending, overdue counts, and overall completion rate.

6. **Module 6: Telegram Bot Notifications**
   - Integration via Telegram Bot API (`https://api.telegram.org/bot<token>`).
   - Single-use 10-minute linking codes (`/link <code>`).
   - Private notifications for new tasks, faculty feedback, and upcoming deadlines.

---

## 3. Technology Stack

- **Backend:** Python 3, Flask 3.1, Flask-SQLAlchemy, Flask-Login, Werkzeug, Requests, PyMySQL
- **Frontend:** Semantic HTML5, CSS3 (DM Sans & Manrope typography), Vanilla JavaScript (no external CDN frameworks)
- **Database:** MySQL 8.0+ (production) / SQLite (development & local testing)
- **External API:** Telegram Bot API

---

## 4. Database Schema (Section VIII-D)

- `users` (user_id, full_name, email, password_hash, role, department)
- `courses` (course_id, course_name, course_code, semester, section, academic_year, faculty_id)
- `enrolments` (enrolment_id, student_id, course_id, joined_at)
- `tasks` (task_id, course_id, faculty_id, title, task_type, description, issue_date, deadline, status)
- `submissions` (submission_id, task_id, student_id, file_path, submitted_at, status, feedback)
- `notices` (notice_id, created_by, title, body, audience, publish_date)
- `telegram_links` (link_id, user_id, chat_id, linked_at, is_active)
- `telegram_codes` (id, user_id, code, expires_at, used)

---

## 5. Getting Started

### Prerequisites
- Python 3.10+
- MySQL Server (optional, SQLite works out of the box)

### Installation
1. Activate virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables in `.env`:
   ```bash
   # Copy example if needed
   cp .env.example .env
   ```
4. Run the application:
   ```bash
   python app.py
   ```
   Open your browser and navigate to `http://127.0.0.1:5000`.

### Default Seed Accounts
- **Administrator:**
  - Email: `ish.isha.dagar@gmail.com`
  - Password: `12345678`
- **Faculty:**
  - Email: `cosmena@vips.edu`
  - Password: `FacultyPass123`

---

## 6. Running Automated Tests

A comprehensive verification test suite covers all 10 sample test cases (TC1 - TC10) and security boundaries from the synopsis:
```bash
python -m unittest tests.py
```
All 12 unit and integration tests validate authentication, task lifecycle, role restrictions, file uploads, notice targeting, and Telegram notifications.
