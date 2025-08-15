# 🏗️ Meeting Flow Architecture – Version 1.0

## 📄 Document Metadata

| Field               | Value                        |
|---------------------|------------------------------|
| **Title**           | Meeting Flow Architecture    |
| **Version**         | 1.0                          |
| **Status**          | In Progress                  |
| **Owner**           | Engineering Team             |
| **Last Updated**    | August 11, 2025              |
| **Scope**           | Technical architecture and implementation details |
| **Audience**        | Engineering, DevOps          |
| **Dependencies**    | Meeting Flow Specification v1.2 |

---

# System Architecture Document: Meeting Automation Service

**Version: v1.1**

***

### 1. Executive Summary

This document provides a final, comprehensive overview of the system architecture for a meeting automation service. The system's purpose is to automatically parse meeting-related emails, store the data, and send out notifications via Zoom and WhatsApp. The architecture is designed to be cost-effective and scalable for a small user base (1-20 users, with potential to grow to 200). The core principles of the design are privacy, security, and automation, all achieved through a serverless, event-driven pattern on **Amazon Web Services (AWS)**.

***

### 2. Architectural Pattern: Gmail API Forwarding & Serverless Processing

The foundation of the architecture is a two-service model that ensures the core parsing logic is completely decoupled from the user's personal inbox. The backend services are built as serverless functions, communicating asynchronously via **AWS SQS** (Simple Queue Service).

* **Non-Intrusive Design:** The system operates by processing emails from a dedicated, service-owned inbox. A filter in the user's personal Gmail account forwards only the relevant meeting emails to this inbox, ensuring the service never has access to personal data without explicit permission.
* **Decoupled Services:** Each service has a single responsibility and is independent of the others, which enhances resilience and allows for simple, linear scalability.

***

### 3. System Components

#### A. Email Parser Service (Core Component)

* **Purpose:** To parse meeting details from forwarded emails.
* **Trigger:** **AWS SQS**. The dedicated service inbox sends a message to an SQS queue for each new email.
* **Execution Environment:** **AWS Lambda**.
* **Data Flow:**
    1.  The Lambda function is triggered by an SQS message.
    2.  It fetches the email content from the dedicated service inbox, which it has been granted permissions to access. **It does not use the Gmail API to access the user's personal inbox.**
    3.  It uses regular expressions to extract key data: meeting date, time, and participant information.
    4.  The extracted data, along with the organizer's personal phone number (as all users are assumed to have opted in), is compiled into a structured JSON payload.
    5.  This payload is published to a new SQS queue, which triggers the next service.

#### B. Meeting Management Service (Core Component)

* **Purpose:** To store, manage, and facilitate notifications for meetings. This service is a single, serverless entity that contains multiple Lambda functions.
* **Architectural Style:** Event-driven, serverless.
* **Data Flow:**
    1.  A **Lambda function** is triggered by the parsed data from the `Email Parser Service`.
    2.  It stores the meeting data, including the organizer's personal WhatsApp number, in **Amazon DynamoDB**.
    3.  A separate **Lambda function**, triggered daily by **AWS EventBridge**, performs the notification logic.
* **Notification Logic:**
    1.  The scheduled function queries DynamoDB for all meetings scheduled exactly two days in advance.
    2.  For each meeting, it retrieves the organizer's personal phone number and other meeting details.
    3.  It then uses the **Zoom API** to create a meeting.
    4.  The service constructs a message and uses a pre-approved WhatsApp template that embeds a `wa.me` link to the organizer's personal number, along with the Zoom link.
    5.  It sends this automated message to all recipients via the **WhatsApp Business Platform API**.
    6.  The service updates the meeting record in DynamoDB to mark the notifications as sent.
* **User Interface (UX):** A separate front-end application will communicate with a dedicated backend server to perform all read and write operations, which in turn will interact with DynamoDB. This architecture provides an additional layer of security and a central place for business logic.

#### C. Gmail API Forwarding Update Service (Optional)

* **Purpose:** To programmatically create a forwarding rule in the user's personal Gmail account. This is the only service that interacts with the user's personal Gmail account and it is a standalone, optional service for a user-friendly setup.
* **Permissions:** It requests the limited `https://www.googleapis.com/auth/gmail.settings.basic` scope.

#### D. Zoom Integration (Free Plan)

* **Limitation:** The service will use a free Zoom account to generate meeting links. This means that meetings with **3 or more participants will have a 40-minute time limit**. This limitation will be a core part of the system's design and should be clearly communicated in the user interface. One-on-one meetings will not have this time limit.

***

### 4. Infrastructure as Code (IaC) with Terraform

For managing the AWS resources, the project will use **Terraform**.

