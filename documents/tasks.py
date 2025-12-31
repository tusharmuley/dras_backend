from celery import shared_task
from django.core.mail import EmailMessage
from .templates.document_approval_email_template import get_document_approval_email_html, get_document_rejection_email_html

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


@shared_task(name='documents.send_document_rejection_email_task')
def send_document_rejection_email_task(employee_email, employee_name, document_title, rejected_date, approver_name, remarks=None):
    """
    Send email notification to employee when their document is rejected.
    """
    print(f"[REJECTION TASK] Starting - Sending document rejection email to {employee_email}")
    print(f"[REJECTION TASK] Document: {document_title}, Rejected by: {approver_name}")
    try:
        html_content = get_document_rejection_email_html(
            employee_name=employee_name,
            document_title=document_title,
            rejected_date=rejected_date,
            approver_name=approver_name,
            remarks=remarks
        )
        
        email_message = EmailMessage(
            subject=f"Document Rejected: {document_title}",
            body=html_content,
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            to=[employee_email],
        )
        email_message.content_subtype = "html"
        print(f"[REJECTION TASK] Attempting to send email...")
        email_message.send(fail_silently=False)
        print(f"[REJECTION TASK] Document rejection email sent successfully to {employee_email}")
    except Exception as e:
        import traceback
        print(f"[REJECTION TASK] Failed to send document rejection email to {employee_email}: {str(e)}")
        print(f"[REJECTION TASK] Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to send document rejection email: {str(e)}")

