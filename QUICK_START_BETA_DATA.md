# Quick Start: Beta Data Generation

## 🚀 Generate Test Data in 3 Steps

### Step 1: Generate Data
```bash
venv/Scripts/python.exe manage.py generate_beta_data --users 50 --settings=School_System.settings.development
```

### Step 2: Start Server
```bash
venv/Scripts/python.exe manage.py runserver 9000 --settings=School_System.settings.development
```

### Step 3: Login
Visit `http://localhost:9000` and login with:

**Admin Access:**
- Username: `admin`
- Password: `admin123`

**Director Access:**
- Username: `director`
- Password: `director123`

**Student Access:**
- Username: `student1` (student2, student3, etc.)
- Password: `student123`

**Lecturer Access:**
- Username: `lecturer1` (lecturer2, ... lecturer10)
- Password: `lecturer123`

**Parent Access:**
- Username: `parent1` (parent2, ... parent20)
- Password: `parent123`

---

## 📊 What Gets Generated

✅ **50 Students** across all programs and levels
✅ **10 Lecturers** assigned to courses
✅ **20 Parents** linked to students
✅ **5 Programs** (CS, IT, SE, Data Science, Cybersecurity)
✅ **40 Courses** across all levels (100-400)
✅ **30 days of attendance** records
✅ **Grades** for all enrolled students
✅ **100 Library books** with borrow records
✅ **15 Events** with registrations
✅ **Forum discussions** with posts
✅ **Analytics data** (engagement, at-risk students)
✅ **Certificates** for top students
✅ **Quizzes** with questions
✅ **Payment records**
✅ **And much more...**

---

## 🔧 Common Options

### Generate more students:
```bash
venv/Scripts/python.exe manage.py generate_beta_data --users 100 --settings=School_System.settings.development
```

### Clear existing data and regenerate:
```bash
venv/Scripts/python.exe manage.py generate_beta_data --clear --users 50 --settings=School_System.settings.development
```

### Small dataset for quick testing:
```bash
venv/Scripts/python.exe manage.py generate_beta_data --users 10 --settings=School_System.settings.development
```

---

## ⚠️ Important Notes

- The `--clear` flag **permanently deletes** all data except superusers
- Generation takes 1-2 minutes for 50 students
- All data is realistic (using Faker library)
- Relationships are properly maintained
- All sessions/semesters are created automatically

---

## 📖 Full Documentation

For complete details, see [BETA_DATA_GUIDE.md](BETA_DATA_GUIDE.md)

---

## 🐛 Troubleshooting

### "No module named 'faker'"
```bash
venv/Scripts/pip.exe install faker factory-boy
```

### Permission errors
Make sure you're in the project root directory

### Database errors
Check that migrations are applied:
```bash
venv/Scripts/python.exe manage.py migrate --settings=School_System.settings.development
```

---

**Happy Testing! 🎉**
