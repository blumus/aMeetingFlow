# 📘 Meeting Flow Spec – Version 1.2

## 📄 Document Metadata

| Field               | Value                        |
|---------------------|------------------------------|
| **Title**           | Meeting Flow Specification   |
| **Version**         | 1.3                          |
| **Status**          | In Progress                  |
| **Owner**           | Baruch                       |
| **Last Updated**    | August 11, 2025              |
| **Scope**           | Email-triggered meeting setup with Zoom and WhatsApp integration |
| **Audience**        | Engineering, Product, QA     |

---

## 🎯 Core Mission & Business Statement

### Current Manual Process
A financial advisor (יועץ הכוון) from Paamonim receives booking emails from yoman.co.il system with meeting details. The advisor then manually:

1. **Parses the booking email** containing:
   - Meeting date and time
   - Client name and contact details (phone, email)
   - Meeting type (individual or couple - not always specified)

2. **Creates a Zoom meeting** for the scheduled time

3. **Sends WhatsApp reminders** 2 days before the meeting:
   - Different templates for individuals vs couples
   - Includes meeting details and preparation instructions

### Sample Email (Translated)
```
Hello, a new call invitation has just been received from the yoman.co.il system - 
(Zoom guidance call - John Smith) scheduled for Tuesday, July 15, 2025 at 12:00
Branch: Financial Services Private
Contact: John Smith
Mobile: 05X-XXX-XXXX
Email: john.smith@example.com
For additional details: https://my.yoman.co.il/Site/[REDACTED]/Event/[REDACTED]/
Best regards, yoman.co.il system
```

### Sample WhatsApp Message (Translated)
```
Hello Lior and Sarah, I just wanted to remind you of the guidance call 
scheduled between us for Sunday, May 11th, at 18:00. During the call, I, 
John Davis, a financial advisor from Financial Services Organization, will present 
the organization and the services we offer. You'll have the opportunity to 
share with me your financial challenges and goals, and we'll end the call 
with planning initial steps for the continuation of the process.

🔔 Important:
✅ Both of your participation in the call is important for the success of the process.
✅ If you cannot participate at the scheduled time, I'd appreciate if you update me.
✅ It's recommended to be available and without interruptions during the call, 
   so we can focus optimally on your needs and goals.

Looking forward to our call on Sunday!
Best regards, John Davis
Financial Advisor, Financial Services Organization
```

### Automation Goal
**Replace this manual 3-step process with an automated flow** that:
- Detects and parses incoming yoman.co.il emails
- Automatically creates Zoom meetings
- Schedules and sends appropriate WhatsApp reminders based on participant count
- Provides a simple interface to manage and monitor the automated messages

---

## 🧩 Overview

This flow automates meeting setup based on incoming emails. It parses structured templates, extracts participant info and meeting time, and triggers Zoom invite creation and WhatsApp reminders. A simple UX allows users to manage scheduled messages.

---

## 📧 Email Parsing (US1)

### ✅ Assumptions
- Trigger fires **only** if email matches a known template
- Template reliably provides:
  - Meeting date and time
  - **First participant’s** name and contact info

### ❌ Edge Cases Not Considered
- Unrecognized format → no trigger
- Missing or ambiguous date/time → unlikely
- Multiple dates/times → unlikely

### ✅ Error Handling
- **None required**

---

## 👤 Participant Info (US2 & US3a)

### ✅ Assumptions
- **Only one participant’s info is extracted from the email**
- Second participant info is **never parsed** and must be entered manually
- System prompts user to confirm whether the meeting is single or couple

### ❌ Edge Cases Not Considered
- Missing second participant → **not an error**, part of normal flow
- Template mismatch → not possible

### ✅ Error Handling
- **Invalid phone/email format**  
  → “Please enter a valid phone number or email address.”

---

## 🕒 Meeting Time Validation (US3b)

### ✅ Assumptions
- Time is extracted from template
- Time zone is either specified or defaulted

### ❌ Edge Cases Not Considered
- Time zone ambiguity → unlikely

### ✅ Error Handling
- **Meeting time is in the past**  
  → “Meeting time must be in the future.”

---

## 🎥 Zoom Invite Creation (US5)

### ✅ Assumptions
- Zoom API is integrated and authenticated
- Meeting time and participants are valid

### ✅ Error Handling
- **Zoom API failure**  
  → “We couldn’t create the Zoom meeting. Try again or create manually.”

- **Missing Zoom credentials/token**  
  → “Zoom setup incomplete. Please check your integration settings.”

---

## 📲 WhatsApp Reminder (US6)

### ✅ Assumptions
- WhatsApp template is selected based on participant count
- Phone number is WhatsApp-enabled

