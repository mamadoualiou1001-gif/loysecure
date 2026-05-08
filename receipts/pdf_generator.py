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
        
        # Couleur bleue LOYSECURE
        LS_BLUE = colors.HexColor('#0b2e83')
        LS_LIGHT_BLUE = colors.HexColor('#f0f4fa')
        
        # Styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=56,
            alignment=TA_CENTER,
            spaceAfter=5,
            textColor=LS_BLUE,
            fontName='Helvetica-Bold',
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=28,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=LS_BLUE,
            fontName='Helvetica-Bold',
        )
        
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=24,
            alignment=TA_LEFT,
            textColor=colors.white,
            fontName='Helvetica-Bold',
        )
        
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontSize=18,
            leading=28,
        )
        
        bold_style = ParagraphStyle(
            'Bold',
            parent=normal_style,
            fontName='Helvetica-Bold',
        )
        
        small_style = ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontSize=14,
            leading=20,
        )
        
        elements = []
        
        # ========== EN-TÊTE ==========
        elements.append(Paragraph("LOYSECURE", title_style))
        elements.append(Paragraph("QUITTANCE DE LOYER", subtitle_style))
        
        # ========== INFORMATIONS GÉNÉRALES (encadré) ==========
        period_bilingual = get_month_bilingual(self.receipt.month)
        
        info_data = [
            [
                f"<b>N° Quittance :</b> {str(self.receipt.id)[:8].upper()}<br/><b>Période :</b> {period_bilingual}",
                f"<b>Date :</b> {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}<br/><b>Heure :</b> {timezone.localtime(self.receipt.certified_at).strftime('%H:%M')}"
            ],
        ]
        
        info_table = Table(info_data, colWidths=[225, 225])
        info_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, LS_BLUE),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 20),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 15))
        
        # ========== SECTION PARTIES PRENANTES ==========
        # Titre de section (fond bleu)
        parties_title = Table([["PARTIES PRENANTES"]], colWidths=[450])
        parties_title.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LS_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('FONTSIZE', (0, 0), (-1, -1), 22),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(parties_title)
        
        # Contenu deux colonnes
        parties_data = [
            [
                f"<b>BAILLEUR (PROPRIETAIRE)</b><br/><br/>{self.owner.get_full_name() or self.owner.username}<br/>Tel : {self.owner.phone}",
                f"<b>PRENANT (LOCATAIRE)</b><br/><br/>{self.tenant.name}<br/>Tel : {self.tenant.phone}"
            ],
        ]
        
        parties_table = Table(parties_data, colWidths=[225, 225])
        parties_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, LS_BLUE),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 20),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 15))
        
        # ========== SECTION LOGEMENT ==========
        logement_title = Table([["LOGEMENT CONCERNE"]], colWidths=[450])
        logement_title.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LS_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('FONTSIZE', (0, 0), (-1, -1), 22),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(logement_title)
        
        logement_data = [
            [f"<b>Adresse :</b> {self.property.address}<br/><b>Nombre de chambres :</b> {self.property.number_of_rooms}"],
        ]
        
        logement_table = Table(logement_data, colWidths=[450])
        logement_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, LS_BLUE),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 20),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
        ]))
        elements.append(logement_table)
        elements.append(Spacer(1, 15))
        
        # ========== SECTION PAIEMENT ==========
        paiement_title = Table([["DETAILS DU PAIEMENT"]], colWidths=[450])
        paiement_title.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LS_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('FONTSIZE', (0, 0), (-1, -1), 22),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(paiement_title)
        
        payment_method_label = dict(self.receipt.PAYMENT_METHOD_CHOICES).get(self.receipt.payment_method, '-')
        
        paiement_data = [
            [f"<b>Mode de paiement :</b> {payment_method_label}<br/><b>Montant :</b> <font color='#0b2e83' size='22'><b>{self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}</b></font>"],
        ]
        
        paiement_table = Table(paiement_data, colWidths=[450])
        paiement_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, LS_BLUE),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 20),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
        ]))
        elements.append(paiement_table)
        elements.append(Spacer(1, 15))
        
        # ========== TOTAL ==========
        total_data = [
            [f"<b>Arrêté la présente quittance à la somme de :</b> <font color='#0b2e83' size='24'><b>{self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}</b></font>"],
        ]
        
        total_table = Table(total_data, colWidths=[450])
        total_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, LS_BLUE),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 20),
            ('FONTSIZE', (0, 0), (-1, -1), 20),
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 15))
        
        # ========== SIGNATURE ==========
        signature_data = [
            [
                f"<b>Cachet et signature du bailleur</b><br/><br/>_________________________",
                f"<b>Date :</b> {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}"
            ],
        ]
        
        signature_table = Table(signature_data, colWidths=[280, 170])
        signature_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, LS_BLUE),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 20),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
        ]))
        elements.append(signature_table)
        elements.append(Spacer(1, 15))
        
        # ========== QR CODE ==========
        qr_title = Table([["QR CODE DE VERIFICATION"]], colWidths=[450])
        qr_title.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LS_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('FONTSIZE', (0, 0), (-1, -1), 22),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(qr_title)
        
        # Génération du QR code
        verification_url = f"https://loysecure-1.onrender.com/verify/{self.receipt.id}"
        qr = qrcode.make(verification_url)
        qr_path = os.path.join(settings.MEDIA_ROOT, f"temp_qr_{self.receipt.id}.png")
        qr.save(qr_path)
        
        from reportlab.platypus import Image
        
        qr_content = []
        qr_content.append(Spacer(1, 10))
        qr_content.append(Image(qr_path, width=100, height=100, hAlign='CENTER'))
        qr_content.append(Spacer(1, 10))
        qr_content.append(Paragraph("Scannez ce code pour vérifier l'authenticité", small_style))
        
        qr_table = Table([[qr_content]], colWidths=[450])
        qr_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 2, LS_BLUE),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 20),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(qr_table)
        elements.append(Spacer(1, 15))
        
        # ========== PIED DE PAGE ==========
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=16,
            textColor=LS_BLUE,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )
        elements.append(Paragraph("Document certifié électroniquement via LOYSECURE - Votre loyer, votre preuve.", footer_style))
        
        # ========== BORDURE GÉNÉRALE ==========
        main_frame = Table([elements], colWidths=[480])
        main_frame.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 3, LS_BLUE),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 20),
            ('PADDING', (0, 0), (-1, -1), 15),
        ]))
        
        # Construction finale
        doc.build([main_frame])
        
        # Nettoyer
        if os.path.exists(qr_path):
            os.remove(qr_path)
        
        buffer.seek(0)
        return buffer