from base64 import b64decode
from datetime import datetime
from html import escape
from logging import DEBUG, ERROR, INFO, WARNING, getLogger
from os import getenv
from re import DOTALL, MULTILINE, Match, Pattern, compile, search
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote

from boto3 import client

logger = getLogger()

# Logging configuration constants
LOG_LEVELS = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARNING": WARNING,
    "ERROR": ERROR,
}
DEFAULT_LOG_LEVEL = "INFO"

# Set log level from environment variable, default to DEBUG for development
log_level = getenv("LOG_LEVEL", "DEBUG").upper()
logger.setLevel(LOG_LEVELS.get(log_level, LOG_LEVELS[DEFAULT_LOG_LEVEL]))

# Initialize clients at module level for connection reuse
# amazonq-ignore-next-line
s3 = client("s3")
ses = client("ses")

MAX_LOG_MESSAGE_LENGTH = 500
EMAIL_PREVIEW_LENGTH = 500
HTML_PREVIEW_LENGTH = 200
DECODED_HTML_PREVIEW_LENGTH = 300

# Business logic constants
MIN_MEETING_FIELDS = 3  # from + at least 2 meeting fields (date/time, client, etc.)

# Email client forwarding markers
FORWARDING_MARKERS = [
    "---------- Forwarded message ---------",  # Gmail
    "Begin forwarded message:",  # Mac Mail
    "-----Original Message-----",  # Outlook
    "From:",  # Sometimes no explicit marker
]

