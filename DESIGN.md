# Meeting Automation Service: Design Document (WIP)

## 📄 Document Metadata

| Field | Value |
| :--- | :--- |
| **Title** | Meeting Automation Service Design |
| **Version** | 0.2 |
| **Status** | Work in Progress |
| **Owner** | [Name] |
| **Last Updated** | August 13, 2025 |
| **Scope** | Design decisions for initial project setup |

---

## 🚀 Phase 1: Setup & Email Parsing Service

### Summary of Requirements & Architecture for Phase 1

This phase focuses on the **Email Parser Service**, a core component of the system's architecture. The service is designed to be serverless and event-driven, operating on **Amazon Web Services (AWS)**.

The primary function of this service is to parse meeting details from forwarded emails. The system uses a non-intrusive design where relevant emails are forwarded from a user's personal Gmail account to a dedicated, service-owned inbox. The service itself never accesses the user's personal inbox.

The service is built on **AWS Lambda** and is triggered by messages from an **AWS SQS** queue. The Lambda function fetches the email content and uses regular expressions to extract key data points, such as the meeting date, time, and participant information. This data is then compiled into a structured JSON payload and published to another SQS queue.

To manage the AWS resources, the project will use **Terraform** for Infrastructure as Code (IaC). A CI/CD workflow will be implemented with **GitHub Actions** to automatically test and deploy the service.

### Task 1.1: Project Setup

* **Platform**: ClickUp is being used for project tracking and management. All project tasks are to be added to the board as cards.
* **Source Control**: A dedicated GitHub repository will be created for the project.
### Task 1.7.1: Set up Gmail Forwarding for POC

This task involves configuring the Gmail account to automatically forward incoming emails to a new, verified AWS SES address. This step will enable the flow of test emails into the AWS environment.



### Task 1.7.2: Configure AWS SES Receipt Rule

This task focuses on configuring an AWS Simple Email Service (SES) receipt rule to capture emails forwarded from Gmail and initiate the next action



### Task 1.7.3: Develop and Test the Lambda Function

This task is for the development and testing of the Lambda function itself. The function will be triggered by the SES receipt rule and should be designed to process the incoming email event.

===========
### AWS SES Email Reception Proof of Concept - Finalized Flow (tasks 1.7.x (all))

This  outlines a proof of concept (PoC) for setting up Gmail forwarding by using Amazon Simple Email Service (SES) to receive and process a verification email, then configuring a final rule to bounce incoming mail.

---

#### ** Goal**

The primary objective of this PoC was to demonstrate a workaround for Gmail's forwarding verification process using AWS SES. The specific steps were to:

* Receive the Gmail forwarding verification email at `meetings@example-domain.com`.
* Manually retrieve the verification link to approve the forwarding from Gmail.
* Validate that Gmail forwarding from a test address to `meetings@example-domain.com` is successfully configured.
* Reconfigure the SES rule to its final state,
    * **1.7.2*    * which is to bounce all emails to `meetings@example-domain.com`.
    * **1.7.3** Develop and Test S3
---

#### ** Setup and Configuration**

The following resources and configurations were used in this PoC:

* **AWS SES Identity:** `arn:aws:ses:eu-west-1:[REDACTED]:identity/example.domain.com`
    * This identity was created in the `eu-west-1` (Ireland) region.
    * Domain verification was completed by adding the following DNS records:
        * **MX:** `ses.example.online` → `inbound-smtp.eu-west-1.amazonaws.com`
        * **CNAME:** `a63dgsnbfiubgs73oor6byqjqizk2n3c._domainkey.ses.example.online` → `a63dgsnbfiubgs73oor6byqjqizk2n3c.dkim.amazonses.com`
        * **CNAME:** `ef6epa2owcleit5tewf5jph7zsvqexzm._domainkey.ses.example.online` → `ef6epa2owcleit5tewf5jph7zsvqexzm.dkim.amazonses.com`
        * **CNAME:** `m34fzhfs7fnb4lu2ulgxcxqwpwkbrkrm._domainkey.ses.example.online` → `m34fzhfs7fnb4lu2ulgxcxqwpwkbrkrm.dkim.amazonses.com`
        * **TXT:** `_dmarc.ses.example.online` → `v=DMARC1; p=none;`

