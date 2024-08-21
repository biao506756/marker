-- 创建数据库 pdf_management 并设置字符集为 utf8mb4
CREATE DATABASE IF NOT EXISTS pdf_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用 pdf_management 数据库
USE pdf_management;

-- 创建 pdf_files 表
CREATE TABLE IF NOT EXISTS pdf_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    filepath VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_filename (filename)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 提示创建完成
SELECT 'Database and table created successfully' AS Message;
