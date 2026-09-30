# EcoMess - Full Desktop Application

A Python + Tkinter desktop app for a college mess management system with three roles: Student, Staff, and Admin. The backend uses MySQL (`eco_mess` database).

## Proposed Changes

### File Structure

```
project/
├── main.py              # Entry point — launches Tkinter window
├── database.py          # All DB connections, schema, and queries
├── home_page.py         # Landing page with project description
├── login_page.py        # Login form (username, password, role)
├── student_dash.py      # Student dashboard (tabbed)
├── staff_dash.py        # Staff dashboard (tabbed)
└── admin_dash.py        # Admin dashboard (tabbed)
```

> [app.py](file:///c:/Users/GKM701/Desktop/software%20engg/project/app.py) will be kept as-is (the old CLI version) and `main.py` becomes the new Tkinter entry point.

---

### Database Schema (10 tables in `eco_mess`)

| Table | Key Columns |
|---|---|
| [users](file:///c:/Users/GKM701/Desktop/software%20engg/project/app.py#162-176) | id, username, password, role, full_name, email |
| `attendance` | id, user_id, date, check_in, check_out, status |
| `menu` | id, day_of_week, meal_type, items, week_start_date |
| `fee_payments` | id, student_id, amount, payment_date, status |
| `poll` | id, student_id, date, item, vote; auto-reset midnight |
| `notifications` | id, sender_id, target_role, title, message, created_at |
| `notification_reads` | id, notification_id, user_id, read_at |
| `complaints` | id, user_id, message, status, created_at |
| `inventory` | id, item_name, quantity, unit, updated_at |
| `food_waste` | id, staff_id, date, item_name, quantity, unit |
| `salary` | id, user_id, month, year, amount, paid_date |

---

### Component: `database.py` [MODIFY]

#### [MODIFY] [database.py](file:///c:/Users/GKM701/Desktop/software%20engg/project/database.py)
All queries and CRUD operations, grouped by feature: auth, attendance, menu, fee, poll, notifications, complaints, inventory, food-waste, salary, user management.

---

### Component: Main App

#### [NEW] [main.py](file:///c:/Users/GKM701/Desktop/software%20engg/project/main.py)
- `EcoMessApp` class — creates root `Tk()` window, dark eco-green theme
- Manages **sidebar** (visible post-login) + **main content frame**
- `show_page(page_name)` swaps the active frame
- Session dict stores `current_user` after login

---

### Component: Pages

#### [NEW] [home_page.py](file:///c:/Users/GKM701/Desktop/software%20engg/project/home_page.py)
- Project logo/title, paragraph description
- "Login" button → navigate to login page

#### [NEW] [login_page.py](file:///c:/Users/GKM701/Desktop/software%20engg/project/login_page.py)
- Role selector (Student / Staff / Admin)
- Username & Password fields
- "Forgot Password" → triggers admin notification stored in DB

#### [NEW] [student_dash.py](file:///c:/Users/GKM701/Desktop/software%20engg/project/student_dash.py)
Tabbed notebook with:
1. **Attendance** — read-only table of attendance records
2. **Weekly Menu** — sliding card view (day-by-day with arrows)
3. **Fee Payment** — outstanding balance + pay button
4. **Poll** — vote for next day's food; shows running totals; resets at midnight via `after()`
5. **User Manual** — scrollable text
6. **Notifications** — list of admin messages
7. **Complaints** — text entry + submit

#### [NEW] [staff_dash.py](file:///c:/Users/GKM701/Desktop/software%20engg/project/staff_dash.py)
Tabbed notebook with:
1. **Attendance** — with check-in/check-out timestamps
2. **Weekly Menu** — same sliding widget as student
3. **Salary** — view monthly salary table
4. **Day Count** — aggregated student poll results for today
5. **User Manual** — scrollable text
6. **Inventory** — read-only table of stock items
7. **Food Waste** — form to record food wastage per item

#### [NEW] [admin_dash.py](file:///c:/Users/GKM701/Desktop/software%20engg/project/admin_dash.py)
Tabbed notebook with:
1. **Menu** — add/edit/delete menu rows
2. **Attendance** — view & mark attendance for students & staff
3. **User Management** — add/delete users, reset passwords, view forgot-password requests
4. **Salary** — view & add salary records
5. **Inventory** — add/edit/delete stock items
6. **Food Waste Report** — aggregated report with filter by date
7. **Complaints** — read-only list with status update
8. **Notifications** — compose and send to role group
9. **User Manual** — edit manual text

---

## Verification Plan

### Automated Tests
None (no existing test suite in the project).

### Manual Verification

> Run: `python main.py` from `c:\Users\GKM701\Desktop\software engg\project\`

1. **Home page loads** — description text visible, Login button present
2. **Admin login** — use seeded `admin / admin123`, verify admin dashboard opens
3. **Add student via admin** → User Management tab → add user, role=student
4. **Login as student** — verify all 7 tabs load without errors
5. **Submit poll** as student → check Poll tab total updates
6. **Add staff via admin** → login as staff → verify all 7 tabs load
7. **Staff enters food waste** → admin Food Waste Report tab shows entry
8. **Admin sends notification** → student logs in → Notifications tab shows message
9. **Student submits complaint** → admin Complaints tab shows it
10. **Forgot password** — student clicks "Forgot Password" → admin User Management shows pending request
