"""Email service for sending verification codes via Gmail SMTP."""

import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timedelta, timezone

import streamlit as st


def generate_verification_code(length: int = 6) -> str:
    """Generate a random numeric verification code."""
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def send_verification_email(email: str, code: str) -> bool:
    """Send a verification code email via Gmail SMTP.
    
    Returns True if email was sent successfully, False otherwise.
    """
    # Load configuration from environment variables
    gmail_email = os.getenv("GMAIL_EMAIL", "").strip()
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    
    # Remove spaces from app password if present
    gmail_app_password = gmail_app_password.replace(" ", "")
    
    if not gmail_email or not gmail_app_password:
        st.error("Email service not configured. Please set GMAIL_EMAIL and GMAIL_APP_PASSWORD environment variables.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_email
        msg['To'] = email
        msg['Subject'] = "ExoQ - Verify Your Email Address"
        
        body = f"""
        <html>
        <body>
            <h2>Welcome to ExoQ!</h2>
            <p>Thank you for signing up. Please use the following verification code to complete your registration:</p>
            <h1 style="color: #1b5e20; font-size: 32px; letter-spacing: 4px;">{code}</h1>
            <p>This code will expire in 15 minutes.</p>
            <p>If you did not request this code, please ignore this email.</p>
            <p>Best regards,<br>The ExoQ Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send via Gmail SMTP with detailed error handling
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as server:
            server.set_debuglevel(1)  # Enable debug output
            server.starttls()
            server.login(gmail_email, gmail_app_password)
            server.send_message(msg)
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        st.error(f"Gmail authentication failed. Please check your email and app password. Error: {e}")
        return False
    except smtplib.SMTPException as e:
        st.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        st.error(f"Failed to send verification email: {str(e)}")
        return False


def is_code_expired(issued_at: str, expiry_minutes: int = 15) -> bool:
    """Check if a verification code has expired."""
    try:
        issued_time = datetime.fromisoformat(issued_at)
        # Handle both timezone-aware and naive datetimes
        if issued_time.tzinfo is None:
            issued_time = issued_time.replace(tzinfo=timezone.utc)
        expiry_time = issued_time + timedelta(minutes=expiry_minutes)
        return datetime.now(timezone.utc) > expiry_time
    except Exception:
        return True
