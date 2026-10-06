
# POCKETSMART AI
## Your Smart Budget & Recommendation Assistant

### 1. Abstract
PocketSmart AI is a personal finance management web application designed to help users record income and expenses, organize spending into categories, set a monthly budget and receive simple personalized recommendations. The system presents financial information through a dashboard and visual chart. The project uses Python Flask for the application layer and SQLite for data storage.

### 2. Problem Statement
Many students and individuals record expenses informally and may not have a clear view of where their money is spent. PocketSmart AI provides a simple centralized system for tracking transactions and understanding spending patterns.

### 3. Objectives
- Record income and expenses.
- Categorize expenses.
- Set a monthly budget.
- Calculate balance/savings.
- Visualize expense distribution.
- Generate understandable budget recommendations.
- Store data in a local database.

### 4. Existing System
Manual notes, spreadsheets or memory-based tracking can make it difficult to maintain consistent records and identify spending patterns.

### 5. Proposed System
PocketSmart AI provides a web dashboard where the user can manage transactions, set a budget and receive recommendations from the stored spending data.

### 6. Modules
- Authentication Module
- Transaction Management Module
- Budget Management Module
- Dashboard & Visualization Module
- Recommendation Module
- Database Module

### 7. Technologies
Frontend: HTML5, CSS3, JavaScript
Backend: Python Flask
Database: SQLite
Chart: Chart.js
Development environment: VS Code / any Python IDE

### 8. Recommendation Logic
The system calculates total income, total expenses and remaining balance. It also calculates spending by category. If expenses exceed the monthly budget, the system reports the budget overrun. If a category forms a large share of total expenses, the system suggests reviewing that category. If savings are low compared with income, the system suggests reducing non-essential spending.

### 9. Database
users(id, name, email, password, created_at)
transactions(id, user_id, kind, amount, category, note, tx_date)
budgets(id, user_id, monthly_budget, updated_at)

### 10. System Flow
User → Login/Register → Dashboard → Add Income/Expense → Database → Calculate Summary → Generate Recommendation → Display Chart & Advice

### 11. Expected Result
The application should provide a simple, user-friendly interface for recording financial transactions and understanding the user's current budget position.

### 12. Future Enhancements
- Mobile application
- Export reports to PDF/Excel
- Recurring transactions
- Advanced ML-based prediction
- Notifications
- Secure password hashing and role-based administration
