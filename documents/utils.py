# =================================PAGINATION=================================
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework import status

class CustomPagination(pagination.PageNumberPagination):
    page_size = None  # No pagination by default (returns all records)
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def paginate_queryset(self, queryset, request, view=None):
        """
        Override to return all records by default unless pagination params are provided.
        """
        page_size = self.get_page_size(request)
        if page_size is None:
            # No pagination requested, return all records as a list
            # Store queryset for get_paginated_response to calculate total_objects
            self._non_paginated_queryset = queryset
            return list(queryset)
        
        # Reset the flag when pagination is applied
        self._non_paginated_queryset = None
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        """
        Return paginated response if pagination was applied, 
        otherwise return all records without pagination metadata.
        """
        # Check if pagination was applied (page attribute exists and is not None)
        if not hasattr(self, 'page') or self.page is None:
            # No pagination was applied, return all records
            # Use stored queryset to get accurate count (handles filtered querysets)
            total_count = getattr(self, '_non_paginated_queryset', None)
            if total_count is not None:
                total_count = total_count.count() if hasattr(total_count, 'count') else len(data)
            else:
                total_count = len(data)
            
            return Response({
                'total_objects': total_count,
                'total_pages': 1,
                'current_page': 1,
                'next_page': None,
                'previous_page': None,
                'results': data
            })
        
        # Pagination was applied, return paginated response
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
import os
from datetime import datetime

def convert_docx_to_pdf(docx_path, pdf_path):
    """
    Convert DOCX file to PDF.
    Uses docx2pdf library which requires Microsoft Word on Windows.
    """
    try:
        from docx2pdf import convert
        # Convert DOCX to PDF
        convert(docx_path, pdf_path)
        print(f"DOCX converted to PDF successfully: {pdf_path}")
        return True
    except ImportError:
        raise Exception("docx2pdf library is not installed. Please install it using: pip install docx2pdf")
    except Exception as e:
        print(f"Failed to convert DOCX to PDF: {e}")
        raise Exception(f"Failed to convert DOCX to PDF: {str(e)}")

def is_docx_file(file_path):
    """Check if the file is a DOCX file based on extension."""
    return file_path.lower().endswith(('.docx', '.doc'))

def stamp_pdf_with_uid(input_pdf_path, uid):
    try:
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
        print("PDF stamped with UID successfully")
    except Exception as e:
        print("Failed to stamp PDF with UID", e)
        raise Exception(e)