* **Purpose:** Terraform will be used to define and provision all the cloud infrastructure required for the project in a declarative configuration file. This includes the Lambda functions, SQS queues, DynamoDB tables, and EventBridge rules.
* **Benefits:** This approach provides a repeatable and version-controlled environment. It ensures consistency across all development stages and simplifies future changes or disaster recovery.

***

### 5. CI/CD Workflow with GitHub Actions

GitHub Actions will be used to automate the deployment pipeline for the project.

* **Purpose:** The workflow serves as the "glue" that connects your source code repository to your AWS infrastructure.
* **Workflow:** Upon a `git push` or pull request, GitHub Actions will automatically perform continuous integration (CI) tasks like testing and Terraform validation. Once checks pass, it will run `terraform plan` and `terraform apply` to provision or update the AWS infrastructure and application code (continuous deployment or CD).
* **Security:** AWS access credentials will be securely stored in **GitHub Secrets** and will be used by the CI/CD workflow to authenticate with your AWS account.
* **Cost:** This is a cost-effective solution with a free tier of **2,000 runner minutes per month** for private repositories.

***

### 6. Security and Privacy Considerations

* **Privacy by Design:** The architecture ensures that no personal data is stored or processed without the user's assumed consent. The use of a dedicated inbox and the `wa.me` link approach ensures the system never has access to or control over a user's personal messaging accounts.
* **Data Isolation:** All meeting data is stored in a secure, isolated database (DynamoDB).
* **Least Privilege:** Each component operates with the minimal permissions necessary for its function.
* **User Control:** The use of the `wa.me` link puts the power in the hands of the organizer, who has a trusted communication method with the recipients. This fulfills the need for a direct communication channel while respecting user privacy.

***

### 7. Rejected Architectural and Implementation Ideas

This section outlines concepts that were considered and rejected to arrive at the final architecture.

* **Google Cloud Platform (GCP):** GCP was considered as an alternative, but AWS was chosen to leverage existing developer experience, which was deemed critical for a fast and efficient build.
* **Using Synchronous Communication:** The idea of using a synchronous API call between services was rejected in favor of the asynchronous SQS message queue, which provides greater resilience and scalability.
* **Using SMS for Notifications:** SMS was considered for its universal reach but was rejected because it lacks the rich UX and one-click conversation initiation that the WhatsApp `wa.me` link provides, which was a high priority for the project.
* **Direct Service Access to Personal WhatsApp:** This was considered to open a direct communication channel but was immediately rejected as a fundamental security and privacy violation. The final architecture uses an explicit opt-in to share a `wa.me` link instead.
* **Manual Infrastructure Setup:** The idea of manually creating all resources via the AWS console was considered for a faster MVP but was ultimately superseded by the decision to use Terraform for its long-term benefits in version control and consistency.

***

### 8. Future Enhancements (Not Implemented)

* **Gmail API Forwarding Update Service:** Automate the one-time setup process for non-technical users.
* **Resend and Cancel Event Functionality:** Add the ability for organizers to manage events from the UX.
* **Calendar Integration:** Automatically create and update events on a user's calendar.
* **Support for Other Platforms:** Expand the system to include other messaging services (e.g., Telegram) and video conferencing tools (e.g., Microsoft Teams).

***

### 9. Estimated Monthly Costs 💰

Here is a breakdown of the estimated monthly costs for the entire system, based on the AWS services and third-party APIs you've chosen. The good news is that for your initial user base, the cost will likely be minimal, if not zero.

* **AWS Services:** All core services (Lambda, DynamoDB, SQS, EventBridge) have generous free tiers. For your expected usage, the cost is approximately **$0 per month**.
* **Zoom Integration:** You are using the free Zoom plan, so the cost is **$0 per month**.
* **WhatsApp Business Platform API:** The free tier includes **1,000 free conversations per month**. For an expanded user base, costs might be in the range of **$10 - $20 per month** once the free conversations are used.

**Overall Cost Summary:** The total monthly cost will likely be **$0** for your initial user base.

***

### 10. Implicit Requirements (Suggested for Best Practices)

This section lists requirements that were not in the original specification but are included in the final architecture. These are **not formal requirements** but are strongly suggested for building a robust, secure, and maintainable system.

* **Cloud Provider and Specific Services:** The architecture specifies the use of **Amazon Web Services (AWS)** and specific services like **AWS Lambda, Amazon DynamoDB, AWS SQS, and AWS EventBridge**.
* **Infrastructure as Code (IaC):** The architecture requires the use of **Terraform** to manage infrastructure. The original requirement document listed IaC as "not in scope."
* **CI/CD Pipeline:** The architecture requires a CI/CD pipeline using **GitHub Actions**. The original requirement document also listed this as "not in scope."
* **Backend Server Layer:** The architecture includes a **backend server** to mediate all front-end and database interactions. This adds a crucial layer of security and centralizes business logic.