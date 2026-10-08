from src.core.decorators import log_execution
from langchain_core.tools import tool

@log_execution()
@tool
def download_email_attachment_tool():
    pass

@log_execution()
@tool
def extract_text_from_pdf_tool():
    pass

@log_execution()
@tool
def search_legal_database_tool():
    pass

@log_execution()
@tool
def save_opinion_to_drive_tool():
    pass

@log_execution()
@tool
def send_slack_notification_tool():
    pass