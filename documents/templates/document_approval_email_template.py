def get_document_approval_email_html(employee_name, document_title, document_uid, approved_date, approver_name):
    """
    Returns HTML content for document approval email.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Document Approved</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0; padding: 0;
            }}
            .container {{
                width: 100%;
                max-width: 600px;
                margin: 50px auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header img {{
                width: 150px;
            }}
            .content {{
                font-size: 16px;
                line-height: 1.5;
                color: #333333;
            }}
            .success-badge {{
                display: inline-block;
                background-color: #4CAF50;
                color: #ffffff;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
                margin: 10px 0;
            }}
            .document-info {{
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #1a73e8;
            }}
            .document-info p {{
                margin: 8px 0;
            }}
            .document-info strong {{
                color: #1a73e8;
            }}
            .uid {{
                display: block;
                font-size: 20px;
                font-weight: bold;
                margin: 15px 0;
                text-align: center;
                color: #1a73e8;
                background-color: #e8f0fe;
                padding: 12px;
                border-radius: 5px;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 12px;
                color: #777777;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://framerusercontent.com/images/65HA7ldXaCcBX1TyIlKb7kJz1iA.png" alt="Company Logo">
            </div>
            <div class="content">
                <p>Hi {employee_name},</p>
                <p>Great news! Your document has been approved.</p>
                <div style="text-align: center;">
                    <span class="success-badge">✓ APPROVED</span>
                </div>
                <div class="document-info">
                    <p><strong>Document Title:</strong> {document_title}</p>
                    <p><strong>Approved By:</strong> {approver_name}</p>
                    <p><strong>Approved Date:</strong> {approved_date}</p>
                </div>
                <p>Your document has been assigned a unique identifier:</p>
                <span class="uid">UID: {document_uid}</span>
                <p>Please keep this UID for your records. The document is now read-only and cannot be modified.</p>
                <p>If you have any questions, please contact your administrator.</p>
                <p>Thanks,<br>Team Quantian Technologies</p>
            </div>
            <div class="footer">
                &copy; 2025 Quantian Technologies. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

