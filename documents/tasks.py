from celery import shared_task
from django.core.mail import EmailMessage
from .templates.document_approval_email_template import get_document_approval_email_html

@shared_task
def send_document_approval_email_task(employee_email, employee_name, document_title, document_uid, approved_date, approver_name):
    """
    Send email notification to employee when their document is approved.
    """
    try:
        html_content = get_document_approval_email_html(
            employee_name=employee_name,
            document_title=document_title,
            document_uid=document_uid,
            approved_date=approved_date,
            approver_name=approver_name
        )
        
        email_message = EmailMessage(
            subject=f"Document Approved: {document_title}",
            body=html_content,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            to=[employee_email],
        )
        email_message.content_subtype = "html"
        email_message.send(fail_silently=False)
        print(f"Document approval email sent successfully to {employee_email}")
    except Exception as e:
        print(f"Failed to send document approval email to {employee_email}: {str(e)}")
        raise Exception(f"Failed to send document approval email: {str(e)}")

