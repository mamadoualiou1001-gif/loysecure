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
        
        # Styles personnalisés
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=22,
            alignment=TA_CENTER,
            spaceAfter=5,
            textColor=colors.white,
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=15,
            textColor=colors.white,
        )
        
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading3'],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=6,
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
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            fontName='Helvetica-Bold',
        )
        
        # ========== EN-TÊTE AVEC FOND DORÉ ==========
        header_text = []
        header_text.append(Paragraph("LOYSECURE", title_style))
        header_text.append(Paragraph("Quittance de loyer certifiée", subtitle_style))
        
        header_table = Table([header_text], colWidths=[450])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#DAA520')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        # ========== INFORMATIONS GÉNÉRALES ==========
        # Période en bilingue
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
        
        # ========== PARTIES PRENANTES ==========
        parties_title = Paragraph("PARTIES PRENANTES", section_style)
        
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
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        
        # ========== LOGEMENT ==========
        logement_title = Paragraph("LOGEMENT CONCERNE", section_style)
        
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
        
        # ========== PAIEMENT ==========
        paiement_title = Paragraph("DETAILS DU PAIEMENT", section_style)
        
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
        
        # ========== MONTANT EN LETTRES ==========
        amount_text = Paragraph(f"Arrêté la présente quittance à la somme de : {self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}", bold_style)
        
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
        
        # ========== QR CODE ==========
        verification_url = f"https://loysecure-1.onrender.com/verify/{self.receipt.id}"
        qr = qrcode.make(verification_url)
        qr_path = os.path.join(settings.MEDIA_ROOT, f"temp_qr_{self.receipt.id}.png")
        qr.save(qr_path)
        
        from reportlab.platypus import Image
        
        qr_title = Paragraph("QR CODE DE VERIFICATION", section_style)
        qr_image = Image(qr_path, width=70, height=70, hAlign='CENTER')
        qr_text = Paragraph("Scannez ce code pour vérifier l'authenticité", normal_style)
        
        qr_content = [qr_title, Spacer(1, 5), qr_image, Spacer(1, 5), qr_text]
        qr_table = Table([[qr_content]], colWidths=[450])
        qr_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4f8')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        # ========== PIED DE PAGE ==========
        footer_text = """
        Document certifié électroniquement via LOYSECURE - Votre loyer, votre preuve.
        Cette quittance a valeur de preuve. Toute modification est interdite.
        """
        footer_style = ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.HexColor('#888888'), alignment=TA_CENTER)
        footer = Paragraph(footer_text, footer_style)
        
        # ========== ASSEMBLAGE FINAL ==========
        story = []
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(info_table)
        story.append(Spacer(1, 10))
        story.append(parties_title)
        story.append(parties_table)
        story.append(Spacer(1, 10))
        story.append(logement_title)
        story.append(property_table)
        story.append(Spacer(1, 10))
        story.append(paiement_title)
        story.append(payment_table)
        story.append(Spacer(1, 10))
        story.append(amount_text)
        story.append(Spacer(1, 15))
        story.append(signature_table)
        story.append(Spacer(1, 15))
        story.append(qr_table)
        story.append(Spacer(1, 20))
        story.append(footer)
        
        # BORDURE GÉNÉRALE
        main_frame = Table([story], colWidths=[480])
        main_frame.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        
        doc.build([main_frame])
        
        # Nettoyer
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        buffer.seek(0)
        return buffer