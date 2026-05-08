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
    """Générateur de quittances PDF professionnelles LOYSECURE avec bordure"""
    
    def __init__(self, receipt):
        self.receipt = receipt
        self.tenant = receipt.tenant
        self.owner = receipt.owner
        self.property = receipt.tenant.property_ref
    
    def generate(self):
        buffer = io.BytesIO()
        
        # Document avec marges pour la bordure
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
            fontSize=24,
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
            fontSize=12,
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
        
        # ========== INFORMATIONS GÉNÉRALES ==========
        info_data = [
            [
                f"<b>N° Quittance :</b> {str(self.receipt.id)[:8].upper()}",
                f"<b>Date :</b> {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"
            ],
            [
                f"<b>Période :</b> {self.receipt.month.strftime('%B %Y')}",
                f"<b>Heure :</b> {timezone.localtime(self.receipt.certified_at).strftime('%H:%M')}"
            ],
        ]
        
        info_table = Table(info_data, colWidths=[225, 225])
        info_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
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
            [f"• <b>Adresse :</b> {self.property.address}"],
            [f"• <b>Nombre de chambres :</b> {self.property.number_of_rooms}"],
        ]
        if self.property.description:
            property_data.append([f"• <b>Description :</b> {self.property.description}"])
        
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
        
        payment_data = [
            [f"• <b>Mode de paiement :</b> {dict(self.receipt.PAYMENT_METHOD_CHOICES).get(self.receipt.payment_method, '-')}"],
            [f"• <b>Montant :</b> {self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}"],
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
        amount_words = f"<b>Arrêté la présente quittance à la somme de :</b> {self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}"
        content.append(Paragraph(amount_words, normal_style))
        content.append(Spacer(1, 15))
        
        # ========== SIGNATURE ==========
        signature_data = [
            [f"<b>Cachet et signature du bailleur :</b>", f"<b>Date :</b> {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"],
            ["_________________________", ""],
        ]
        
        signature_table = Table(signature_data, colWidths=[250, 200])
        signature_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 1), (0, 1), 1, colors.black),
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
        qr_section.append(Paragraph("Scannez ce code pour vérifier l'authenticité", normal_style))
        
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
        <i>Document certifié électroniquement via LOYSECURE – Votre loyer, votre preuve.</i><br/>
        <i>Cette quittance a valeur de preuve conformément à la législation en vigueur.</i><br/>
        <i>Toute modification est interdite.</i>
        """
        footer_style = ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.HexColor('#888888'), alignment=TA_CENTER)
        content.append(Paragraph(footer_text, footer_style))
        
        # ========== BORDURE GÉNÉRALE ==========
        # On encadre TOUT le contenu
        main_frame = Table([[content]], colWidths=[480])
        main_frame.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#1e3a5f')),  # Bordure bleue épaisse
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        # Générer le document
        doc.build([main_frame])
        
        # Nettoyer
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        buffer.seek(0)
        return buffer