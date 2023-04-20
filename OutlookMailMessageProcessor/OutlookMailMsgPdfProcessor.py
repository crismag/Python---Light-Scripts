"""
# ---------------------------------------------------------------------
# Outlook Mail Message Attachment and PDF converter - processor.
#
# ---------------------------------------------------------------------
# Author: Cristopher S. Magalang
# Date created: 20 April 2023
# Python Version: 3.8
# ---------------------------------------------------------------------
# Code is refactored in ChatGPT. Not tested after refactoring. New Errors might be introduced. 
#
# ---------------------------------------------------------------------
# The following script processes a Microsoft Outlook email message file (.msg) to extract any PDF attachments 
# and generate a new PDF file that includes the extracted attachments and the original email message.
#
# The script consists of two classes:
#
# OutlookMailMsgAttachmentProcessor which is responsible for extracting attachments from the .msg file 
# and saving them to a specified directory.
#
# OutlookMailMsgToPdfConverter which converts the .msg file to a PDF file and merges 
# any extracted PDF attachments to create a new PDF file.
#
# The script takes command-line arguments including the input .msg file, output directory, 
# output filename, and a log file where the status of each operation is recorded.
#
# A third class, OutlookMailMsgProcessor, combines the functionality of both classes to process 
# a .msg file, download its attachments, and generate a new merged PDF file containing 
# all PDF attachments and the original email message. 
# The class can be invoked using command-line arguments or integrated into a larger script.
"""

from OutlookMailMsgAttachmentProcessor import OutlookMailMsgAttachmentProcessor
from OutlookMailMsgToPdfConverter import OutlookMailMsgToPdfConverter
import os
import argparse

class OutlookMailMsgPdfProcessor:
    def __init__(self, in_msg, out_dir, out_file, log_file):
        self.in_msg = in_msg
        self.out_dir = out_dir
        self.out_file = out_file
        self.log_file = log_file
        self.logger = self.create_logger()

    def create_logger(self):
        import logging
        logger = logging.getLogger('outlook_mail_msg_pdf_processor')
        logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        return logger

    def process_msg(self):
        try:
            # Instantiate OutlookMailMsgAttachmentProcessor and call extract_attachments method
            attachment_processor = OutlookMailMsgAttachmentProcessor(self.in_msg, self.out_dir, self.logger)
            attachment_processor.extract_attachments()

            # Instantiate OutlookMailMsgToPdfConverter and call convert_to_pdf method
            converter = OutlookMailMsgToPdfConverter(self.in_msg, self.out_dir, self.logger)
            pdf_file = converter.convert_to_pdf()

            # Combine pdf attachments and new pdf from msg into one pdf file
            pdf_files = [os.path.join(self.out_dir, f) for f in os.listdir(self.out_dir) if f.endswith(".pdf")]
            pdf_files.remove(pdf_file) # remove the new pdf file from msg
            pdf_files.append(pdf_file) # add the new pdf file from msg as the last page
            merger = PdfFileMerger()
            for pdf_file in pdf_files:
                merger.append(open(pdf_file, 'rb'))
            merged_pdf_file = os.path.join(self.out_dir, self.out_file)
            merger.write(merged_pdf_file)
            merger.close()

            self.logger.info(f"Pdf created successfully: {merged_pdf_file}")

        except Exception as e:
            self.logger.error(f"Error processing msg: {str(e)}")


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description='Process Outlook .msg files, download attachments, and generate a merged PDF file.')
    parser.add_argument('in_msg', type=str, help='Input .msg file path')
    parser.add_argument('out_dir', type=str, help='Output directory path')
    parser.add_argument('out_file', type=str, help='Output merged PDF file name')
    parser.add_argument('log_file', type=str, help='Output log file path')
    args = parser.parse_args()

    # Process .msg file and generate merged PDF file
    processor = OutlookMailMsgPdfProcessor(args.in_msg, args.out_dir, args.out_file, args.log_file)
    processor.process_msg()


if __name__ == '__main__':
    main()

#
# Usage:
# python my_script.py example.msg /output/directory merged.pdf log.txt
#
