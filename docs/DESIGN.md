# Meeting Automation Service: Design Document

## 📄 Document Metadata

| Field | Value |
| :--- | :--- |
| **Title** | Meeting Automation Service Design |
| **Version** | 0.4 |
| **Status** | Ready for Implementation |
| **Owner** | [Name] |
| **Last Updated** | August 18, 2025 |
| **Scope** | System architecture and MVP definition |

---

## **System Architecture**

### **Current Implementation**
**Email Flow:** yoman.co.il email → Gmail forwarding → SES → S3 → Lambda → Reply email

**Components:**
- **AWS SES**: Receives forwarded emails at `receive@receive.hechven.online`
- **S3 Bucket**: Temporary email storage
- **Lambda Function**: Parses emails, generates replies, cleans up S3
- **User Identification**: Via `From:` field in forwarded emails

### **Future Architecture**
- Web app with Google OAuth, DynamoDB storage, user dashboard
- Google Meet creation, automated Gmail forwarding setup

**Note**: This design differs from the original ARCHITECTURE.md document, which described a more complex SQS-based flow. The current implementation prioritizes simplicity and user control while maintaining all core functional requirements.

---

## **MVP Definition**

### **Scope: Email Reply MVP**
**Flow:** yoman.co.il email → Gmail forwarding → SES → S3 → Lambda → Reply email → S3 cleanup

### **What It Does:**
1. **Receives** forwarded yoman.co.il emails via SES
2. **Parses** meeting details (date, time, client name, phone)
3. **Sends reply email** with meeting confirmation and helpful links
4. **Cleans up** processed emails from S3

### **Reply Email Contains:**
- Meeting confirmation details
- `wa.me` link with pre-filled WhatsApp reminder
- Google Calendar "Add to Calendar" link

### **Infrastructure Components:**
- S3 bucket for temporary email storage
- Lambda function for processing
- SES configuration for receiving and sending
- CloudWatch monitoring and alerts

### **MVP Limitations:**
- Manual Gmail forwarding setup
- No deduplication (duplicate forwards = duplicate replies)
- No automatic video meeting creation
- Basic error handling (no reply = failed)

---

## **Future Development**

### **Web Application**
- User dashboard with Google OAuth
- Meeting management interface
- Multi-user data isolation

### **Full Automation**
- Automatic Google Meet creation
- Automated Gmail forwarding setup
- WhatsApp Business API integration

---

## **Security & Privacy**

### **User Data Isolation**
- **Email Security**: Users only see meetings from their own Gmail account
- **Identification**: Via `From:` field in forwarded emails
- **Multi-tenant**: DynamoDB partitioning by user email address

### **Data Controls**
- **Retention Policy**: 2-year automatic cleanup
- **User Rights**: Delete account, delete individual meetings, export data
- **Privacy**: GDPR-compliant approach (stronger than required)