"""
BlackHole Invoice Generator - Create professional HTML invoices and track payments.
"""

import os
import sys
from datetime import datetime, timedelta

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "invoices")

def create_invoice(args):
    if len(args) < 3:
        print("Usage: python run.py invoice create <client_name> <description> <amount> [--due DAYS]")
        return

    client = args[0]
    description = args[1]
    amount = float(args[2])
    due_days = 14

    i = 3
    while i < len(args):
        if args[i] == "--due" and i + 1 < len(args):
            due_days = int(args[i + 1])
            i += 2
        else:
            i += 1

    # Save to database
    from engine.crm import get_db
    conn = get_db()

    # Find or reference client
    client_row = conn.execute("SELECT id FROM clients WHERE company LIKE ?", (f"%{client}%",)).fetchone()
    client_id = client_row['id'] if client_row else None

    cursor = conn.execute(
        "INSERT INTO invoices (client_id, description, amount) VALUES (?, ?, ?)",
        (client_id, description, amount)
    )
    invoice_id = cursor.lastrowid
    conn.commit()

    invoice_number = f"BH-{datetime.now().strftime('%Y%m')}-{invoice_id:04d}"
    issue_date = datetime.now().strftime("%B %d, %Y")
    due_date = (datetime.now() + timedelta(days=due_days)).strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Invoice {invoice_number}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #333; background: #fff; }}
    .invoice {{ max-width: 800px; margin: 0 auto; padding: 50px 40px; }}
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 50px; }}
    .brand h1 {{ font-size: 28px; color: #0f3460; }}
    .brand p {{ font-size: 13px; color: #666; margin-top: 5px; }}
    .invoice-title {{ text-align: right; }}
    .invoice-title h2 {{ font-size: 36px; color: #0f3460; letter-spacing: 3px; }}
    .invoice-title p {{ font-size: 14px; color: #666; margin-top: 5px; }}
    .details {{ display: flex; justify-content: space-between; margin-bottom: 40px; }}
    .details-block h3 {{ font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #999; margin-bottom: 8px; }}
    .details-block p {{ font-size: 14px; margin-bottom: 3px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
    th {{ background: #0f3460; color: white; padding: 12px 15px; text-align: left; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }}
    th:last-child {{ text-align: right; }}
    td {{ padding: 15px; border-bottom: 1px solid #eee; font-size: 14px; }}
    td:last-child {{ text-align: right; font-weight: 500; }}
    .totals {{ display: flex; justify-content: flex-end; }}
    .totals-table {{ width: 280px; }}
    .totals-table tr td {{ padding: 8px 15px; font-size: 14px; }}
    .totals-table tr:last-child td {{ font-size: 20px; font-weight: bold; color: #0f3460; border-top: 2px solid #0f3460; padding-top: 12px; }}
    .payment {{ background: #f8f9ff; border-radius: 10px; padding: 25px; margin-top: 30px; }}
    .payment h3 {{ font-size: 14px; color: #0f3460; margin-bottom: 10px; }}
    .payment p {{ font-size: 13px; margin-bottom: 5px; }}
    .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #999; }}
    @media print {{ .invoice {{ padding: 20px; }} }}
</style>
</head>
<body>
<div class="invoice">
    <div class="header">
        <div class="brand">
            <h1>[Your Name / Brand]</h1>
            <p>[Your Address]<br>[City, UAE]<br>[your@email.com]<br>[+971 XX XXX XXXX]</p>
        </div>
        <div class="invoice-title">
            <h2>INVOICE</h2>
            <p>{invoice_number}</p>
        </div>
    </div>

    <div class="details">
        <div class="details-block">
            <h3>Bill To</h3>
            <p><strong>{client}</strong></p>
            <p>[Client Address]</p>
            <p>[Client Email]</p>
        </div>
        <div class="details-block" style="text-align: right;">
            <h3>Invoice Details</h3>
            <p><strong>Invoice:</strong> {invoice_number}</p>
            <p><strong>Issued:</strong> {issue_date}</p>
            <p><strong>Due:</strong> {due_date}</p>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th style="text-align: right;">Amount</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>
                    <strong>{description}</strong><br>
                    <span style="font-size: 12px; color: #666;">[Add detailed breakdown here]</span>
                </td>
                <td>${amount:,.2f}</td>
            </tr>
        </tbody>
    </table>

    <div class="totals">
        <table class="totals-table">
            <tr>
                <td>Subtotal</td>
                <td>${amount:,.2f}</td>
            </tr>
            <tr>
                <td>VAT (0%)</td>
                <td>$0.00</td>
            </tr>
            <tr>
                <td>Total Due</td>
                <td>${amount:,.2f}</td>
            </tr>
        </table>
    </div>

    <div class="payment">
        <h3>Payment Methods</h3>
        <p><strong>Bank Transfer (Wise):</strong></p>
        <p>Account Name: [Your Name]</p>
        <p>IBAN: [Your IBAN]</p>
        <p>SWIFT/BIC: [Your SWIFT]</p>
        <p style="margin-top: 10px;"><strong>Stripe:</strong> [Payment link]</p>
        <p style="margin-top: 10px;"><strong>PayPal:</strong> [your@email.com]</p>
    </div>

    <div class="footer">
        <p>Thank you for your business. Payment is due within {due_days} days of invoice date.</p>
        <p>Questions? Contact [your@email.com]</p>
    </div>
</div>
</body>
</html>"""

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_name = client.replace(" ", "_").lower()
    filename = f"invoice_{invoice_number}_{safe_name}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  Invoice #{invoice_number} created: {filepath}")
    print(f"  Client: {client}")
    print(f"  Amount: ${amount:,.2f}")
    print(f"  Due: {due_date}")
    print(f"  Open in browser to view/print to PDF.")
    conn.close()

def list_invoices(args=None):
    from engine.crm import get_db
    conn = get_db()
    rows = conn.execute("""
        SELECT i.*, c.company FROM invoices i
        LEFT JOIN clients c ON i.client_id = c.id
        ORDER BY i.created_at DESC
    """).fetchall()

    if not rows:
        print("  No invoices found.")
        return

    total_invoiced = 0
    total_paid = 0
    total_outstanding = 0

    print(f"\n  {'ID':<6} {'Client':<20} {'Description':<25} {'Amount':<12} {'Status':<10} {'Date':<12}")
    print("  " + "-" * 85)

    for r in rows:
        client_name = r['company'] or 'Unknown'
        status = r['status']
        amount = r['amount']
        total_invoiced += amount
        if status == 'paid':
            total_paid += amount
        else:
            total_outstanding += amount

        print(f"  {r['id']:<6} {client_name:<20} {r['description'][:24]:<25} ${amount:<11,.2f} {status:<10} {r['created_at'][:10]:<12}")

    print(f"\n  Total Invoiced:    ${total_invoiced:,.2f}")
    print(f"  Total Paid:        ${total_paid:,.2f}")
    print(f"  Total Outstanding: ${total_outstanding:,.2f}")
    conn.close()

def mark_paid(args):
    if not args:
        print("Usage: python run.py invoice mark-paid <invoice_id>")
        return

    invoice_id = int(args[0])
    from engine.crm import get_db
    conn = get_db()

    inv = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
    if not inv:
        print(f"  Invoice #{invoice_id} not found.")
        return

    conn.execute(
        "UPDATE invoices SET status = 'paid', paid_at = CURRENT_TIMESTAMP WHERE id = ?",
        (invoice_id,)
    )
    conn.commit()
    print(f"  Invoice #{invoice_id} marked as PAID (${inv['amount']:,.2f})")
    conn.close()

def main(args):
    if not args:
        print("Usage: python run.py invoice <create|list|mark-paid> [args]")
        return

    cmd = args[0].lower()
    if cmd == "create":
        create_invoice(args[1:])
    elif cmd == "list":
        list_invoices(args[1:])
    elif cmd in ("mark-paid", "markpaid", "paid"):
        mark_paid(args[1:])
    else:
        print(f"  Unknown invoice command: {cmd}")
