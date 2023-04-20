"""
Outlook Mail Message to PDF Converter

This script converts an Outlook mail message (.msg) file to a PDF file, and combines any PDF attachments into a single PDF
file, with the PDF generated from the message file as the last page of the new PDF. It also logs operation stages and
status into a specified output log file.

Code is re-factored in ChatGPT. New errors may have been introduced.- Not tested after refactoring.

Author: Cristopher S. Magalang
Date created: 20 April 2023
Python Version: 3.8
"""

import os
import win32com.client
import comtypes.client
from PyPDF2 import PdfFileMerger, PdfFileReader
import logging


class OutlookMailMsgToPdfConverter:
    def __init__(self, input_file, output_dir, output_name, log_file):
        self.input_file = input_file
        self.output_dir = output_dir
        self.output_name = output_name
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def convert_to_pdf(self):
        self.logger.info(f"Converting message {self.input_file} to pdf...")
        # Create a new instance of the Outlook application
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

        # Open the .msg file
        msg = outlook.OpenSharedItem(self.input_file)

        # Get the subject of the message
        subject = msg.Subject

        # Create a new pdf file for the message
        pdf_name = f"{subject}.pdf"
        pdf_path = os.path.join(self.output_dir, pdf_name)

        # Use comtypes to convert the message to pdf
        try:
            # Create a COM object to handle the conversion
            outlook_pdf = comtypes.client.CreateObject("Outlook.Application")
            # Get the email as a document
            msg_doc = outlook_pdf.Session.OpenSharedItem(self.input_file)
            # Save the document as a pdf
            msg_doc.ExportAsFixedFormat(0, pdf_path, 0, 0, 0, 0, 0, 0)
            # Close the document
            msg_doc.Close(0)
            self.logger.info(f"Message {self.input_file} converted successfully to pdf: {pdf_path}")
        except Exception as e:
            self.logger.error(f"Error converting message {self.input_file} to pdf: {e}")
            return

        # Initialize a PdfFileMerger object
        merger = PdfFileMerger()

        # Add the attachments to the merger
        for attachment in msg.Attachments:
            # Get the attachment file name
            file_name = attachment.FileName
            # Construct the full path to save the attachment
            save_path = os.path.join(self.output_dir, file_name)
            # Save the attachment to disk
            attachment.SaveAsFile(save_path)
            # Check if the attachment is a pdf file
            if file_name.endswith(".pdf"):
                # Add the pdf to the merger
                try:
                    merger.append(PdfFileReader(save_path, "rb"))
                    self.logger.info(f"Attachment {file_name} added successfully to pdf")
                except Exception as e:
                    self.logger.error(f"Error adding attachment {file_name} to pdf: {e}")

        # Add the message pdf to the merger
        try:
            merger.append(PdfFileReader(pdf_path, "rb"))
            self.logger.info(f"Message pdf {pdf_path} added successfully to pdf")
        except Exception as e:
            self.logger.error(f"Error adding message pdf to pdf: {e}")

        # Save the merged pdf
        output_path = os.path.join(self.output_dir, self.output_name)
        with open(output_path, "wb") as output_file:
            merger.write(output_file)
        self.logger.info(f"Pdf created successfully: {output_path}")
