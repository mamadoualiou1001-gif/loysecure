from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import qrcode
from django.conf import settings
from django.utils import timezone
import os

def get_month_bilingual(month_date):
    """Retourne le nom du mois en anglais/français"""
    months = {
        1: ('January', 'Janvier'),
        2: ('February', 'Février'),
        3: ('March', 'Mars'),
        4: ('April', 'Avril'),
        5: ('May', 'Mai'),
        6: ('June', 'Juin'),
        7: ('July', 'Juillet'),
        8: ('August', 'Août'),
        9: ('September', 'Septembre'),
        10: ('October', 'Octobre'),
        11: ('November', 'Novembre'),
        12: ('December', 'Décembre'),
    }
    month_num = month_date.month
    en, fr = months[month_num]
    return f"{en}/{fr} {month_date.year}"

class ReceiptPDFGenerator:
    """Générateur de quittances PDF professionnelles LOYSECURE"""
    
    def __init__(self, receipt):
        self.receipt = receipt
        self.tenant = receipt.tenant
        self.owner = receipt.owner
        self.property = receipt.tenant.property_ref
    
    def generate(self):
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=20*mm,
            bottomMargin=20*mm,
            leftMargin=20*mm,
            rightMargin=20*mm,
        )
        
        styles = getSampleStyleSheet()
        
        # Styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=22,
            alignment=TA_CENTER,
            textColor=colors.white,
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.white,
        )
        
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading3'],
            fontSize=11,
            spaceBefore=8,
            spaceAfter=4,
            textColor=colors.HexColor('#1e3a5f'),
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
        )
        
        bold_style = ParagraphStyle(
            'Bold',
            parent=normal_style,
            fontName='Helvetica-Bold',
        )
        
        # Liste des éléments
        elements = []
        
        # ========== EN-TÊTE ==========
        header_elements = []
        header_elements.append(Paragraph("LOYSECURE", title_style))
        header_elements.append(Spacer(1, 2))
        header_elements.append(Paragraph("Quittance de loyer certifiée", subtitle_style))
        
        header_table = Table([header_elements], colWidths=[450])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#DAA520')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))
        
        # ========== INFORMATIONS ==========
        period_bilingual = get_month_bilingual(self.receipt.month)
        
        info_data = [
            [f"N° Quittance : {str(self.receipt.id)[:8].upper()}", f"Date : {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"],
            [f"Période : {period_bilingual}", f"Heure : {timezone.localtime(self.receipt.certified_at).strftime('%H:%M')}"],
        ]
        
        info_table = Table(info_data, colWidths=[220, 230])
        info_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 10))
        
        # ========== PARTIES ==========
        elements.append(Paragraph("PARTIES PRENANTES", section_style))
        
        parties_data = [
            ['BAILLEUR (PROPRIETAIRE)', 'PRENANT (LOCATAIRE)'],
            [self.owner.get_full_name() or self.owner.username, self.tenant.name],
            [f"Tel : {self.owner.phone}", f"Tel : {self.tenant.phone}"],
            [f"Email : {self.owner.email or '-'}", f"Email : {self.tenant.email or '-'}"],
        ]
        
        parties_table = Table(parties_data, colWidths=[220, 230])
        parties_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 10))
        
        # ========== LOGEMENT ==========
        elements.append(Paragraph("LOGEMENT CONCERNE", section_style))
        
        property_data = [
            [f"Adresse : {self.property.address}"],
            [f"Nombre de chambres : {self.property.number_of_rooms}"],
        ]
        
        property_table = Table(property_data, colWidths=[450])
        property_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(property_table)
        elements.append(Spacer(1, 10))
        
        # ========== PAIEMENT ==========
        elements.append(Paragraph("DETAILS DU PAIEMENT", section_style))
        
        payment_method_label = dict(self.receipt.PAYMENT_METHOD_CHOICES).get(self.receipt.payment_method, '-')
        
        payment_data = [
            [f"Mode de paiement : {payment_method_label}"],
            [f"Montant : {self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}"],
        ]
        
        payment_table = Table(payment_data, colWidths=[450])
        payment_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 10))
        
        # ========== MONTANT EN LETTRES ==========
        elements.append(Paragraph(f"Arrêté la présente quittance à la somme de : {self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}", bold_style))
        elements.append(Spacer(1, 15))
        
        # ========== SIGNATURE ==========
        signature_data = [
            ["Cachet et signature du bailleur :", f"Date : {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"],
            ["_________________________", ""],
        ]
        
        signature_table = Table(signature_data, colWidths=[280, 170])
        signature_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(signature_table)
        elements.append(Spacer(1, 15))
        
        # ========== QR CODE ==========
        verification_url = f"https://loysecure-1.onrender.com/verify/{self.receipt.id}"
        qr = qrcode.make(verification_url)
        qr_path = os.path.join(settings.MEDIA_ROOT, f"temp_qr_{self.receipt.id}.png")
        qr.save(qr_path)
        
        from reportlab.platypus import Image
        
        elements.append(Paragraph("QR CODE DE VERIFICATION", section_style))
        elements.append(Spacer(1, 5))
        elements.append(Image(qr_path, width=80, height=80, hAlign='CENTER'))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("Scannez ce code pour vérifier l'authenticité", normal_style))
        
        # ========== PIED DE PAGE ==========
        elements.append(Spacer(1, 20))
        footer = Paragraph(
            "Document certifié électroniquement via LOYSECURE - Votre loyer, votre preuve.",
            ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.HexColor('#888888'), alignment=TA_CENTER)
        )
        elements.append(footer)
        
        # ========== BORDURE GÉNÉRALE ==========
        main_frame = Table([elements], colWidths=[480])
        main_frame.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        doc.build([main_frame])
        
        # Nettoyer
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        buffer.seek(0)
        return buffer