* ** Initial Active Rule Set:** `example-domain-rules`
    * After the forwarding was verified, SES did a **`Bounce` action**. 
* ** Final Rule Set for Verification:** `example-domain-rules`
    * The rule was  configured with an **S3 bucket action** to receive the Gmail verification email to a bucket named `example-email-inbox`.
    * The verification link was manually retrieved from the S3 bucket to complete the Gmail forwarding setup.



---

#### ** Validation and Results**

The PoC successfully demonstrated the following:

* The initial SES rule was confirmed with an immediate bounce notification, confirming the initial state of the rule.
* After thatm a test email sent from Gmail to `meetings@example-domain.com` was successfully received in the S3 bucket.
* The confirmation link was manually extracted from the raw email file in S3, and Gmail forwarding was successfully activated.


---

#### ** Conclusion**

* The proof of concept successfully demonstrated a manual process for using AWS SES to receive and verify a forwarding address from Gmail. By temporarily using an S3 bucket to capture the verification email, it was possible to bypass the inability to access the destination mailbox directly. The final configuration ensures that any future emails can be processed. That automation of gmail forwarding will require additional steps to fully implement. At this stage, will not be pursued further.

* For this project (now), the direct SES -> Lambda rule is the most efficient. This avoids the complexity of an SNS topic, which acts as a pub/sub service for more scalable, multi-consumer systems. While SES -> SNS -> Lambda offers resilience and fan-out capability, it's unnecessary for a simple, single-purpose workflow. The conclusion is to stick with the simpler direct integration for now.

---

#### ** Reversion **

Upon successful completion of the PoC, all created resources and settings were reverted. The SES identity for `example.domain.com` was removed, along with the associated DNS records and the SES rule set, to ensure no lingering resources remained active.

---

### Task 1.2: AWS Account & Repo Setup

* **AWS Account**: The existing AWS account `[REDACTED]` will be used. This account is in its first year and is within the free tier, which aligns with the project's low-cost hosting strategy. The account is also designated for potential future projects.
* **IAM Roles**: IAM roles will be configured with the principle of least privilege, ensuring each service has only the necessary permissions.
* **Secure Credentials**: AWS access credentials will be securely stored in **GitHub Secrets** for use by the CI/CD pipeline.

### Task 1.3: Email Parsing Service

* **Purpose**: Develop the core logic for the AWS Lambda function that parses email content.
* **Technology**: The service will be written in Python.
* **Trigger**: The Lambda function will be triggered by messages from an AWS SQS queue.
* **Data Extraction**: The function will use regular expressions to extract key data points from the email body, including meeting date, time, and participant details.
* **Output**: The extracted data will be formatted into a structured JSON payload and published to another SQS queue.

### Task 1.4: CI/CD Pipeline

* **Automation**: The project will use **GitHub Actions** to automate the deployment pipeline.
* **Workflow**: The workflow will automatically run continuous integration (CI) tasks, such as testing and Terraform validation, and then execute `terraform plan` and `terraform apply` for continuous deployment (CD).

### Task 1.5: Testing

* **Unit Tests**: Unit tests will be written for the Email Parsing Service to ensure the parsing logic correctly extracts data from a variety of email templates.
* **Integration Tests**: The CI/CD pipeline will be configured to run tests that validate the interaction between the AWS Lambda function and the SQS queue.

---

## Addendum: Implicit Requirements and Considerations

The following are implicit requirements and considerations identified during the design phase that need to be addressed in future design discussions.

* **Development Environment**: A choice needs to be made on the standard development environment, including the code editor (e.g., VSCode or Cursor) and whether to use development containers to maintain consistency across the team.
* **Dedicated Email Address**: The specific email address for the service's inbox needs to be chosen and set up. This address is a critical piece of the email parsing flow.
* **User Authentication and Authorization**: While the system is designed to be multi-user ready, the specific authentication mechanism (e.g., Google OAuth, email/password) has not been selected yet. This will need to be decided before developing the front-end and backend server layers.
* **Template Management**: The system uses different WhatsApp templates based on the number of participants. The design documents do not specify how these templates are stored, managed, or edited within the system. This will need to be a part of the design for the Meeting Management Service.
* **Error Reporting and Monitoring**: The project plan mentions basic logging and error reporting via console logs or a simple dashboard. A more robust monitoring and alerting strategy for a production environment will need to be defined.