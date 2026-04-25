"""
Invoice PDF Generator
Generates PDF receipts for appointment payments
"""

from io import BytesIO
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime

from app.models.appointment_payment import AppointmentPayment
from app.models.appointment_request import AppointmentRequest
from app.models.appointment import Appointment


def generate_invoice_pdf(
    db: Session,
    payment: AppointmentPayment,
    appointment_request: AppointmentRequest
) -> bytes:
    """
    Generate PDF invoice receipt for a payment
    
    Args:
        db: Database session
        payment: AppointmentPayment object
        appointment_request: AppointmentRequest object
        
    Returns:
        PDF content as bytes
    """
    try:
        # Try to import reportlab
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except ImportError:
            logger.error("reportlab is not installed. Please install it: pip install reportlab")
            # Fallback: return a simple text-based receipt
            return _generate_simple_text_receipt(payment, appointment_request)
        
        # Create PDF buffer - compact margins for single-page fit
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles (compact for single page)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=4,
            spaceBefore=6
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 9
        
        # Get related data
        patient = appointment_request.patient if appointment_request else None
        doctor = appointment_request.doctor if appointment_request else None
        service = appointment_request.service if appointment_request else None
        
        # Get appointment if exists
        appointment = None
        if appointment_request:
            appointment = db.query(Appointment).filter(
                Appointment.doctor_id == appointment_request.doctor_id,
                Appointment.patient_id == appointment_request.patient_id,
                Appointment.appointment_date == appointment_request.preferred_date,
                Appointment.start_time == appointment_request.preferred_time,
                Appointment.deleted_at.is_(None)
            ).first()
        
        invoice_number = f"INV-{str(payment.id)[:8].upper()}"
        appointment_date = appointment.appointment_date if appointment else appointment_request.preferred_date if appointment_request else None
        appointment_time = appointment.start_time if appointment else appointment_request.preferred_time if appointment_request else None
        consultation_mode = appointment.consultation_mode if appointment else appointment_request.consultation_mode if appointment_request else None
        
        # Title (compact)
        elements.append(Paragraph("INVOICE RECEIPT", title_style))
        elements.append(Spacer(1, 0.12*inch))
        
        # Single row: Invoice | Patient | Doctor (all aligned in one line/block)
        col_width = 2.25 * inch
        invoice_col = [
            [Paragraph('<b>Invoice</b>', normal_style)],
            [f"{invoice_number}"],
            [payment.created_at.strftime('%b %d, %Y') if payment.created_at else 'N/A'],
            [payment.created_at.strftime('%I:%M %p') if payment.created_at else 'N/A'],
        ]
        patient_col = [
            [Paragraph('<b>Patient</b>', normal_style)],
            [patient.name if patient else 'N/A'],
            [patient.email if patient else 'N/A'],
            [patient.phone if patient else 'N/A'],
        ]
        doctor_col = [
            [Paragraph('<b>Doctor</b>', normal_style)],
            [doctor.name if doctor else 'N/A'],
            [doctor.email if doctor else 'N/A'],
            [''],
        ]
        # Build one table with 3 columns
        line1_data = []
        for i in range(4):
            line1_data.append([
                invoice_col[i][0] if i < len(invoice_col) else '',
                patient_col[i][0] if i < len(patient_col) else '',
                doctor_col[i][0] if i < len(doctor_col) else '',
            ])
        one_line_table = Table(line1_data, colWidths=[col_width, col_width, col_width])
        one_line_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#333333')),
        ]))
        elements.append(one_line_table)
        elements.append(Spacer(1, 0.15*inch))
        
        # Appointment + Payment in one row (two columns: appointment left, payment right)
        appointment_details = [
            [Paragraph('<b>Appointment</b>', normal_style), ''],
            ['Service', service.name if service else 'N/A'],
            ['Date', appointment_date.strftime('%b %d, %Y') if appointment_date else 'N/A'],
            ['Time', appointment_time.strftime('%I:%M %p') if appointment_time else 'N/A'],
            ['Mode', consultation_mode.replace('_', ' ').title() if consultation_mode else 'N/A'],
        ]
        payment_details = [['Description', 'Amount']]
        if getattr(payment, 'amount_before_waiver', None) is not None and getattr(payment, 'waiver_percent', None) not in (None, 0):
            payment_details.append(['Original Fee (before waiver)', f"{payment.currency} {float(payment.amount_before_waiver):.2f}"])
            payment_details.append(['Waiver Applied', f"-{payment.waiver_percent}%"])
        payment_details.append(['Appointment Fee', f"{payment.currency} {float(payment.amount):.2f}"])
        payment_details.append(['Total Amount', f"{payment.currency} {float(payment.amount):.2f}"])
        payment_details.append(['Status', payment.status])
        payment_details.append(['Mode', 'Online'])
        
        appt_table = Table(appointment_details, colWidths=[1.1*inch, 2.5*inch])
        appt_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#333333')),
        ]))
        pay_table = Table(payment_details, colWidths=[2.2*inch, 1.4*inch])
        pay_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        combined = Table([[appt_table, pay_table]], colWidths=[3.75*inch, 3.75*inch])
        combined.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
            ('RIGHTPADDING', (1, 0), (1, -1), 0),
        ]))
        elements.append(combined)
        elements.append(Spacer(1, 0.15*inch))
        
        # Footer (compact)
        footer_text = "Thank you for your payment. This is a computer-generated receipt and does not require a signature."
        elements.append(Paragraph(footer_text, ParagraphStyle(
            'Footer',
            parent=normal_style,
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceBefore=4
        )))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
        
    except Exception as e:
        logger.error(f"Error generating PDF invoice: {str(e)}", exc_info=True)
        # Fallback to simple text receipt
        return _generate_simple_text_receipt(payment, appointment_request)


