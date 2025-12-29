# =================================PAGINATION=================================
from rest_framework import pagination
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'total_objects': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'next_page': self.page.next_page_number() if self.page.has_next() else None,
            'previous_page': self.page.previous_page_number() if self.page.has_previous() else None,
            'results': data
        })
    

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader, PdfWriter
import io
from datetime import datetime

def stamp_pdf_with_uid(input_pdf_path, uid):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)

        can.setFont("Helvetica-Bold", 9)
        can.drawString(40, 20, f"UID: {uid}")
        can.drawString(300, 20, f"Approved On: {datetime.now().strftime('%d-%m-%Y')}")

        can.save()
        packet.seek(0)

        overlay_pdf = PdfReader(packet)
        page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

    with open(input_pdf_path, "wb") as f:
        writer.write(f)


