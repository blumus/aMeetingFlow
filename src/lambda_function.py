from datetime import datetime
from html import escape
from logging import INFO, getLogger
from re import DOTALL, MULTILINE, compile, search
from typing import Any, Dict, Optional
from urllib.parse import quote

from boto3 import client

logger = getLogger()
logger.setLevel(INFO)

# Initialize clients at module level for connection reuse
# amazonq-ignore-next-line
s3 = client("s3")
ses = client("ses")

# Logging configuration constants
MAX_LOG_MESSAGE_LENGTH = 500
EMAIL_PREVIEW_LENGTH = 500
HTML_PREVIEW_LENGTH = 200
DECODED_HTML_PREVIEW_LENGTH = 300

# Business logic constants
MIN_MEETING_FIELDS = 3  # from + at least 2 meeting fields (date/time, client, etc.)

# Hebrew month names to numbers mapping
HEBREW_MONTHS = {
    "ינואר": "01",
    "פברואר": "02",
    "מרץ": "03",
    "אפריל": "04",
    "מאי": "05",
    "יוני": "06",
    "יולי": "07",
    "אוגוסט": "08",
    "ספטמבר": "09",
    "אוקטובר": "10",
    "נובמבר": "11",
    "דצמבר": "12",
}

# Supported email domains for meeting automation
SUPPORTED_DOMAINS = ["yoman.co.il", "tagatime.com"]

# Hebrew day names for weekday conversion
HEBREW_DAYS = [
    "יום שני",
    "יום שלישי",
    "יום רביעי",
    "יום חמישי",
    "יום שישי",
    "שבת",
    "יום ראשון",
]

# Email source address for notifications
EMAIL_SOURCE = "receive@receive.hechven.online"

# WhatsApp message template
WHATSAPP_MESSAGE_TEMPLATE = """שלום {client},
רק רציתי להזכיר לכם ששיחת ההכוון שלנו תתקיים ב{day_name}, {date}, בשעה {time}.

במהלך השיחה אציג לכם את ארגון פעמונים ואת הכלים שאנו מציעים להתנהלות כלכלית נכונה. תהיה לכם הזדמנות לשתף אותי באתגרים ובמטרות הכלכליות שלכם, ונסיים את השיחה בתכנון צעדים ראשוניים להמשך התהליך.

חשוב:
- חשוב מאוד ששניכם תיקחו חלק בשיחה.
- אם השעה אינה מתאימה - אשמח שתעדכנו מראש.
- מומלץ להיות במקום שקט, ללא הפרעות, כדי שנוכל להתמקד בצורה מיטבית.

מצפה לשיחה שלנו,
{consultant_name}
יועץ הכוון מטעם פעמונים"""

# HTML email template
HTML_EMAIL_TEMPLATE = """<html><body style="font-family: Arial, sans-serif; direction: rtl;">
<p>שלום,</p>

<p><strong>קישורים שימושיים:</strong></p>
<p>📱 <a href="{whatsapp_link}" style="color: #25D366; text-decoration: underline; font-weight: bold;">שלח תזכורת WhatsApp</a><br>
📅 <a href="{calendar_link}" style="color: #4285F4; text-decoration: underline; font-weight: bold;">הוסף ליומן Google Calendar</a></p>

<p><strong>אישור פגישה:</strong></p>
<p>📅 תאריך: {date}<br>
🕐 שעה: {time}<br>
👤 לקוח: {client}<br>
📱 טלפון: {phone}<br>
📧 אימייל: {email}</p>

<p>בהצלחה!</p>
</body></html>"""

# Compiled regex patterns for Hebrew email parsing
DATE_REGEX = compile(r"(\d{1,2}) ([^\s]+) (\d{4}) בשעה (\d{1,2}:\d{2})")
CLIENT_REGEX = compile(r"פרטי קשר: <b>([^<]+)</b>")
PHONE_REGEX = compile(r"נייד: ([0-9]+)")
EMAIL_REGEX = compile(r'דוא&quot;ל: <a href="mailto:([^"]+)"')

