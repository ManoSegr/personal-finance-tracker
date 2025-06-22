import sqlite3
from datetime import datetime, timedelta
import random

class FinanceTracker:
    """Personal Finance Management System"""
    
    def __init__(self, db_name="finance.db"):
        self.db_name = db_name
        self.setup_database()
    
    def setup_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                type TEXT CHECK(type IN ('income', 'expense')),
                date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Categories with budget limits
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT CHECK(type IN ('income', 'expense')),
                budget_limit REAL DEFAULT 0
            )
        ''')
        
        # Default categories
        categories = [
            ('Salary', 'income', 0),
            ('Freelance', 'income', 0),
            ('Food', 'expense', 500),
            ('Transport', 'expense', 200),
            ('Entertainment', 'expense', 150),
            ('Utilities', 'expense', 300),
            ('Shopping', 'expense', 400),
            ('Healthcare', 'expense', 200),
            ('Rent', 'expense', 1200)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO categories (name, type, budget_limit)
            VALUES (?, ?, ?)
        ''', categories)
        
        conn.commit()
        conn.close()
        print("✓ Database initialized")
    
    def add_transaction(self, amount, category, description="", trans_type="expense", date=None):
        """Add new transaction"""
        if date is None:
            date = datetime.now().date()
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (amount, category, description, type, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (amount, category, description, trans_type, date))
        
        conn.commit()
        conn.close()
        print(f"✓ Added {trans_type}: €{amount} - {category}")
        return True
    
    def get_monthly_summary(self):
        """Get current month financial summary"""
        now = datetime.now()
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                type,
                SUM(amount) as total,
                COUNT(*) as count
            FROM transactions 
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY type
        ''', (now.strftime('%Y-%m'),))
        
        results = cursor.fetchall()
        conn.close()
        
        summary = {'income': 0, 'expense': 0}
        for trans_type, total, count in results:
            summary[trans_type] = total
        
        summary['balance'] = summary['income'] - summary['expense']
        summary['savings_rate'] = (summary['balance'] / summary['income'] * 100) if summary['income'] > 0 else 0
        
        return summary
    
    def get_category_spending(self, days=30):
        """Get spending by category for last N days"""
        start_date = datetime.now().date() - timedelta(days=days)
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                category,
                SUM(amount) as total,
                COUNT(*) as transactions
            FROM transactions 
            WHERE type = 'expense' AND date >= ?
            GROUP BY category
            ORDER BY total DESC
        ''', (start_date,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def check_budgets(self):
        """Check budget status for current month"""
        month_start = datetime.now().replace(day=1).date()
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.name,
                c.budget_limit,
                COALESCE(SUM(t.amount), 0) as spent
            FROM categories c
            LEFT JOIN transactions t ON c.name = t.category 
                AND t.type = 'expense' 
                AND t.date >= ?
            WHERE c.type = 'expense' AND c.budget_limit > 0
            GROUP BY c.name, c.budget_limit
            ORDER BY (COALESCE(SUM(t.amount), 0) / c.budget_limit) DESC
        ''', (month_start,))
        
        results = cursor.fetchall()
        conn.close()
        
        budget_status = []
        for category, budget, spent in results:
            percentage = (spent / budget * 100) if budget > 0 else 0
            
            if percentage > 100:
                status = "OVER BUDGET"
            elif percentage > 80:
                status = "NEAR LIMIT"
            else:
                status = "OK"
            
            budget_status.append({
                'category': category,
                'budget': budget,
                'spent': spent,
                'percentage': percentage,
                'status': status
            })
        
        return budget_status
    
    def generate_sample_data(self):
        """Create sample transactions for demonstration"""
        print("Generating sample data...")
        
        transactions = [
            # Income
            (3000, "Salary", "Monthly salary", "income"),
            (500, "Freelance", "Web project", "income"),
            
            # Expenses
            (1200, "Rent", "Monthly rent", "expense"),
            (150, "Utilities", "Electric bill", "expense"),
            (80, "Food", "Groceries", "expense"),
            (45, "Food", "Restaurant", "expense"),
            (60, "Transport", "Gas", "expense"),
            (35, "Transport", "Bus pass", "expense"),
            (120, "Shopping", "Clothes", "expense"),
            (75, "Entertainment", "Movies", "expense"),
            (90, "Healthcare", "Doctor visit", "expense"),
        ]
        
        for amount, category, description, trans_type in transactions:
            # Random date in last 30 days
            days_ago = random.randint(0, 30)
            trans_date = datetime.now().date() - timedelta(days=days_ago)
            self.add_transaction(amount, category, description, trans_type, trans_date)
        
        print(f"✓ Generated {len(transactions)} sample transactions")
    
    def show_report(self):
        """Display comprehensive financial report"""
        print("\n" + "="*50)
        print("FINANCIAL REPORT")
        print("="*50)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Monthly summary
        summary = self.get_monthly_summary()
        print(f"\nMONTHLY SUMMARY ({datetime.now().strftime('%B %Y')})")
        print("-" * 30)
        print(f"Income:      €{summary['income']:8,.2f}")
        print(f"Expenses:    €{summary['expense']:8,.2f}")
        print(f"Balance:     €{summary['balance']:8,.2f}")
        print(f"Savings:     {summary['savings_rate']:6.1f}%")
        
        # Budget status
        print(f"\nBUDGET STATUS")
        print("-" * 30)
        budgets = self.check_budgets()
        for item in budgets:
            print(f"{item['category']:12} €{item['spent']:6,.0f}/€{item['budget']:6,.0f} "
                  f"({item['percentage']:5.1f}%) {item['status']}")
        
        # Category spending
        print(f"\nCATEGORY SPENDING (Last 30 days)")
        print("-" * 30)
        spending = self.get_category_spending()
        for category, total, count in spending:
            print(f"{category:12} €{total:8,.2f} ({count} transactions)")

def main():
    """Main function"""
    tracker = FinanceTracker()
    
    print("PERSONAL FINANCE TRACKER")
    print("=" * 40)
    
    # Generate and analyze sample data
    tracker.generate_sample_data()
    tracker.show_report()

if __name__ == "__main__":
    main()