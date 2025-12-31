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

def convert_docx_to_pdf_using_libreoffice(docx_path, pdf_path):
    """
    Convert DOCX to PDF using LibreOffice command-line tool.
    Works on both Windows and Linux.
    """
    import platform
    import subprocess
    import shutil
    
    # Find LibreOffice executable
    if platform.system() == 'Windows':
        # Common Windows paths for LibreOffice
        possible_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        soffice_cmd = None
        for path in possible_paths:
            if os.path.exists(path):
                soffice_cmd = path
                break
        
        # Also try to find it in PATH
        if not soffice_cmd:
            soffice_cmd = shutil.which("soffice")
    else:
        # Linux/Unix - try common locations or PATH
        soffice_cmd = shutil.which("soffice") or shutil.which("libreoffice")
    
    if not soffice_cmd:
        raise Exception(
            "LibreOffice is not installed or not found in PATH. "
            "Please install LibreOffice:\n"
            "- Linux: sudo apt-get install libreoffice (or use your package manager)\n"
            "- Windows: Download from https://www.libreoffice.org/"
        )
    
    # Get output directory
    output_dir = os.path.dirname(pdf_path)
    
    try:
        # LibreOffice command: soffice --headless --convert-to pdf --outdir <output_dir> <input_file>
        cmd = [
            soffice_cmd,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            docx_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
            check=True
        )
        
        # LibreOffice creates PDF with same name as input file
        input_basename = os.path.splitext(os.path.basename(docx_path))[0]
        generated_pdf = os.path.join(output_dir, f"{input_basename}.pdf")
        
        # If the generated PDF has a different name, rename it
        if os.path.exists(generated_pdf) and generated_pdf != pdf_path:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            os.rename(generated_pdf, pdf_path)
        
        if not os.path.exists(pdf_path):
            raise Exception(f"PDF was not generated. Expected: {pdf_path}")
        
        print(f"DOCX converted to PDF successfully using LibreOffice: {pdf_path}")
        return True
        
    except subprocess.TimeoutExpired:
        raise Exception("LibreOffice conversion timed out. The document may be too large or complex.")
    except subprocess.CalledProcessError as e:
        error_output = e.stderr or e.stdout or "Unknown error"
        raise Exception(f"LibreOffice conversion failed: {error_output}")
    except Exception as e:
        raise Exception(f"Failed to convert DOCX to PDF using LibreOffice: {str(e)}")


