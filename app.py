import os
import secrets
from datetime import datetime, timedelta
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    send_from_directory,
    jsonify,
)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(BASE_DIR, "campusconnect.db")
)

engine_options = {}

if database_url.startswith("mysql+pymysql://"):
    engine_options["connect_args"] = {
        "ssl": {
            "ca": "/etc/ssl/certs/ca-certificates.crt"
        }
    }

app = Flask(__name__)

# Render (and other hosts) should provide DATABASE_URL for the hosted database.
# Support common MySQL URLs by selecting the PyMySQL SQLAlchemy driver.
database_url = os.getenv(
    "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "campusconnect.db")
).strip()
if database_url.startswith("mysql://"):
    database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)

app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "campusconnect-development-secret-key-2026"),
    SQLALCHEMY_DATABASE_URI=database_url,
    SQLALCHEMY_ENGINE_OPTIONS=engine_options,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=int(os.getenv("MAX_CONTENT_LENGTH", 12 * 1024 * 1024)),
)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to access this page."
login_manager.login_message_category = "info"


# ==============================================================================
# DATABASE MODELS (Section VIII-D, Tables VI and VII)
# ==============================================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # admin, faculty, student
    department = db.Column(db.String(120), nullable=False, default="")

    # Relationships
    courses_taught = db.relationship("Course", back_populates="faculty")
    enrolments = db.relationship("Enrolment", back_populates="student", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", back_populates="student", cascade="all, delete-orphan")
    notices_created = db.relationship("Notice", back_populates="author", cascade="all, delete-orphan")
    telegram_link = db.relationship("TelegramLink", back_populates="user", uselist=False, cascade="all, delete-orphan")
    telegram_codes = db.relationship("TelegramCode", back_populates="user", cascade="all, delete-orphan")

    def get_id(self):
        return str(self.user_id)

    @property
    def id(self):
        return self.user_id

    @property
    def name(self):
        return self.full_name

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Course(db.Model):
    __tablename__ = "courses"

    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(150), nullable=False)
    course_code = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(20), nullable=False, default="")
    section = db.Column(db.String(20), nullable=False, default="")
    academic_year = db.Column(db.String(20), nullable=False, default="")
    faculty_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)

    # Relationships
    faculty = db.relationship("User", back_populates="courses_taught")
    enrolments = db.relationship("Enrolment", back_populates="course", cascade="all, delete-orphan")
    tasks = db.relationship("Task", back_populates="course", cascade="all, delete-orphan")

    @property
    def id(self):
        return self.course_id

    @property
    def name(self):
        return self.course_name

    @property
    def code(self):
        return self.course_code


class Enrolment(db.Model):
    __tablename__ = "enrolments"

    enrolment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )

    # Relationships
    student = db.relationship("User", back_populates="enrolments")
    course = db.relationship("Course", back_populates="enrolments")

    @property
    def id(self):
        return self.enrolment_id


class Task(db.Model):
    __tablename__ = "tasks"

    task_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    task_type = db.Column(db.String(30), nullable=False, default="Assignment")  # Assignment, Project, Practical
    description = db.Column(db.Text, nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Published")  # Draft, Published, Closed, Archived

    # Relationships
    course = db.relationship("Course", back_populates="tasks")
    faculty = db.relationship("User")
    submissions = db.relationship("Submission", back_populates="task", cascade="all, delete-orphan")

    @property
    def id(self):
        return self.task_id

    @property
    def kind(self):
        return self.task_type


class Submission(db.Model):
    __tablename__ = "submissions"

    submission_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Submitted")  # Submitted, Reviewed, Resubmission Required
    feedback = db.Column(db.Text, nullable=False, default="")

    __table_args__ = (
        db.UniqueConstraint("task_id", "student_id", name="uq_task_student"),
    )

    # Relationships
    task = db.relationship("Task", back_populates="submissions")
    student = db.relationship("User", back_populates="submissions")

    @property
    def id(self):
        return self.submission_id

    @property
    def filename(self):
        return self.file_path


class Notice(db.Model):
    __tablename__ = "notices"

    notice_id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    audience = db.Column(db.String(100), nullable=False, default="all")  # 'all' or str(course_id)
    publish_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    author = db.relationship("User", back_populates="notices_created")

    @property
    def id(self):
        return self.notice_id

    @property
    def created_at(self):
        return self.publish_date


class TelegramLink(db.Model):
    __tablename__ = "telegram_links"

    link_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    chat_id = db.Column(db.String(100), nullable=False)
    linked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="telegram_link")

    @property
    def id(self):
        return self.link_id


class TelegramCode(db.Model):
    __tablename__ = "telegram_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="telegram_codes")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ==============================================================================
# AUTHORISATION & HELPER FUNCTIONS
# ==============================================================================

def roles(*allowed_roles):
    """Enforces server-side role-based access control (Principle P2, SEC2)."""
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in allowed_roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_submission_status(task, student_id):
    """Determines submission lifecycle state (Table IX)."""
    sub = Submission.query.filter_by(task_id=task.task_id, student_id=student_id).first()
    if sub:
        return sub.status
    if datetime.utcnow() > task.deadline:
        return "Overdue"
    return "Pending"


