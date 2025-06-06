import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import structlog
import aiosmtplib

from config import settings

logger = structlog.get_logger()

class EmailService:
    """Service for sending email responses"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_USERNAME or "support@agentic-comms.com"
        
    async def send_response(
        self,
        to_email: str,
        subject: str,
        content: str,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email response"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            if reply_to:
                message["Reply-To"] = reply_to
            
            if cc:
                message["Cc"] = ", ".join(cc)
            
            # Create HTML and text versions
            text_content = content
            html_content = f"""
            <html>
              <body>
                <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                  {content.replace('\n', '<br>')}
                  <br><br>
                  <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                  <p style="font-size: 12px; color: #666;">
                    This is an automated response from our AI customer service system.
                    If you need further assistance, please reply to this email.
                  </p>
                </div>
              </body>
            </html>
            """
            
            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            if self.username and self.password:
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.username,
                    password=self.password,
                    use_tls=True
                )
            else:
                # Development mode - just log
                logger.info(
                    "Email would be sent",
                    to=to_email,
                    subject=subject,
                    content_length=len(content)
                )
            
            logger.info(
                "Email sent successfully",
                to_email=to_email,
                subject=subject
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send email",
                to_email=to_email,
                subject=subject,
                error=str(e)
            )
            return False
    
    async def send_escalation_notification(
        self,
        conversation_id: str,
        customer_email: str,
        original_message: str,
        agent_response: str,
        escalation_reason: str
    ) -> bool:
        """Send escalation notification to human agents"""
        try:
            subject = f"[ESCALATION] Conversation {conversation_id[:8]}"
            
            content = f"""
A customer conversation has been escalated and requires human attention.

Conversation ID: {conversation_id}
Customer Email: {customer_email}
Escalation Reason: {escalation_reason}

Original Customer Message:
{original_message}

AI Agent Response:
{agent_response}

Please review and respond to the customer directly.

Dashboard Link: https://agentic-comms-v1.surge.sh/dashboard/conversations/{conversation_id}
            """
            
            # In production, this would go to a support team email
            support_email = "support-team@company.com"
            
            return await self.send_response(
                to_email=support_email,
                subject=subject,
                content=content
            )
            
        except Exception as e:
            logger.error(
                "Failed to send escalation notification",
                conversation_id=conversation_id,
                error=str(e)
            )
            return False
    
    async def health_check(self) -> bool:
        """Check if email service is healthy"""
        try:
            if not self.username or not self.password:
                # In development mode, consider healthy
                return True
            
            # Test SMTP connection
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(self.username, self.password)
            
            return True
            
        except Exception as e:
            logger.error("Email service health check failed", error=str(e))
            return False 