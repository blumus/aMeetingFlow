# TODO List - aMeetingFlow

## Current MVP Tasks (from PLAN.md)

### **4. SAM Infrastructure Updates**
- [ ] S3 bucket for email storage
- [ ] SES receipt rule → S3 storage  
- [ ] Lambda permissions (S3 read/delete, SES send)
- [ ] CloudWatch log groups

### **5. Terraform Updates**
- [ ] SES sending configuration
- [ ] Domain verification for outbound emails
- [ ] Required IAM permissions

### **6. Lambda Function**
- [x] Email parsing from S3
- [x] Reply email generation with meeting details
- [x] `wa.me` link creation
- [x] Google Calendar link creation
- [x] S3 cleanup after processing

### **7. Monitoring & Alerts**
- [ ] CloudWatch alerts for parsing failures
- [ ] CloudWatch alerts for Lambda timeouts
- [ ] Log retention policies

### **8. End-to-End Testing**
- [ ] Forward test yoman.co.il email
- [ ] Verify reply email received with correct links
- [ ] Confirm S3 cleanup works
- [ ] Test error scenarios

## New Feature: Automatic Email Verification

### **9. Email Verification Detection**
- [ ] Check if sender email is verified in SES before sending reply
- [ ] Detect unverified emails and trigger verification process
- [ ] Store verification status in DynamoDB or S3
- [ ] Handle verification pending state

### **10. Automatic Verification Process**
- [ ] Auto-initiate SES email verification for new addresses
- [ ] Send verification email via SES VerifyEmailIdentity API
- [ ] Track verification status with SES GetIdentityVerificationAttributes
- [ ] Retry verification if needed

### **11. Semi-Automatic Fallback**
- [ ] Send notification to admin when auto-verification fails
- [ ] Provide manual verification trigger via email/webhook
- [ ] Queue unverified emails for later processing
- [ ] Admin dashboard/email for managing verifications

### **12. Lambda Function Updates**
- [ ] Add verification check before sending replies
- [ ] Implement verification workflow in Lambda
- [ ] Add retry logic for verification process
- [ ] Handle verification errors gracefully
- [ ] Queue emails during verification process

### **13. Infrastructure Updates**
- [ ] Add DynamoDB table for verification tracking
- [ ] Add SES verification permissions to Lambda role
- [ ] Add CloudWatch alarms for verification failures
- [ ] Add dead letter queue for failed verifications

### **14. Testing**
- [ ] Test with unverified email addresses
- [ ] Test verification process end-to-end
- [ ] Test queuing and retry mechanisms
- [ ] Test admin notifications
- [ ] Test verification status tracking

## New Feature: Lambda Error Handling & Notifications

### **15. Error Notification System**
- [ ] Send error email to user when Lambda fails (if email verified)
- [ ] Send error email to admin when user email not verified
- [ ] Include failure reason and debug info in error emails
- [ ] Clean up S3 object after sending error notification
- [ ] Format error emails with readable debug information

### **16. Lambda Function Updates**
- [ ] Add comprehensive error handling wrapper
- [ ] Capture detailed error context and stack traces
- [ ] Implement error email templates
- [ ] Add S3 cleanup in error scenarios
- [ ] Log errors to CloudWatch before sending notifications

### **17. Error Email Templates**
- [ ] User error email template (when verified)
- [ ] Admin error email template (when user not verified)
- [ ] Include original email details in error notification
- [ ] Add troubleshooting steps in error emails

### **18. Testing**
- [ ] Test error notifications with verified emails
- [ ] Test admin notifications with unverified emails
- [ ] Test S3 cleanup on errors
- [ ] Test error email formatting
- [ ] Test various failure scenarios