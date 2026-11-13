-- CampusConnect MySQL Database Setup
-- Compatible with MySQL 8.0+

CREATE DATABASE IF NOT EXISTS campusconnect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'campus_user'@'localhost' IDENTIFIED BY 'change-this-password';
GRANT ALL PRIVILEGES ON campusconnect.* TO 'campus_user'@'localhost';
FLUSH PRIVILEGES;

USE campusconnect;

-- 1. USER Entity (Table VII)
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(150) NOT NULL,
    `email` VARCHAR(180) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` VARCHAR(20) NOT NULL DEFAULT 'student',
    `department` VARCHAR(120) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. COURSE Entity (Table VII)
CREATE TABLE IF NOT EXISTS `courses` (
    `course_id` INT AUTO_INCREMENT PRIMARY KEY,
    `course_name` VARCHAR(150) NOT NULL,
    `course_code` VARCHAR(50) NOT NULL,
    `semester` VARCHAR(20) NOT NULL DEFAULT '',
    `section` VARCHAR(20) NOT NULL DEFAULT '',
    `academic_year` VARCHAR(20) NOT NULL DEFAULT '',
    `faculty_id` INT NULL,
    CONSTRAINT `fk_course_faculty` FOREIGN KEY (`faculty_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. ENROLMENT Entity (Table VII)
CREATE TABLE IF NOT EXISTS `enrolments` (
    `enrolment_id` INT AUTO_INCREMENT PRIMARY KEY,
    `student_id` INT NOT NULL,
    `course_id` INT NOT NULL,
    `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_enrolment_student` FOREIGN KEY (`student_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_enrolment_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE,
    CONSTRAINT `uq_student_course` UNIQUE (`student_id`, `course_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. TASK Entity (Table VII)
CREATE TABLE IF NOT EXISTS `tasks` (
    `task_id` INT AUTO_INCREMENT PRIMARY KEY,
    `course_id` INT NOT NULL,
    `faculty_id` INT NOT NULL,
    `title` VARCHAR(200) NOT NULL,
    `task_type` VARCHAR(30) NOT NULL DEFAULT 'Assignment',
    `description` TEXT NOT NULL,
    `issue_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `deadline` DATETIME NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'Published',
    CONSTRAINT `fk_task_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_task_faculty` FOREIGN KEY (`faculty_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. SUBMISSION Entity (Table VII)
CREATE TABLE IF NOT EXISTS `submissions` (
    `submission_id` INT AUTO_INCREMENT PRIMARY KEY,
    `task_id` INT NOT NULL,
    `student_id` INT NOT NULL,
    `file_path` VARCHAR(255) NOT NULL,
    `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `status` VARCHAR(30) NOT NULL DEFAULT 'Submitted',
    `feedback` TEXT NULL,
    CONSTRAINT `fk_submission_task` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`task_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_submission_student` FOREIGN KEY (`student_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `uq_task_student` UNIQUE (`task_id`, `student_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. NOTICE Entity (Table VII)
CREATE TABLE IF NOT EXISTS `notices` (
    `notice_id` INT AUTO_INCREMENT PRIMARY KEY,
    `created_by` INT NOT NULL,
    `title` VARCHAR(200) NOT NULL,
    `body` TEXT NOT NULL,
    `audience` VARCHAR(100) NOT NULL DEFAULT 'all',
    `publish_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_notice_author` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. TELEGRAM_LINK Entity (Table VII)
CREATE TABLE IF NOT EXISTS `telegram_links` (
    `link_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `chat_id` VARCHAR(100) NOT NULL,
    `linked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT `fk_telegram_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. TELEGRAM_CODE Temporary Linking Tokens (Section VIII-E)
CREATE TABLE IF NOT EXISTS `telegram_codes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `code` VARCHAR(100) NOT NULL UNIQUE,
    `expires_at` DATETIME NOT NULL,
    `used` BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT `fk_code_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
