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
    import platform
    import sys
    
    try:
        from docx2pdf import convert
        
        # On Windows, initialize COM before conversion (required for docx2pdf)
        if platform.system() == 'Windows':
            try:
                import pythoncom
                # Initialize COM for this thread (required for COM operations)
                # This must be called before any COM operations
                try:
                    pythoncom.CoInitialize()
                except pythoncom.com_error as com_err:
                    # Error code -2147221008 means "CoInitialize has not been called"
                    # If we get a different error, COM might already be initialized
                    error_code = com_err.args[0] if com_err.args else None
                    if error_code == -2147221008:
                        # This shouldn't happen if we just called CoInitialize, but handle it
                        raise Exception("COM initialization failed. Please ensure Microsoft Word is installed.")
                    # Otherwise, COM might already be initialized, which is okay
                    pass
            except ImportError:
                # pywin32 not installed - docx2pdf should handle this
                print("Warning: pywin32 not installed. COM initialization skipped.")
            except Exception as com_error:
                print(f"Warning: COM initialization issue: {com_error}")
        
        # Convert DOCX to PDF
        convert(docx_path, pdf_path)
        print(f"DOCX converted to PDF successfully: {pdf_path}")
        return True
    except ImportError:
        raise Exception("docx2pdf library is not installed. Please install it using: pip install docx2pdf")
    except Exception as e:
        print(f"Failed to convert DOCX to PDF: {e}")
        # Re-raise with more context
        error_msg = str(e)
        if "CoInitialize" in error_msg or "-2147221008" in error_msg:
            raise Exception(f"Failed to convert DOCX to PDF: COM initialization error. Make sure Microsoft Word is installed and pywin32 is available. Original error: {error_msg}")
        raise Exception(f"Failed to convert DOCX to PDF: {error_msg}")

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

            can.setFont("Helvetica-Bold", 8)
            # Right bottom corner - UID above, Approved On below
            # A4 width is 595.27 points, using ~450 for right alignment
            uid_text = f"UID: {uid}"
            approved_text = f"Approved On: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
            
            X_POSITION = 430   # 👈 control left/right here
            Y_UID = 32
            Y_APPROVED = 22

            can.drawString(X_POSITION, Y_UID, uid_text)
            can.drawString(X_POSITION, Y_APPROVED, approved_text)

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
