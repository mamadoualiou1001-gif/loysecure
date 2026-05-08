from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from django.conf import settings
from django.utils import timezone

import io
import qrcode
import os


def get_month_bilingual(month_date):
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

    en, fr = months[month_date.month]
    return f"{en}/{fr} {month_date.year}"


class ReceiptPDFGenerator:

    def __init__(self, receipt):
        self.receipt = receipt
        self.tenant = receipt.tenant
        self.owner = receipt.owner
        self.property = receipt.tenant.property_ref

    def generate(self):

        buffer = io.BytesIO()

        # ========= DOCUMENT =========
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=6 * mm,
            bottomMargin=6 * mm,
            leftMargin=8 * mm,
            rightMargin=8 * mm,
        )

        styles = getSampleStyleSheet()

        # ========= COULEURS =========
        LS_BLUE = colors.HexColor("#0b2e83")
        WHITE = colors.white

        # ========= LARGEURS =========
        FULL_WIDTH = 535
        HALF_WIDTH = 267
        SIGN_LEFT = 350
        SIGN_RIGHT = 185

        # ========= STYLES =========
        title_style = ParagraphStyle(
            "title",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=34,
            alignment=TA_CENTER,
            textColor=LS_BLUE,
            spaceAfter=0,
        )

        subtitle_style = ParagraphStyle(
            "subtitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            alignment=TA_CENTER,
            textColor=LS_BLUE,
            spaceAfter=10,
        )

        normal_style = ParagraphStyle(
            "normal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
        )

        footer_style = ParagraphStyle(
            "footer",
            parent=normal_style,
            alignment=TA_CENTER,
            fontSize=9,
            textColor=LS_BLUE,
            fontName="Helvetica-Bold",
        )

        # ========= STYLES TABLEAUX =========
        section_header_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), LS_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, -1), WHITE),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])

        box_style = TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.5, LS_BLUE),
            ('ROUNDEDCORNERS', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ])

        elements = []

        # ========= TITRE =========
        elements.append(Paragraph("LOYSECURE", title_style))

        elements.append(
            Paragraph(
                "QUITTANCE DE PAIEMENT DU LOYER",
                subtitle_style
            )
        )

        # ========= INFOS =========
        period_bilingual = get_month_bilingual(self.receipt.month)

        top_info = Table([
            [
                Paragraph(
                    f"""
                    <b>N° Quittance :</b> {str(self.receipt.id)[:8].upper()}<br/>
                    <b>Période :</b> {period_bilingual}
                    """,
                    normal_style
                ),

                Paragraph(
                    f"""
                    <b>Date :</b> {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}<br/>
                    <b>Heure :</b> {timezone.localtime(self.receipt.certified_at).strftime('%H:%M')}
                    """,
                    normal_style
                ),
            ]
        ], colWidths=[HALF_WIDTH, HALF_WIDTH])

        top_info.setStyle(box_style)

        elements.append(top_info)
        elements.append(Spacer(1, 8))

        # ========= PARTIES PRENANTES =========
        header = Table(
            [["PARTIES PRENANTES"]],
            colWidths=[FULL_WIDTH]
        )

        header.setStyle(section_header_style)
        elements.append(header)

        parties = Table([
            [
                Paragraph(
                    f"""
                    <b>BAILLEUR (PROPRIETAIRE)</b><br/><br/>
                    {self.owner.get_full_name() or self.owner.username}<br/><br/>
                    Tel : {self.owner.phone}
                    """,
                    normal_style
                ),

                Paragraph(
                    f"""
                    <b>PRENANT (LOCATAIRE)</b><br/><br/>
                    {self.tenant.name or ''}<br/><br/>
                    Tel : {self.tenant.phone or ''}
                    """,
                    normal_style
                ),
            ]
        ], colWidths=[HALF_WIDTH, HALF_WIDTH])

        parties.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.5, LS_BLUE),
            ('LINEBEFORE', (1, 0), (1, 0), 1, LS_BLUE),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))

        elements.append(parties)
        elements.append(Spacer(1, 8))

        # ========= LOGEMENT =========
        logement_header = Table(
            [["LOGEMENT CONCERNE"]],
            colWidths=[FULL_WIDTH]
        )

        logement_header.setStyle(section_header_style)
        elements.append(logement_header)

        logement = Table([
            [
                Paragraph(
                    f"""
                    <b>Adresse :</b> {self.property.address}<br/><br/>
                    <b>Nombre de chambres :</b> {self.property.number_of_rooms}
                    """,
                    normal_style
                )
            ]
        ], colWidths=[FULL_WIDTH])

        logement.setStyle(box_style)

        elements.append(logement)
        elements.append(Spacer(1, 8))

        # ========= PAIEMENT =========
        payment_header = Table(
            [["DETAILS DU PAIEMENT"]],
            colWidths=[FULL_WIDTH]
        )

        payment_header.setStyle(section_header_style)
        elements.append(payment_header)

        payment_method = dict(
            self.receipt.PAYMENT_METHOD_CHOICES
        ).get(self.receipt.payment_method, "-")

        payment = Table([
            [
                Paragraph(
                    f"""
                    <b>Mode de paiement :</b> {payment_method}<br/><br/>
                    <b>Montant :</b>
                    <font color="#0b2e83">
                    <b>{self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}</b>
                    </font>
                    """,
                    normal_style
                )
            ],

            [
                Paragraph(
                    f"""
                    <b>Arrêté la présente quittance à la somme de :</b>
                    <font color="#0b2e83">
                    <b>{self.receipt.amount:,.0f} {self.owner.get_currency_symbol()}</b>
                    </font>
                    """,
                    normal_style
                )
            ]
        ], colWidths=[FULL_WIDTH])

        payment.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.5, LS_BLUE),
            ('LINEABOVE', (0, 1), (-1, 1), 1, colors.grey),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(payment)
        elements.append(Spacer(1, 8))

        # ========= SIGNATURE =========
        signature = Table([
            [
                Paragraph(
                    """
                    <b>Cachet et signature du bailleur :</b><br/><br/>
                    ________________________
                    """,
                    normal_style
                ),

                Paragraph(
                    f"""
                    <b>Date :</b><br/>
                    {timezone.localtime(self.receipt.certified_at).strftime('%d/%m/%Y')}
                    """,
                    normal_style
                )
            ]
        ], colWidths=[SIGN_LEFT, SIGN_RIGHT])

        signature.setStyle(box_style)

        elements.append(signature)
        elements.append(Spacer(1, 8))

        # ========= QR CODE =========
        qr_header = Table(
            [["QR CODE DE VERIFICATION"]],
            colWidths=[FULL_WIDTH]
        )

        qr_header.setStyle(section_header_style)

        elements.append(qr_header)

        verification_url = (
            f"https://loysecure-1.onrender.com/verify/{self.receipt.id}"
        )

        qr = qrcode.make(verification_url)

        qr_path = os.path.join(
            settings.MEDIA_ROOT,
            f"temp_qr_{self.receipt.id}.png"
        )

        qr.save(qr_path)

        qr_image = Image(
            qr_path,
            width=60,
            height=60
        )

        qr_table = Table([
            [
                qr_image,

                Paragraph(
                    "Scannez ce code pour vérifier l'authenticité",
                    normal_style
                )
            ]
        ], colWidths=[90, 445])

        qr_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.5, LS_BLUE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(qr_table)
        elements.append(Spacer(1, 8))

        # ========= FOOTER =========
        elements.append(
            Paragraph(
                "Document certifié électroniquement via LOYSECURE - Votre loyer, votre preuve.",
                footer_style
            )
        )

        # ========= CONSTRUCTION =========
        doc.build(elements)

        # ========= SUPPRESSION QR =========
        if os.path.exists(qr_path):
            os.remove(qr_path)

        buffer.seek(0)

        return buffer