# Hebrew month names to numbers mapping
HEBREW_MONTHS: Dict[str, str] = {
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
SUPPORTED_DOMAINS: List[str] = ["yoman.co.il", "tagatime.com"]

# Hebrew day names for weekday conversion
HEBREW_DAYS: List[str] = [
    "יום שני",
    "יום שלישי",
    "יום רביעי",
    "יום חמישי",
    "יום שישי",
    "שבת",
    "יום ראשון",
]

# Email source address for notifications (configurable via environment)
EMAIL_SOURCE = getenv("EMAIL_SOURCE", "receive@receive.hechven.online")

# WhatsApp message template for couples
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

# WhatsApp message template for single person
WHATSAPP_MESSAGE_TEMPLATE_SINGLE = """שלום {client},
רציתי להזכיר לך את שיחת ההכוון הטלפונית המתוכננת בינינו ב{day_name}, {date}, בשעה {time}. הפגישה צפויה להימשך כ-30 דקות.

במהלך השיחה, אני, {consultant_name}, יועץ הכוון מטעם ארגון פעמונים, אציג בפנייך את הארגון ואת שירותים שאנו מציעים. בנוסף, תהיה לך הזדמנות לספר לי על עצמך ועל יעדי תקציב הבית שלך. נסיים את השיחה בתכנון צעדים שבאים.

חשוב!
- במידה ולא נוכל ליצור קשר בזמן שקבענו, נסגור את הפניה
- אנא הודיעי בהקדם במידה ואינך יכולה, ונקבע זמן חדש.

בברכה,
{consultant_name}
יועץ הכוון מטעם פעמונים"""

# HTML email template
HTML_EMAIL_TEMPLATE = """<html><body style="font-family: Arial, sans-serif; direction: rtl;">
<p>שלום,</p>

<p><strong>קישורים שימושיים:</strong></p>
<p>{whatsapp_links_html}<br>
📅 <a href="{calendar_link}" style="color: #4285F4; text-decoration: underline; font-weight: bold;">הוסף ליומן Google Calendar</a></p>

<p><strong>אישור פגישה:</strong></p>
<p>📅 תאריך: {date}<br>
🕐 שעה: {time}<br>
👤 לקוח: {client}<br>
📱 טלפון: {phone}<br>
📧 אימייל: {email}{additional_attendee_html}</p>

<p>בהצלחה!</p>
</body></html>"""

# Regex patterns for extracting meeting details from forwarded content
DATE_REGEX: Pattern[str] = compile(r"(\d{1,2}) ([^\s]+) (\d{4}) בשעה (\d{1,2}:\d{2})")
CLIENT_REGEX: Pattern[str] = compile(r"פרטי קשר: ([^\n\r]+)")
PHONE_REGEX: Pattern[str] = compile(r"נייד: ([0-9]+)")
EMAIL_REGEX: Pattern[str] = compile(r'דוא"ל: ([^\n\r]+)')

# Compiled regex patterns for HTML content parsing
BASE64_HTML_REGEX: Pattern[str] = compile(
    r"Content-Type: text/html[^\r\n]*\r?\nContent-Transfer-Encoding: base64\r?\n\r?\n([^-]+)",
    DOTALL,
)
QUOTED_HTML_REGEX: Pattern[str] = compile(
    r"Content-Type: text/html[^\r\n]*\r?\n[^\r\n]*\r?\n\r?\n([^\r\n-]+)",
    DOTALL | MULTILINE,
)


def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text while preserving content and spacing."""
    if not text:
        return ""
    # First decode HTML entities
    text = (
        text.replace("&quot;", '"')
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
    )

    # Remove HTML tags but preserve line breaks and spacing
    import re

    # Replace <br> and </br> with newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Remove other HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Clean up extra whitespace but preserve intentional spacing
    text = re.sub(r"\n\s*\n", "\n\n", text)  # Multiple newlines to double newlines
    text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces/tabs to single space
    text = text.strip()

    return text


def sanitize_for_log(value: Any) -> str:
    """Sanitize user input for safe logging by removing control characters."""
    if value is None:
        return "None"
    text = str(value)
    # Remove all control characters using regex (more efficient)
    from re import sub

    sanitized = sub(r"[\x00-\x1F\x7F-\x9F]", "", text)
    # Limit length to prevent log flooding
    return (
        sanitized[:MAX_LOG_MESSAGE_LENGTH] + "..."
        if len(sanitized) > MAX_LOG_MESSAGE_LENGTH
        else sanitized
    )


def handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    key: str = "unknown"  # Default for error logging
    try:
        # Validate S3 event structure
        if not event.get("Records") or not event["Records"]:
            logger.error("No Records found in event")
            return {"statusCode": 400}

        record: Dict[str, Any] = event["Records"][0]
        if (
            "s3" not in record
            or "bucket" not in record["s3"]
            or "object" not in record["s3"]
        ):
            logger.error("Invalid S3 event structure")
            return {"statusCode": 400}

        # Get S3 object details from S3 event
        bucket: str = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Get email content from S3
        try:
            response: Any = s3.get_object(Bucket=bucket, Key=key)
            email_content: str = response["Body"].read().decode("utf-8")
        except Exception as e:
            error_code: str = (
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
        try:
            meeting_details: Dict[str, str] = parse_email(email_content)
        except ValueError as e:
            logger.error(f"Email parsing failed: {sanitize_for_log(str(e))}")
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
        logger.error(
            f"Error processing S3 object {sanitize_for_log(key)}: {sanitize_for_log(str(e))}"
        )
        return {"statusCode": 500}


def decode_html_content(content: str) -> Optional[str]:
    from quopri import decodestring

    html_match: Optional[Match[str]] = BASE64_HTML_REGEX.search(content)
    if html_match:
        base64_content: str = html_match.group(1).replace("\n", "").replace("\r", "")
        logger.debug(f"Base64 HTML content found: {len(base64_content)} characters")
        try:
            return b64decode(base64_content).decode("utf-8")
        except Exception as e:
            logger.error(f"Error decoding base64: {e}")
            return None

    html_match = QUOTED_HTML_REGEX.search(content)
    if html_match:
        html_content: str = html_match.group(1)
        logger.debug(
            f"Quoted-printable HTML content found: {sanitize_for_log(html_content[:HTML_PREVIEW_LENGTH])}"
        )
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


def _safe_regex_extract(
    regex: Pattern[str],
    html: str,
    field_name: str,
    extractor_func: Optional[Callable[[Match[str]], Any]] = None,
) -> Optional[Any]:
    """Helper function for safe regex extraction with consistent error handling."""
    try:
        match: Optional[Match[str]] = regex.search(html)
        if match:
            return extractor_func(match) if extractor_func else match.group(1)
        return None
    except Exception as e:
        raise ValueError(
            f"Critical error extracting {field_name}: {sanitize_for_log(str(e))}"
        ) from e


def extract_meeting_details(decoded_html: str) -> Dict[str, str]:
    # Extract only from forwarded content to avoid contamination
    forwarded_content = extract_forwarded_content(decoded_html)

    # Clean HTML entities from the content before applying regex
    forwarded_content = clean_html_tags(forwarded_content)

    details: Dict[str, str] = {}

    # Extract date with custom logic
    def extract_date(match: Match[str]) -> Dict[str, str]:
        groups: tuple[str, ...] = match.groups()
        if len(groups) != 4:  # day, month, year, time
            raise ValueError(f"Date regex returned {len(groups)} groups, expected 4")
        day: str
        month_heb: str
        year: str
        time: str
        day, month_heb, year, time = groups
        logger.debug(f"Date match: {sanitize_for_log(match.groups())}")
        month: Optional[str] = HEBREW_MONTHS.get(month_heb)
        if month is None:
            logger.warning(
                f"Unknown Hebrew month '{sanitize_for_log(month_heb)}', defaulting to January"
            )
            month = "01"  # January fallback
        return {"date": f"{day.zfill(2)}/{month}/{year}", "time": time}

    date_result: Optional[Any] = _safe_regex_extract(
        DATE_REGEX, forwarded_content, "date", extract_date
    )
    if date_result:
        details.update(date_result)

    # Extract client name from forwarded content only
    client: Optional[Any] = _safe_regex_extract(
        CLIENT_REGEX, forwarded_content, "client"
    )
    if client:
        details["client"] = client  # Already cleaned by clean_html_tags
        logger.debug(f"Client found: {sanitize_for_log(client)}")

    # Extract phone from forwarded content only
    phone: Optional[Any] = _safe_regex_extract(PHONE_REGEX, forwarded_content, "phone")
    if phone:
        details["phone"] = phone  # Already cleaned by clean_html_tags
        logger.debug(f"Phone found: {sanitize_for_log(phone)}")

    # Extract client email from forwarded content only
    email = _safe_regex_extract(EMAIL_REGEX, forwarded_content, "email")
    if email:
        details["email"] = email  # Already cleaned by clean_html_tags
        logger.debug(f"Client email found: {sanitize_for_log(email)}")

    return details


def extract_forwarder_email(content: str) -> str:
    """Extract forwarder email from headers section only."""
    # RFC 5322: headers are separated from body by a blank line
    headers_end = content.find("\n\n")
    if headers_end == -1:
        headers_end = content.find("\r\n\r\n")

    if headers_end == -1:
        # Non-RFC compliant email - this should not happen
        raise ValueError(
            "Invalid email format: no blank line separating headers from body"
        )

    headers_only = content[:headers_end]
    from_match = search(r"^From:\s*(.+?)$", headers_only, MULTILINE)

    if not from_match:
        raise ValueError("No From address found in email headers")
    return from_match.group(1).strip()


def find_forwarding_marker(content: str) -> Optional[Tuple[int, str]]:
    """Find forwarding marker position and type in email content."""
    logger.debug("Searching for forwarding marker in email content")

    # First try to decode any base64 content
    decoded_content = content
    if "Content-Transfer-Encoding: base64" in content:
        try:
            # Find base64 content after the header
            base64_match = search(
                r"Content-Transfer-Encoding: base64\r?\n\r?\n([^-]+)",
                content,
                DOTALL,
            )
            if base64_match:
                base64_content = (
                    base64_match.group(1).replace("\n", "").replace("\r", "")
                )
                decoded_content = b64decode(base64_content).decode("utf-8")
                logger.debug(f"Decoded base64 content, length: {len(decoded_content)}")
        except Exception as e:
            logger.debug(f"Failed to decode base64: {e}")

    # Find forwarded message marker from various email clients in decoded content
    for marker in FORWARDING_MARKERS:
        pos = decoded_content.find(marker)
        if pos != -1:
            logger.info(f"Found marker '{marker}' at position {pos}")
            return pos, marker

    logger.info("No forwarding marker found")
    return None


def decode_base64_content(content: str) -> str:
    """Decode base64 content if present in email."""
    logger.debug("Checking for base64 content")

    if "Content-Transfer-Encoding: base64" in content:
        try:
            # Find base64 content after the header
            base64_match = search(
                r"Content-Transfer-Encoding: base64\r?\n\r?\n([^-]+)",
                content,
                DOTALL,
            )
            if base64_match:
                base64_content = (
                    base64_match.group(1).replace("\n", "").replace("\r", "")
                )
                decoded_content = b64decode(base64_content).decode("utf-8")
                logger.debug(f"Decoded base64 content, length: {len(decoded_content)}")
                return decoded_content
        except Exception as e:
            logger.debug(f"Failed to decode base64: {e}")

    # Return original content if no base64 found
    return content


def extract_pre_forwarded_content(content: str, marker_pos: int) -> str:
    """Extract content before the forwarding marker."""
    pre_forwarded_content = content[:marker_pos].strip()
    logger.debug(f"Pre-forwarded content length: {len(pre_forwarded_content)}")
    logger.debug(
        f"Pre-forwarded content preview: {sanitize_for_log(pre_forwarded_content[:100])}"
    )
    return pre_forwarded_content


def parse_attendee_from_content(content: str) -> Optional[Dict[str, str]]:
    """Parse attendee info from pre-forwarded content using ADD/הוסף prefixes."""
    logger.debug("Parsing attendee info from content using prefix-based detection")

    if not content:
        logger.info("No pre-forwarded content found")
        return None

    # Split into lines and process
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    logger.debug(f"Processing {len(lines)} lines for attendee info")

    # Track what we've found
    found_name = False
    attendee = {}

    # Process each line
    for line in lines:
        # Skip empty or very short lines
        if len(line) < 2:
            continue

        # Check for Hebrew prefix first
        if line.startswith("הוסף "):
            line_content = line[5:].strip()  # Remove "הוסף "
            logger.debug(
                f"Found Hebrew prefix, content: {sanitize_for_log(line_content)}"
            )
        # Check for English prefix (case-insensitive)
        elif line.upper().startswith("ADD "):
            line_content = line[4:].strip()  # Remove "ADD " (any case)
            logger.debug(
                f"Found English prefix, content: {sanitize_for_log(line_content)}"
            )
        else:
            # Skip lines without ADD/הוסף prefix
            continue

        # Parse the content after prefix
        if not found_name:
            # First name - create attendee
            attendee["name"] = line_content
            found_name = True
            logger.debug(f"Found first name: {sanitize_for_log(line_content)}")
        else:
            # Already have name - only add phone/email if not already set
            phone = parse_phone_number(line_content)
            if "phone" not in attendee and phone:
                attendee["phone"] = phone
                logger.debug(f"Added phone: {sanitize_for_log(attendee['phone'])}")
            elif "email" not in attendee and is_email(line_content):
                attendee["email"] = line_content
                logger.debug(f"Added email: {sanitize_for_log(line_content)}")
            else:
                logger.debug(
                    f"Ignoring line (duplicate or invalid): {sanitize_for_log(line_content)}"
                )

    # Must have at least a name
    if not found_name:
        logger.debug("No valid name found with ADD/הוסף prefix")
        return None

    logger.info(
        f"Additional attendee parsed successfully: {sanitize_for_log(attendee)}"
    )
    return attendee


def parse_phone_number(content: str) -> Optional[str]:
    """Parse phone number from content. Returns None if invalid."""
    # Support both Israeli 05x and international +972-5x formats
    phone_pattern = compile(r"(05[0-9]|\+972-5[0-9])-?[0-9]{7}")
    phone_match = phone_pattern.search(content)
    if not phone_match:
        return None

    # Remove dashes and convert +972-5x to 05x format
    phone = phone_match.group(0).replace("-", "")
    if phone.startswith("+9725"):
        phone = "0" + phone[4:]  # Convert +9725x to 05x
    return phone


def is_email(content: str) -> bool:
    """Check if content is a valid email address."""
    # Simple regex validation: basic email format check
    return bool(search(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", content))


def parse_additional_attendee(content: str) -> Optional[Dict[str, str]]:
    """Parse additional attendee info from content, with or without forwarding marker."""
    logger.debug("Starting additional attendee parsing")

    # First try to find forwarding marker
    marker_result = find_forwarding_marker(content)

    if marker_result:
        # Use the original logic when marker is present
        marker_pos, used_marker = marker_result
        logger.debug(
            f"Found forwarding marker '{used_marker}' at position {marker_pos}"
        )

        # The marker position is in the decoded content, so we need to decode first
        decoded_content = decode_base64_content(content)

        # Find the marker in the decoded content
        marker_pos_in_decoded = decoded_content.find(used_marker)
        if marker_pos_in_decoded == -1:
            logger.debug("Marker not found in decoded content")
            return None

        # Extract pre-forwarded content from decoded content
        pre_forwarded_content = decoded_content[:marker_pos_in_decoded].strip()
        logger.debug(f"Pre-forwarded content length: {len(pre_forwarded_content)}")

        # Parse attendee from decoded content
        result = parse_attendee_from_content(pre_forwarded_content)
        if result:
            return result

    # Fallback: if no forwarding marker or parsing failed, try parsing entire content
    logger.debug("No forwarding marker found or parsing failed, trying entire content")

    # Decode base64 content if present
    decoded_content = decode_base64_content(content)

    # Try to parse ADD lines from the entire decoded content
    result = parse_attendee_from_content(decoded_content)
    if result:
        logger.debug("Successfully parsed additional attendee from entire content")
        return result

    logger.debug("No additional attendee found in any content")
    return None


def extract_forwarded_content(decoded_html: str) -> str:
    """Extract content after forwarded message marker."""
    for marker in FORWARDING_MARKERS:
        marker_pos = decoded_html.find(marker)
        if marker_pos != -1:
            return decoded_html[marker_pos + len(marker) :]

    # Fallback: use entire content if no marker found
    return decoded_html


def parse_email(content: str) -> Dict[str, str]:
    logger.debug(
        f"Email content preview: {sanitize_for_log(content[:EMAIL_PREVIEW_LENGTH])}"
    )

    # Extract From address from headers only
    from_address = extract_forwarder_email(content)
    logger.debug(f"From address: {sanitize_for_log(from_address)}")

    # Check if this is from a supported domain
    if not any(domain in content for domain in SUPPORTED_DOMAINS):
        raise ValueError(
            f"Email not from supported domain. Supported: {SUPPORTED_DOMAINS}"
        )

    logger.debug("Found supported domain email")
    details = {"from": from_address}

    # Decode HTML content
    decoded_html = decode_html_content(content)
    if not decoded_html:
        raise ValueError("Failed to decode HTML content from email")

    logger.debug(
        f"Decoded HTML: {sanitize_for_log(decoded_html[:DECODED_HTML_PREVIEW_LENGTH])}"
    )

    # Parse additional attendee from raw email content (before HTML decoding)
    additional_attendee: Optional[Dict[str, str]] = parse_additional_attendee(content)
    if additional_attendee:
        details["additional_name"] = additional_attendee.get("name", "")
        details["additional_email"] = additional_attendee.get("email", "")
        details["additional_phone"] = additional_attendee.get("phone", "")
        logger.debug(
            f"Additional attendee found: {sanitize_for_log(additional_attendee)}"
        )

    # Extract meeting details
    meeting_data = extract_meeting_details(decoded_html)
    details.update(meeting_data)

    logger.debug(f"Final details: {sanitize_for_log(details)}")
    if len(details) < MIN_MEETING_FIELDS:
        raise ValueError(
            f"Insufficient meeting details found. Got {len(details)}, need {MIN_MEETING_FIELDS}"
        )
    return details


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
    consultant_name = extract_consultant_name(details.get("from", ""))

    # Choose template based on whether there's an additional attendee (regardless of phone duplicates)
    additional_name_value = details.get("additional_name", "")
    has_additional_attendee = (
        "additional_name" in details
        and additional_name_value
        and additional_name_value.strip()
    )

    if has_additional_attendee:
        # Build combined name for couple template
        client_name = details.get("client", "")
        additional_name = details.get("additional_name", "")
        combined_client = f"{client_name} ו{additional_name}"
        template = WHATSAPP_MESSAGE_TEMPLATE
        logger.debug(f"Using couple template for: {sanitize_for_log(combined_client)}")
    else:
        combined_client = details.get("client", "")
        template = WHATSAPP_MESSAGE_TEMPLATE_SINGLE
        logger.debug(f"Using single template for: {sanitize_for_log(combined_client)}")

    return template.format(
        client=combined_client,
        day_name=day_name,
        date=details.get("date", "").replace("/", "."),
        time=details.get("time", ""),
        consultant_name=consultant_name,
    )


def generate_whatsapp_links(details: Dict[str, str], whatsapp_text: str) -> List[str]:
    """Generate WhatsApp links for all recipients with phone numbers."""
    links = []

    # Main client phone
    main_phone = details.get("phone", "").replace("-", "").replace(" ", "")
    if main_phone and main_phone.isdigit() and len(main_phone) >= 9:
        if main_phone.startswith("0"):
            main_phone = "972" + main_phone[1:]  # Convert Israeli 0xx to +972xx
        links.append(f"https://wa.me/{main_phone}?text={quote(whatsapp_text)}")

    # Additional attendee phone
    additional_phone = (
        details.get("additional_phone", "").replace("-", "").replace(" ", "")
    )
    if additional_phone and additional_phone.isdigit() and len(additional_phone) >= 9:
        if additional_phone.startswith("0"):
            additional_phone = (
                "972" + additional_phone[1:]
            )  # Convert Israeli 0xx to +972xx
        # Only add if different from main phone
        if additional_phone != main_phone:
            links.append(
                f"https://wa.me/{additional_phone}?text={quote(whatsapp_text)}"
            )

    return links


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

    # Build subject with client name(s)
    client_name = details.get("client", "")
    additional_name = details.get("additional_name", "")
    if additional_name:
        client_name = f"{client_name} ו{additional_name}"

    subject = f"פעמונים - שיחת הכוון בזום - {client_name}"

    # Build attendees list
    attendees_list = [email_address]

    # Add main client email
    client_email = details.get("email", "")
    if client_email:
        attendees_list.append(client_email)

    # Add additional attendee email
    additional_email = details.get("additional_email", "")
    if additional_email and additional_email not in attendees_list:
        attendees_list.append(additional_email)

    attendees = ",".join(attendees_list)

    return f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={quote(subject)}&dates={start_time}/{end_time}&add={attendees}&details={quote(whatsapp_text)}"


def send_email_notification(
    email_address: str,
    whatsapp_links: List[str],
    calendar_link: str,
    details: Dict[str, str],
    ses: Any,
) -> None:
    """Send email notification with meeting details and links."""
    # Format WhatsApp links with labels
    if len(whatsapp_links) > 1:
        whatsapp_section = f"📱 WhatsApp {details.get('client', '')}: {whatsapp_links[0]}\n📱 WhatsApp {details.get('additional_name', '')}: {whatsapp_links[1]}"
    elif whatsapp_links:
        whatsapp_section = f"📱 WhatsApp: {whatsapp_links[0]}"
    else:
        whatsapp_section = "📱 WhatsApp: לא זמין"

    # Build attendee info
    attendee_info = f"👤 לקוח: {sanitize_for_log(details.get('client', ''))}"
    if details.get("phone"):
        attendee_info += f"\n📱 טלפון: {sanitize_for_log(details.get('phone', ''))}"
    if details.get("email"):
        attendee_info += f"\n📧 אימייל: {sanitize_for_log(details.get('email', ''))}"

    # Add additional attendee if present
    additional_name = details.get("additional_name", "")
    if additional_name and additional_name.strip():
        attendee_info += f"\n\n👥 משתתף נוסף: {additional_name.strip()}"

        # Check for duplicate phone
        additional_phone = details.get("additional_phone", "")
        main_phone = details.get("phone", "")
        if additional_phone:
            if additional_phone.replace("-", "") == main_phone.replace("-", ""):
                attendee_info += f"\n📱 טלפון: {additional_phone} (כפול)"
            else:
                attendee_info += f"\n📱 טלפון: {additional_phone}"

        # Check for duplicate email
        additional_email = details.get("additional_email", "")
        main_email = details.get("email", "")
        if additional_email:
            if additional_email == main_email:
                attendee_info += f"\n📧 אימייל: {additional_email} (כפול)"
            else:
                attendee_info += f"\n📧 אימייל: {additional_email}"

    body = f"""שלום,

קישורים שימושיים:
{whatsapp_section}
📅 הוסף ליומן: {calendar_link}

אישור פגישה:
📅 תאריך: {sanitize_for_log(details.get("date", ""))}
🕐 שעה: {sanitize_for_log(details.get("time", ""))}
{attendee_info}

בהצלחה!"""

    # Build additional attendee HTML section
    additional_attendee_html = ""
    additional_name = details.get("additional_name", "")
    if additional_name and additional_name.strip():
        additional_attendee_html = (
            f"<br><br>משתתף נוסף:<br>👤 לקוח: {escape(additional_name.strip())}<br>"
        )

        # Add phone with duplicate check
        additional_phone = details.get("additional_phone", "")
        main_phone = details.get("phone", "")
        if additional_phone:
            if additional_phone.replace("-", "") == main_phone.replace("-", ""):
                additional_attendee_html += (
                    f"📱 טלפון: {escape(additional_phone)}(כפול)<br>"
                )
            else:
                additional_attendee_html += f"📱 טלפון: {escape(additional_phone)}<br>"
        else:
            additional_attendee_html += "📱 טלפון: חסר<br>"

        # Add email with duplicate check
        additional_email = details.get("additional_email", "")
        main_email = details.get("email", "")
        if additional_email:
            if additional_email == main_email:
                additional_attendee_html += (
                    f"📧 אימייל: {escape(additional_email)}(כפול)"
                )
            else:
                additional_attendee_html += f"📧 אימייל: {escape(additional_email)}"
        else:
            additional_attendee_html += "📧 אימייל: חסר"

    # Build HTML WhatsApp links section
    if len(whatsapp_links) > 1:
        whatsapp_links_html = f'📱 <a href="{escape(whatsapp_links[0])}" style="color: #25D366; text-decoration: underline; font-weight: bold;">WhatsApp {escape(details.get("client", ""))}</a><br>\n📱 <a href="{escape(whatsapp_links[1])}" style="color: #25D366; text-decoration: underline; font-weight: bold;">WhatsApp {escape(details.get("additional_name", ""))}</a>'
    elif whatsapp_links:
        whatsapp_links_html = f'📱 <a href="{escape(whatsapp_links[0])}" style="color: #25D366; text-decoration: underline; font-weight: bold;">שלח תזכורת WhatsApp</a>'
    else:
        whatsapp_links_html = "📱 WhatsApp: לא זמין"

    html_body = HTML_EMAIL_TEMPLATE.format(
        whatsapp_links_html=whatsapp_links_html,
        calendar_link=escape(calendar_link),
        date=escape(details.get("date", "")),
        time=escape(details.get("time", "")),
        client=escape(details.get("client", "")),
        phone=escape(details.get("phone", "")),
        email=escape(details.get("email", "")),
        additional_attendee_html=additional_attendee_html,
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
    whatsapp_text = generate_whatsapp_text(details)
    whatsapp_links = generate_whatsapp_links(details, whatsapp_text)
    calendar_link = generate_calendar_link(details, email_address, whatsapp_text)
    send_email_notification(email_address, whatsapp_links, calendar_link, details, ses)
