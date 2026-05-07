from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import io
import qrcode
from django.conf import settings
from django.utils import timezone
import os

class ReceiptPDFGenerator:
    """Générateur de quittances PDF certifiées LOYSECURE"""
    
    def __init__(self, receipt):
        self.receipt = receipt
        self.tenant = receipt.tenant
        self.owner = receipt.owner
        # CORRIGÉ : property → property_ref
        self.property = receipt.tenant.property_ref
    
    def _get_bilingual_month(self, date_obj):
        """Retourne le mois en français et anglais (ex: Mai/May 2026)"""
        months_fr = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }
        months_en = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        month_num = date_obj.month
        year = date_obj.year
        return f"{months_fr[month_num]}/{months_en[month_num]} {year}"
    
    def generate(self):
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=20*mm,
            bottomMargin=20*mm,
            leftMargin=15*mm,
            rightMargin=15*mm
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=22,
            alignment=1,
            spaceAfter=20,
            textColor=colors.HexColor('#1e3a5f')
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=14,
            alignment=1,
            spaceAfter=30
        )
        
        normal_style = styles['Normal']
        bold_style = ParagraphStyle('Bold', parent=normal_style, fontName='Helvetica-Bold')
        
        elements = []
        
        # En-tête
        elements.append(Paragraph("LOYSECURE", title_style))
        elements.append(Paragraph("Quittance de loyer certifiée", subtitle_style))
        elements.append(Spacer(1, 5))
        
        # Informations générales
        elements.append(Paragraph(f"<b>N° Quittance :</b> {str(self.receipt.id)[:8].upper()}", normal_style))
        elements.append(Paragraph(f"<b>Date de certification :</b> {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y à %H:%M')}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Tableau propriétaire / locataire
        data = [
            ['BAILLEUR (PROPRIÉTAIRE)', 'PRENANT (LOCATAIRE)'],
            [self.owner.get_full_name() or self.owner.username, self.tenant.name],
            [f"Tél : {self.owner.phone}", f"Tél : {self.tenant.phone}"],
            [f"Email : {self.owner.email or '-'}", f"Email : {self.tenant.email or '-'}"],
        ]
        
        table = Table(data, colWidths=[200, 200])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Logement
        elements.append(Paragraph(f"<b>Logement loué :</b> {self.property.address}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Détails du paiement
        elements.append(Paragraph("DÉTAILS DU PAIEMENT", bold_style))
        
        # Utilisation de la fonction bilingue pour la période
        payment_data = [
            ['Période concernée', self._get_bilingual_month(self.receipt.month)],
            ['Montant du loyer', f"{self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}"],
            ['Mode de paiement', dict(self.receipt.PAYMENT_METHOD_CHOICES).get(self.receipt.payment_method, '')],
        ]
        
        payment_table = Table(payment_data, colWidths=[120, 280])
        payment_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 20))
        
        # Signature
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Cachet et signature du bailleur :", normal_style))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("_________________________", normal_style))
        
        # QR Code
        qr = qrcode.make(f"https://loysecure.com/verify/{self.receipt.id}")
        qr_path = os.path.join(settings.MEDIA_ROOT, f"temp_qr_{self.receipt.id}.png")
        qr.save(qr_path)
        
        from reportlab.platypus import Image
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("QR Code de vérification :", normal_style))
        elements.append(Image(qr_path, width=80, height=80))
        
        # Mention légale
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(
            "<i>Document certifié électroniquement via LOYSECURE. "
            "Cette quittance a valeur de preuve. Toute modification est interdite.</i>",
            ParagraphStyle('Italic', parent=styles['Italic'], fontSize=8, textColor=colors.grey)
        ))
        
        doc.build(elements)
        
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        buffer.seek(0)
        return buffer