# Compiled regex patterns for HTML content parsing
BASE64_HTML_REGEX = compile(r"Content-Type: text/html[^\r\n]*\r?\nContent-Transfer-Encoding: base64\r?\n\r?\n([^-]+)", DOTALL)
QUOTED_HTML_REGEX = compile(r"Content-Type: text/html[^\r\n]*\r?\n[^\r\n]*\r?\n\r?\n([^\r\n-]+)", DOTALL | MULTILINE)


def sanitize_for_log(value: Any) -> str:
    """Sanitize user input for safe logging by removing control characters."""
    if value is None:
        return "None"
    text = str(value)
    # Remove all control characters using regex (more efficient)
    from re import sub
    sanitized = sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    # Limit length to prevent log flooding
    return sanitized[:MAX_LOG_MESSAGE_LENGTH] + "..." if len(sanitized) > MAX_LOG_MESSAGE_LENGTH else sanitized


def handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    key = "unknown"  # Default for error logging
    try:
        # Validate S3 event structure
        if not event.get("Records") or not event["Records"]:
            logger.error("No Records found in event")
            return {"statusCode": 400}

        record = event["Records"][0]
        if (
            "s3" not in record
            or "bucket" not in record["s3"]
            or "object" not in record["s3"]
        ):
            logger.error("Invalid S3 event structure")
            return {"statusCode": 400}

        # Get S3 object details from S3 event
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Get email content from S3
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            email_content = response["Body"].read().decode("utf-8")
        except Exception as e:
            error_code = (
                getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
            )
            if error_code == "NoSuchKey":
                logger.error(f"S3 object not found: {sanitize_for_log(key)}")
            elif error_code == "AccessDenied":
                logger.error(f"Access denied to S3 object: {sanitize_for_log(key)}")
            else:
                logger.error(f"S3 get_object failed: {sanitize_for_log(str(e))}")
            return {"statusCode": 500}

        # Parse email
        meeting_details = parse_email(email_content)
        if not meeting_details:
            logger.error("Email parsing failed")
            return {"statusCode": 422}  # Unprocessable Entity

        # Send reply
        send_reply(meeting_details, ses)

        # Clean up S3
        try:
            s3.delete_object(Bucket=bucket, Key=key)
        except Exception as e:
            logger.warning(
                f"Failed to delete S3 object {sanitize_for_log(key)}: {sanitize_for_log(str(e))}"
            )
            # Continue execution - cleanup failure shouldn't stop the process

        return {"statusCode": 200}

    except Exception as e:
        logger.error(f"Error processing S3 object {sanitize_for_log(key)}: {sanitize_for_log(str(e))}")
        return {"statusCode": 500}


def decode_html_content(content: str) -> Optional[str]:
    from quopri import decodestring

    html_match = BASE64_HTML_REGEX.search(content)
    if html_match:
        base64_content = html_match.group(1).replace("\n", "").replace("\r", "")
        logger.debug(f"Base64 HTML content found: {len(base64_content)} characters")
        try:
            from base64 import b64decode

            return b64decode(base64_content).decode("utf-8")
        except Exception as e:
            logger.error(f"Error decoding base64: {e}")
            return None

    html_match = QUOTED_HTML_REGEX.search(content)
    if html_match:
        html_content = html_match.group(1)
        logger.debug(f"Quoted-printable HTML content found: {sanitize_for_log(html_content[:HTML_PREVIEW_LENGTH])}")
        try:
            return decodestring(html_content).decode("utf-8")
        except UnicodeDecodeError:
            try:
                return decodestring(html_content).decode("latin-1")
            except Exception as e:
                logger.error(f"Error decoding quoted-printable with latin-1: {e}")
                return None
        except Exception as e:
            logger.error(f"Error decoding quoted-printable with utf-8: {e}")
            return None

    logger.warning("No HTML content found - both regexes failed")
    return None


def _safe_regex_extract(regex: Any, html: str, field_name: str, extractor_func: Optional[Any] = None) -> Optional[Any]:
    """Helper function for safe regex extraction with consistent error handling."""
    try:
        match = regex.search(html)
        if match:
            return extractor_func(match) if extractor_func else match.group(1)
        return None
    except Exception as e:
        raise ValueError(f"Critical error extracting {field_name}: {sanitize_for_log(str(e))}") from e


