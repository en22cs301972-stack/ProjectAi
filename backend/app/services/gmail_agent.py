"""
Gmail Agent - Sample autonomous agent implementation
Reads emails and sends AI-generated auto-responses
"""
import json
import asyncio
from typing import Dict, Any, Optional
import structlog

logger = structlog.get_logger()


async def gmail_auto_responder(
    gmail_credentials: Dict,
    ai_client,
    check_interval: int = 60,
    max_emails: int = 5,
    stop_event: asyncio.Event = None,
) -> Dict[str, Any]:
    """
    Gmail auto-responder agent.
    
    Reads unread emails and sends intelligent AI-generated responses.
    """
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    import base64
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    results = {
        "processed": 0,
        "responded": 0,
        "errors": [],
    }

    try:
        creds = Credentials(**gmail_credentials)
        service = build("gmail", "v1", credentials=creds)

        # Get user's email address
        profile = service.users().getProfile(userId="me").execute()
        user_email = profile.get("emailAddress", "")
        logger.info("Gmail agent started", email=user_email)

        # List unread emails
        messages_result = service.users().messages().list(
            userId="me",
            q="is:unread -from:me",
            maxResults=max_emails,
        ).execute()

        messages = messages_result.get("messages", [])
        logger.info("Found unread emails", count=len(messages))

        for msg_data in messages:
            if stop_event and stop_event.is_set():
                logger.info("Gmail agent stopped by user")
                break

            msg_id = msg_data["id"]

            try:
                # Get full message
                msg = service.users().messages().get(
                    userId="me",
                    id=msg_id,
                    format="full",
                ).execute()

                # Extract email details
                headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                sender = headers.get("From", "")
                subject = headers.get("Subject", "No subject")
                body = extract_email_body(msg["payload"])

                results["processed"] += 1
                logger.info("Processing email", subject=subject, from_=sender)

                # Generate AI response
                ai_response = await generate_email_response(
                    sender=sender,
                    subject=subject,
                    body=body,
                    ai_client=ai_client,
                )

                # Send reply
                reply = create_reply_email(
                    to=sender,
                    subject=f"Re: {subject}",
                    body=ai_response,
                    in_reply_to=msg_id,
                )
                raw_reply = base64.urlsafe_b64encode(reply.as_bytes()).decode()

                service.users().messages().send(
                    userId="me",
                    body={
                        "raw": raw_reply,
                        "threadId": msg.get("threadId"),
                    },
                ).execute()

                # Mark as read
                service.users().messages().modify(
                    userId="me",
                    id=msg_id,
                    body={"removeLabelIds": ["UNREAD"]},
                ).execute()

                results["responded"] += 1
                logger.info("Replied to email", subject=subject)

            except Exception as e:
                error_msg = f"Error processing email {msg_id}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error("Email processing error", error=str(e))

        return {
            "success": True,
            "summary": f"Processed {results['processed']} emails, responded to {results['responded']}",
            **results,
        }

    except Exception as e:
        logger.error("Gmail agent error", error=str(e))
        return {"success": False, "error": str(e), **results}


def extract_email_body(payload: Dict) -> str:
    """Extract plain text body from email payload."""
    import base64

    body = ""

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                data = part["body"].get("data", "")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    break
            elif "parts" in part:
                body = extract_email_body(part)
                if body:
                    break
    elif payload.get("mimeType") == "text/plain":
        data = payload["body"].get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return body[:2000]  # Limit body length


async def generate_email_response(
    sender: str,
    subject: str,
    body: str,
    ai_client,
) -> str:
    """Generate an AI response to an email."""
    try:
        prompt = f"""Write a professional and helpful email response to this message:

From: {sender}
Subject: {subject}

Email content:
{body}

Write a concise, helpful, and professional reply. Be friendly but brief."""

        response = await ai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful email assistant. Write professional email responses."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Thank you for your email regarding '{subject}'. I'll get back to you shortly. (Auto-reply)"


def create_reply_email(
    to: str,
    subject: str,
    body: str,
    in_reply_to: str = None,
) -> MIMEMultipart:
    """Create a reply email message."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    msg.attach(MIMEText(body, "plain"))
    return msg
