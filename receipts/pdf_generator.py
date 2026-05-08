from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import qrcode
from django.conf import settings
from django.utils import timezone
import os

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
            topMargin=15*mm,
            bottomMargin=15*mm,
            leftMargin=15*mm,
            rightMargin=15*mm,
        )
        
        styles = getSampleStyleSheet()
        
        # Styles personnalisés
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=22,
            alignment=TA_CENTER,
            spaceAfter=5,
            textColor=colors.HexColor('#1e3a5f'),
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=15,
            textColor=colors.HexColor('#666666'),
        )
        
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading3'],
            fontSize=11,
            spaceBefore=12,
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
        
        # Contenu principal
        content = []
        
        # ========== EN-TÊTE ==========
        content.append(Paragraph("LOYSECURE", title_style))
        content.append(Paragraph("Quittance de loyer certifiée", subtitle_style))
        
        # Ligne décorative
        line_table = Table([['']], colWidths=[450])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 1.5, colors.HexColor('#1e3a5f')),
        ]))
        content.append(line_table)
        content.append(Spacer(1, 10))
        
        # ========== INFORMATIONS GÉNÉRALES (sans balises HTML) ==========
        info_data = [
            [
                f"N° Quittance : {str(self.receipt.id)[:8].upper()}",
                f"Date : {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"
            ],
            [
                f"Période : {self.receipt.month.strftime('%B %Y')}",
                f"Heure : {timezone.localtime(self.receipt.certified_at).strftime('%H:%M')}"
            ],
        ]
        
        info_table = Table(info_data, colWidths=[225, 225])
        info_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 12))
        
        # ========== PARTIES PRENANTES ==========
        content.append(Paragraph("PARTIES PRENANTES", section_style))
        
        parties_data = [
            ['BAILLEUR (PROPRIETAIRE)', 'PRENANT (LOCATAIRE)'],
            [self.owner.get_full_name() or self.owner.username, self.tenant.name],
            [f"Tel : {self.owner.phone}", f"Tel : {self.tenant.phone}"],
            [f"Email : {self.owner.email or '-'}", f"Email : {self.tenant.email or '-'}"],
        ]
        
        parties_table = Table(parties_data, colWidths=[225, 225])
        parties_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        content.append(parties_table)
        content.append(Spacer(1, 12))
        
        # ========== LOGEMENT ==========
        content.append(Paragraph("LOGEMENT CONCERNE", section_style))
        
        property_data = [
            [f"• Adresse : {self.property.address}"],
            [f"• Nombre de chambres : {self.property.number_of_rooms}"],
        ]
        if self.property.description:
            property_data.append([f"• Description : {self.property.description}"])
        
        property_table = Table(property_data, colWidths=[450])
        property_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        content.append(property_table)
        content.append(Spacer(1, 12))
        
        # ========== DÉTAILS PAIEMENT ==========
        content.append(Paragraph("DETAILS DU PAIEMENT", section_style))
        
        # Récupérer le libellé du mode de paiement
        payment_method_label = dict(self.receipt.PAYMENT_METHOD_CHOICES).get(self.receipt.payment_method, '-')
        
        payment_data = [
            [f"• Mode de paiement : {payment_method_label}"],
            [f"• Montant : {self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}"],
        ]
        
        payment_table = Table(payment_data, colWidths=[450])
        payment_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        content.append(payment_table)
        content.append(Spacer(1, 12))
        
        # ========== MONTANT EN LETTRES ==========
        amount_text = f"Arrêté la présente quittance à la somme de : {self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}"
        content.append(Paragraph(amount_text, bold_style))
        content.append(Spacer(1, 15))
        
        # ========== SIGNATURE ==========
        signature_data = [
            ["Cachet et signature du bailleur :", f"Date : {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"],
            ["_________________________", ""],
        ]
        
        signature_table = Table(signature_data, colWidths=[250, 200])
        signature_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        content.append(signature_table)
        content.append(Spacer(1, 15))
        
        # ========== QR CODE ==========
        verification_url = f"https://loysecure-1.onrender.com/verify/{self.receipt.id}"
        qr = qrcode.make(verification_url)
        qr_path = os.path.join(settings.MEDIA_ROOT, f"temp_qr_{self.receipt.id}.png")
        qr.save(qr_path)
        
        from reportlab.platypus import Image
        
        qr_section = []
        qr_section.append(Paragraph("QR CODE DE VERIFICATION", section_style))
        qr_section.append(Spacer(1, 5))
        qr_section.append(Image(qr_path, width=80, height=80, hAlign='CENTER'))
        qr_section.append(Spacer(1, 5))
        qr_section.append(Paragraph("Scannez ce code pour vérifier l'identite", normal_style))
        
        qr_table = Table([[qr_section]], colWidths=[450])
        qr_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4f8')),
        ]))
        content.append(qr_table)
        
        # ========== PIED DE PAGE ==========
        content.append(Spacer(1, 20))
        footer_text = """
        Document certifié électroniquement via LOYSECURE - Votre loyer, votre preuve.
        Cette quittance a valeur de preuve conformément à la législation en vigueur.
        Toute modification est interdite.
        """
        footer_style = ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.HexColor('#888888'), alignment=TA_CENTER)
        content.append(Paragraph(footer_text, footer_style))
        
        # ========== BORDURE GÉNÉRALE ==========
        main_frame = Table([[content]], colWidths=[480])
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