### ✅ Error Handling
- **Phone number not WhatsApp-enabled**  
  → “This number may not be reachable via WhatsApp.”

- **Message delivery failure**  
  → “Reminder could not be sent. Please try again later.”

---

## 🧩 Template Selection Logic

- System determines template based on **user input**:
  - User confirms whether meeting is single or couple
  - 1 participant → single template
  - 2 participants → couple template

- ❌ Template mismatch should **never occur**

---

## 🗂️ Message Management UX

The system must provide a simple interface for managing scheduled messages.

### ✅ Capabilities
- **View messages**  
  - Show recipient, type (Zoom/WhatsApp), scheduled time, and status

- **Edit message**  
  - Allow changes to time, recipient, or content before delivery

- **Delete message**  
  - Cancel scheduled delivery

- **Manual actions**  
  - Resend or retry if needed

- **Status tracking**  
  - Show: pending, sent, failed

---

## 📊 Logging & Audit Trail

The system must log key actions and events for traceability and support.

### ✅ What to Log
- Email parsed: timestamp, template used, extracted fields
- Message scheduled: type, recipient, scheduled time
- Message sent: timestamp, delivery status, error (if any)
- Message edited/deleted: action type, timestamp
- Zoom invite created: meeting ID, time, participants

### 🛠️ Storage & Access
- Logs stored in backend with timestamps
- Accessible for support and troubleshooting
- Retained for a reasonable period (e.g., 30–90 days)

---

## ✅ Final Error Table

| Area             | Error Condition           | Message                                      |
|------------------|---------------------------|----------------------------------------------|
| Participant Info | Invalid phone/email       | “Please enter a valid phone number or email.”|
| Meeting Time     | Time is in the past       | “Meeting time must be in the future.”        |
| Zoom Invite      | API failure               | “Zoom meeting could not be created.”         |
| Zoom Invite      | Missing credentials       | “Zoom setup incomplete.”                     |
| WhatsApp         | Number not reachable      | “This number may not be reachable via WhatsApp.”|
| WhatsApp         | Delivery failure          | “Reminder could not be sent.”                |

---

## 🔐 Authentication & Access Control

### ✅ Assumptions
- System is **multi-user ready**, even if MVP starts with limited users
- Each user’s data is **isolated** — no cross-access
- An **admin user** can view and manage all data

### ✅ Requirements
- Authentication mechanism is **pluggable**:
  - Could be Google OAuth, email/password, or other provider
  - Should support secure login and session management
- All user-specific data is tagged with a `user_id`
- Admin dashboard provides visibility across all users

### ✅ Roles
| Role   | Permissions |
|--------|-------------|
| **Admin** | Full access to all data, users, and settings |
| **User**  | Access only to their own data |

### ❌ Not in Scope
- Advanced role hierarchies
- Team/group sharing
- Field-level permissions

---

## 🗄️ Data Storage

### ✅ Assumptions
- Data model includes:
  - Meeting records (date, time, participants)
  - User profiles (basic info, login method)
- **No specific storage tech chosen yet**
  - Should support tagging records by `user_id`
  - Ready for scaling to a few thousand users

### ❌ Not in Scope
- Schema design
- Storage optimization

---

## 🔐 Security

### ✅ Requirements
- **SSL/TLS encryption** for all data in transit
- Basic protection against unauthorized access
- **Audit logging** for:
  - Login attempts
  - Data changes
  - Admin actions

### ❌ Not in Scope
- End-to-end encryption
- Advanced threat detection

---

## 📈 Scalability

### ✅ Assumptions
- MVP targets ~100 users
- Should handle up to a few thousand without major rework

### ❌ Not in Scope
- Load balancing
- Horizontal scaling

---

## 🎨 UI/UX

### ✅ Assumptions
- Simple web interface for:
  - Users to view their own meetings
  - Admin to view all users and meetings
- Mobile-friendly layout is **nice to have**, not required

### ❌ Not in Scope
- Custom branding
- Accessibility compliance

---

## 🚀 Deployment & Ops

### ✅ Requirements
- Use **free or low-cost hosting** (e.g., Vercel, Firebase, Render)
- Basic monitoring and logging via free tier tools
- Error reporting via console logs or simple dashboard


### 🟡 Optional
- CI/CD pipelines (e.g., GitHub Actions)
- Infrastructure-as-code (e.g., Terraform)

---

## 🧪 Testing & Validation

### ✅ Requirements
- **Automated tests** for core logic
- **Email parsing** will have test cases and validation rules
  - Details to be defined later

### ❌ Not in Scope
- Full test coverage
- Performance testing