def extract_meeting_details(decoded_html: str) -> Dict[str, str]:
    details = {}

    # Extract date with custom logic
    def extract_date(match: Any) -> Dict[str, str]:
        groups = match.groups()
        if len(groups) != 4:  # day, month, year, time
            raise ValueError(f"Date regex returned {len(groups)} groups, expected 4")
        day, month_heb, year, time = groups
        logger.debug(f"Date match: {sanitize_for_log(match.groups())}")
        month = HEBREW_MONTHS.get(month_heb)
        if month is None:
            logger.warning(
                f"Unknown Hebrew month '{sanitize_for_log(month_heb)}', defaulting to January"
            )
            month = "01"  # January fallback
        return {"date": f"{day.zfill(2)}/{month}/{year}", "time": time}

    date_result = _safe_regex_extract(DATE_REGEX, decoded_html, "date", extract_date)
    if date_result:
        details.update(date_result)

    # Extract client name
    client = _safe_regex_extract(CLIENT_REGEX, decoded_html, "client")
    if client:
        details["client"] = client
        logger.debug(f"Client found: {sanitize_for_log(client)}")

    # Extract phone
    phone = _safe_regex_extract(PHONE_REGEX, decoded_html, "phone")
    if phone:
        details["phone"] = phone
        logger.debug(f"Phone found: {sanitize_for_log(phone)}")

    # Extract client email
    email = _safe_regex_extract(EMAIL_REGEX, decoded_html, "email")
    if email:
        details["email"] = email
        logger.debug(f"Client email found: {sanitize_for_log(email)}")

    return details


def parse_email(content: str) -> Optional[Dict[str, str]]:
    logger.debug(f"Email content preview: {sanitize_for_log(content[:EMAIL_PREVIEW_LENGTH])}")

    # Extract From address for reply
    from_match = search(r"From: ([^\n]+)", content)
    if not from_match:
        logger.error("No From address found")
        return None

    from_address = from_match.group(1).strip()
    logger.debug(f"From address: {sanitize_for_log(from_address)}")

    # Check if this is from a supported domain
    if not any(domain in content for domain in SUPPORTED_DOMAINS):
        logger.info("Not a supported email domain")
        return None

    logger.debug("Found supported domain email")
    details = {"from": from_address}

    # Decode HTML content
    decoded_html = decode_html_content(content)
    if not decoded_html:
        return details

    logger.debug(f"Decoded HTML: {sanitize_for_log(decoded_html[:DECODED_HTML_PREVIEW_LENGTH])}")

    # Extract meeting details
    meeting_data = extract_meeting_details(decoded_html)
    details.update(meeting_data)

    logger.debug(f"Final details: {sanitize_for_log(details)}")
    return details if len(details) >= MIN_MEETING_FIELDS else None


def extract_email_address(from_field: str) -> str:
    """Extract clean email address from 'Name <email>' format."""
    if "<" in from_field and ">" in from_field:
        try:
            return from_field.split("<")[1].split(">")[0]
        except IndexError as e:
            raise ValueError(f"Malformed email address format: {from_field}") from e
    return from_field


def extract_consultant_name(from_field: str) -> str:
    """Extract consultant name from 'Name <email>' format."""
    if "<" in from_field and ">" in from_field:
        try:
            return from_field.split("<")[0].strip()
        except IndexError:
            return "ברוך ליימן"  # fallback
    return from_field.strip()


def generate_whatsapp_text(details: Dict[str, str]) -> str:
    """Generate WhatsApp message text."""
    # Calculate day of week
    day_name = ""
    date_parts = details.get("date", "").split("/")
    if len(date_parts) == 3:  # day, month, year
        day, month, year = date_parts
        try:
            date_obj = datetime(int(year), int(month), int(day))
            day_name = HEBREW_DAYS[date_obj.weekday()]
        except (ValueError, TypeError, IndexError) as e:
            logger.error(
                f"Error parsing date {sanitize_for_log(day)}/{sanitize_for_log(month)}/{sanitize_for_log(year)}: {sanitize_for_log(e)}"
            )

    # Extract consultant name from From field
    consultant_name = extract_consultant_name(details.get('from', ''))

    return WHATSAPP_MESSAGE_TEMPLATE.format(
        client=details.get('client', ''),
        day_name=day_name,
        date=details.get('date', '').replace('/', '.'),
        time=details.get('time', ''),
        consultant_name=consultant_name
    )


