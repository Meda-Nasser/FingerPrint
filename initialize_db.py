
import sqlite3

# Path to your database file
DATABASE = "hr_management_system.db"

# Connect to the database
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Create Users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('employee', 'manager', 'hr')) NOT NULL
)
''')
# إنشاء جدول تقييم الأداء
cursor.execute('''
CREATE TABLE IF NOT EXISTS performance_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    review_date TEXT NOT NULL,
    score INTEGER NOT NULL,
    comments TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')
# Create Attendance table
cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    check_in_time TEXT,
    check_out_time TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# Create Leaves table
cursor.execute('''
CREATE TABLE IF NOT EXISTS leaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT CHECK(status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    reason TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# Create Salaries table
cursor.execute('''
CREATE TABLE IF NOT EXISTS salaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month TEXT NOT NULL,
    year INTEGER NOT NULL,
    base_salary REAL NOT NULL,
    bonuses REAL DEFAULT 0,
    deductions REAL DEFAULT 0,
    total_salary REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# Insert a default admin user
cursor.execute('''
INSERT OR IGNORE INTO users (username, password, role) 
VALUES ('admin', 'admin123', 'hr')
''')

# Commit changes and close the connection
conn.commit()
conn.close()

print("Database initialized successfully with default admin user.")