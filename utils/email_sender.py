import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()
import os


SENDER_EMAIL = "stegosafe6@gmail.com"
SENDER_PASSWORD = os.getenv("Email_key")

def send_email_core(to_email, subject, html_content):
    msg = MIMEMultipart("alternative")
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    part = MIMEText(html_content, 'html')
    msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def get_base_template(content):
    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f9; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #6366f1; margin: 0;">StegoSafe</h1>
                <p style="color: #64748b; font-size: 14px; margin-top: 5px;">Secure Communication Platform</p>
            </div>
            
            <div style="padding: 20px 0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                {content}
            </div>

            <div style="text-align: center; margin-top: 30px; color: #94a3b8; font-size: 12px;">
                <p>&copy; 2026 StegoSafe. All rights reserved.</p>
                <p>If you did not request this email, please ignore it.</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_otp_email(to_email, otp):
    subject = "Your StegoSafe Verification Code"
    content = f"""
        <h2 style="color: #1e293b; margin-bottom: 20px; text-align: center;">Password Reset Request</h2>
        <p style="font-size: 16px; line-height: 1.6;">Hello,</p>
        <p style="font-size: 16px; line-height: 1.6;">We received a request to reset your StegoSafe account password. Use the following OTP code to proceed:</p>
        
        <div style="background-color: #f1f5f9; padding: 15px; text-align: center; border-radius: 8px; margin: 30px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #6366f1;">{otp}</span>
        </div>
        
        <p style="font-size: 16px; line-height: 1.6;">This code will expire shortly. Do not share this code with anyone.</p>
    """
    return send_email_core(to_email, subject, get_base_template(content))

def send_password_success_email(to_email):
    subject = "Password Changed Successfully - StegoSafe"
    content = f"""
        <h2 style="color: #1e293b; margin-bottom: 20px; text-align: center;">Password Updated</h2>
        <div style="text-align: center; margin-bottom: 20px;">
            <span style="font-size: 48px;">✅</span>
        </div>
        <p style="font-size: 16px; line-height: 1.6; text-align: center;">Your StegoSafe account password has been successfully updated.</p>
        <p style="font-size: 16px; line-height: 1.6; text-align: center;">You can now login with your new credentials.</p>
        
        <div style="text-align: center; margin-top: 30px;">
            <a href="http://127.0.0.1:5000/login" style="background-color: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Login Now</a>
        </div>
    """
    return send_email_core(to_email, subject, get_base_template(content))