def generate_whatsapp_link(details: Dict[str, str], whatsapp_text: str) -> str:
    """Generate WhatsApp link with pre-generated message text."""
    phone = details.get("phone", "").replace("-", "").replace(" ", "")
    if phone.startswith("0"):
        phone = "972" + phone[1:]  # Convert Israeli 0xx to +972xx

    return f"https://wa.me/{phone}?text={quote(whatsapp_text)}"


def generate_calendar_link(
    details: Dict[str, str], email_address: str, whatsapp_text: str
) -> str:
    """Generate Google Calendar link for the meeting."""
    date_parts = details.get("date", "").split("/")
    time_parts = details.get("time", "").split(":")

    if len(date_parts) != 3 or len(time_parts) != 2:  # day/month/year and hour:minute
        return "#invalid-date"

    day, month, year = date_parts
    hour, minute = time_parts

    try:
        from datetime import timedelta

        start_dt = datetime(int(year), int(month), int(day), int(hour), int(minute))
        end_dt = start_dt + timedelta(hours=1)  # Default 1-hour meeting
        start_time = start_dt.strftime("%Y%m%dT%H%M%S")
        end_time = end_dt.strftime("%Y%m%dT%H%M%S")
    except ValueError:
        logger.error(
            f"Invalid date/time values: {sanitize_for_log(date_parts)} {sanitize_for_log(time_parts)}"
        )
        return "#invalid-date"

    subject = f"פעמונים - שיחת הכוון בזום - {details.get('client', '')}"
    client_email = details.get("email", "")
    attendees = f"{email_address},{client_email}" if client_email else email_address

    return f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={quote(subject)}&dates={start_time}/{end_time}&add={attendees}&details={quote(whatsapp_text)}"


def send_email_notification(
    email_address: str,
    whatsapp_link: str,
    calendar_link: str,
    details: Dict[str, str],
    ses: Any,
) -> None:
    """Send email notification with meeting details and links."""
    body = f"""שלום,

קישורים שימושיים:
📱 WhatsApp: {whatsapp_link}
📅 הוסף ליומן: {calendar_link}

אישור פגישה:
📅 תאריך: {sanitize_for_log(details.get("date", ""))}
🕐 שעה: {sanitize_for_log(details.get("time", ""))}
👤 לקוח: {sanitize_for_log(details.get("client", ""))}
📱 טלפון: {sanitize_for_log(details.get("phone", ""))}
📧 אימייל: {sanitize_for_log(details.get("email", ""))}

בהצלחה!"""

    html_body = HTML_EMAIL_TEMPLATE.format(
        whatsapp_link=escape(whatsapp_link),
        calendar_link=escape(calendar_link),
        date=escape(details.get("date", "")),
        time=escape(details.get("time", "")),
        client=escape(details.get("client", "")),
        phone=escape(details.get("phone", "")),
        email=escape(details.get("email", ""))
    )

    try:
        ses.send_email(
            Source=EMAIL_SOURCE,
            Destination={"ToAddresses": [email_address]},
            Message={
                "Subject": {"Data": "אישור פגישה", "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body, "Charset": "UTF-8"},
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
        logger.info(f"Email sent successfully to {sanitize_for_log(email_address)}")
    except Exception as e:
        logger.error(
            f"Failed to send email to {sanitize_for_log(email_address)}: {sanitize_for_log(str(e))}"
        )
        raise


def send_reply(details: Dict[str, str], ses: Any) -> None:
    """Send meeting confirmation reply with WhatsApp and calendar links."""
    if "from" not in details:
        raise ValueError("Missing required 'from' field in meeting details")
    email_address = extract_email_address(details["from"])
    # Generate WhatsApp text once to avoid duplication
    whatsapp_text = generate_whatsapp_text(details)
    whatsapp_link = generate_whatsapp_link(details, whatsapp_text)
    calendar_link = generate_calendar_link(details, email_address, whatsapp_text)
    send_email_notification(email_address, whatsapp_link, calendar_link, details, ses)