def convert_docx_to_pdf(docx_path, pdf_path):
    """
    Convert DOCX file to PDF.
    Cross-platform solution:
    - On Windows: Tries docx2pdf first (requires Microsoft Word), falls back to LibreOffice
    - On Linux: Uses LibreOffice command-line tool (most reliable)
    """
    import platform
    import subprocess
    import shutil
    
    system = platform.system()
    
    # On Linux, prefer LibreOffice (more reliable)
    if system == 'Linux':
        try:
            return convert_docx_to_pdf_using_libreoffice(docx_path, pdf_path)
        except Exception as e:
            # If LibreOffice fails, try docx2pdf as fallback
            print(f"LibreOffice conversion failed, trying docx2pdf: {e}")
            try:
                from docx2pdf import convert
                convert(docx_path, pdf_path)
                print(f"DOCX converted to PDF successfully using docx2pdf: {pdf_path}")
                return True
            except ImportError:
                raise Exception(
                    f"LibreOffice conversion failed: {str(e)}\n"
                    "docx2pdf is also not available. Please install one of:\n"
                    "- LibreOffice: sudo apt-get install libreoffice\n"
                    "- docx2pdf: pip install docx2pdf (requires LibreOffice on Linux)"
                )
            except Exception as docx2pdf_error:
                raise Exception(
                    f"Both conversion methods failed.\n"
                    f"LibreOffice error: {str(e)}\n"
                    f"docx2pdf error: {str(docx2pdf_error)}\n"
                    "Please ensure LibreOffice is installed: sudo apt-get install libreoffice"
                )
    
    # On Windows, try docx2pdf first (requires Microsoft Word)
    elif system == 'Windows':
        try:
            from docx2pdf import convert
            
            # Initialize COM before conversion (required for docx2pdf on Windows)
            try:
                import pythoncom
                try:
                    pythoncom.CoInitialize()
                except pythoncom.com_error as com_err:
                    error_code = com_err.args[0] if com_err.args else None
                    if error_code == -2147221008:
                        raise Exception("COM initialization failed. Please ensure Microsoft Word is installed.")
                    pass
            except ImportError:
                print("Warning: pywin32 not installed. COM initialization skipped.")
            except Exception as com_error:
                print(f"Warning: COM initialization issue: {com_error}")
            
            # Convert DOCX to PDF using docx2pdf
            convert(docx_path, pdf_path)
            print(f"DOCX converted to PDF successfully using docx2pdf: {pdf_path}")
            return True
            
        except ImportError:
            # docx2pdf not installed, try LibreOffice
            print("docx2pdf not available, trying LibreOffice...")
            try:
                return convert_docx_to_pdf_using_libreoffice(docx_path, pdf_path)
            except Exception as lo_error:
                raise Exception(
                    "Neither docx2pdf nor LibreOffice is available.\n"
                    "Please install one of:\n"
                    "- docx2pdf: pip install docx2pdf (requires Microsoft Word)\n"
                    "- LibreOffice: Download from https://www.libreoffice.org/\n"
                    f"LibreOffice error: {str(lo_error)}"
                )
        except Exception as e:
            error_msg = str(e)
            # If docx2pdf fails, try LibreOffice as fallback
            print(f"docx2pdf conversion failed: {error_msg}, trying LibreOffice...")
            try:
                return convert_docx_to_pdf_using_libreoffice(docx_path, pdf_path)
            except Exception as lo_error:
                # Both methods failed
                if "CoInitialize" in error_msg or "-2147221008" in error_msg:
                    raise Exception(
                        f"Both conversion methods failed.\n"
                        f"docx2pdf error: COM initialization error. Make sure Microsoft Word is installed and pywin32 is available.\n"
                        f"LibreOffice error: {str(lo_error)}\n"
                        "Please install either Microsoft Word (for docx2pdf) or LibreOffice."
                    )
                raise Exception(
                    f"Both conversion methods failed.\n"
                    f"docx2pdf error: {error_msg}\n"
                    f"LibreOffice error: {str(lo_error)}\n"
                    "Please install either Microsoft Word (for docx2pdf) or LibreOffice."
                )
    
    # Other platforms (macOS, etc.)
    else:
        # Try LibreOffice first (works on macOS too)
        try:
            return convert_docx_to_pdf_using_libreoffice(docx_path, pdf_path)
        except Exception as lo_error:
            # Fall back to docx2pdf
            try:
                from docx2pdf import convert
                convert(docx_path, pdf_path)
                print(f"DOCX converted to PDF successfully using docx2pdf: {pdf_path}")
                return True
            except ImportError:
                raise Exception(
                    f"LibreOffice conversion failed: {str(lo_error)}\n"
                    "docx2pdf is also not available. Please install one of:\n"
                    "- LibreOffice\n"
                    "- docx2pdf: pip install docx2pdf"
                )
            except Exception as docx2pdf_error:
                raise Exception(
                    f"Both conversion methods failed.\n"
                    f"LibreOffice error: {str(lo_error)}\n"
                    f"docx2pdf error: {str(docx2pdf_error)}"
                )

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

            can.setFont("Helvetica", 8)
            # Right bottom corner - only UID text (no approved date)
            # A4 width is 595.27 points, using ~430 for right alignment
            uid_text = f"UID: {uid}"

            X_POSITION = 430   # control left/right here
            Y_UID = 32

            # Draw only the UID on the page
            can.drawString(X_POSITION, Y_UID, uid_text)

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
