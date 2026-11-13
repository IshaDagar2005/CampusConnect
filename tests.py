"""
CampusConnect Automated Verification Suite
Validates Synopsis Requirements, Benchmarks, and Test Cases (TC1 - TC10).
"""

import io
import os
import unittest
import unittest.mock as mock
from datetime import datetime, timedelta

# Configure test environment
os.environ["SECRET_KEY"] = "test-secret-key-12345"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FLASK_DEBUG"] = "0"
os.environ["TELEGRAM_BOT_TOKEN"] = "mock_telegram_token"

from app import app, db, User, Course, Enrolment, Task, Submission, Notice, TelegramLink, TelegramCode, send_telegram


class CampusConnectTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["WTF_CSRF_ENABLED"] = False
        self.app = app.test_client()

        with app.app_context():
            db.create_all()

            # Seed Admin
            self.admin = User(
                full_name="Administrator",
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

            # Seed Student 1 (Enrolled in course 1)
            self.student1 = User(
                full_name="Isha Dagar",
                email="student1@campusconnect.local",
                role="student",
                department="MCA",
            )
            self.student1.set_password("StudentPass123")

            # Seed Student 2 (Enrolled in course 2 only)
            self.student2 = User(
                full_name="Peer Student",
                email="student2@campusconnect.local",
                role="student",
                department="MCA",
            )
            self.student2.set_password("StudentPass123")

            db.session.add_all([self.admin, self.faculty, self.student1, self.student2])
            db.session.commit()

            # Seed Courses
            self.course1 = Course(
                course_name="Advanced Java Programming",
                course_code="MCA-101",
                semester="1",
                section="B",
                academic_year="2026-2027",
                faculty_id=self.faculty.user_id,
            )
            self.course2 = Course(
                course_name="Software Engineering",
                course_code="MCA-102",
                semester="1",
                section="B",
                academic_year="2026-2027",
                faculty_id=self.faculty.user_id,
            )
            db.session.add_all([self.course1, self.course2])
            db.session.commit()

            # Enrol Student 1 in Course 1
            e1 = Enrolment(student_id=self.student1.user_id, course_id=self.course1.course_id)
            # Enrol Student 2 in Course 2
            e2 = Enrolment(student_id=self.student2.user_id, course_id=self.course2.course_id)
            db.session.add_all([e1, e2])
            db.session.commit()

            # Store IDs for tests
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
        return self.app.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self.app.get("/logout", follow_redirects=True)

    # --------------------------------------------------------------------------
    # TC1: A valid faculty user logs in -> Faculty dashboard opens
    # --------------------------------------------------------------------------
    def test_tc1_faculty_login(self):
        res = self.login("faculty@campusconnect.local", "FacultyPass123")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Faculty Workspace", res.data)
        self.assertIn(b"Academic Dashboard", res.data)

    # --------------------------------------------------------------------------
    # TC2: A student logs in -> Student dashboard opens
    # --------------------------------------------------------------------------
    def test_tc2_student_login(self):
        res = self.login("student1@campusconnect.local", "StudentPass123")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Student Workspace", res.data)
        self.assertIn(b"Hello, Isha.", res.data)

    # --------------------------------------------------------------------------
    # TC3: Faculty creates an assignment for a course -> Visible to enrolled students
    # --------------------------------------------------------------------------
    def test_tc3_faculty_create_assignment(self):
        self.login("faculty@campusconnect.local", "FacultyPass123")
        due = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")
        res = self.app.post(
            "/tasks/new",
            data={
                "course_id": self.course1_id,
                "title": "Lab Exercise 1: Multithreading",
                "task_type": "Practical",
                "description": "Implement thread synchronization in Java.",
                "deadline": due,
                "status": "Published",
            },
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Practical published successfully", res.data)

        # Verify enrolled student 1 sees it on dashboard
        self.logout()
        self.login("student1@campusconnect.local", "StudentPass123")
        res_student = self.app.get("/dashboard")
        self.assertIn(b"Lab Exercise 1: Multithreading", res_student.data)

    # --------------------------------------------------------------------------
    # TC4: A student not enrolled in the course opens the task URL -> Access denied (403)
    # --------------------------------------------------------------------------
    def test_tc4_non_enrolled_access_denied(self):
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Course 1 Exclusive Task",
                task_type="Assignment",
                description="Instructions...",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=5),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id

        # Student 2 is only enrolled in Course 2, not Course 1
        self.login("student2@campusconnect.local", "StudentPass123")
        res = self.app.get(f"/tasks/{task_id}")
        self.assertEqual(res.status_code, 403)
        self.assertIn(b"Access denied", res.data)

    # --------------------------------------------------------------------------
    # TC5: Student submits a permitted file before deadline -> Status = Submitted
    # --------------------------------------------------------------------------
    def test_tc5_student_submit_permitted_file(self):
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Homework Assignment",
                task_type="Assignment",
                description="Upload solution PDF.",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=3),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id

        self.login("student1@campusconnect.local", "StudentPass123")
        file_data = (io.BytesIO(b"%PDF-1.4 sample pdf content"), "homework.pdf")
        res = self.app.post(
            f"/tasks/{task_id}/submit",
            data={"file": file_data},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Your submission has been uploaded successfully", res.data)

        with app.app_context():
            sub = Submission.query.filter_by(task_id=task_id, student_id=self.student1_id).first()
            self.assertIsNotNone(sub)
            self.assertEqual(sub.status, "Submitted")

    # --------------------------------------------------------------------------
    # TC6: Faculty reviews a submission and adds feedback -> Status & feedback update
    # --------------------------------------------------------------------------
    def test_tc6_faculty_review_submission(self):
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="Mini Project Phase 1",
                task_type="Project",
                description="Submit design doc.",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=2),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id

            sub = Submission(
                task_id=task_id,
                student_id=self.student1_id,
                file_path="mock_phase1.pdf",
                submitted_at=datetime.utcnow(),
                status="Submitted",
                feedback="",
            )
            db.session.add(sub)
            db.session.commit()
            sub_id = sub.submission_id

        self.login("faculty@campusconnect.local", "FacultyPass123")
        res = self.app.post(
            f"/submissions/{sub_id}/review",
            data={"status": "Reviewed", "feedback": "Well structured design document. Approved."},
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Review and feedback saved successfully", res.data)

        # Student checks the review feedback
        self.logout()
        self.login("student1@campusconnect.local", "StudentPass123")
        res_student = self.app.get(f"/tasks/{task_id}")
        self.assertIn(b"Reviewed", res_student.data)
        self.assertIn(b"Well structured design document", res_student.data)

    # --------------------------------------------------------------------------
    # TC7: Faculty publishes a notice for selected section -> Visible only to audience
    # --------------------------------------------------------------------------
    def test_tc7_faculty_publish_targeted_notice(self):
        self.login("faculty@campusconnect.local", "FacultyPass123")
        res = self.app.post(
            "/notices/new",
            data={
                "title": "Course 1 Class Postponed",
                "audience": str(self.course1_id),
                "body": "The lab session is shifted to 3 PM.",
            },
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)

        # Student 1 is in Course 1 -> Must see it
        self.logout()
        self.login("student1@campusconnect.local", "StudentPass123")
        res1 = self.app.get("/notices")
        self.assertIn(b"Course 1 Class Postponed", res1.data)

        # Student 2 is NOT in Course 1 -> Must NOT see it
        self.logout()
        self.login("student2@campusconnect.local", "StudentPass123")
        res2 = self.app.get("/notices")
        self.assertNotIn(b"Course 1 Class Postponed", res2.data)

    # --------------------------------------------------------------------------
    # TC8: A user links Telegram using a valid code -> Telegram chat linked
    # --------------------------------------------------------------------------
    def test_tc8_user_links_telegram_with_valid_code(self):
        self.login("student1@campusconnect.local", "StudentPass123")
        res = self.app.post("/telegram/code", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"One-time linking code generated", res.data)

        with app.app_context():
            code_rec = TelegramCode.query.filter_by(user_id=self.student1_id, used=False).first()
            self.assertIsNotNone(code_rec)
            code_val = code_rec.code

        # Simulate Telegram bot webhook receiving /link code
        webhook_res = self.app.post(
            "/telegram/webhook",
            json={
                "message": {
                    "chat": {"id": 987654321},
                    "text": f"/link {code_val}",
                }
            },
        )
        self.assertEqual(webhook_res.status_code, 200)

        with app.app_context():
            link = TelegramLink.query.filter_by(user_id=self.student1_id).first()
            self.assertIsNotNone(link)
            self.assertEqual(link.chat_id, "987654321")
            self.assertTrue(link.is_active)

    # --------------------------------------------------------------------------
    # TC9: A new task is published for course with linked users -> Alert dispatched
    # --------------------------------------------------------------------------
    def test_tc9_task_published_alerts_linked_users(self):
        with app.app_context():
            link = TelegramLink(
                user_id=self.student1_id,
                chat_id="55667788",
                linked_at=datetime.utcnow(),
                is_active=True,
            )
            db.session.add(link)
            db.session.commit()

        self.login("faculty@campusconnect.local", "FacultyPass123")
        due = (datetime.utcnow() + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M")

        with mock.patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            res = self.app.post(
                "/tasks/new",
                data={
                    "course_id": self.course1_id,
                    "title": "Telegram Notification Test Task",
                    "task_type": "Assignment",
                    "description": "Test body",
                    "deadline": due,
                    "status": "Published",
                },
                follow_redirects=True,
            )
            self.assertEqual(res.status_code, 200)
            # Verify Telegram API was called for the linked student
            self.assertTrue(mock_post.called)
            sent_payload = mock_post.call_args[1]["json"]
            self.assertEqual(sent_payload["chat_id"], "55667788")
            self.assertIn("Telegram Notification Test Task", sent_payload["text"])

    # --------------------------------------------------------------------------
    # TC10: An unlinked user is targeted for a notification -> No message sent
    # --------------------------------------------------------------------------
    def test_tc10_unlinked_user_receives_no_telegram(self):
        # Student 2 has no TelegramLink
        with app.app_context():
            u2 = db.session.get(User, self.student2_id)
            with mock.patch("requests.post") as mock_post:
                ok = send_telegram(u2, "This should not be sent")
                self.assertFalse(ok)
                self.assertFalse(mock_post.called)

    # --------------------------------------------------------------------------
    # Security: Server-side role boundaries (SEC2)
    # --------------------------------------------------------------------------
    def test_security_student_cannot_access_admin_routes(self):
        self.login("student1@campusconnect.local", "StudentPass123")
        res_users = self.app.get("/admin/users")
        self.assertEqual(res_users.status_code, 403)
        res_courses = self.app.get("/admin/courses")
        self.assertEqual(res_courses.status_code, 403)
        res_task_new = self.app.get("/tasks/new")
        self.assertEqual(res_task_new.status_code, 403)

    # --------------------------------------------------------------------------
    # Security: File type validation (SEC5)
    # --------------------------------------------------------------------------
    def test_security_disallowed_file_extension(self):
        with app.app_context():
            task = Task(
                course_id=self.course1_id,
                faculty_id=self.faculty_id,
                title="File Upload Security Task",
                task_type="Assignment",
                description="Instructions",
                issue_date=datetime.utcnow(),
                deadline=datetime.utcnow() + timedelta(days=2),
                status="Published",
            )
            db.session.add(task)
            db.session.commit()
            task_id = task.task_id

        self.login("student1@campusconnect.local", "StudentPass123")
        # Try uploading a disallowed executable script (.exe)
        malicious_file = (io.BytesIO(b"binary executable"), "malicious.exe")
        res = self.app.post(
            f"/tasks/{task_id}/submit",
            data={"file": malicious_file},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Please select a valid file in one of the permitted formats", res.data)

        with app.app_context():
            sub = Submission.query.filter_by(task_id=task_id, student_id=self.student1_id).first()
            self.assertIsNone(sub)


if __name__ == "__main__":
    unittest.main()