def send_telegram(user, message_text):
    """Dispatches Telegram notifications to linked and active users (M6, SEC8)."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or not user:
        return False

    link = TelegramLink.query.filter_by(user_id=user.user_id, is_active=True).first()
    if not link or not link.chat_id:
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": link.chat_id,
            "text": message_text,
            "parse_mode": "HTML",
        }
        res = requests.post(url, json=payload, timeout=8)
        return res.ok
    except Exception:
        return False


def notify_task_published(task):
    """Alerts enrolled students when a new academic task is published (TC9)."""
    enrolments = Enrolment.query.filter_by(course_id=task.course_id).all()
    due_str = task.deadline.strftime("%d %b %Y, %I:%M %p")
    text = (
        f"<b>CampusConnect Academic Alert</b>\n"
        f"<b>New {task.task_type}:</b> {task.title}\n"
        f"<b>Course:</b> {task.course.course_code} - {task.course.course_name}\n"
        f"<b>Deadline:</b> {due_str}\n"
        f"Log in to the portal to view full instructions and submit work."
    )
    for e in enrolments:
        send_telegram(e.student, text)


def notify_notice_published(notice):
    """Alerts targeted audience when a notice is published (TC7)."""
    text = (
        f"<b>CampusConnect Notice</b>\n"
        f"<b>{notice.title}</b>\n\n"
        f"{notice.body[:400]}"
    )
    if notice.audience == "all":
        students = User.query.filter_by(role="student").all()
        for s in students:
            send_telegram(s, text)
    else:
        try:
            cid = int(notice.audience)
            enrolments = Enrolment.query.filter_by(course_id=cid).all()
            for e in enrolments:
                send_telegram(e.student, text)
        except (ValueError, TypeError):
            pass


@app.context_processor
def inject_globals():
    return {
        "app_name": "CampusConnect",
        "current_time": datetime.utcnow(),
    }


# ==============================================================================
# AUTHENTICATION ROUTES (Module 1, FR1)
# ==============================================================================

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        department = request.form.get("department", "").strip()

        if not full_name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists.", "error")
            return render_template("register.html")

        new_student = User(
            full_name=full_name,
            email=email,
            role="student",
            department=department,
        )
        new_student.set_password(password)
        db.session.add(new_student)
        db.session.commit()

        flash("Account created successfully. Please sign in to access your dashboard.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Signed in successfully.", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password. Please try again.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))


# ==============================================================================
# DASHBOARDS (FR2, FR11, Module 5)
# ==============================================================================

@app.route("/dashboard")
@login_required
def dashboard():
    # 1. Administrator Dashboard
    if current_user.role == "admin":
        total_users = User.query.count()
        total_courses = Course.query.count()
        total_tasks = Task.query.count()
        total_subs = Submission.query.count()
        recent_courses = Course.query.order_by(Course.course_id.desc()).limit(5).all()
        recent_users = User.query.order_by(User.user_id.desc()).limit(5).all()
        return render_template(
            "dashboard.html",
            role="admin",
            users=total_users,
            courses=total_courses,
            tasks=total_tasks,
            subs=total_subs,
            recent_courses=recent_courses,
            recent_users=recent_users,
        )

    # 2. Faculty Dashboard
    if current_user.role == "faculty":
        courses = Course.query.filter_by(faculty_id=current_user.user_id).all()
        course_ids = [c.course_id for c in courses]

        tasks = (
            Task.query.filter(Task.course_id.in_(course_ids))
            .order_by(Task.deadline.asc())
            .all()
            if course_ids
            else []
        )

        # Calculate Academic Progress Indicators (Table VIII)
        total_tasks = len(tasks)
        total_submitted = 0
        total_pending = 0
        total_overdue = 0
        total_reviewed = 0

        # Detailed per-course breakdown
        course_summaries = []
        for c in courses:
            c_tasks = [t for t in tasks if t.course_id == c.course_id]
            enrolled_count = Enrolment.query.filter_by(course_id=c.course_id).count()
            c_submitted = 0
            c_pending = 0
            c_overdue = 0
            c_reviewed = 0

            for t in c_tasks:
                subs = Submission.query.filter_by(task_id=t.task_id).all()
                c_submitted += len(subs)
                c_reviewed += len([s for s in subs if s.status == "Reviewed"])

                unsubmitted = max(0, enrolled_count - len(subs))
                if datetime.utcnow() > t.deadline:
                    c_overdue += unsubmitted
                else:
                    c_pending += unsubmitted

            c_total_expected = len(c_tasks) * enrolled_count
            c_rate = round((c_submitted / c_total_expected * 100), 1) if c_total_expected > 0 else 0

            course_summaries.append({
                "course": c,
                "tasks_count": len(c_tasks),
                "enrolled_count": enrolled_count,
                "submitted": c_submitted,
                "pending": c_pending,
                "overdue": c_overdue,
                "reviewed": c_reviewed,
                "submission_rate": c_rate,
            })

            total_submitted += c_submitted
            total_pending += c_pending
            total_overdue += c_overdue
            total_reviewed += c_reviewed

        total_expected = sum(cs["tasks_count"] * cs["enrolled_count"] for cs in course_summaries)
        submission_rate = round((total_submitted / total_expected * 100), 1) if total_expected > 0 else 0

        return render_template(
            "dashboard.html",
            role="faculty",
            courses=courses,
            tasks=tasks[:10],
            course_summaries=course_summaries,
            total_tasks=total_tasks,
            total_submitted=total_submitted,
            total_pending=total_pending,
            total_overdue=total_overdue,
            total_reviewed=total_reviewed,
            submission_rate=submission_rate,
        )

    # 3. Student Dashboard
    enrolments = Enrolment.query.filter_by(student_id=current_user.user_id).all()
    course_ids = [e.course_id for e in enrolments]

    # Only Published tasks are visible to students
    tasks = (
        Task.query.filter(Task.course_id.in_(course_ids), Task.status == "Published")
        .order_by(Task.deadline.asc())
        .all()
        if course_ids
        else []
    )

    task_rows = []
    submitted_count = 0
    pending_count = 0
    overdue_count = 0
    reviewed_count = 0

    for t in tasks:
        st = get_submission_status(t, current_user.user_id)
        task_rows.append((t, st))

        if st in ("Submitted", "Reviewed", "Resubmission Required"):
            submitted_count += 1
        if st == "Reviewed":
            reviewed_count += 1
        elif st == "Pending":
            pending_count += 1
        elif st == "Overdue":
            overdue_count += 1

    total_assigned = len(tasks)
    submission_rate = round((submitted_count / total_assigned * 100), 1) if total_assigned > 0 else 0

    # Targeted Notices (Section VI-B.4, TC7)
    notices = (
        Notice.query.filter(
            (Notice.audience == "all") | (Notice.audience.in_([str(cid) for cid in course_ids]))
        )
        .order_by(Notice.publish_date.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        role="student",
        enrolments=enrolments,
        task_rows=task_rows,
        notices=notices,
        total_assigned=total_assigned,
        submitted_count=submitted_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
        reviewed_count=reviewed_count,
        submission_rate=submission_rate,
    )


# ==============================================================================
# ACADEMIC TASK MANAGEMENT (FR3, FR4, FR5, FR6, Module 2)
# ==============================================================================

@app.route("/tasks")
@login_required
def tasks_list():
    """Lists tasks with filtering by course, task type, and status (Secondary Obj B.3)."""
    selected_course = request.args.get("course_id", type=int)
    selected_type = request.args.get("task_type", "").strip()
    selected_status = request.args.get("status", "").strip()
    search_query = request.args.get("q", "").strip()

    if current_user.role == "faculty":
        user_courses = Course.query.filter_by(faculty_id=current_user.user_id).all()
        allowed_course_ids = [c.course_id for c in user_courses]
    elif current_user.role == "student":
        enrolments = Enrolment.query.filter_by(student_id=current_user.user_id).all()
        user_courses = [e.course for e in enrolments]
        allowed_course_ids = [c.course_id for c in user_courses]
    else:  # admin
        user_courses = Course.query.all()
        allowed_course_ids = [c.course_id for c in user_courses]

    query = Task.query.filter(Task.course_id.in_(allowed_course_ids))

    # Students only see Published tasks in listings
    if current_user.role == "student":
        query = query.filter(Task.status == "Published")

    if selected_course and selected_course in allowed_course_ids:
        query = query.filter(Task.course_id == selected_course)

    if selected_type and selected_type in ("Assignment", "Project", "Practical"):
        query = query.filter(Task.task_type == selected_type)

    if search_query:
        query = query.filter(Task.title.ilike(f"%{search_query}%"))

    all_tasks = query.order_by(Task.deadline.asc()).all()

    # For students, filter by submission status if requested
    items = []
    for t in all_tasks:
        if current_user.role == "student":
            st = get_submission_status(t, current_user.user_id)
            if selected_status and st != selected_status:
                continue
            items.append((t, st))
        else:
            if selected_status and t.status != selected_status:
                continue
            items.append((t, t.status))

    return render_template(
        "tasks.html",
        items=items,
        courses=user_courses,
        selected_course=selected_course,
        selected_type=selected_type,
        selected_status=selected_status,
        search_query=search_query,
    )


@app.route("/tasks/new", methods=["GET", "POST"])
@roles("faculty", "admin")
def task_new():
    if current_user.role == "faculty":
        available_courses = Course.query.filter_by(faculty_id=current_user.user_id).all()
    else:
        available_courses = Course.query.all()

    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        title = request.form.get("title", "").strip()
        task_type = request.form.get("task_type", "Assignment")
        description = request.form.get("description", "").strip()
        deadline_raw = request.form.get("deadline", "")
        status = request.form.get("status", "Published")

        course = Course.query.get_or_404(course_id)
        if current_user.role == "faculty" and course.faculty_id != current_user.user_id:
            abort(403)

        if not title or not description or not deadline_raw:
            flash("All fields are required.", "error")
            return render_template("task_new.html", courses=available_courses)

        try:
            deadline = datetime.strptime(deadline_raw, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid deadline format.", "error")
            return render_template("task_new.html", courses=available_courses)

        task = Task(
            course_id=course.course_id,
            faculty_id=current_user.user_id,
            title=title,
            task_type=task_type,
            description=description,
            issue_date=datetime.utcnow(),
            deadline=deadline,
            status=status,
        )
        db.session.add(task)
        db.session.commit()

        # Send Telegram notification if published (TC9)
        if status == "Published":
            notify_task_published(task)

        flash(f"{task_type} published successfully.", "success")
        return redirect(url_for("task_detail", task_id=task.task_id))

    return render_template("task_new.html", courses=available_courses)


@app.route("/tasks/<int:task_id>")
@login_required
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)

    # Role and Enrolment Access Validation (TC4, SEC3, SEC4)
    if current_user.role == "student":
        enrolment = Enrolment.query.filter_by(
            student_id=current_user.user_id, course_id=task.course_id
        ).first()
        if not enrolment:
            abort(403)

        submission = Submission.query.filter_by(
            task_id=task.task_id, student_id=current_user.user_id
        ).first()
        computed_status = get_submission_status(task, current_user.user_id)

        return render_template(
            "task_detail.html",
            task=task,
            submission=submission,
            computed_status=computed_status,
        )

    # Faculty & Admin View
    if current_user.role == "faculty" and task.course.faculty_id != current_user.user_id:
        abort(403)

    enrolments = Enrolment.query.filter_by(course_id=task.course_id).all()
    submissions = Submission.query.filter_by(task_id=task.task_id).all()
    sub_map = {s.student_id: s for s in submissions}

    roster = []
    for e in enrolments:
        student_sub = sub_map.get(e.student_id)
        if student_sub:
            st = student_sub.status
        else:
            st = "Overdue" if datetime.utcnow() > task.deadline else "Pending"

        roster.append({
            "student": e.student,
            "submission": student_sub,
            "status": st,
        })

    return render_template(
        "task_detail.html",
        task=task,
        roster=roster,
        submissions_count=len(submissions),
        enrolled_count=len(enrolments),
    )


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@roles("faculty", "admin")
def task_edit(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user.role == "faculty" and task.course.faculty_id != current_user.user_id:
        abort(403)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        task_type = request.form.get("task_type", "Assignment")
        description = request.form.get("description", "").strip()
        deadline_raw = request.form.get("deadline", "")
        status = request.form.get("status", "Published")

        if not title or not description or not deadline_raw:
            flash("All fields are required.", "error")
            return render_template("task_edit.html", task=task)

        try:
            deadline = datetime.strptime(deadline_raw, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid deadline format.", "error")
            return render_template("task_edit.html", task=task)

        was_published = task.status == "Published"
        task.title = title
        task.task_type = task_type
        task.description = description
        task.deadline = deadline
        task.status = status
        db.session.commit()

        # If changed from Draft to Published, dispatch alert
        if not was_published and status == "Published":
            notify_task_published(task)

        flash("Task updated successfully.", "success")
        return redirect(url_for("task_detail", task_id=task.task_id))

    return render_template("task_edit.html", task=task)


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@roles("faculty", "admin")
def task_delete(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user.role == "faculty" and task.course.faculty_id != current_user.user_id:
        abort(403)

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted successfully.", "success")
    return redirect(url_for("tasks_list"))


# ==============================================================================
# SUBMISSION & REVIEW (FR7, FR8, FR9, Module 3, SEC5)
# ==============================================================================

@app.route("/tasks/<int:task_id>/submit", methods=["POST"])
@roles("student")
def submit_task(task_id):
    task = Task.query.get_or_404(task_id)

    # Check enrolment
    enrolment = Enrolment.query.filter_by(
        student_id=current_user.user_id, course_id=task.course_id
    ).first()
    if not enrolment:
        abort(403)

    if task.status == "Closed":
        flash("This task is closed. Submissions are no longer accepted.", "error")
        return redirect(url_for("task_detail", task_id=task.task_id))

    uploaded_file = request.files.get("file")
    allowed_exts = {
        "pdf", "doc", "docx", "ppt", "pptx", "xls", "xlsx",
        "zip", "txt", "png", "jpg", "jpeg"
    }

    if (
        not uploaded_file
        or not uploaded_file.filename
        or "." not in uploaded_file.filename
        or uploaded_file.filename.rsplit(".", 1)[1].lower() not in allowed_exts
    ):
        flash(
            "Please select a valid file in one of the permitted formats: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, ZIP, TXT, PNG, JPG.",
            "error",
        )
        return redirect(url_for("task_detail", task_id=task.task_id))

    safe_name = secure_filename(uploaded_file.filename)
    filename = f"{current_user.user_id}_{task.task_id}_{secrets.token_hex(4)}_{safe_name}"
    file_full_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    uploaded_file.save(file_full_path)

    submission = Submission.query.filter_by(
        task_id=task.task_id, student_id=current_user.user_id
    ).first()

    if not submission:
        submission = Submission(
            task_id=task.task_id,
            student_id=current_user.user_id,
            file_path=filename,
            submitted_at=datetime.utcnow(),
            status="Submitted",
            feedback="",
        )
        db.session.add(submission)
    else:
        # Replace existing file
        submission.file_path = filename
        submission.submitted_at = datetime.utcnow()
        submission.status = "Submitted"

    db.session.commit()
    flash("Your submission has been uploaded successfully.", "success")
    return redirect(url_for("task_detail", task_id=task.task_id))


@app.route("/submissions/<int:submission_id>/file")
@login_required
def submission_file(submission_id):
    """Secure file retrieval with strict access control (SEC3, SEC4)."""
    sub = Submission.query.get_or_404(submission_id)

    if current_user.role == "student" and sub.student_id != current_user.user_id:
        abort(403)
    if current_user.role == "faculty" and sub.task.course.faculty_id != current_user.user_id:
        abort(403)

    return send_from_directory(
        app.config["UPLOAD_FOLDER"], sub.file_path, as_attachment=True
    )


@app.route("/submissions/<int:submission_id>/review", methods=["POST"])
@roles("faculty", "admin")
def review_submission(submission_id):
    sub = Submission.query.get_or_404(submission_id)
    if current_user.role == "faculty" and sub.task.course.faculty_id != current_user.user_id:
        abort(403)

    new_status = request.form.get("status", "Reviewed")
    feedback = request.form.get("feedback", "").strip()

    if new_status not in ("Reviewed", "Resubmission Required"):
        flash("Invalid review status.", "error")
        return redirect(url_for("task_detail", task_id=sub.task_id))

    sub.status = new_status
    sub.feedback = feedback
    db.session.commit()

    # Dispatch Telegram notification to student (TC6)
    telegram_msg = (
        f"<b>CampusConnect Submission Update</b>\n"
        f"<b>Task:</b> {sub.task.title}\n"
        f"<b>Status:</b> {new_status}\n"
        f"<b>Feedback:</b> {feedback or 'No written comments.'}\n"
        f"Log in to the portal for full details."
    )
    send_telegram(sub.student, telegram_msg)

    flash("Review and feedback saved successfully.", "success")
    return redirect(url_for("task_detail", task_id=sub.task_id))


# ==============================================================================
# NOTICES & COMMUNICATION (FR10, Module 4, TC7)
# ==============================================================================

@app.route("/notices")
@login_required
def notices_list():
    if current_user.role == "student":
        enrolments = Enrolment.query.filter_by(student_id=current_user.user_id).all()
        c_ids = [str(e.course_id) for e in enrolments]
        notices = (
            Notice.query.filter((Notice.audience == "all") | (Notice.audience.in_(c_ids)))
            .order_by(Notice.publish_date.desc())
            .all()
        )
    else:
        notices = Notice.query.order_by(Notice.publish_date.desc()).all()

    return render_template("notices.html", notices=notices)


@app.route("/notices/new", methods=["GET", "POST"])
@roles("faculty", "admin")
def notice_new():
    if current_user.role == "faculty":
        courses = Course.query.filter_by(faculty_id=current_user.user_id).all()
    else:
        courses = Course.query.all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        audience = request.form.get("audience", "all").strip()

        if not title or not body:
            flash("Title and body are required.", "error")
            return render_template("notice_new.html", courses=courses)

        notice = Notice(
            created_by=current_user.user_id,
            title=title,
            body=body,
            audience=audience,
            publish_date=datetime.utcnow(),
        )
        db.session.add(notice)
        db.session.commit()

        notify_notice_published(notice)
        flash("Notice published successfully.", "success")
        return redirect(url_for("notices_list"))

    return render_template("notice_new.html", courses=courses)


@app.route("/notices/<int:notice_id>/delete", methods=["POST"])
@roles("faculty", "admin")
def notice_delete(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    if current_user.role == "faculty" and notice.created_by != current_user.user_id:
        abort(403)

    db.session.delete(notice)
    db.session.commit()
    flash("Notice removed successfully.", "success")
    return redirect(url_for("notices_list"))


# ==============================================================================
# PROGRESS DASHBOARD & ANALYTICS (Section IX-C, IX-E, Table VIII)
# ==============================================================================

@app.route("/progress")
@roles("faculty", "admin")
def progress():
    """Detailed Course-wise Progress and Student Tracking Matrix."""
    if current_user.role == "faculty":
        courses = Course.query.filter_by(faculty_id=current_user.user_id).all()
    else:
        courses = Course.query.all()

    selected_course_id = request.args.get("course_id", type=int)
    selected_course = None
    student_matrix = []

    course_stats = []
    for c in courses:
        tasks = Task.query.filter_by(course_id=c.course_id).all()
        enrolments = Enrolment.query.filter_by(course_id=c.course_id).all()
        enrolled_count = len(enrolments)
        task_count = len(tasks)

        total_reqs = task_count * enrolled_count
        submitted_count = 0
        reviewed_count = 0
        overdue_count = 0
        pending_count = 0

        for t in tasks:
            subs = Submission.query.filter_by(task_id=t.task_id).all()
            submitted_count += len(subs)
            reviewed_count += len([s for s in subs if s.status == "Reviewed"])

            unsubmitted = max(0, enrolled_count - len(subs))
            if datetime.utcnow() > t.deadline:
                overdue_count += unsubmitted
            else:
                pending_count += unsubmitted

        rate = round((submitted_count / total_reqs * 100), 1) if total_reqs > 0 else 0

        course_stats.append({
            "course": c,
            "tasks_count": task_count,
            "enrolled_count": enrolled_count,
            "total_reqs": total_reqs,
            "submitted": submitted_count,
            "reviewed": reviewed_count,
            "pending": pending_count,
            "overdue": overdue_count,
            "rate": rate,
        })

        if selected_course_id and c.course_id == selected_course_id:
            selected_course = c
            # Build student-by-student matrix for this course
            for e in enrolments:
                st_submitted = 0
                st_reviewed = 0
                st_pending = 0
                st_overdue = 0

                for t in tasks:
                    sub = Submission.query.filter_by(task_id=t.task_id, student_id=e.student_id).first()
                    if sub:
                        st_submitted += 1
                        if sub.status == "Reviewed":
                            st_reviewed += 1
                    else:
                        if datetime.utcnow() > t.deadline:
                            st_overdue += 1
                        else:
                            st_pending += 1

                st_rate = round((st_submitted / task_count * 100), 1) if task_count > 0 else 0
                student_matrix.append({
                    "student": e.student,
                    "submitted": st_submitted,
                    "reviewed": st_reviewed,
                    "pending": st_pending,
                    "overdue": st_overdue,
                    "rate": st_rate,
                })

    return render_template(
        "progress.html",
        courses=courses,
        course_stats=course_stats,
        selected_course=selected_course,
        student_matrix=student_matrix,
    )


# ==============================================================================
# TELEGRAM BOT INTEGRATION (FR12, FR13, Module 6, SEC7, TC8, TC10)
# ==============================================================================

@app.route("/telegram")
@login_required
def telegram_page():
    link = TelegramLink.query.filter_by(user_id=current_user.user_id).first()
    active_code = (
        TelegramCode.query.filter_by(user_id=current_user.user_id, used=False)
        .filter(TelegramCode.expires_at > datetime.utcnow())
        .first()
    )
    bot_name = os.getenv("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")

    return render_template(
        "telegram.html",
        link=link,
        code=active_code,
        bot_username=bot_name,
    )


@app.route("/telegram/code", methods=["POST"])
@login_required
def telegram_code():
    """Generates a secure, single-use, 10-minute linking code (SEC7, TC8)."""
    TelegramCode.query.filter_by(user_id=current_user.user_id, used=False).update({"used": True})

    token = secrets.token_urlsafe(12)
    code = TelegramCode(
        user_id=current_user.user_id,
        code=token,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
    )
    db.session.add(code)
    db.session.commit()

    flash("One-time linking code generated. Send this code to the Telegram bot within 10 minutes.", "success")
    return redirect(url_for("telegram_page"))


@app.route("/telegram/test", methods=["POST"])
@login_required
def telegram_test():
    ok = send_telegram(
        current_user,
        "<b>CampusConnect Test Notification</b>\nYour Telegram account is connected and ready to receive updates.",
    )
    if ok:
        flash("Test message delivered to Telegram.", "success")
    else:
        flash("Could not deliver message. Ensure you have started the bot in Telegram.", "error")
    return redirect(url_for("telegram_page"))


@app.route("/telegram/unlink", methods=["POST"])
@login_required
def telegram_unlink():
    link = TelegramLink.query.filter_by(user_id=current_user.user_id).first()
    if link:
        db.session.delete(link)
        db.session.commit()
        flash("Your Telegram account has been unlinked.", "success")
    return redirect(url_for("telegram_page"))


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    """Processes bot updates via Telegram webhook."""
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    if secret:
        hdr = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if hdr != secret:
            abort(403)

    data = request.get_json(silent=True) or {}
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id or not text:
        return jsonify({"ok": True})

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    def reply(msg):
        if bot_token:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"},
                    timeout=8,
                )
            except requests.RequestException:
                pass

    if text.startswith("/start"):
        reply(
            "Welcome to CampusConnect Notification Bot.\n\n"
            "To link your account, generate a one-time code on the portal (under the Telegram page) and send:\n"
            "<code>/link YOUR_CODE</code>"
        )
        return jsonify({"ok": True})

    if text.startswith("/link"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            reply("Please provide your code. Example: <code>/link abc123xyz</code>")
            return jsonify({"ok": True})

        code_val = parts[1].strip()
        code_record = TelegramCode.query.filter_by(code=code_val, used=False).first()

        if not code_record or code_record.expires_at < datetime.utcnow():
            reply("This code is invalid or has expired. Please generate a new code in CampusConnect.")
            return jsonify({"ok": True})

        # Link chat ID to authenticated user
        link = TelegramLink.query.filter_by(user_id=code_record.user_id).first()
        if link:
            link.chat_id = str(chat_id)
            link.is_active = True
            link.linked_at = datetime.utcnow()
        else:
            link = TelegramLink(
                user_id=code_record.user_id,
                chat_id=str(chat_id),
                linked_at=datetime.utcnow(),
                is_active=True,
            )
            db.session.add(link)

        code_record.used = True
        db.session.commit()

        user = User.query.get(code_record.user_id)
        reply(
            f"Success! Your Telegram account has been linked to {user.full_name} ({user.email}). "
            f"You will now receive notifications for new tasks, deadlines, and announcements."
        )
        return jsonify({"ok": True})

    reply("Unrecognized command. Use /start for instructions or /link <code> to connect your account.")
    return jsonify({"ok": True})


@app.route("/telegram/reminders", methods=["POST", "GET"])
@roles("faculty", "admin")
def dispatch_reminders():
    """Planned Enhancement E1: Automated deadline reminder service for approaching deadlines."""
    now = datetime.utcnow()
    reminder_window = now + timedelta(hours=24)

    approaching_tasks = Task.query.filter(
        Task.status == "Published",
        Task.deadline > now,
        Task.deadline <= reminder_window,
    ).all()

    sent_count = 0
    for t in approaching_tasks:
        enrolments = Enrolment.query.filter_by(course_id=t.course_id).all()
        for e in enrolments:
            sub = Submission.query.filter_by(task_id=t.task_id, student_id=e.student_id).first()
            if not sub:
                due_str = t.deadline.strftime("%d %b %Y, %I:%M %p")
                msg = (
                    f"<b>CampusConnect Deadline Reminder</b>\n"
                    f"<b>Task:</b> {t.title}\n"
                    f"<b>Course:</b> {t.course.course_code}\n"
                    f"<b>Deadline:</b> {due_str}\n"
                    f"This task is due in less than 24 hours. Please submit your work on time."
                )
                if send_telegram(e.student, msg):
                    sent_count += 1

    flash(f"Dispatched {sent_count} deadline reminder alerts.", "success")
    return redirect(url_for("dashboard"))


# ==============================================================================
# ADMINISTRATOR MANAGEMENT (AC1, Scope S1, S3)
# ==============================================================================

@app.route("/admin/users", methods=["GET", "POST"])
@roles("admin")
def admin_users():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "student")
        department = request.form.get("department", "").strip()

        if role not in ("admin", "faculty", "student"):
            abort(400)

        if not full_name or not email or not password:
            flash("Name, email, and password are required.", "error")
            return redirect(url_for("admin_users"))

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("admin_users"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return redirect(url_for("admin_users"))

        new_user = User(
            full_name=full_name,
            email=email,
            role=role,
            department=department,
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash(f"User account created for {full_name} ({role}).", "success")
        return redirect(url_for("admin_users"))

    all_users = User.query.order_by(User.role.asc(), User.full_name.asc()).all()
    return render_template("users.html", users=all_users)


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@roles("admin")
def admin_user_delete(user_id):
    if user_id == current_user.user_id:
        flash("You cannot delete your own administrator account.", "error")
        return redirect(url_for("admin_users"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User account deleted.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/courses", methods=["GET", "POST"])
@roles("admin")
def admin_courses():
    if request.method == "POST":
        course_name = request.form.get("course_name", "").strip()
        course_code = request.form.get("course_code", "").strip().upper()
        semester = request.form.get("semester", "").strip()
        section = request.form.get("section", "").strip()
        academic_year = request.form.get("academic_year", "").strip()
        faculty_id = request.form.get("faculty_id", type=int)

        if not course_name or not course_code:
            flash("Course name and course code are required.", "error")
            return redirect(url_for("admin_courses"))

        course = Course(
            course_name=course_name,
            course_code=course_code,
            semester=semester,
            section=section,
            academic_year=academic_year,
            faculty_id=faculty_id if faculty_id else None,
        )
        db.session.add(course)
        db.session.commit()

        flash(f"Course {course_code} created successfully.", "success")
        return redirect(url_for("admin_courses"))

    courses = Course.query.order_by(Course.course_code.asc()).all()
    faculty_list = User.query.filter_by(role="faculty").order_by(User.full_name.asc()).all()
    return render_template("courses.html", courses=courses, faculty=faculty_list)


@app.route("/admin/courses/<int:course_id>/delete", methods=["POST"])
@roles("admin")
def admin_course_delete(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Course deleted successfully.", "success")
    return redirect(url_for("admin_courses"))


@app.route("/admin/enrolments", methods=["GET", "POST"])
@roles("admin")
def admin_enrolments():
    if request.method == "POST":
        student_id = request.form.get("student_id", type=int)
        course_id = request.form.get("course_id", type=int)

        if not student_id or not course_id:
            flash("Please select both a student and a course.", "error")
            return redirect(url_for("admin_enrolments"))

        existing = Enrolment.query.filter_by(student_id=student_id, course_id=course_id).first()
        if existing:
            flash("Student is already enrolled in this course.", "error")
            return redirect(url_for("admin_enrolments"))

        enrolment = Enrolment(
            student_id=student_id,
            course_id=course_id,
            joined_at=datetime.utcnow(),
        )
        db.session.add(enrolment)
        db.session.commit()

        flash("Student enrolled successfully.", "success")
        return redirect(url_for("admin_enrolments"))

    students = User.query.filter_by(role="student").order_by(User.full_name.asc()).all()
    courses = Course.query.order_by(Course.course_code.asc()).all()
    enrolments = Enrolment.query.order_by(Enrolment.enrolment_id.desc()).all()
    return render_template(
        "enrolments.html",
        students=students,
        courses=courses,
        enrolments=enrolments,
    )


@app.route("/admin/enrolments/<int:enrolment_id>/delete", methods=["POST"])
@roles("admin")
def admin_enrolment_delete(enrolment_id):
    enrolment = Enrolment.query.get_or_404(enrolment_id)
    db.session.delete(enrolment)
    db.session.commit()
    flash("Enrolment removed.", "success")
    return redirect(url_for("admin_enrolments"))


# ==============================================================================
# ERROR HANDLERS (NFR3, Usability)
# ==============================================================================

@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code="400", message="Bad request. Please verify the submitted data."), 400


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code="403", message="Access denied. You do not have permission to view or manage this academic resource."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code="404", message="The requested resource or page could not be found."), 404


@app.errorhandler(413)
def request_entity_too_large(e):
    return render_template("error.html", code="413", message="File upload exceeds the 12 MB limit. Please select a smaller file."), 413


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code="500", message="An unexpected server error occurred. Please contact the administrator."), 500


# ==============================================================================
# DATABASE SEEDING & INITIALISATION
# ==============================================================================

def init_db():
    with app.app_context():
        db.create_all()

        # Seed Administrator Account from Environment
        admin_email = os.getenv("ADMIN_EMAIL", "ish.isha.dagar@gmail.com").strip().lower()
        admin_password = os.getenv("ADMIN_PASSWORD", "12345678")
        admin_name = os.getenv("ADMIN_NAME", "Isha Dagar")
        admin_dept = os.getenv("ADMIN_DEPARTMENT", "Computer Applications")

        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                full_name=admin_name,
                email=admin_email,
                role="admin",
                department=admin_dept,
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()

        # Seed baseline faculty and sample courses if none exist
        if Course.query.count() == 0:
            faculty = User.query.filter_by(role="faculty").first()
            if not faculty:
                faculty = User(
                    full_name="Dr. Cosmena",
                    email="cosmena@vips.edu",
                    role="faculty",
                    department="Computer Applications",
                )
                faculty.set_password("FacultyPass123")
                db.session.add(faculty)
                db.session.commit()

            c1 = Course(
                course_name="Advanced Java Programming",
                course_code="MCA-101",
                semester="1",
                section="B",
                academic_year="2026-2027",
                faculty_id=faculty.user_id,
            )
            c2 = Course(
                course_name="Web Technologies & Frameworks",
                course_code="MCA-103",
                semester="1",
                section="B",
                academic_year="2026-2027",
                faculty_id=faculty.user_id,
            )
            c3 = Course(
                course_name="Software Engineering & Design",
                course_code="MCA-105",
                semester="1",
                section="B",
                academic_year="2026-2027",
                faculty_id=faculty.user_id,
            )
            db.session.add_all([c1, c2, c3])
            db.session.commit()

            # Seed sample published task
            sample_task = Task(
                course_id=c1.course_id,
                faculty_id=faculty.user_id,
                title="Practical Assignment 1: Thread Synchronization in Java",
                task_type="Assignment",
                description=(
                    "Implement a producer-consumer solution using Java multithreading and wait/notify synchronization. "
                    "Submit your source code and execution output report in a single PDF or ZIP archive."
                ),
                issue_date=datetime.utcnow() - timedelta(days=2),
                deadline=datetime.utcnow() + timedelta(days=5),
                status="Published",
            )
            db.session.add(sample_task)

            # Seed sample notice
            notice = Notice(
                created_by=faculty.user_id,
                title="MCA Semester 1 Laboratory Schedule",
                body=(
                    "All students of MCA 1 (B) must bring their practical notebooks for verification "
                    "during the scheduled lab hours on Monday."
                ),
                audience="all",
                publish_date=datetime.utcnow(),
            )
            db.session.add(notice)
            db.session.commit()


# Gunicorn imports this module rather than executing it as __main__.
# Initialise tables and seed the configured administrator on every app startup.
init_db()

if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=debug_mode)
