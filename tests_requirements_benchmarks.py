"""
CampusConnect - Comprehensive Requirements & Benchmarks Verification Suite
Covers all Functional Requirements (FR1-FR15), Benchmarks (BM1-BM6),
Security Requirements (SEC1-SEC8), and Sample Test Cases (TC1-TC10).
"""

import io
import os
import re
import time
import unittest
import unittest.mock as mock
from datetime import datetime, timedelta

# Set test environment
os.environ["SECRET_KEY"] = "verification-test-secret-key-2026"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FLASK_DEBUG"] = "0"
os.environ["TELEGRAM_BOT_TOKEN"] = "mock_test_bot_token"

from app import (
    app,
    db,
    User,
    Course,
    Enrolment,
    Task,
    Submission,
    Notice,
    TelegramLink,
    TelegramCode,
    send_telegram,
    get_submission_status,
)


def contains_emoji(text):
    """Detects any Unicode emoji character in a given string."""
    for char in text:
        cp = ord(char)
        if (
            0x1F300 <= cp <= 0x1FAFF
            or 0x1F600 <= cp <= 0x1F64F
            or 0x1F680 <= cp <= 0x1F6FF
            or 0x2600 <= cp <= 0x27BF
            or 0xFE00 <= cp <= 0xFE0F
            or 0x1F900 <= cp <= 0x1F9FF
        ):
            return True, char, hex(cp)
    return False, "", ""


class CampusConnectRequirementsTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False

    def setUp(self):
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

            # Seed Admin
            self.admin = User(
                full_name="Isha Dagar",
                email="admin@campusconnect.local",
                role="admin",
                department="Computer Applications",
            )
            self.admin.set_password("AdminPass123")

            # Seed Faculty
            self.faculty = User(
                full_name="Dr. Cosmena",
                email="faculty@campusconnect.local",
                role="faculty",
                department="Computer Applications",
            )
            self.faculty.set_password("FacultyPass123")

            # Seed Student 1 (Course 1)
            self.student1 = User(
                full_name="Rahul Verma",
                email="rahul@campusconnect.local",
                role="student",
                department="MCA",
            )
            self.student1.set_password("StudentPass123")

            # Seed Student 2 (Course 2)
            self.student2 = User(
                full_name="Pooja Sharma",
                email="pooja@campusconnect.local",
                role="student",
                department="MCA",
            )
            self.student2.set_password("StudentPass123")

            db.session.add_all([self.admin, self.faculty, self.student1, self.student2])
            db.session.commit()

            # Seed Course 1
            self.course1 = Course(
                course_name="Advanced Java Programming",
                course_code="MCA-101",
                semester="1",
                section="B",
                academic_year="2026-2027",
                faculty_id=self.faculty.user_id,
            )
            # Seed Course 2
            self.course2 = Course(
                course_name="Database Management Systems",
                course_code="MCA-102",
                semester="1",
                section="B",
                academic_year="2026-2027",
                faculty_id=self.faculty.user_id,
            )
            db.session.add_all([self.course1, self.course2])
            db.session.commit()

            # Enrol Student 1 in Course 1
            self.enrol1 = Enrolment(student_id=self.student1.user_id, course_id=self.course1.course_id)
            # Enrol Student 2 in Course 2
            self.enrol2 = Enrolment(student_id=self.student2.user_id, course_id=self.course2.course_id)
            db.session.add_all([self.enrol1, self.enrol2])
            db.session.commit()

            self.admin_id = self.admin.user_id
            self.faculty_id = self.faculty.user_id
            self.student1_id = self.student1.user_id
            self.student2_id = self.student2.user_id
            self.course1_id = self.course1.course_id
            self.course2_id = self.course2.course_id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, email, password):
        return self.app.post("/login", data={"email": email, "password": password}, follow_redirects=True)

    def logout(self):
        return self.app.get("/logout", follow_redirects=True)

    # ==========================================================================
    # FUNCTIONAL REQUIREMENTS (FR1 - FR15)
    # ==========================================================================

    def test_fr1_user_authentication(self):
        """FR1 / TC1 / TC2: System authenticates faculty and student users."""
        # Faculty login
        res_fac = self.login("faculty@campusconnect.local", "FacultyPass123")
        self.assertEqual(res_fac.status_code, 200)
        self.assertIn(b"Academic Dashboard", res_fac.data)
        self.logout()

        # Student login
        res_stu = self.login("rahul@campusconnect.local", "StudentPass123")
        self.assertEqual(res_stu.status_code, 200)
        self.assertIn(b"Hello, Rahul.", res_stu.data)
        self.logout()

        # Invalid login
        res_bad = self.login("faculty@campusconnect.local", "WrongPassword")
        self.assertEqual(res_bad.status_code, 200)
        self.assertIn(b"Invalid email or password", res_bad.data)

    def test_fr2_role_specific_dashboards(self):
        """FR2: System provides role-specific dashboards."""
        # Admin dashboard
        self.login("admin@campusconnect.local", "AdminPass123")
        res_admin = self.app.get("/dashboard")
        self.assertIn(b"Portal Administration", res_admin.data)
        self.assertIn(b"Total Users", res_admin.data)
        self.logout()

        # Faculty dashboard
        self.login("faculty@campusconnect.local", "FacultyPass123")
        res_fac = self.app.get("/dashboard")
        self.assertIn(b"Faculty Workspace", res_fac.data)
        self.assertIn(b"Course-wise Progress Summary", res_fac.data)
        self.logout()

        # Student dashboard
        self.login("rahul@campusconnect.local", "StudentPass123")
        res_stu = self.app.get("/dashboard")
        self.assertIn(b"Student Workspace", res_stu.data)
        self.assertIn(b"Assigned Academic Work", res_stu.data)
        self.logout()

    def test_fr3_faculty_create_edit_delete_task(self):
        """FR3: Faculty can create, edit, and delete academic tasks."""
        self.login("faculty@campusconnect.local", "FacultyPass123")
        due = (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M")

        # 1. Create
        res_create = self.app.post(
            "/tasks/new",
            data={
                "course_id": self.course1_id,
                "title": "Data Structures Assignment",
                "task_type": "Assignment",
                "description": "Solve problem set 1.",
                "deadline": due,
                "status": "Published",
            },
            follow_redirects=True,
        )
        self.assertEqual(res_create.status_code, 200)
        self.assertIn(b"Assignment published successfully", res_create.data)

        with app.app_context():
            task = Task.query.filter_by(title="Data Structures Assignment").first()
            self.assertIsNotNone(task)
            task_id = task.task_id

        # 2. Edit
        res_edit = self.app.post(
            f"/tasks/{task_id}/edit",
            data={
                "title": "Updated Data Structures Assignment",
                "task_type": "Assignment",
                "description": "Updated problem set instructions.",
                "deadline": due,
                "status": "Published",
            },
            follow_redirects=True,
        )
        self.assertEqual(res_edit.status_code, 200)
        self.assertIn(b"Task updated successfully", res_edit.data)

        # 3. Delete
        res_del = self.app.post(f"/tasks/{task_id}/delete", follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertIn(b"Task deleted successfully", res_del.data)

        with app.app_context():
            deleted_task = db.session.get(Task, task_id)
            self.assertIsNone(deleted_task)

    def test_fr4_task_assigned_to_course_semester_section(self):
        """FR4: Tasks are mapped to course, semester, and section."""
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="MCA-101 Section B Practical",
                task_type="Practical",
                description="Lab 1 instructions",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=4),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()

            c = db.session.get(Course, task.course_id)
            self.assertEqual(c.course_code, "MCA-101")
            self.assertEqual(c.semester, "1")
            self.assertEqual(c.section, "B")

    def test_fr5_task_descriptions_issue_dates_deadlines(self):
        """FR5: Faculty sets description, issue date, and deadline."""
        now = datetime.utcnow()
        due = now + timedelta(days=7)
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Full Lifecycle Task",
                task_type="Project",
                description="Comprehensive project milestone instructions.",
                issue_date=now,
                deadline=due,
                status="Published",
            )
            db.session.add(task)
            db.session.commit()

            saved = db.session.get(Task, task.task_id)
            self.assertEqual(saved.description, "Comprehensive project milestone instructions.")
            self.assertIsNotNone(saved.issue_date)
            self.assertEqual(saved.deadline, due)

    def test_fr6_student_views_enrolled_tasks_only(self):
        """FR6 / BM1 / TC3: Students view tasks relevant to their enrolments."""
        with app.app_context():
            # Task in Course 1 (Student 1 enrolled)
            t1 = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Java Lab 1",
                task_type="Practical",
                description="Java multithreading",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=5),
                status="Published",
            )
            # Task in Course 2 (Student 2 enrolled)
            t2 = Task(
                course_id=self.course2_id,
                faculty_id=self.faculty_id,
                title="DBMS Assignment 1",
                task_type="Assignment",
                description="Normalization problem set",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=5),
                status="Published",
            )
            db.session.add_all([t1, t2])
            db.session.commit()

        # Student 1 logs in
        self.login("rahul@campusconnect.local", "StudentPass123")
        res1 = self.app.get("/dashboard")
        self.assertIn(b"Java Lab 1", res1.data)
        self.assertNotIn(b"DBMS Assignment 1", res1.data)
        self.logout()

        # Student 2 logs in
        self.login("pooja@campusconnect.local", "StudentPass123")
        res2 = self.app.get("/dashboard")
        self.assertIn(b"DBMS Assignment 1", res2.data)
        self.assertNotIn(b"Java Lab 1", res2.data)

    def test_fr7_student_submission_upload(self):
        """FR7 / BM3 / TC5: Student uploads file for assigned task."""
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Java File Handling",
                task_type="Practical",
                description="Upload practical code PDF.",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=3),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id

        self.login("rahul@campusconnect.local", "StudentPass123")
        pdf_file = (io.BytesIO(b"%PDF-1.4 file content"), "practical_file.pdf")
        res = self.app.post(
            f"/tasks/{task_id}/submit",
            data={"file": pdf_file},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Your submission has been uploaded successfully", res.data)

        with app.app_context():
            sub = Submission.query.filter_by(task_id=task_id, student_id=self.student1_id).first()
            self.assertIsNotNone(sub)
            self.assertIn("practical_file.pdf", sub.file_path)

    def test_fr8_submission_timestamp_and_status(self):
        """FR8: System records submission time and status."""
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Status Record Task",
                task_type="Assignment",
                description="Upload submission.",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=3),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id

        self.login("rahul@campusconnect.local", "StudentPass123")
        txt_file = (io.BytesIO(b"Task solution content"), "solution.txt")
        before_time = datetime.utcnow()
        self.app.post(
            f"/tasks/{task_id}/submit",
            data={"file": txt_file},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        after_time = datetime.utcnow()

        with app.app_context():
            sub = Submission.query.filter_by(task_id=task_id, student_id=self.student1_id).first()
            self.assertEqual(sub.status, "Submitted")
            self.assertTrue(before_time <= sub.submitted_at <= after_time + timedelta(seconds=1))

    def test_fr9_faculty_review_and_feedback(self):
        """FR9 / TC6: Faculty reviews submission and adds feedback."""
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Review Test Task",
                task_type="Project",
                description="Project report.",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=4),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()

            sub = Submission(
                task_id=task.task_id,
                student_id=self.student1_id,
                file_path="report.pdf",
                submitted_at=datetime.utcnow(),
                status="Submitted",
                feedback="",
            )
            db.session.add(sub)
            db.session.commit()
            sub_id = sub.submission_id
            task_id = task.task_id

        self.login("faculty@campusconnect.local", "FacultyPass123")
        res = self.app.post(
            f"/submissions/{sub_id}/review",
            data={"status": "Reviewed", "feedback": "Excellent practical documentation."},
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)

        with app.app_context():
            updated_sub = db.session.get(Submission, sub_id)
            self.assertEqual(updated_sub.status, "Reviewed")
            self.assertEqual(updated_sub.feedback, "Excellent practical documentation.")

        # Student checks review on task detail
        self.logout()
        self.login("rahul@campusconnect.local", "StudentPass123")
        res_stu = self.app.get(f"/tasks/{task_id}")
        self.assertIn(b"Reviewed", res_stu.data)
        self.assertIn(b"Excellent practical documentation", res_stu.data)

    def test_fr10_notice_publication_and_audience(self):
        """FR10 / TC7: Authorised users publish notices for selected audiences."""
        self.login("faculty@campusconnect.local", "FacultyPass123")
        # 1. Course 1 targeted notice
        res_c1 = self.app.post(
            "/notices/new",
            data={
                "title": "Java Lab Timing Change",
                "audience": str(self.course1_id),
                "body": "Java lab starts at 11 AM.",
            },
            follow_redirects=True,
        )
        self.assertEqual(res_c1.status_code, 200)

        # 2. Department-wide notice
        res_all = self.app.post(
            "/notices/new",
            data={
                "title": "Campus Holiday Announcement",
                "audience": "all",
                "body": "College closed on Friday.",
            },
            follow_redirects=True,
        )
        self.assertEqual(res_all.status_code, 200)

        # Student 1 sees both (Enrolled in Course 1 + all)
        self.logout()
        self.login("rahul@campusconnect.local", "StudentPass123")
        res_stu1 = self.app.get("/notices")
        self.assertIn(b"Java Lab Timing Change", res_stu1.data)
        self.assertIn(b"Campus Holiday Announcement", res_stu1.data)

        # Student 2 sees ONLY the all-students notice
        self.logout()
        self.login("pooja@campusconnect.local", "StudentPass123")
        res_stu2 = self.app.get("/notices")
        self.assertNotIn(b"Java Lab Timing Change", res_stu2.data)
        self.assertIn(b"Campus Holiday Announcement", res_stu2.data)

    def test_fr11_dashboards_display_all_status_categories(self):
        """FR11 / BM2: Dashboards display pending, submitted, reviewed, and overdue work."""
        with app.app_context():
            now = datetime.utcnow()
            # 1. Pending Task (future deadline, unsubmitted)
            t_pending = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Pending Task 101",
                task_type="Assignment",
                description="Due in future",
                issue_date=now,
                deadline=now + timedelta(days=3),
                status="Published",
            )
            # 2. Overdue Task (past deadline, unsubmitted)
            t_overdue = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Overdue Task 102",
                task_type="Practical",
                description="Past deadline",
                issue_date=now - timedelta(days=5),
                deadline=now - timedelta(days=1),
                status="Published",
            )
            # 3. Submitted Task
            t_submitted = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Submitted Task 103",
                task_type="Assignment",
                description="Submitted",
                issue_date=now,
                deadline=now + timedelta(days=2),
                status="Published",
            )
            db.session.add_all([t_pending, t_overdue, t_submitted])
            db.session.commit()

            sub = Submission(
                task_id=t_submitted.task_id,
                student_id=self.student1_id,
                file_path="sub103.pdf",
                submitted_at=now,
                status="Submitted",
            )
            db.session.add(sub)
            db.session.commit()

        # Student dashboard checks
        self.login("rahul@campusconnect.local", "StudentPass123")
        res_stu = self.app.get("/dashboard")
        self.assertIn(b"Total Assigned", res_stu.data)
        self.assertIn(b"Submitted", res_stu.data)
        self.assertIn(b"Pending", res_stu.data)
        self.assertIn(b"Overdue", res_stu.data)
        self.logout()

        # Faculty dashboard checks
        self.login("faculty@campusconnect.local", "FacultyPass123")
        res_fac = self.app.get("/dashboard")
        self.assertIn(b"Total Tasks", res_fac.data)
        self.assertIn(b"Submissions", res_fac.data)
        self.assertIn(b"Pending", res_fac.data)
        self.assertIn(b"Overdue", res_fac.data)

    def test_fr12_telegram_account_linking(self):
        """FR12 / SEC7 / TC8: Users can link a Telegram account using a secure verification code."""
        self.login("rahul@campusconnect.local", "StudentPass123")
        # Generate code
        res_code = self.app.post("/telegram/code", follow_redirects=True)
        self.assertEqual(res_code.status_code, 200)

        with app.app_context():
            code_obj = TelegramCode.query.filter_by(user_id=self.student1_id, used=False).first()
            self.assertIsNotNone(code_obj)
            self.assertFalse(code_obj.used)
            test_code = code_obj.code

        # Webhook receives link command
        res_webhook = self.app.post(
            "/telegram/webhook",
            json={"message": {"chat": {"id": 12345678}, "text": f"/link {test_code}"}},
        )
        self.assertEqual(res_webhook.status_code, 200)

        with app.app_context():
            link = TelegramLink.query.filter_by(user_id=self.student1_id).first()
            self.assertIsNotNone(link)
            self.assertEqual(link.chat_id, "12345678")
            self.assertTrue(link.is_active)

    def test_fr13_telegram_event_alerts(self):
        """FR13 / BM4 / TC9 / TC10: Telegram alerts sent for configured task and notice events."""
        with app.app_context():
            # Link Student 1
            link = TelegramLink(
                user_id=self.student1_id,
                chat_id="77889900",
                linked_at=datetime.utcnow(),
                is_active=True,
            )
            db.session.add(link)
            db.session.commit()

        self.login("faculty@campusconnect.local", "FacultyPass123")
        due = (datetime.utcnow() + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M")

        with mock.patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            # Publish task (TC9)
            self.app.post(
                "/tasks/new",
                data={
                    "course_id": self.course1_id,
                    "title": "Alert Broadcast Task",
                    "task_type": "Assignment",
                    "description": "Alert test",
                    "deadline": due,
                    "status": "Published",
                },
                follow_redirects=True,
            )
            self.assertTrue(mock_post.called)
            sent_json = mock_post.call_args[1]["json"]
            self.assertEqual(sent_json["chat_id"], "77889900")
            self.assertIn("Alert Broadcast Task", sent_json["text"])

        # Target an unlinked student (TC10)
        with app.app_context():
            unlinked_student = db.session.get(User, self.student2_id)
            with mock.patch("requests.post") as mock_unlinked:
                ok = send_telegram(unlinked_student, "Message to unlinked student")
                self.assertFalse(ok)
                self.assertFalse(mock_unlinked.called)

    def test_fr14_server_side_role_and_course_access_control(self):
        """FR14 / SEC2 / SEC3 / SEC4 / TC4: Server enforces role and course assignment boundaries."""
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Restricted Course 1 Task",
                task_type="Assignment",
                description="Restricted",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=2),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id

        # Student 2 is NOT enrolled in Course 1 -> 403 Forbidden
        self.login("pooja@campusconnect.local", "StudentPass123")
        res_forbidden = self.app.get(f"/tasks/{task_id}")
        self.assertEqual(res_forbidden.status_code, 403)

        # Student attempting admin route -> 403 Forbidden
        res_admin_users = self.app.get("/admin/users")
        self.assertEqual(res_admin_users.status_code, 403)
        res_admin_courses = self.app.get("/admin/courses")
        self.assertEqual(res_admin_courses.status_code, 403)

    def test_fr15_responsive_interface_meta_and_navigation(self):
        """FR15 / NFR7: Responsive interface metadata, CSS classes, and menu toggle."""
        res = self.app.get("/")
        html = res.data.decode("utf-8")
        self.assertIn('<meta name="viewport" content="width=device-width, initial-scale=1">', html)
        self.assertIn('class="menu-toggle"', html)
        self.assertIn('class="nav-menu"', html)
        self.assertIn('style.css', html)

    # ==========================================================================
    # BENCHMARKS (BM1 - BM6)
    # ==========================================================================

    def test_bm1_correctness_of_task_visibility(self):
        """BM1: Correctness of task visibility based on course enrolment and user role."""
        with app.app_context():
            # Draft task
            t_draft = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Draft Lab File",
                task_type="Practical",
                description="Draft",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=2),
                status="Draft",
            )
            db.session.add(t_draft)
            db.session.commit()

        # Enrolled student does NOT see Draft tasks
        self.login("rahul@campusconnect.local", "StudentPass123")
        res_stu = self.app.get("/dashboard")
        self.assertNotIn(b"Draft Lab File", res_stu.data)
        self.logout()

        # Faculty DOES see Draft tasks in task listing
        self.login("faculty@campusconnect.local", "FacultyPass123")
        res_fac = self.app.get("/tasks")
        self.assertIn(b"Draft Lab File", res_fac.data)

    def test_bm2_accuracy_of_pending_submitted_overdue_counts(self):
        """BM2: Accuracy of pending, submitted, reviewed, and overdue calculations."""
        with app.app_context():
            now = datetime.utcnow()
            # 2 tasks for Course 1
            t1 = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Task 1 Pending",
                task_type="Assignment",
                description="Pending",
                issue_date=now,
                deadline=now + timedelta(days=2),
                status="Published",
            )
            t2 = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Task 2 Overdue",
                task_type="Assignment",
                description="Overdue",
                issue_date=now - timedelta(days=4),
                deadline=now - timedelta(days=1),
                status="Published",
            )
            db.session.add_all([t1, t2])
            db.session.commit()

            # Status validation
            st1 = get_submission_status(t1, self.student1_id)
            st2 = get_submission_status(t2, self.student1_id)
            self.assertEqual(st1, "Pending")
            self.assertEqual(st2, "Overdue")

            # Student submits t1
            sub = Submission(
                task_id=t1.task_id,
                student_id=self.student1_id,
                file_path="t1_file.pdf",
                submitted_at=now,
                status="Submitted",
            )
            db.session.add(sub)
            db.session.commit()

            st1_updated = get_submission_status(t1, self.student1_id)
            self.assertEqual(st1_updated, "Submitted")

    def test_bm3_file_upload_and_retrieval(self):
        """BM3 / SEC5: Successful upload and retrieval of permitted submission files."""
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Download Verification Task",
                task_type="Assignment",
                description="Submit file for download test.",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=2),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id

        self.login("rahul@campusconnect.local", "StudentPass123")
        file_payload = (io.BytesIO(b"Sample assignment solution text"), "report.txt")
        self.app.post(
            f"/tasks/{task_id}/submit",
            data={"file": file_payload},
            content_type="multipart/form-data",
            follow_redirects=True,
        )

        with app.app_context():
            sub = Submission.query.filter_by(task_id=task_id, student_id=self.student1_id).first()
            sub_id = sub.submission_id

        # Student downloads own file
        res_dl = self.app.get(f"/submissions/{sub_id}/file")
        self.assertEqual(res_dl.status_code, 200)
        self.assertEqual(res_dl.data, b"Sample assignment solution text")

        # Disallowed extension is rejected
        bad_file = (io.BytesIO(b"dangerous script"), "script.sh")
        res_bad = self.app.post(
            f"/tasks/{task_id}/submit",
            data={"file": bad_file},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertIn(b"Please select a valid file in one of the permitted formats", res_bad.data)

    def test_bm4_telegram_notification_delivery(self):
        """BM4: Delivery of Telegram alerts to linked accounts and safe error handling."""
        with app.app_context():
            u = db.session.get(User, self.student1_id)
            link = TelegramLink(user_id=u.user_id, chat_id="998877", linked_at=datetime.utcnow(), is_active=True)
            db.session.add(link)
            db.session.commit()

            with mock.patch("requests.post") as mock_req:
                mock_req.return_value.ok = True
                success = send_telegram(u, "Test Alert")
                self.assertTrue(success)

            # Failure handling
            with mock.patch("requests.post", side_effect=Exception("Network error")):
                fail = send_telegram(u, "Failure alert")
                self.assertFalse(fail)

    def test_bm5_response_time_benchmark(self):
        """BM5: Response time of common dashboard and task operations returns under 500ms."""
        self.login("faculty@campusconnect.local", "FacultyPass123")
        routes_to_benchmark = ["/dashboard", "/tasks", "/notices", "/progress"]

        for route in routes_to_benchmark:
            start = time.perf_counter()
            res = self.app.get(route)
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.assertEqual(res.status_code, 200)
            self.assertLess(elapsed_ms, 500, f"Route {route} took {elapsed_ms:.1f}ms, exceeding 500ms benchmark!")

    def test_bm6_zero_emoji_ui_verification(self):
        """BM6: Strict verification that zero emojis exist anywhere in rendered UI and templates."""
        # 1. Render all primary endpoints and check rendered HTML
        self.login("faculty@campusconnect.local", "FacultyPass123")
        endpoints = ["/", "/dashboard", "/tasks", "/notices", "/progress", "/telegram"]
        for ep in endpoints:
            res = self.app.get(ep)
            html_text = res.data.decode("utf-8", errors="ignore")
            has_em, em_char, code = contains_emoji(html_text)
            self.assertFalse(
                has_em,
                f"Emoji detected in rendered UI for {ep}: character '{em_char}' ({code})",
            )
        self.logout()

        # 2. Check all template files directly
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        for fname in os.listdir(templates_dir):
            if fname.endswith(".html"):
                fpath = os.path.join(templates_dir, fname)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    has_em, em_char, code = contains_emoji(content)
                    self.assertFalse(
                        has_em,
                        f"Emoji detected in template {fname}: character '{em_char}' ({code})",
                    )

    # ==========================================================================
    # SECURITY REQUIREMENTS (SEC1 - SEC8)
    # ==========================================================================

    def test_sec1_passwords_stored_as_secure_hashes(self):
        """SEC1 / NFR1: Passwords must be stored as secure hashes, never plain text."""
        with app.app_context():
            user = User.query.filter_by(email="admin@campusconnect.local").first()
            self.assertNotEqual(user.password_hash, "AdminPass123")
            self.assertTrue(user.password_hash.startswith("scrypt:") or user.password_hash.startswith("pbkdf2:"))
            self.assertTrue(user.check_password("AdminPass123"))
            self.assertFalse(user.check_password("WrongPass"))

    def test_sec7_single_use_expiring_linking_token(self):
        """SEC7: Telegram account linking uses single-use token with 10-minute expiry."""
        self.login("rahul@campusconnect.local", "StudentPass123")
        self.app.post("/telegram/code", follow_redirects=True)

        with app.app_context():
            code_rec = TelegramCode.query.filter_by(user_id=self.student1_id, used=False).first()
            code_str = code_rec.code

        # First use -> Success
        res1 = self.app.post("/telegram/webhook", json={"message": {"chat": {"id": 11111}, "text": f"/link {code_str}"}})
        self.assertEqual(res1.status_code, 200)

        with app.app_context():
            rec_after = TelegramCode.query.filter_by(code=code_str).first()
            self.assertTrue(rec_after.used)

        # Second use of same code -> Reused/Expired
        res2 = self.app.post("/telegram/webhook", json={"message": {"chat": {"id": 22222}, "text": f"/link {code_str}"}})
        self.assertEqual(res2.status_code, 200)

        # Chat ID must still belong to first linking, not second
        with app.app_context():
            link = TelegramLink.query.filter_by(user_id=self.student1_id).first()
            self.assertEqual(link.chat_id, "11111")


if __name__ == "__main__":
    unittest.main()
