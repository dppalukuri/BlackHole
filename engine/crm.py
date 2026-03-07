"""
BlackHole CRM - SQLite-based pipeline and revenue tracker.

Tracks leads from first contact through to payment.
Pipeline: lead -> contacted -> proposal -> negotiation -> won -> delivered -> paid
"""

import sqlite3
import os
import sys
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "blackhole.db")

STATUSES = ["lead", "contacted", "proposal", "negotiation", "won", "delivered", "paid", "lost"]

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            contact_name TEXT,
            email TEXT,
            phone TEXT,
            source TEXT,
            status TEXT DEFAULT 'lead',
            deal_value REAL DEFAULT 0,
            monthly_value REAL DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            follow_up_date TEXT,
            tags TEXT DEFAULT ''
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            description TEXT,
            amount REAL,
            status TEXT DEFAULT 'unpaid',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            paid_at TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            activity_type TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    conn.commit()
    return conn

def add_client(args):
    if len(args) < 5:
        print("Usage: python run.py crm add <company> <contact> <email> <source> <deal_value>")
        print("  Optional: --phone <phone> --monthly <monthly_value> --tags <tag1,tag2>")
        return

    company, contact, email, source = args[0], args[1], args[2], args[3]
    deal_value = float(args[4])

    phone = ""
    monthly_value = 0
    tags = ""

    i = 5
    while i < len(args):
        if args[i] == "--phone" and i + 1 < len(args):
            phone = args[i + 1]
            i += 2
        elif args[i] == "--monthly" and i + 1 < len(args):
            monthly_value = float(args[i + 1])
            i += 2
        elif args[i] == "--tags" and i + 1 < len(args):
            tags = args[i + 1]
            i += 2
        else:
            i += 1

    conn = get_db()
    follow_up = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    cursor = conn.execute(
        """INSERT INTO clients (company, contact_name, email, phone, source, deal_value, monthly_value, tags, follow_up_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (company, contact, email, phone, source, deal_value, monthly_value, tags, follow_up)
    )
    conn.execute(
        "INSERT INTO activities (client_id, activity_type, description) VALUES (?, ?, ?)",
        (cursor.lastrowid, "created", f"Lead added from {source}")
    )
    conn.commit()
    print(f"  Added: {company} (#{cursor.lastrowid}) - ${deal_value:,.0f} deal")
    print(f"  Follow-up set: {follow_up}")
    conn.close()

def list_clients(args):
    conn = get_db()
    status_filter = None
    if args and args[0] == "--status" and len(args) > 1:
        status_filter = args[1]

    if status_filter:
        rows = conn.execute("SELECT * FROM clients WHERE status = ? ORDER BY updated_at DESC", (status_filter,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM clients ORDER BY status, updated_at DESC").fetchall()

    if not rows:
        print("  No clients found.")
        return

    print(f"\n  {'ID':<4} {'Company':<20} {'Contact':<15} {'Status':<12} {'Deal Value':<12} {'Source':<12} {'Follow-up':<12}")
    print("  " + "-" * 87)
    for r in rows:
        follow_up = r['follow_up_date'] or '-'
        overdue = ""
        if r['follow_up_date'] and r['follow_up_date'] < datetime.now().strftime("%Y-%m-%d") and r['status'] not in ('won', 'delivered', 'paid', 'lost'):
            overdue = " OVERDUE"
        print(f"  {r['id']:<4} {r['company']:<20} {r['contact_name']:<15} {r['status']:<12} ${r['deal_value']:<11,.0f} {r['source']:<12} {follow_up}{overdue}")

    conn.close()

def update_status(args):
    if len(args) < 2:
        print(f"Usage: python run.py crm update <id> <status>")
        print(f"  Statuses: {', '.join(STATUSES)}")
        return

    client_id = int(args[0])
    new_status = args[1].lower()

    if new_status not in STATUSES:
        print(f"  Invalid status. Choose from: {', '.join(STATUSES)}")
        return

    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if not client:
        print(f"  Client #{client_id} not found.")
        return

    old_status = client['status']
    conn.execute(
        "UPDATE clients SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_status, client_id)
    )
    conn.execute(
        "INSERT INTO activities (client_id, activity_type, description) VALUES (?, ?, ?)",
        (client_id, "status_change", f"{old_status} -> {new_status}")
    )
    conn.commit()
    print(f"  Updated {client['company']}: {old_status} -> {new_status}")

    if new_status == "won":
        print(f"  DEAL WON! ${client['deal_value']:,.0f}")
        print(f"  Next: deliver the project, then update to 'delivered'")

    conn.close()

def add_note(args):
    if len(args) < 2:
        print("Usage: python run.py crm note <id> <note text...>")
        return

    client_id = int(args[0])
    note = " ".join(args[1:])

    conn = get_db()
    client = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    if not client:
        print(f"  Client #{client_id} not found.")
        return

    existing = client['notes']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_notes = f"{existing}\n[{timestamp}] {note}" if existing else f"[{timestamp}] {note}"

    conn.execute("UPDATE clients SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_notes, client_id))
    conn.execute(
        "INSERT INTO activities (client_id, activity_type, description) VALUES (?, ?, ?)",
        (client_id, "note", note)
    )
    conn.commit()
    print(f"  Note added to {client['company']}")
    conn.close()

def set_followup(args):
    if len(args) < 2:
        print("Usage: python run.py crm followup <id> <YYYY-MM-DD | +Ndays>")
        return

    client_id = int(args[0])
    date_input = args[1]

    if date_input.startswith("+"):
        days = int(date_input[1:])
        follow_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    else:
        follow_date = date_input

    conn = get_db()
    conn.execute("UPDATE clients SET follow_up_date = ? WHERE id = ?", (follow_date, client_id))
    conn.commit()
    print(f"  Follow-up set for {follow_date}")
    conn.close()

def show_pipeline(args=None):
    conn = get_db()
    print("\n  === PIPELINE ===\n")

    for status in STATUSES:
        rows = conn.execute(
            "SELECT * FROM clients WHERE status = ? ORDER BY deal_value DESC", (status,)
        ).fetchall()
        total = sum(r['deal_value'] for r in rows)
        count = len(rows)
        bar = "#" * count
        print(f"  {status.upper():<12} [{count:>2}] ${total:>10,.0f}  {bar}")
        for r in rows:
            print(f"               - {r['company']} (${r['deal_value']:,.0f})")

    all_rows = conn.execute("SELECT * FROM clients WHERE status NOT IN ('lost', 'paid')").fetchall()
    pipeline_value = sum(r['deal_value'] for r in all_rows)
    print(f"\n  Total Pipeline: ${pipeline_value:,.0f}")
    conn.close()

def show_revenue(args=None):
    conn = get_db()
    print("\n  === REVENUE ===\n")

    won = conn.execute("SELECT * FROM clients WHERE status IN ('won', 'delivered', 'paid')").fetchall()
    total_won = sum(r['deal_value'] for r in won)
    monthly_recurring = sum(r['monthly_value'] for r in won)

    paid_invoices = conn.execute("SELECT * FROM invoices WHERE status = 'paid'").fetchall()
    total_collected = sum(r['amount'] for r in paid_invoices)

    unpaid = conn.execute("SELECT * FROM invoices WHERE status = 'unpaid'").fetchall()
    total_outstanding = sum(r['amount'] for r in unpaid)

    print(f"  Deals Won:         ${total_won:,.0f}")
    print(f"  Monthly Recurring: ${monthly_recurring:,.0f}/mo")
    print(f"  Collected:         ${total_collected:,.0f}")
    print(f"  Outstanding:       ${total_outstanding:,.0f}")
    print(f"  Projected Annual:  ${(monthly_recurring * 12 + total_won):,.0f}")
    conn.close()

def show_dashboard():
    conn = get_db()
    print("\n  ============================================")
    print("  BLACKHOLE DASHBOARD")
    print("  ============================================\n")

    total = conn.execute("SELECT COUNT(*) as c FROM clients").fetchone()['c']
    by_status = conn.execute(
        "SELECT status, COUNT(*) as c, SUM(deal_value) as v FROM clients GROUP BY status"
    ).fetchall()

    print(f"  Total Contacts: {total}\n")

    for row in by_status:
        print(f"  {row['status'].upper():<12} {row['c']:>3} contacts   ${row['v'] or 0:>10,.0f}")

    print()
    show_revenue()

    # Show overdue follow-ups
    today = datetime.now().strftime("%Y-%m-%d")
    overdue = conn.execute(
        "SELECT * FROM clients WHERE follow_up_date <= ? AND status NOT IN ('won', 'delivered', 'paid', 'lost')",
        (today,)
    ).fetchall()

    if overdue:
        print(f"\n  === OVERDUE FOLLOW-UPS ({len(overdue)}) ===\n")
        for r in overdue:
            print(f"  #{r['id']} {r['company']} - {r['contact_name']} - due: {r['follow_up_date']}")

    conn.close()

def main(args):
    if not args:
        print("Usage: python run.py crm <add|list|update|pipeline|revenue|note|followup>")
        return

    cmd = args[0].lower()

    if cmd == "add":
        add_client(args[1:])
    elif cmd == "list":
        list_clients(args[1:])
    elif cmd == "update":
        update_status(args[1:])
    elif cmd == "pipeline":
        show_pipeline()
    elif cmd == "revenue":
        show_revenue()
    elif cmd == "note":
        add_note(args[1:])
    elif cmd == "followup":
        set_followup(args[1:])
    else:
        print(f"  Unknown CRM command: {cmd}")
