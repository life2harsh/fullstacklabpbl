import csv
from io import BytesIO

from django.http import HttpResponse


def csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


def pdf_response(filename, title, blocks):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#171717")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bbbbbb")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])
    story = [Paragraph(title, styles["Title"])]
    for kind, value in blocks:
        if kind == "h":
            story += [Spacer(1, 10), Paragraph(value, styles["Heading2"])]
        elif kind == "p":
            story.append(Paragraph(value, styles["BodyText"]))
        elif kind == "table":
            story.append(Table(value, repeatRows=1, style=table_style, hAlign="LEFT") if len(value) > 1 else Paragraph("No data for this period.", styles["Italic"]))
    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, title=title, leftMargin=40, rightMargin=40).build(story)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
