# 📧 Manual Email Verification - User Instructions

## 🎯 **What You Need to Do Before Using MeetingFlow**

MeetingFlow requires your email address to be verified before you can send meeting requests. This is a one-time process to ensure security and prevent abuse.

## 📋 **Step-by-Step Process:**

### **Step 1: Contact the Administrator**
- **Email:** [Admin Email Address]
- **Subject:** "Request Email Verification for MeetingFlow"
- **Include:** Your email address that you want to use with MeetingFlow

**Example:**
```
To: [Admin Email]
Subject: Request Email Verification for MeetingFlow

Hi,

I would like to use MeetingFlow. Please verify my email address:
user@example.com

Thank you!
```

### **Step 2: Wait for Verification**
- The administrator will verify your email address in the system
- This process typically takes 1-2 business days
- You will receive a verification email from Amazon SES

### **Step 3: Complete Verification**
- **Check your email** for a message from Amazon SES
- **Click the verification link** in the email
- **Confirm your email address** is now verified

### **Step 4: Start Using MeetingFlow**
- Once verified, you can send meeting request emails to MeetingFlow
- Your requests will be processed automatically
- No further verification needed for future requests

## ❓ **Frequently Asked Questions:**

### **Q: Why do I need email verification?**
A: Email verification ensures that only legitimate users can access MeetingFlow and prevents system abuse.

### **Q: How long does verification take?**
A: Typically 1-2 business days, depending on administrator availability.

### **Q: What if I don't receive a verification email?**
A: Check your spam folder first, then contact the administrator if you still don't receive it.

### **Q: Can I use a different email address?**
A: Yes, but you'll need to go through the verification process for each new email address.

### **Q: Is this a one-time process?**
A: Yes, once your email is verified, you can use MeetingFlow without further verification.

## 🚀 **How to Use MeetingFlow (After Verification):**

### **What MeetingFlow Does:**
MeetingFlow automatically processes your meeting request emails and creates:
- **Meeting summaries** with key details
- **WhatsApp links** for easy communication
- **Google Calendar links** for scheduling
- **Organized meeting information**

### **How to Send a Meeting Request:**

#### **Step 1: Compose Your Email**
- **To:** [MeetingFlow Email Address]
- **Subject:** Any subject (MeetingFlow will process the content)
- **Body:** Include your meeting details

#### **Step 2: Include Meeting Information**
MeetingFlow automatically extracts:
- **Meeting date and time**
- **Location or platform**
- **Attendees** (from email addresses)
- **Meeting purpose/agenda**

### **Step 2a: Including Additional Attendees (Optional)**
You can include additional attendees using special prefixes:

#### **Hebrew Format:**
```
הוסף יוסי כהן          ← Name found, attendee created
הוסף 0543333333        ← Phone added
הוסף sara@example.com  ← Email added
```

#### **English Format:**
```
ADD Yossi Cohen        ← Name found, attendee created
ADD 0543333333         ← Phone added
ADD sara@example.com   ← Email added
```

#### **Rules:**
- **Only ONE additional attendee** total per meeting
- **First ADD/הוסף line that contains a name** becomes the attendee
- **Any ADD lines before the name line** are ignored
- **After the name line**, subsequent ADD lines can only add phone/email to that person
- **No second name allowed** after first name is found
- **First phone/email wins** (duplicates ignored)

#### **Step 3: Send and Wait**
- Send your email to MeetingFlow
- You'll receive an automated response with:
  - Meeting summary
  - WhatsApp group link
  - Google Calendar event link
  - Any additional details

### **Example Meeting Request Email:**
```
To: paamonim@paamonim.hechven.online
Subject: ברגעים אלה התקבלה הזמנה חדשה לשיחה ממערכת yoman.co.il (שיחת הכוון בזום)

Date: August 24, 2025 at 14:00
Location: פועלים (Workers)
Party: אופיר (Ofir)
Phone: 050-XXX-XXXX
Email: organizer@example.com

Attendees: user1@example.com, user2@example.com, user3@example.com

Meeting details and agenda information...
```

**Note:** This example shows the actual Hebrew content and format that MeetingFlow processes, with personal information obscured for privacy.

### **What You'll Receive Back:**
```
MeetingFlow Response:

📅 Meeting Summary:
Date: 24/08/2025
Time: 14:00
Location: Organizer Name
Phone: 050-XXX-XXXX
Email: organizer@example.com

📱 WhatsApp Organizer: [Click to join WhatsApp chat]
📱 WhatsApp Attendee: [Click to join WhatsApp chat]
📅 Google Calendar: [Add to calendar]

MeetingFlow automatically processed your request and created the necessary links for easy coordination.
```

**Note:** MeetingFlow supports both Hebrew and English content, and will automatically detect the language and respond appropriately.

### **Tips for Best Results:**
- **Be specific** about date and time
- **Include all attendees** in the email
- **Mention location or platform** (Zoom, Teams, etc.)
- **Keep it simple** - MeetingFlow handles the rest

## 🆘 **Need Help?**

If you encounter any issues during the verification process, contact the administrator at [Admin Email Address].

For questions about using MeetingFlow after verification, contact the administrator or check the system documentation.

---

*Last updated: [Date]*
*Document version: 1.0*
