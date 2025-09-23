from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from pathlib import Path
from datetime import date

STORAGE = Path("storage/challans")
STORAGE.mkdir(parents=True, exist_ok=True)

def challan_pdf_path(challan_id: str) -> Path:
    return STORAGE / f"{challan_id}.pdf"

def generate_challan_pdf(challan, student, guardians, payments) -> str:
    """
    challan: Challan ORM
    student: Student ORM
    guardians: list[Guardian]
    payments: list[Payment]
    """
    p = challan_pdf_path(challan.id)
    c = Canvas(str(p), pagesize=A4)
    W, H = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, H-25*mm, "School Fee Challan")

    c.setFont("Helvetica", 10)
    c.drawString(20*mm, H-35*mm, f"Student: {student.first_name} {student.last_name or ''}  (GR: {student.gr_number})")
    prim = guardians[0].name + " / " + guardians[0].phone if guardians else "N/A"
    c.drawString(20*mm, H-40*mm, f"Guardian: {prim}")
    c.drawString(20*mm, H-45*mm, f"Month: {challan.month.strftime('%b %Y')}  |  Due: {(challan.due_date.strftime('%Y-%m-%d') if challan.due_date else 'N/A')}")

    # Box
    c.setStrokeColor(colors.black)
    c.rect(18*mm, H-110*mm, W-36*mm, 60*mm, stroke=1, fill=0)

    # Amounts
    c.setFont("Helvetica-Bold", 12)
    c.drawString(22*mm, H-60*mm, f"Gross Amount: {float(challan.gross):.2f}")
    c.drawString(22*mm, H-70*mm, f"Discount: {float(challan.discount):.2f}")
    total_paid = sum(float(p.amount) for p in payments)
    net = float(challan.gross) - float(challan.discount)
    balance = max(0.0, net - total_paid)
    c.drawString(22*mm, H-80*mm, f"Net Payable: {net:.2f}")
    c.drawString(22*mm, H-90*mm, f"Paid: {total_paid:.2f}  |  Balance: {balance:.2f}")
    c.setFont("Helvetica", 10)
    c.drawString(22*mm, H-100*mm, f"Status: {challan.status}")
    if challan.note:
        c.drawString(22*mm, H-110*mm, f"Note: {challan.note}")

    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(20*mm, 15*mm, "This is a system-generated document.")
    c.showPage(); c.save()
    return str(p)
