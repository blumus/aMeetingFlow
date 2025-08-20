import json
from boto3 import client
import re
from datetime import datetime
from urllib.parse import quote
import html
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
    try:
        # Initialize clients inside handler for better connection management
        s3 = client('s3')
        ses = client('ses')
        
        # Get S3 object details from S3 event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # Get email content from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        email_content = response['Body'].read().decode('utf-8')
        
        # Parse email
        meeting_details = parse_email(email_content)
        if not meeting_details:
            logger.info("No meeting details found")
            return {'statusCode': 200}
        
        # Send reply
        send_reply(meeting_details, ses)
        
        # Clean up S3
        s3.delete_object(Bucket=bucket, Key=key)
        
        return {'statusCode': 200}
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {'statusCode': 500}

def decode_html_content(content: str) -> Optional[str]:
    from quopri import decodestring
    
    html_match = re.search(r'Content-Type: text/html[^\r\n]*\r?\nContent-Transfer-Encoding: base64\r?\n\r?\n([^-]+)', content, re.DOTALL)
    if html_match:
        base64_content = html_match.group(1).replace('\n', '').replace('\r', '')
        logger.info(f"Base64 HTML content found: {base64_content[:100]}")
        try:
            from base64 import b64decode
            return b64decode(base64_content).decode('utf-8')
        except Exception as e:
            logger.error(f"Error decoding base64: {e}")
            return None
    
    html_match = re.search(r'Content-Type: text/html[^\r\n]*\r?\n[^\r\n]*\r?\n\r?\n([^\r\n-]+)', content, re.DOTALL | re.MULTILINE)
    if html_match:
        html_content = html_match.group(1)
        logger.info(f"Quoted-printable HTML content found: {html_content[:200]}")
        try:
            return decodestring(html_content).decode('utf-8')
        except Exception as e:
            logger.error(f"Error decoding quoted-printable: {e}")
            return None
    
    logger.warning("No HTML content found - both regexes failed")
    return None

def extract_meeting_details(decoded_html: str) -> Dict[str, str]:
    details = {}
    
    # Extract date
    date_match = re.search(r'(\d{1,2}) ([^\s]+) (\d{4}) בשעה (\d{1,2}:\d{2})', decoded_html)
    if date_match:
        day, month_heb, year, time = date_match.groups()
        logger.info(f"Date match: {date_match.groups()}")
        month_map = {'יולי': '07', 'אוגוסט': '08', 'ספטמבר': '09'}
        month = month_map.get(month_heb, '01')
        details['date'] = f"{day.zfill(2)}/{month}/{year}"
        details['time'] = time
    
    # Extract client name
    client_match = re.search(r'פרטי קשר: <b>([^<]+)</b>', decoded_html)
    if client_match:
        details['client'] = client_match.group(1)
        logger.info(f"Client found: {details['client']}")
    
    # Extract phone
    phone_match = re.search(r'נייד: ([0-9]+)', decoded_html)
    if phone_match:
        details['phone'] = phone_match.group(1)
        logger.info(f"Phone found: {details['phone']}")
    
    # Extract client email
    email_match = re.search(r'דוא&quot;ל: <a href="mailto:([^"]+)"', decoded_html)
    if email_match:
        details['email'] = email_match.group(1)
        logger.info(f"Client email found: {details['email']}")
    
    return details

def parse_email(content: str) -> Optional[Dict[str, str]]:
    logger.info(f"Email content preview: {content[:500]}")
    
    # Extract From address for reply
    from_match = re.search(r'From: ([^\n]+)', content)
    if not from_match:
        logger.error("No From address found")
        return None
    
    from_address = from_match.group(1).strip()
    logger.info(f"From address: {from_address}")
    
    # Check if this is a yoman.co.il email
    if 'yoman.co.il' not in content and 'tagatime.com' not in content:
        logger.info("Not a yoman.co.il email")
        return None
    
    logger.info("Found yoman.co.il email")
    details = {'from': from_address}
    
    # Decode HTML content
    decoded_html = decode_html_content(content)
    if not decoded_html:
        return details
    
    logger.info(f"Decoded HTML: {decoded_html[:300]}")
    
    # Extract meeting details
    meeting_data = extract_meeting_details(decoded_html)
    details.update(meeting_data)
    
    logger.info(f"Final details: {details}")
    return details if len(details) > 2 else None

