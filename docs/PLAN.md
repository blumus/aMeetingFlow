# Meeting Automation Service: Project Plan (Incremental Approach)

## 1. Project Overview

This plan reorders the development process to be more incremental and interwoven, focusing on completing each core service from start to finish before moving to the next. This approach reduces the risk of long feedback loops and allows for continuous integration and testing.

***

## 2. Phase 1: Setup & Email Parsing Service

This phase combines all tasks necessary to get the first core service fully functional, from infrastructure to testing.

* **Task 1.1: Project Tracking Setup:** Create a Trello board (or alternative) and add all the tasks from this project plan as cards.
* **Task 1.2: AWS Account & Repo Setup:** Create a dedicated AWS account, set up IAM roles, and configure the project repository on GitHub.
* **Task 1.3: IaC for Email Parser:** Write and deploy the Terraform scripts to provision the AWS Lambda function, SQS queue, and necessary permissions for the Email Parsing Service.
* **Task 1.4: Coding - Email Parser Service:** Write the Python code for the Lambda function that consumes SQS messages and parses email content.
## Task 1.4: Coding - Email Parser Service

### Steps:
1. Start the Infrastructure as Code (IaC) pipeline to deploy/update resources (Lambda, SES, etc.).
2. Send a test email to the configured SES address.
3. Observe and document the current system behavior:
	- Check AWS CloudWatch logs for Lambda execution details.
	- Note any errors, unexpected results, or missing functionality.
4. Only after observing, begin coding or fixing the email parser service as needed.
5. Optionally, add SES filters to ensure only the "right emails" are processed (e.g., by sender, subject, etc.).

### Additional Suggestions:
- Document the observed behavior/results after sending the test email.
- Confirm the IaC pipeline deploys all necessary resources.
- Ensure access to AWS CloudWatch for Lambda logs and troubleshooting.
- Clarify criteria for SES filters ("right emails").

* **Task 1.5: Unit Testing:** Write and execute unit tests for the parsing logic to ensure it correctly extracts data from various email templates.
* **Task 1.6: CI/CD Pipeline Integration:** Configure the GitHub Actions workflow to automatically test and deploy the `Email Parser Service` when code changes are pushed.

***

## 3. Phase 2: Meeting Management & Data Storage Service

This phase focuses on the service responsible for data storage and the core notification logic.

* **Task 2.1: Third-Party API Integration:** Secure API keys and credentials for Zoom and the WhatsApp Business Platform.
* **Task 2.2: IaC for Meeting Management:** Write and deploy the Terraform scripts for the DynamoDB table and the Lambda functions within the Meeting Management Service.
* **Task 2.3: Coding - Data Storage Logic:** Develop the Lambda function that takes parsed data and stores it in DynamoDB.
* **Task 2.4: Integration Testing (Parser to DynamoDB):** Test the full data flow from the `Email Parser Service` to the `Meeting Management Service` to confirm data is correctly passed and stored.
* **Task 2.5: Coding - Notification Logic:** Develop the Lambda function that queries DynamoDB and prepares meeting data for Zoom and WhatsApp.
* **Task 2.6: Coding - Zoom and WhatsApp Integration:** Implement the logic to create a Zoom meeting and send a WhatsApp message using the respective APIs.

***

## 4. Phase 3: Front-End & UX Development

This phase focuses on the user-facing part of the system, including the new backend server layer.

* **Task 3.1: IaC for Backend Server:** Provision the infrastructure for the backend server layer that will mediate between the front-end and DynamoDB.
* **Task 3.2: Coding - Backend Server:** Develop the API endpoints on the backend server that provide CRUD functionality for the front-end.
* **Task 3.3: UI/UX Mockups & Implementation:** Design and build the front-end application, connecting it to the new backend server.
* **Task 3.4: End-to-End Testing (UI):** Test all front-end functionality, ensuring the dashboard displays meetings correctly and CRUD operations work as expected.

***

## 5. Phase 4: Final Testing & Deployment

This final phase prepares the entire system for production release.

* **Task 4.1: Final End-to-End Testing:** Conduct a full test of the entire system, from a forwarded email to a received WhatsApp reminder, to confirm all components are working correctly and securely.
* **Task 4.2: Security Review:** Conduct a security review to ensure API keys are not exposed and the new backend server is secure.
* **Task 4.3: Production Deployment:** Deploy the entire system to a production environment using the established CI/CD pipeline.

***

## 6. Milestones

* **Milestone 1:** Completed and tested `Email Parsing Service`.
* **Milestone 2:** Completed and tested `Meeting Management Service`, including data storage and notification logic.
* **Milestone 3:** Completed and tested front-end UI and its backend server.
* **Milestone 4:** Full system deployed to production.