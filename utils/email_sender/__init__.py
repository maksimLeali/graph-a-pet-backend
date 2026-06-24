import sib_api_v3_sdk 
from sib_api_v3_sdk.rest import ApiException
from config import cfg
import os
from utils.logger import logger


def send_confirmation_code_email(recipient_email,  code):
    # Configure API key authorization: api-key
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = cfg['brevo']['api_key']
    current_directory = os.getcwd()
    logger.info("Current directory: %s", current_directory)

    # Initialize the API instance
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Load email content from the file
    with open('utils/email_sender/templates/confirmation-code.html', 'r') as file:
        email_content = file.read()

    # Replace placeholder with the actual code
    email_content = email_content.replace('{{CODE}}', code)

    # Create send email request
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender={"email": cfg['brevo']['sender']},
        to=[{"email": recipient_email}],
        subject="your confirmation code",
        html_content=email_content
    )

    logger.info("Sending email to: %s with code: %s", recipient_email, code)
    # Send email
    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print("Email sent successfully. Message ID: %s" % api_response.message_id)
    except ApiException as e:
        logger.error("Exception when calling TransactionalEmailsApi->send_transac_email: %s\n" % e)
        print("Exception when calling TransactionalEmailsApi->s end_transac_email: %s\n" % e)
