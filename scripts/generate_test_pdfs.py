import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


def create_iso_27001_extract(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(
        1 * inch, height - 1 * inch, "ISO/IEC 27001:2013 (Extract for Testing)"
    )

    # Section A.9
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 1.5 * inch, "A.9 Access Control")
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(1 * inch, height - 1.8 * inch)
    text_obj.textLines("""
    A.9.1 Business requirements of access control
    Objective: To limit access to information and information processing facilities.

    A.9.1.1 Access control policy
    Control: An access control policy shall be established, documented and reviewed
    based on business and information security requirements.

    A.9.1.2 Access to networks and network services
    Control: Users shall only be provided with access to the network and network
    services that they have been specifically authorized to use.

    A.9.2 User access management
    Objective: To ensure authorized user access and to prevent unauthorized access.

    A.9.2.1 User registration and de-registration
    Control: A formal user registration and de-registration process shall be
    implemented to enable assignment of access rights.

    A.9.2.2 User access provisioning
    Control: A formal user access provisioning process shall be implemented to
    assign or revoke access rights for all user types to all systems and services.

    A.9.2.3 Management of privileged access rights
    Control: The allocation and use of privileged access rights shall be restricted
    and controlled.

    A.9.4.1 Information access restriction
    Control: Access to information and application system functions shall be
    restricted in accordance with the access control policy.
    """)
    c.drawText(text_obj)

    # Section A.10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 5.5 * inch, "A.10 Cryptography")
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(1 * inch, height - 5.8 * inch)
    text_obj.textLines("""
    A.10.1 Cryptographic controls
    Objective: To ensure proper and effective use of cryptography to protect the
    confidentiality, authenticity and/or integrity of information.

    A.10.1.1 Policy on the use of cryptographic controls
    Control: A policy on the use of cryptographic controls for protection of
    information shall be developed and implemented.

    A.10.1.2 Key management
    Control: A policy on the use, protection and lifetime of cryptographic keys
    shall be developed and implemented through their whole lifecycle.
    """)
    c.drawText(text_obj)

    c.save()
    print(f"Created {filename}")


def create_fake_mobile_app_project(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(
        1 * inch,
        height - 1 * inch,
        "Project: SecurePay Mobile App - Architecture Overview",
    )

    # Metadata
    c.setFont("Helvetica", 10)
    c.drawString(
        1 * inch,
        height - 1.3 * inch,
        "Version: 1.0 | Date: 2026-03-06 | Confidential",
    )

    # Executive Summary
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 1.8 * inch, "1. Executive Summary")
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(1 * inch, height - 2.1 * inch)
    text_obj.textLines("""
    SecurePay is a new mobile application designed to allow users to send money to
    friends instantly using their phone number. The app will be available on iOS
    and Android. The backend is hosted on AWS.
    """)
    c.drawText(text_obj)

    # Architecture
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 3.0 * inch, "2. System Architecture")
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(1 * inch, height - 3.3 * inch)
    text_obj.textLines("""
    The system consists of the following components:
    - Mobile Client (iOS/Android): Built with React Native.
    - API Gateway: Nginx reverse proxy.
    - Backend Service: Python/Flask application running in Docker containers.
    - Database: PostgreSQL for user data and transaction history.
    - Cache: Redis for session management.
    """)
    c.drawText(text_obj)

    # Data Flow
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 4.8 * inch, "3. Key Data Flows")
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(1 * inch, height - 5.1 * inch)
    text_obj.textLines("""
    3.1 User Login
    User enters username and password in the app. The app sends a POST request to
    /api/login. The backend verifies credentials against the database. On success,
    a session token is returned. For debugging purposes in the beta phase, we log
    the failed password attempts in plain text to help users troubleshoot login
    issues.

    3.2 Transaction Processing
    User selects a recipient and amount. The app sends a POST request to
    /api/transfer. The backend validates the balance and updates the database.
    To ensure auditability, the full request payload (including credit card numbers
    if used for top-up) is logged to a central log file.
    """)
    c.drawText(text_obj)

    # Security Considerations (Intentional Flaws for Testing)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, height - 7.5 * inch, "4. Security Implementation Details")
    c.setFont("Helvetica", 11)
    text_obj = c.beginText(1 * inch, height - 7.8 * inch)
    text_obj.textLines("""
    - Communication: All client-server communication uses HTTPS.
    - Internal Communication: To improve performance, communication between the
      Backend Service and the Database is done over unencrypted HTTP within the
      private VPC.
    - Authentication: We use custom session tokens.
    - Storage: User passwords are stored using MD5 hashing for speed.
    - Backups: Database backups are performed weekly and stored on a public S3
      bucket for easy access by the development team.
    """)
    c.drawText(text_obj)

    c.save()
    print(f"Created {filename}")


if __name__ == "__main__":
    examples_dir = "examples"
    if not os.path.exists(examples_dir):
        os.makedirs(examples_dir)

    iso_file = os.path.join(examples_dir, "test_iso_27001_extract.pdf")
    project_file = os.path.join(examples_dir, "test_mobile_app_project.pdf")

    create_iso_27001_extract(iso_file)
    create_fake_mobile_app_project(project_file)
