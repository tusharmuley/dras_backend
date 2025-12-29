def get_otp_email_html(first_name, otp, reset_password_url=None):
    """
    Returns HTML content for OTP email.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Password Reset OTP</title>
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
            .otp {{
                display: block;
                font-size: 24px;
                font-weight: bold;
                margin: 20px 0;
                text-align: center;
                color: #1a73e8;
            }}
            .button {{
                display: inline-block;
                padding: 12px 20px;
                background-color: #1a73e8;
                color: #fff !important;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
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
                <p>Hi {first_name},</p>
                <p>You requested to reset your password. Use the following OTP to reset your password:</p>
                <span class="otp">{otp}</span>
    """
    if reset_password_url:
        html_content += f"""
                <p style="text-align:center;">
                    <a href="{reset_password_url}" class="button">Reset Password</a>
                </p>
        """
    html_content += """
                <p>This OTP is valid for 10 minutes. If you did not request a password reset, please ignore this email.</p>
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
