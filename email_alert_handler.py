import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from fpdf import FPDF
from datetime import datetime
import pandas as pd

# Your improved PDF class with headers and footers
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Knowledge Gap Report', 0, 1, 'C')
        self.set_font('Arial', '', 8)
        self.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

# Main class structure that app.py expects
class EmailAlertHandler:
    """
    Handles the creation of PDF reports and sending them via email.
    """
    def __init__(self):
        # Load credentials once when the class is instantiated
        self.host = os.getenv("EMAIL_HOST")
        self.port = os.getenv("EMAIL_PORT")
        self.user = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASSWORD")

        if not all([self.host, self.port, self.user, self.password]):
            raise ValueError(
                "Email configuration is incomplete. Please check EMAIL_HOST, EMAIL_PORT, "
                "EMAIL_USER, and EMAIL_PASSWORD in your .env file."
            )

    def create_knowledge_gap_pdf(self, df: pd.DataFrame, filename="knowledge_gap_report.pdf"):
        """
        Generates a PDF report from a DataFrame using the custom PDF class.
        """
        if df.empty:
            print("DataFrame is empty, cannot generate PDF.")
            return None
        
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 10, txt="Knowledge Gap Report", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=10)

        for index, row in df.iterrows():
            pdf.set_font('Arial', 'B', 11)
        #     pdf.multi_cell(0, 10, f"ID: {row.get('ID', 'N/A')}")
            
        #     pdf.set_font('Arial', 'B', 10)
        #     pdf.multi_cell(0, 10, f"Timestamp: {row.get('Timestamp', 'N/A')}")
            
        #     pdf.set_font('Arial', 'B', 10)
        #     pdf.multi_cell(0, 10, "User Query:")
        #     pdf.set_font('Arial', '', 10)
        #     pdf.multi_cell(0, 10, str(row.get('Query', 'N/A')))
            
        #     pdf.set_font('Arial', 'B', 10)
        #     pdf.multi_cell(0, 10, "Model's Answer:")
        #     pdf.set_font('Arial', '', 10)
        #     # Corrected the key to match the one used in google_sheets_handler
        #     pdf.multi_cell(0, 10, str(row.get('Generated Response', 'N/A')))
            
        #     pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5)
        #     pdf.ln(10)
            query_id = str(row.get('ID', 'N/A')).encode('latin-1', 'replace').decode('latin-1')
            timestamp = str(row.get('Timestamp', 'N/A')).encode('latin-1', 'replace').decode('latin-1')
            user_query = str(row.get('Query', 'N/A')).encode('latin-1', 'replace').decode('latin-1')
            model_response = str(row.get('Generated Response', 'N/A')).encode('latin-1', 'replace').decode('latin-1')

            pdf.multi_cell(0, 7, f"Query ID: {query_id}")
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 7, f"Timestamp: {timestamp}")
            pdf.multi_cell(0, 7, f"User Query: {user_query}")
            pdf.multi_cell(0, 7, f"Model's Response: {model_response}")
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
            pdf.ln(5)

        pdf_path = "knowledge_gap_report.pdf"
        pdf.output(pdf_path)
        return pdf_path

        # pdf.output(filename)
        # return filename
        
        

    def send_email_with_attachment(self, recipient_email, attachment_path):
        """
        Sends an email with the PDF report as an attachment.
        """
        subject = "Action Required: Knowledge Gap Report for Ticket Resolution Bot"
        body = "Please find attached the latest report on unresolved user queries that indicate a knowledge gap in the RAG model. Review is required to improve the knowledge base."
        
        msg = MIMEMultipart()
        msg['From'] = self.user
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Attach the file
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {os.path.basename(attachment_path)}",
        )
        msg.attach(part)

        try:
            
            # Connect to server and send email
            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            server.login(self.user, self.password)
            text = msg.as_string()
            server.sendmail(self.user, recipient_email, text)
            server.quit()
            # with smtplib.SMTP(self.host, int(self.port)) as server:
                # server.starttls()
                # server.login(self.user, self.password)
                # server.send_message(msg)
                
            print(f"Email sent successfully to {recipient_email}")
        except smtplib.SMTPAuthenticationError:
            raise Exception("SMTP Authentication Error: The username or password you provided is not correct.")
        except Exception as e:
            raise Exception(f"Failed to send email: {e}")

