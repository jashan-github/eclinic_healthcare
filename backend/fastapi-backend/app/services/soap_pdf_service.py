"""
SOAP PDF Generation Service
Generates medical prescription/SOAP note PDFs based on RX templates
"""

import os
from io import BytesIO
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from sqlalchemy.orm import Session

from app.models.soap_note import SoapNote
from app.models.appointment import Appointment
from app.models.rx_template import RxTemplate
from app.models.user import User
from app.models.clinic_location import ClinicLocation
from app.models.profile import UserProfile, ContactDetail
from app.core.exceptions import NotFoundException, ForbiddenException
from app.core.config import settings
from loguru import logger


class SoapPdfService:
    """Service for generating SOAP note PDFs"""
    
    # PDF dimensions (A4)
    PAGE_WIDTH, PAGE_HEIGHT = A4
    # No margins - header sticks to top, body has padding
    MARGIN_TOP = 0
    MARGIN_BOTTOM = 0
    MARGIN_LEFT = 0
    MARGIN_RIGHT = 0
    
    # Body padding (for content below header)
    BODY_PADDING = 12  # 24 points = ~0.33 inch (matching HTML padding: 24px)
    
    # Header dimensions
    HEADER_HEIGHT = 1 * inch
    HEADER_IMAGE_MAX_HEIGHT = 1.2 * inch
    HEADER_IMAGE_MAX_WIDTH = 3 * inch
    
    def __init__(self, db: Session):
        self.db = db
        self._register_fonts()
    
    def _register_fonts(self):
        """Register fonts for PDF generation"""
        try:
            # Try to register common fonts (fallback to default if not available)
            # ReportLab uses Helvetica by default, which is fine for medical documents
            pass
        except Exception as e:
            logger.warning(f"Could not register custom fonts: {e}. Using default fonts.")
    
    def _get_header_info(
        self,
        appointment: Appointment,
        rx_template: Optional[RxTemplate] = None
    ) -> Dict[str, Any]:
        """
        Get header information for PDF (two-column layout or letterhead image)
        
        Returns:
            Dictionary with header data:
            - If letterhead_image_path exists: {"letterhead_image_path": path, "use_image": True}
            - Otherwise: {"left_column": [...], "right_column": [...], "use_image": False}
        """
        # Check if RX template has letterhead image
        letterhead_image_path = None
        if rx_template and rx_template.letterhead_image_path:
            # Resolve the full path to the image file
            from pathlib import Path
            from app.core.config import settings
            
            # Try multiple path resolution strategies
            image_paths_to_try = []
            
            # Strategy 1: If it's already an absolute path
            if rx_template.letterhead_image_path.startswith('/'):
                image_paths_to_try.append(Path(rx_template.letterhead_image_path))
            
            # Strategy 2: Relative to /app/uploads
            image_paths_to_try.append(Path("/app") / settings.UPLOAD_DIR / rx_template.letterhead_image_path.lstrip('/'))
            
            # Strategy 3: Relative to uploads directory (if UPLOAD_DIR is already /app/uploads)
            if not settings.UPLOAD_DIR.startswith('/'):
                image_paths_to_try.append(Path("/app") / settings.UPLOAD_DIR / rx_template.letterhead_image_path.lstrip('/'))
            
            # Strategy 4: Just the path as-is (if it's relative to current working directory)
            image_paths_to_try.append(Path(rx_template.letterhead_image_path))
            
            # Strategy 5: If path contains "uploads", try /app/uploads/...
            if 'uploads' in rx_template.letterhead_image_path:
                # Extract path after "uploads/"
                parts = rx_template.letterhead_image_path.split('uploads/', 1)
                if len(parts) > 1:
                    image_paths_to_try.append(Path("/app/uploads") / parts[1])
            
            # Try each path until we find one that exists
            for image_path in image_paths_to_try:
                try:
                    if image_path.exists() and image_path.is_file():
                        letterhead_image_path = str(image_path.resolve())
                        logger.info(f"Found letterhead image at: {letterhead_image_path}")
                        break
                except Exception as e:
                    logger.debug(f"Path check failed for {image_path}: {e}")
                    continue
            
            if not letterhead_image_path:
                logger.warning(f"Letterhead image not found. Tried paths: {[str(p) for p in image_paths_to_try]}")
        
        # If letterhead image exists, return it
        if letterhead_image_path:
            return {
                "letterhead_image_path": letterhead_image_path,
                "use_image": True
            }
        
        # Otherwise, use location data from RX template's clinic_location_id
        clinic_location = None
        if rx_template and rx_template.clinic_location_id:
            # Get the specific clinic location from RX template's clinic_location_id
            clinic_location = self.db.query(ClinicLocation).filter(
                ClinicLocation.id == rx_template.clinic_location_id,
                ClinicLocation.deleted_at.is_(None)
            ).first()
            
            if not clinic_location:
                logger.warning(f"RX template clinic_location_id {rx_template.clinic_location_id} not found, falling back to any clinic location")
        
        # Fallback: Get clinic location from appointment if RX template doesn't have one
        if not clinic_location:
            clinic_location = self.db.query(ClinicLocation).filter(
                ClinicLocation.clinic_id == appointment.clinic_id,
                ClinicLocation.deleted_at.is_(None)
            ).first()
        
        # Get doctor information
        doctor = appointment.doctor
        doctor_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == appointment.doctor_id
        ).first()
        
        # Get clinic information
        from app.models.user import Clinic
        clinic = self.db.query(Clinic).filter(
            Clinic.id == appointment.clinic_id,
            Clinic.deleted_at.is_(None)
        ).first()
        
        # Build left column (clinic name, doctor name, education)
        # Priority: location name > clinic name > default
        # Location name is more specific and should be used when available
        left_column = []
        if clinic_location and clinic_location.name:
            clinic_name = clinic_location.name
        elif clinic and clinic.name:
            clinic_name = clinic.name
        else:
            clinic_name = "Medical Clinic"
        left_column.append(clinic_name)
        
        if doctor:
            doctor_name = f"Dr. {doctor.name}" if not doctor.name.startswith("Dr.") else doctor.name
            left_column.append(doctor_name)
        
        if doctor_profile and doctor_profile.education:
            left_column.append(doctor_profile.education)
        
        # Build right column (clinic name, contact, address)
        right_column = []
        right_column.append(clinic_name)
        
        # Contact information
        if clinic_location and clinic_location.phone:
            right_column.append(f"Clinic landline: {clinic_location.phone}")
        
        # Address
        address_parts = []
        if clinic_location:
            if clinic_location.building_name:
                address_parts.append(clinic_location.building_name)
            if clinic_location.street_name:
                address_parts.append(clinic_location.street_name)
            if clinic_location.city:
                city_name = clinic_location.city.name if hasattr(clinic_location.city, 'name') else str(clinic_location.city)
                address_parts.append(city_name)
            if clinic_location.state:
                state_name = clinic_location.state.name if hasattr(clinic_location.state, 'name') else str(clinic_location.state)
                address_parts.append(state_name)
            if clinic_location.pincode:
                address_parts.append(clinic_location.pincode)
        
        if address_parts:
            right_column.append(f"Location: {', '.join(address_parts)}")
        
        return {
            "left_column": left_column,
            "right_column": right_column,
            "use_image": False
        }
    
    def _get_patient_info(self, appointment: Appointment) -> Dict[str, Any]:
        """Get patient information for PDF"""
        patient = appointment.patient
        patient_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == appointment.patient_id
        ).first()
        
        # Calculate age
        age = None
        if patient_profile and patient_profile.date_of_birth:
            today = datetime.now().date()
            age = today.year - patient_profile.date_of_birth.year
            if (today.month, today.day) < (patient_profile.date_of_birth.month, patient_profile.date_of_birth.day):
                age -= 1
        
        # Get gender
        gender = None
        if patient_profile and patient_profile.gender:
            gender = patient_profile.gender
        
        return {
            "name": patient.name if patient else "N/A",
            "age": age,
            "gender": gender
        }
    
    def _format_text_for_pdf(self, text: Optional[str]) -> str:
        """Format text for PDF (handle None, newlines, special characters)
        
        Note: This method is used for text that will be split by <br/> tags.
        We preserve <br/> tags but escape other HTML characters.
        """
        if not text:
            return ""
        
        # First, normalize line breaks - convert \n to <br/> for consistency
        text = text.replace('\n', '<br/>')
        text = text.replace('\r\n', '<br/>')
        text = text.replace('\r', '<br/>')
        
        # Escape special characters for ReportLab, but preserve <br/> tags
        # Temporarily replace <br/> with a placeholder
        text = text.replace('<br/>', '___BR_TAG___')
        text = text.replace('<br>', '___BR_TAG___')
        text = text.replace('<BR/>', '___BR_TAG___')
        text = text.replace('<BR>', '___BR_TAG___')
        
        # Now escape HTML characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        # Restore <br/> tags (they're now safe since we escaped < and >)
        text = text.replace('___BR_TAG___', '<br/>')
        
        return text
    
    def _create_header(self, story, header_info: Dict[str, Any]):
        """Create PDF header (two-column layout) - NOT USED, header drawn on canvas"""
        # Header is now drawn on canvas, not in story
        pass
    
    def _calculate_header_height(self, header_info: Dict[str, Any]) -> float:
        """Calculate the actual header height (for spacing in story)"""
        use_image = header_info.get("use_image", False)
        letterhead_image_path = header_info.get("letterhead_image_path")
        
        if use_image and letterhead_image_path:
            try:
                from PIL import Image as PILImage
                image_path = Path(letterhead_image_path)
                
                if image_path.exists() and image_path.is_file():
                    # Get image dimensions using PIL
                    with PILImage.open(str(image_path)) as pil_img:
                        img_width, img_height = pil_img.size
                    
                    # Calculate dimensions to fit page width while maintaining aspect ratio
                    aspect_ratio = img_height / img_width if img_width > 0 else 1
                    
                    # Scale to fit full page width
                    scaled_width = self.PAGE_WIDTH
                    scaled_height = scaled_width * aspect_ratio
                    
                    # Limit height to reasonable size (e.g., 2 inches max)
                    max_height = 2 * inch
                    if scaled_height > max_height:
                        scaled_height = max_height
                    
                    # Return height + divider (6 points)
                    return scaled_height + 6
            except Exception as e:
                logger.warning(f"Error calculating image header height: {str(e)}, using default")
        
        # Default text header height
        return self.HEADER_HEIGHT
    
    def _draw_header_on_canvas(self, canvas, header_info: Dict[str, Any]):
        """Draw header on canvas (sticky to top, full width, no margins)
        
        Supports two modes:
        1. Image mode: If letterhead_image_path is provided, draw the image
        2. Text mode: Draw two-column text layout with clinic/doctor info
        """
        canvas.saveState()
        
        # Header position (at very top of page)
        y = self.PAGE_HEIGHT - 10  # Start from top with small offset
        
        available_width = self.PAGE_WIDTH  # Full page width
        
        # Check if we should use letterhead image
        use_image = header_info.get("use_image", False)
        letterhead_image_path = header_info.get("letterhead_image_path")
        
        if use_image and letterhead_image_path:
            # Draw letterhead image
            try:
                from PIL import Image as PILImage
                image_path = Path(letterhead_image_path)
                
                if image_path.exists() and image_path.is_file():
                    # Get image dimensions using PIL
                    with PILImage.open(str(image_path)) as pil_img:
                        img_width, img_height = pil_img.size
                    
                    # Calculate dimensions to fit page width while maintaining aspect ratio
                    aspect_ratio = img_height / img_width if img_width > 0 else 1
                    
                    # Scale to fit full page width (no padding for letterhead image)
                    scaled_width = available_width
                    scaled_height = scaled_width * aspect_ratio
                    
                    # Limit height to reasonable size (e.g., 2 inches max) to prevent huge headers
                    max_height = 2 * inch
                    if scaled_height > max_height:
                        scaled_height = max_height
                        scaled_width = scaled_height / aspect_ratio
                        # Center horizontally if we had to limit height
                        x_offset = (available_width - scaled_width) / 2
                    else:
                        # Full width, no offset
                        x_offset = 0
                    
                    # Draw image at very top of page (y is at top, so subtract height)
                    # Start from top with minimal offset
                    image_y = self.PAGE_HEIGHT - scaled_height
                    
                    canvas.drawImage(
                        str(image_path),
                        x_offset,
                        image_y,
                        width=scaled_width,
                        height=scaled_height,
                        preserveAspectRatio=True
                    )
                    
                    # Draw divider line below image
                    divider_y = image_y - 6
                    canvas.setStrokeColor(colors.HexColor('#c5c5c5'))
                    canvas.setLineWidth(1)
                    canvas.line(0, divider_y, available_width, divider_y)
                else:
                    logger.warning(f"Letterhead image not found: {letterhead_image_path}, falling back to text header")
                    # Fall back to text header
                    self._draw_text_header(canvas, header_info, y, available_width)
            except ImportError:
                logger.warning("PIL/Pillow not available, falling back to text header")
                self._draw_text_header(canvas, header_info, y, available_width)
            except Exception as e:
                logger.error(f"Error drawing letterhead image: {str(e)}, falling back to text header")
                # Fall back to text header
                self._draw_text_header(canvas, header_info, y, available_width)
        else:
            # Draw text header (two-column layout)
            self._draw_text_header(canvas, header_info, y, available_width)
        
        canvas.restoreState()
    
    def _draw_text_header(self, canvas, header_info: Dict[str, Any], y: float, available_width: float):
        """Draw text-based header (two-column layout)"""
        # Get header data
        left_column = header_info.get("left_column", [])
        right_column = header_info.get("right_column", [])
        
        # Draw left column
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(colors.HexColor('#0b57d0'))
        current_y = y - 10
        line_height = 16
        
        if left_column:
            # First line: Clinic name (blue, bold)
            if len(left_column) > 0:
                canvas.drawString(10, current_y, left_column[0])
                current_y -= line_height
            
            # Rest: Doctor name and education (black, regular)
            canvas.setFont("Helvetica", 12)
            canvas.setFillColor(colors.HexColor('#111'))
            for line in left_column[1:]:
                canvas.drawString(10, current_y, line)
                current_y -= (line_height - 2)
        
        # Draw right column (right-aligned)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.setFillColor(colors.HexColor('#0b57d0'))
        current_y = y - 10
        
        if right_column:
            # First line: Clinic name (blue, bold, right-aligned)
            if len(right_column) > 0:
                text_width = canvas.stringWidth(right_column[0], "Helvetica-Bold", 14)
                canvas.drawString(available_width - text_width - 10, current_y, right_column[0])
                current_y -= line_height
            
            # Rest: Contact and address (gray, regular, right-aligned)
            canvas.setFont("Helvetica", 11)
            canvas.setFillColor(colors.HexColor('#666'))
            for line in right_column[1:]:
                text_width = canvas.stringWidth(line, "Helvetica", 11)
                canvas.drawString(available_width - text_width - 10, current_y, line)
                current_y -= (line_height - 3)
        
        # Draw divider line
        divider_y = current_y - 6
        canvas.setStrokeColor(colors.HexColor('#c5c5c5'))
        canvas.setLineWidth(1)
        canvas.line(0, divider_y, available_width, divider_y)
    
    def _create_patient_meta_section(self, story, patient_info: Dict[str, Any], soap_note: SoapNote):
        """Create patient and metadata section (single line format)"""
        styles = getSampleStyleSheet()
        # Body has padding from all sides
        available_width = self.PAGE_WIDTH - (2 * self.BODY_PADDING)
        
        # Left-aligned patient info (single line: "Patient Name, Gender, Age year(s)")
        left_style = ParagraphStyle(
            'PatientLeft',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#111'),
            leading=14,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        # Right-aligned date/time (format: "13/04/2025, 22:02 AM")
        right_style = ParagraphStyle(
            'PatientRight',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#111'),
            leading=14,
            alignment=TA_RIGHT
        )
        
        # Build patient info string: "Demo Patient, Male, 41 year(s)"
        patient_parts = []
        if patient_info.get('name'):
            patient_parts.append(patient_info['name'])
        if patient_info.get('gender'):
            patient_parts.append(patient_info['gender'].capitalize())
        if patient_info.get('age') is not None:
            patient_parts.append(f"{patient_info['age']} year(s)")
        
        patient_text = ", ".join(patient_parts)
        
        # Right column: Date/Time (format: "13/04/2025, 22:02 AM")
        created_at = soap_note.created_at or datetime.now()
        date_str = created_at.strftime("%d/%m/%Y")
        time_str = created_at.strftime("%I:%M %p").lstrip('0')  # Remove leading zero from hour
        date_time_text = f"{date_str}, {time_str}"
        
        # Create table with body padding
        col_width = available_width / 2
        data = [
            [Paragraph(patient_text, left_style), Paragraph(date_time_text, right_style)]
        ]
        
        table = Table(data, colWidths=[col_width, col_width])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), self.BODY_PADDING),
            ('RIGHTPADDING', (0, 0), (-1, -1), self.BODY_PADDING),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))
    
    def _create_soap_section(self, story, section_letter: str, section_title: str, section_content: Optional[str]):
        """Create a SOAP section with icon box and content"""
        styles = getSampleStyleSheet()
        # Body has padding from all sides
        available_width = self.PAGE_WIDTH - (2 * self.BODY_PADDING)
        
        # Icon column width
        icon_width = 0.6 * inch
        content_width = available_width - icon_width
        
        # Icon style (blue rounded box)
        icon_style = ParagraphStyle(
            f'{section_letter}Icon',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#0230d4'),
            leading=16,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            backColor=colors.HexColor('#e8eefd'),
            borderPadding=10
        )
        
        # Section title style
        title_style = ParagraphStyle(
            f'{section_letter}Title',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#111'),
            leading=14,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=6
        )
        
        # Content style (for bullet points)
        content_style = ParagraphStyle(
            f'{section_letter}Content',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#111'),
            leading=14,
            alignment=TA_LEFT,
            leftIndent=16,
            spaceAfter=4,
            bulletIndent=0
        )
        
        # Create icon box (blue rounded background)
        icon_box = Table(
            [[Paragraph(f"<b>{section_letter}</b>", icon_style)]],
            colWidths=[icon_width]
        )
        icon_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8eefd')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0230d4')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            # Rounded corners effect (approximate with border)
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#e8eefd')]),
        ]))
        
        # Build content column
        content_items = []
        
        # Section title
        content_items.append(Paragraph(section_title, title_style))
        
        # Content as bullet points
        if section_content:
            formatted_content = self._format_text_for_pdf(section_content)
            # Split by lines and create bullet points
            lines = formatted_content.split('<br/>')
            for line in lines:
                if line.strip():
                    # Create bullet point
                    bullet_text = f"• {line.strip()}"
                    content_items.append(Paragraph(bullet_text, content_style))
        else:
            content_items.append(Paragraph("• No information provided.", content_style))
        
        # Create content column table
        content_table_data = [[item] for item in content_items]
        content_table = Table(content_table_data, colWidths=[content_width])
        content_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        # Combine icon and content in a single row table
        section_table = Table(
            [[icon_box, content_table]],
            colWidths=[icon_width, content_width]
        )
        section_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), self.BODY_PADDING),
            ('RIGHTPADDING', (0, 0), (-1, -1), self.BODY_PADDING),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(section_table)
        
        # Add divider line (with body padding)
        divider = Table(
            [[Paragraph("", styles['Normal'])]],
            colWidths=[available_width]
        )
        divider.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#c5c5c5')),
            ('LEFTPADDING', (0, 0), (-1, -1), (self.BODY_PADDING / 2)),
            ('RIGHTPADDING', (0, 0), (-1, -1), (self.BODY_PADDING / 2)),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(divider)
    
    def _create_footer(self, canvas, doc):
        """Create footer with page numbers"""
        canvas.saveState()
        
        # Footer text
        footer_text = f"Page {doc.page}"
        
        # Draw footer
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor('#666666'))
        
        # Center footer
        text_width = canvas.stringWidth(footer_text, "Helvetica", 9)
        x = (self.PAGE_WIDTH - text_width) / 2
        y = 0.5 * inch
        
        canvas.drawString(x, y, footer_text)
        canvas.restoreState()
    
    def generate_pdf(
        self,
        soap_note_id: UUID,
        rx_template_id: Optional[UUID] = None,
        current_user_id: Optional[UUID] = None
    ) -> BytesIO:
        """
        Generate SOAP note PDF
        
        Args:
            soap_note_id: SOAP note ID
            rx_template_id: Optional RX template ID (if None, uses default or text header)
            current_user_id: Current user ID for authorization
        
        Returns:
            BytesIO object containing PDF data
        
        Raises:
            NotFoundException: If SOAP note or template not found
            ForbiddenException: If user doesn't have access
        """
        # Get SOAP note with relationships
        soap_note = self.db.query(SoapNote).filter(
            SoapNote.id == soap_note_id,
            SoapNote.deleted_at.is_(None)
        ).first()
        
        if not soap_note:
            raise NotFoundException(
                message="SOAP note not found",
                errors={"soap_note_id": ["SOAP note with this ID does not exist"]}
            )
        
        # Get appointment
        appointment = self.db.query(Appointment).filter(
            Appointment.id == soap_note.appointment_id,
            Appointment.deleted_at.is_(None)
        ).first()
        
        if not appointment:
            raise NotFoundException(
                message="Appointment not found",
                errors={"appointment_id": ["Appointment associated with this SOAP note does not exist"]}
            )
        
        # Authorization check
        if current_user_id:
            # Check if user is the doctor, clinic admin, or staff
            current_user = self.db.query(User).filter(User.id == current_user_id).first()
            if current_user:
                is_authorized = (
                    current_user.id == appointment.doctor_id or
                    current_user.role in ['clinic_admin', 'super_admin'] or
                    (current_user.role in ['nurse', 'staff', 'receptionist'] and 
                     current_user.clinic_id == appointment.clinic_id)
                )
                if not is_authorized:
                    raise ForbiddenException(
                        message="Access denied",
                        errors={"soap_note_id": ["You do not have permission to access this SOAP note"]}
                    )
        
        # Get RX template if provided
        rx_template = None
        if rx_template_id:
            rx_template = self.db.query(RxTemplate).filter(
                RxTemplate.id == rx_template_id,
                RxTemplate.deleted_at.is_(None)
            ).first()
            
            if not rx_template:
                raise NotFoundException(
                    message="RX template not found",
                    errors={"rx_template_id": ["RX template with this ID does not exist"]}
                )
            
            # Verify template belongs to the doctor
            if rx_template.doctor_id != appointment.doctor_id:
                raise ForbiddenException(
                    message="Access denied",
                    errors={"rx_template_id": ["This template does not belong to the appointment's doctor"]}
                )
        else:
            # Try to get default template for this doctor at this clinic location
            # First, get clinic location from appointment
            clinic_location = self.db.query(ClinicLocation).filter(
                ClinicLocation.clinic_id == appointment.clinic_id,
                ClinicLocation.deleted_at.is_(None)
            ).first()
            
            if clinic_location:
                rx_template = self.db.query(RxTemplate).filter(
                    RxTemplate.doctor_id == appointment.doctor_id,
                    RxTemplate.clinic_location_id == clinic_location.id,
                    RxTemplate.is_default == True,
                    RxTemplate.deleted_at.is_(None)
                ).first()
        
        # Get header information
        header_info = self._get_header_info(appointment, rx_template)
        
        # Calculate actual header height (for image or text)
        actual_header_height = self._calculate_header_height(header_info)
        
        # Get patient information
        patient_info = self._get_patient_info(appointment)
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=self.MARGIN_RIGHT,
            leftMargin=self.MARGIN_LEFT,
            topMargin=self.MARGIN_TOP,
            bottomMargin=self.MARGIN_BOTTOM
        )
        
        # Build story (content)
        story = []
        
        # Header will be drawn on canvas (sticky to top)
        # Add spacer for header height (use calculated height)
        story.append(Spacer(1, actual_header_height))
        
        # Patient & Meta section (with body padding)
        self._create_patient_meta_section(story, patient_info, soap_note)
        
        # SOAP sections
        # S - Subjective
        self._create_soap_section(
            story,
            "S",
            "Subjective",
            soap_note.subjective
        )
        
        # O - Objective
        self._create_soap_section(
            story,
            "O",
            "Objective",
            soap_note.objective
        )
        
        # A - Assessment
        self._create_soap_section(
            story,
            "A",
            "Assessment",
            soap_note.assessment
        )
        
        # P - Plan
        self._create_soap_section(
            story,
            "P",
            "Plan",
            soap_note.plan
        )
        
        # Build PDF with header/footer on all pages
        def on_first_page(canvas, doc):
            self._draw_header_on_canvas(canvas, header_info)
            self._create_footer(canvas, doc)
        
        def on_later_pages(canvas, doc):
            self._draw_header_on_canvas(canvas, header_info)
            self._create_footer(canvas, doc)
        
        doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
        
        buffer.seek(0)
        return buffer
    