def send_reply(details: Dict[str, str], ses: Any) -> None:
    # Generate WhatsApp link with +972 prefix
    phone = details.get('phone', '').replace('-', '').replace(' ', '')
    if phone.startswith('0'):
        phone = '972' + phone[1:]  # Replace leading 0 with 972
    # Calculate day of week
    from datetime import datetime
    date_parts = details.get('date', '').split('/')
    day_name = ''
    if len(date_parts) == 3:
        day, month, year = date_parts
        try:
            date_obj = datetime(int(year), int(month), int(day))
            hebrew_days = ['יום שני', 'יום שלישי', 'יום רביעי', 'יום חמישי', 'יום שישי', 'שבת', 'יום ראשון']
            day_name = hebrew_days[date_obj.weekday()]
        except (ValueError, TypeError, IndexError) as e:
            logger.error(f"Error parsing date {day}/{month}/{year}: {e}")
            day_name = ''
    
    whatsapp_text = f"שלום {details.get('client', '')},\nרק רציתי להזכיר לכם ששיחת ההכוון שלנו תתקיים ב{day_name}, {details.get('date', '').replace('/', '.')}, בשעה {details.get('time', '')}.\n\nבמהלך השיחה אציג לכם את ארגון פעמונים ואת הכלים שאנו מציעים להתנהלות כלכלית נכונה. תהיה לכם הזדמנות לשתף אותי באתגרים ובמטרות הכלכליות שלכם, ונסיים את השיחה בתכנון צעדים ראשוניים להמשך התהליך.\n\nחשוב:\n- חשוב מאוד ששניכם תיקחו חלק בשיחה.\n- אם השעה אינה מתאימה - אשמח שתעדכנו מראש.\n- מומלץ להיות במקום שקט, ללא הפרעות, כדי שנוכל להתמקד בצורה מיטבית.\n\nמצפה לשיחה שלנו,\nברוך ליימן\nיועץ הכוון מטעם פעמונים"
    whatsapp_link = f"https://wa.me/{phone}?text={quote(whatsapp_text)}"
    
    # Generate calendar link with proper date format and 1-hour duration
    date_parts = details.get('date', '').split('/')  # Split DD/MM/YYYY
    time_parts = details.get('time', '').split(':')  # Split HH:MM
    client_name = details.get('client', '')
    if len(date_parts) == 3 and len(time_parts) == 2:
        day, month, year = date_parts
        hour, minute = time_parts
        start_time = f"{year}{month.zfill(2)}{day.zfill(2)}T{hour.zfill(2)}{minute.zfill(2)}00"
        # Add 1 hour for end time
        end_hour = str(int(hour) + 1).zfill(2)
        end_time = f"{year}{month.zfill(2)}{day.zfill(2)}T{end_hour}{minute.zfill(2)}00"
        subject = f"פעמונים - שיחת הכוון בזום - {client_name}"
        # Extract just email from 'Baruch L <email@domain.com>' format
        attendee_email = details['from']
        if '<' in attendee_email and '>' in attendee_email:
            attendee_email = attendee_email.split('<')[1].split('>')[0]
        
        # Add client email if available (from parsed email content)
        client_email = details.get('email', '')
        attendees = attendee_email
        if client_email:
            attendees = f"{attendee_email},{client_email}"
        
        calendar_link = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={quote(subject)}&dates={start_time}/{end_time}&add={attendees}&details={quote(whatsapp_text)}"
    else:
        calendar_link = "#invalid-date"
    
    # Email body - links moved to beginning
    body = f"""שלום,

קישורים שימושיים:
📱 WhatsApp: {whatsapp_link}
📅 הוסף ליומן: {calendar_link}

אישור פגישה:
📅 תאריך: {details.get('date', '')}
🕐 שעה: {details.get('time', '')}
👤 לקוח: {details.get('client', '')}
📱 טלפון: {details.get('phone', '')}
📧 אימייל: {details.get('email', '')}

בהצלחה!"""
    
    # Extract just email from 'Baruch L <email@domain.com>' format
    to_email = details['from']
    if '<' in to_email and '>' in to_email:
        to_email = to_email.split('<')[1].split('>')[0]
    
    # Create HTML version with clickable links (HTML escape user input) - links moved to beginning
    html_body = f"""<html><body style="font-family: Arial, sans-serif; direction: rtl;">
<p>שלום,</p>

<p><strong>קישורים שימושיים:</strong></p>
<p>📱 <a href="{whatsapp_link}" style="color: #25D366; text-decoration: underline; font-weight: bold;">שלח תזכורת WhatsApp</a><br>
📅 <a href="{calendar_link}" style="color: #4285F4; text-decoration: underline; font-weight: bold;">הוסף ליומן Google Calendar</a></p>

<p><strong>אישור פגישה:</strong></p>
<p>📅 תאריך: {html.escape(details.get('date', ''))}<br>
🕐 שעה: {html.escape(details.get('time', ''))}<br>
👤 לקוח: {html.escape(details.get('client', ''))}<br>
📱 טלפון: {html.escape(details.get('phone', ''))}<br>
📧 אימייל: {html.escape(details.get('email', ''))}</p>

<p>בהצלחה!</p>
</body></html>"""
    
    ses.send_email(
        Source='receive@receive.hechven.online',
        Destination={'ToAddresses': [to_email]},
        Message={
            'Subject': {'Data': 'אישור פגישה', 'Charset': 'UTF-8'},
            'Body': {
                'Text': {'Data': body, 'Charset': 'UTF-8'},
                'Html': {'Data': html_body, 'Charset': 'UTF-8'}
            }
        }
    )
