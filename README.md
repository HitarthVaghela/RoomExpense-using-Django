# RoomExpense - Expense Sharing and Tracking App for Roommates 🏠💰

**RoomExpense** is a Django-based web application designed to help roommates manage and track shared expenses in a transparent and efficient way. This platform supports real-time balance updates, group management, and secure user authentication without relying on Django's default admin panel.

## 🔧 Tech Stack

- **Backend**: Django 4.x
- **Database**: SQLite (default) – easily switchable to PostgreSQL/MySQL
- **Frontend**: HTML, CSS, Bootstrap (customizable)
- **Auth**: Django Authentication (custom forms)

---

## 🚀 Features

### 👥 User Management
- Custom **sign-up** with username, email, and strong password validation.
- Secure **login** and session handling.
- Unique usernames and emails.
- Authenticated users redirected to personalized dashboards.

### 🏘️ Group System
- Users can **create** a new group (e.g., "Flat 5B") or **join** using an invite code.
- Each group has a unique auto-generated code for secure access.
- Only group members can view and manage the group's expenses.

### 💸 Expense Tracking
- Add expenses with:
  - Title, amount, payer, and selected participants.
- Automatic real-time splitting of expenses among selected members.
- Track and display:
  - **Who owes whom** and **how much**.
  - **Net balance** of each user within the group (positive = owed, negative = owes).

### 📊 Dashboard & Logs
- Dashboard view for group members showing:
  - Recent expenses
  - Current balances
  - Member-to-member dues
- View, edit, or delete past expenses (by the creator).

### 🔒 Access Control
- Only **authenticated users** can access dashboards and group features.
- **Unauthenticated users** are redirected to the login page.
- Cross-group access is strictly restricted.