def _generate_simple_text_receipt(
    payment: AppointmentPayment,
    appointment_request: AppointmentRequest
) -> bytes:
    """
    Generate a simple text-based receipt as fallback
    
    Args:
        payment: AppointmentPayment object
        appointment_request: AppointmentRequest object
        
    Returns:
        Text receipt as bytes
    """
    invoice_number = f"INV-{str(payment.id)[:8].upper()}"
    
    patient = appointment_request.patient if appointment_request else None
    doctor = appointment_request.doctor if appointment_request else None
    service = appointment_request.service if appointment_request else None
    
    receipt_text = f"""
INVOICE RECEIPT
{'=' * 50}

Invoice Number: {invoice_number}
Invoice Date: {payment.created_at.strftime('%B %d, %Y') if payment.created_at else 'N/A'}
Payment Date: {payment.created_at.strftime('%B %d, %Y %I:%M %p') if payment.created_at else 'N/A'}

Patient Information:
  Name: {patient.name if patient else 'N/A'}
  Email: {patient.email if patient else 'N/A'}
  Phone: {patient.phone if patient else 'N/A'}

Doctor Information:
  Name: {doctor.name if doctor else 'N/A'}
  Email: {doctor.email if doctor else 'N/A'}

Appointment Details:
  Service: {service.name if service else 'N/A'}
  Date: {appointment_request.preferred_date.strftime('%B %d, %Y') if appointment_request and appointment_request.preferred_date else 'N/A'}
  Time: {appointment_request.preferred_time.strftime('%I:%M %p') if appointment_request and appointment_request.preferred_time else 'N/A'}
  Consultation Mode: {appointment_request.consultation_mode.replace('_', ' ').title() if appointment_request and appointment_request.consultation_mode else 'N/A'}

Payment Details:
  Description: Appointment Fee
  Amount: {payment.currency} {float(payment.amount):.2f}
"""
    if getattr(payment, 'amount_before_waiver', None) is not None and getattr(payment, 'waiver_percent', None) not in (None, 0):
        receipt_text += f"""  Original Fee (before waiver): {payment.currency} {float(payment.amount_before_waiver):.2f}
  Waiver Applied: -{payment.waiver_percent}%

"""
    receipt_text += f"""
  Total Amount: {payment.currency} {float(payment.amount):.2f}
  Payment Status: {payment.status}
  Payment Mode: Online

{'=' * 50}
Thank you for your payment.
This is a computer-generated receipt and does not require a signature.
"""
    
    return receipt_text.encode('utf-8')
