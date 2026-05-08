from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
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
        self.property = receipt.tenant.property
    
    def generate(self):
        buffer = io.BytesIO()
        
        # Créer le document avec une marge élégante
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=15*mm,
            bottomMargin=15*mm,
            leftMargin=15*mm,
            rightMargin=15*mm,
            title=f"Quittance_{self.receipt.month.strftime('%Y_%m')}_{self.tenant.name}",
            author="LoySecure"
        )
        
        # Styles personnalisés
        styles = getSampleStyleSheet()
        
        # Style pour le titre principal
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=5,
            textColor=colors.HexColor('#1e3a5f'),
            fontName='Helvetica-Bold'
        )
        
        # Style pour le sous-titre
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor('#7f8c8d'),
            fontName='Helvetica'
        )
        
        # Style pour les sections
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading3'],
            fontSize=11,
            spaceBefore=15,
            spaceAfter=5,
            textColor=colors.HexColor('#1e3a5f'),
            fontName='Helvetica-Bold'
        )
        
        # Style pour le texte normal
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=9,
            leading=14,
            fontName='Helvetica'
        )
        
        # Style pour le texte en gras
        bold_style = ParagraphStyle(
            'Bold',
            parent=normal_style,
            fontName='Helvetica-Bold'
        )
        
        # Style pour le pied de page
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#95a5a6')
        )
        
        elements = []
        
        # ========== EN-TÊTE ==========
        # Logo et nom
        elements.append(Paragraph("LOYSECURE", title_style))
        elements.append(Paragraph("Quittance de loyer certifiée", subtitle_style))
        elements.append(Spacer(1, 5))
        
        # Ligne de séparation
        elements.append(Paragraph("<hr color='#1e3a5f' />", normal_style))
        elements.append(Spacer(1, 10))
        
        # ========== INFORMATIONS GÉNÉRALES ==========
        # Encadré d'information
        info_data = [
            [f"<b>N° Quittance :</b> {str(self.receipt.id)[:8].upper()}", 
             f"<b>Date d'émission :</b> {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"],
            [f"<b>Période concernée :</b> {self.receipt.month.strftime('%B %Y')}",
             f"<b>Heure :</b> {timezone.localtime(self.receipt.certified_at).strftime('%H:%M')}"],
        ]
        
        info_table = Table(info_data, colWidths=[200, 150])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 15))
        
        # ========== PARTIES PRENANTES ==========
        elements.append(Paragraph("PARTIES PRENANTES", section_style))
        
        # Tableau propriétaire / locataire
        parties_data = [
            ['<b>BAILLEUR (PROPRIÉTAIRE)</b>', '<b>PRENANT (LOCATAIRE)</b>'],
            [self.owner.get_full_name() or self.owner.username, self.tenant.name],
            [f"Tél : {self.owner.phone}", f"Tél : {self.tenant.phone}"],
            [f"Email : {self.owner.email or '-'}", f"Email : {self.tenant.email or '-'}"],
        ]
        
        parties_table = Table(parties_data, colWidths=[200, 200])
        parties_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 15))
        
        # ========== LOGEMENT ==========
        elements.append(Paragraph("LOGEMENT CONCERNÉ", section_style))
        
        property_data = [
            [f"<b>Adresse :</b> {self.property.address}"],
            [f"<b>Nombre de chambres :</b> {self.property.number_of_rooms}"],
        ]
        if self.property.description:
            property_data.append([f"<b>Description :</b> {self.property.description}"])
        
        property_table = Table(property_data, colWidths=[400])
        property_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(property_table)
        elements.append(Spacer(1, 15))
        
        # ========== DÉTAILS DU PAIEMENT ==========
        elements.append(Paragraph("DÉTAILS DU PAIEMENT", section_style))
        
        payment_data = [
            ['', ''],
            ['<b>Montant du loyer :</b>', f"{self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}"],
            ['<b>Mode de paiement :</b>', dict(self.receipt.PAYMENT_METHOD_CHOICES).get(self.receipt.payment_method, '')],
            ['<b>Date de paiement :</b>', timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y') if self.receipt.certified_at else '-'],
            ['', ''],
        ]
        
        payment_table = Table(payment_data, colWidths=[120, 280])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#e9ecef')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 20))
        
        # ========== MONTANT EN LETTRES ==========
        elements.append(Paragraph(self._amount_to_words(self.receipt.amount), normal_style))
        elements.append(Spacer(1, 20))
        
        # ========== SIGNATURE ET CACHET ==========
        signature_data = [
            ['', ''],
            ['<b>Cachet et signature du bailleur :</b>', '<b>Date :</b>'],
            ['_________________________', f"{timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"],
            ['', ''],
        ]
        
        signature_table = Table(signature_data, colWidths=[200, 200])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(signature_table)
        elements.append(Spacer(1, 15))
        
        # ========== QR CODE ==========
        verification_url = f"https://loysecure.onrender.com/verify/{self.receipt.id}"
        qr = qrcode.make(verification_url)
        qr_path = os.path.join(settings.MEDIA_ROOT, f"temp_qr_{self.receipt.id}.png")
        qr.save(qr_path)
        
        qr_data = [
            ['<b>QR Code de vérification</b>'],
            ['Scannez ce code pour vérifier l\'authenticité de votre quittance en ligne'],
        ]
        
        qr_table = Table(qr_data, colWidths=[400])
        qr_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(qr_table)
        
        # Ajouter l'image du QR code
        elements.append(Spacer(1, 5))
        elements.append(Image(qr_path, width=70, height=70, hAlign='CENTER'))
        elements.append(Spacer(1, 10))
        
        # ========== PIED DE PAGE ==========
        elements.append(Paragraph("<hr color='#1e3a5f' />", normal_style))
        elements.append(Spacer(1, 5))
        
        footer_text = """
        <i>Document certifié électroniquement via LOYSECURE – Votre loyer, votre preuve.<br/>
        Cette quittance a valeur de preuve conformément à la législation en vigueur.<br/>
        Toute modification est interdite. Pour vérifier l'authenticité, scannez le QR code.</i>
        """
        elements.append(Paragraph(footer_text, footer_style))
        
        # Générer le document
        doc.build(elements)
        
        # Nettoyer le fichier temporaire du QR code
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        buffer.seek(0)
        return buffer
    
    def _amount_to_words(self, amount):
        """Convertir le montant en lettres (version simplifiée)"""
        units = ['', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf']
        teens = ['dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf']
        tens = ['', 'dix', 'vingt', 'trente', 'quarante', 'cinquante', 'soixante', 'soixante-dix', 'quatre-vingt', 'quatre-vingt-dix']
        
        currency = self.owner.get_currency_symbol()
        
        # Simplification pour l'instant : on retourne juste le montant en chiffres
        # Tu pourras améliorer cette fonction plus tard
        return f"<b>Arrêté la présente quittance à la somme de :</b> {amount:,.0f} {currency}"