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
from django.core.files import File

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

def ensure_pdf_file(document):
    """
    Ensure the document file is a PDF. If it's a DOCX file, convert it to PDF.
    Updates the document's file field and cleans up temporary/original files.
    
    Args:
        document: UploadedDocument instance
        
    Returns:
        str: Path to the final PDF file
    """
    original_file_path = document.file.path
    file_name_without_ext = os.path.splitext(os.path.basename(original_file_path))[0]
    
    # Check if file is DOCX and convert to PDF if needed
    if is_docx_file(original_file_path):
        # Convert DOCX to PDF to a temporary location
        temp_pdf_path = os.path.join(os.path.dirname(original_file_path), f"{file_name_without_ext}_temp.pdf")
        convert_docx_to_pdf(original_file_path, temp_pdf_path)
        
        # Update document's file field to point to the new PDF
        with open(temp_pdf_path, 'rb') as pdf_file:
            # Generate new filename for the PDF (keep same base name, change extension)
            pdf_filename = f"{file_name_without_ext}.pdf"
            document.file.save(pdf_filename, File(pdf_file), save=False)
        
        # Delete the temporary PDF file (Django has saved a copy)
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        
        # Delete the original DOCX file
        if os.path.exists(original_file_path):
            os.remove(original_file_path)
        
        # Save document to persist file field changes
        document.save()
    
    # Return the final PDF path
    return document.file.path

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
