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
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=5,
            textColor=colors.HexColor('#1e3a5f'),  # Bleu marine
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
        
        # Style pour le texte dans l'en-tête doré (blanc)
        header_text_style = ParagraphStyle(
            'HeaderText',
            parent=styles['Heading1'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=5,
            textColor=colors.white,  # Texte blanc sur fond doré
        )
        
        # Contenu principal
        content = []
        
        # ========== EN-TÊTE AVEC FOND DORÉ ==========
        # Création d'un tableau avec fond doré pour l'en-tête
        header_content = []
        header_content.append(Paragraph("LOYSECURE", header_text_style))
        header_content.append(Paragraph("Quittance de loyer certifiée", subtitle_style))
        
        header_table = Table([[header_content]], colWidths=[480])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#DAA520')),  # Fond doré
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 15),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#B8860B')),  # Bordure dorée foncée
        ]))
        content.append(header_table)
        content.append(Spacer(1, 10))
        
        # ========== CADRE 1 : INFORMATIONS GÉNÉRALES ==========
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
        
        info_table = Table(info_data, colWidths=[200, 200])
        info_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        content.append(info_table)
        content.append(Spacer(1, 10))
        
        # ========== CADRE 2 : PARTIES PRENANTES ==========
        content.append(Paragraph("PARTIES PRENANTES", section_style))
        
        parties_data = [
            ['BAILLEUR (PROPRIETAIRE)', 'PRENANT (LOCATAIRE)'],
            [self.owner.get_full_name() or self.owner.username, self.tenant.name],
            [f"Tel : {self.owner.phone}", f"Tel : {self.tenant.phone}"],
            [f"Email : {self.owner.email or '-'}", f"Email : {self.tenant.email or '-'}"],
        ]
        
        parties_table = Table(parties_data, colWidths=[200, 200])
        parties_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        content.append(parties_table)
        content.append(Spacer(1, 10))
        
        # ========== CADRE 3 : LOGEMENT ==========
        content.append(Paragraph("LOGEMENT CONCERNE", section_style))
        
        property_data = [
            [f"Adresse : {self.property.address}"],
            [f"Nombre de chambres : {self.property.number_of_rooms}"],
        ]
        if self.property.description:
            property_data.append([f"Description : {self.property.description}"])
        
        property_table = Table(property_data, colWidths=[400])
        property_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        content.append(property_table)
        content.append(Spacer(1, 10))
        
        # ========== CADRE 4 : PAIEMENT ==========
        content.append(Paragraph("DETAILS DU PAIEMENT", section_style))
        
        payment_method_label = dict(self.receipt.PAYMENT_METHOD_CHOICES).get(self.receipt.payment_method, '-')
        
        payment_data = [
            [f"Mode de paiement : {payment_method_label}"],
            [f"Montant : {self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}"],
        ]
        
        payment_table = Table(payment_data, colWidths=[400])
        payment_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        content.append(payment_table)
        content.append(Spacer(1, 10))
        
        # ========== TEXTE MONTANT EN LETTRES ==========
        amount_text = f"Arrêté la présente quittance à la somme de : {self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}"
        content.append(Paragraph(amount_text, bold_style))
        content.append(Spacer(1, 15))
        
        # ========== LIGNE SIGNATURE ==========
        signature_data = [
            ["Cachet et signature du bailleur :", f"Date : {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"],
            ["_________________________", ""],
        ]
        
        signature_table = Table(signature_data, colWidths=[250, 150])
        signature_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        content.append(signature_table)
        content.append(Spacer(1, 15))
        
        # ========== CADRE 5 : QR CODE ==========
        verification_url = f"https://loysecure-1.onrender.com/verify/{self.receipt.id}"
        qr = qrcode.make(verification_url)
        qr_path = os.path.join(settings.MEDIA_ROOT, f"temp_qr_{self.receipt.id}.png")
        qr.save(qr_path)
        
        from reportlab.platypus import Image
        
        qr_content = []
        qr_content.append(Paragraph("QR CODE DE VERIFICATION", section_style))
        qr_content.append(Spacer(1, 5))
        qr_content.append(Image(qr_path, width=70, height=70, hAlign='CENTER'))
        qr_content.append(Spacer(1, 5))
        qr_content.append(Paragraph("Scannez ce code pour vérifier l'authenticité", normal_style))
        
        qr_table = Table([[qr_content]], colWidths=[400])
        qr_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1e3a5f')),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4f8')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        content.append(qr_table)
        
        # ========== PIED DE PAGE ==========
        content.append(Spacer(1, 20))
        footer_text = """
        Document certifié électroniquement via LOYSECURE - Votre loyer, votre preuve.
        Cette quittance a valeur de preuve. Toute modification est interdite.
        """
        footer_style = ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.HexColor('#888888'), alignment=TA_CENTER)
        content.append(Paragraph(footer_text, footer_style))
        
        # ========== BORDURE GÉNÉRALE AUTOUR DE TOUT ==========
        main_frame = Table([[content]], colWidths=[480])
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