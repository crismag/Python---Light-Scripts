
"""
Script Name: OutlookMailMsgAttachmentProcessor.py
Description: A script to extract attachments from an Outlook .msg file and save them to a directory.
Note: Refactored using ChatGPT before release. Might contain errors because of that.
Version: 1.0
Author: Cristopher S. Magalang
Date: April 20, 2023
"""

import os
import win32com.client
import zipfile
import tarfile
import gzip
import logging
import datetime

class OutlookMailMsgAttachmentProcessor :
    def __init__(self, input_file, output_dir, log_file):
        self.input_file = input_file
        self.output_dir = output_dir
        self.log_file = log_file

        # Create a logger object
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Create a file handler and set the logging level
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)

        # Create a formatter and add it to the file handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        self.logger.addHandler(file_handler)

    def extract_attachments(self):
        # Get start datetime
        start_time = datetime.datetime.now()

        # Log start time and input file
        self.logger.info(f"Starting attachment extraction for {self.input_file} at {start_time}")

        # Create a new instance of the Outlook application
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

        # Open the .msg file
        msg = outlook.OpenSharedItem(self.input_file)

        # Iterate over the attachments
        for attachment in msg.Attachments:
            # Get the attachment file name
            file_name = attachment.FileName
            # Construct the full path to save the attachment
            save_path = os.path.join(self.output_dir, file_name)
            # Save the attachment to disk
            attachment.SaveAsFile(save_path)
            self.logger.info(f"Attachment saved to {save_path}")
            # Check if the attachment is a compressed file
            if file_name.endswith(".gz") or file_name.endswith(".tar") or file_name.endswith(".zip"):
                # Extract the file to the current directory
                if file_name.endswith(".gz"):
                    with gzip.open(save_path, 'rb') as f_in:
                        with open(os.path.splitext(save_path)[0], 'wb') as f_out:
                            f_out.write(f_in.read())
                elif file_name.endswith(".tar"):
                    with tarfile.open(save_path, 'r') as tar:
                        tar.extractall(path=os.path.dirname(save_path))
                elif file_name.endswith(".zip"):
                    with zipfile.ZipFile(save_path, 'r') as zip:
                        zip.extractall(path=os.path.dirname(save_path))
                self.logger.info(f"Compressed file extracted to {os.path.dirname(save_path)}")

        # Close the message
        msg.Close(0)

        # Verify that the attachments were created
        if os.path.exists(self.output_dir):
            self.logger.info("Attachments created successfully.")
        else:
            self.logger.error("Attachment creation failed.")

        # Get end datetime
        end_time = datetime.datetime.now()

        # Log end time and total duration
        duration = end_time - start_time
        self.logger.info(f"Attachment extraction completed for {self.input_file} at {end_time} (Total duration: {duration})")


# Set up argument parsing
import argparse

parser = argparse.ArgumentParser(description="Extract attachments from an Outlook .msg file and save them to a directory.")
parser.add_argument("-in_msg", required=True, help="Path to the input .msg file.")
parser.add_argument("-out_dir", required=True, help="Path to the directory where attachments should be saved.")
parser.add_argument("-log", required=True, help="Path to the log file.")

args = parser.parse_args()

# Instantiate MessageParser and call extract_attachments method
parser
