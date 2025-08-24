# 🔧 Manual Email Verification - Administrator Instructions

## 🎯 **Overview**

This document explains how to manually verify user email addresses in AWS SES so they can use MeetingFlow. This is a manual process to ensure security and control over system access.

## 📋 **Prerequisites**

- **AWS CLI configured** with appropriate permissions
- **SES access** to the `eu-west-1` region
- **Administrator role** for MeetingFlow

## 🔧 **Step-by-Step Verification Process:**

### **Step 1: Receive User Request**
- User contacts you requesting email verification
- User provides their email address
- Verify the request is legitimate

### **Step 2: Verify Email in AWS SES**

#### **Option A: Using AWS CLI (Recommended)**
```bash
# Replace user@example.com with the actual email address
aws ses verify-email-identity \
  --email-address user@example.com \
  --region eu-west-1
```

#### **Option B: Using AWS Console**
1. Go to [AWS SES Console](https://console.aws.amazon.com/ses/)
2. Select `eu-west-1` region
3. Click on "Identities" in the left sidebar
4. Click "Create identity"
5. Select "Email address"
6. Enter the user's email address
7. Click "Create identity"

### **Step 3: User Receives Verification Email**
- AWS SES automatically sends a verification email to the user
- User clicks the verification link in the email
- Email address becomes verified in SES

### **Step 4: Confirm Verification Status**
```bash
# Check if email is verified
aws ses get-identity-verification-attributes \
  --identities user@example.com \
  --region eu-west-1
```

**Expected Response:**
```json
{
  "VerificationAttributes": {
    "user@example.com": {
      "VerificationStatus": "Success",
      "VerificationToken": "..."
    }
  }
}
```

### **Step 5: Notify User**
- Send confirmation to user that their email is verified
- Inform them they can now use MeetingFlow
- Provide any additional instructions if needed

## 📧 **Example Admin Response Email:**

```
Subject: Your MeetingFlow Email Verification is Complete

Hi [User Name],

Your email address (user@example.com) has been verified and you can now use MeetingFlow.

To get started:
1. Send your meeting request email to [MeetingFlow Email Address]
2. MeetingFlow will process your request automatically
3. You'll receive a response with meeting details and calendar links

If you have any questions, please let me know.

Best regards,
[Admin Name]
```

## 🔍 **Verification Status Commands:**

### **Check Single Email:**
```bash
aws ses get-identity-verification-attributes \
  --identities user@example.com \
  --region eu-west-1
```

### **List All Verified Emails:**
```bash
aws ses list-identities \
  --identity-type EmailAddress \
  --region eu-west-1
```

### **Check Multiple Emails:**
```bash
aws ses get-identity-verification-attributes \
  --identities user1@example.com user2@example.com \
  --region eu-west-1
```

## ⚠️ **Important Notes:**

- **Verification is permanent** - once verified, email stays verified
- **One email per verification** - each email address must be verified separately
- **No automatic verification** - all verifications must be done manually
- **Monitor for abuse** - only verify legitimate user requests

## 🚨 **Troubleshooting:**

### **Email Already Verified:**
```bash
# If you get an error about email already being verified
aws ses get-identity-verification-attributes \
  --identities user@example.com \
  --region eu-west-1
```

### **Permission Denied:**
- Ensure your AWS credentials have SES permissions
- Check if you're in the correct AWS account and region

### **Verification Email Not Sent:**
- Check SES sending limits
- Verify the email address format is correct
- Check CloudWatch logs for errors

## 📊 **Monitoring and Maintenance:**

### **Regular Tasks:**
- Monitor verification requests
- Track verified email addresses
- Review and clean up if needed

### **Security Considerations:**
- Only verify legitimate user requests
- Keep verification process secure
- Document all verifications for audit purposes

---

*Last updated: [Date]*
*Document version: 1.0*
*For MeetingFlow administrators only*
