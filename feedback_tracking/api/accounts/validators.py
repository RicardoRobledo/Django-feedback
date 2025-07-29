__author__ = "Ricardo"
__version__ = "0.1"


def validate_unique_organization(name_exists, company_email_exists, phone_number_exists):
    """
    Validate if there are any existing organizations with the same name, administrative email, company email or phone number.

    :param name_exists(bool): indicating if the name exists
    :param company_email_exists(bool): indicating if the company email exists
    :param phone_number_exists(bool): indicating if the phone number 

    :return: message with the validation result 
    """

    message = {}

    if name_exists:

        message['name'] = 'That organization already exists'

    if company_email_exists:

        message['company_email'] = 'That company email already exists'

    if phone_number_exists:

        message['phone_number'] = 'That phone number already exists'

    return message


def validate_unique_user(username_exists, email_exists):
    """
    Validate if there are any existing users with the same username or email.

    :param username_exists(bool): indicating if the username exists
    :param email_exists(bool): indicating if the email exists
    :return: message with the validation result
    """

    message = {}

    if username_exists:

        message['username'] = 'That user already exists'

    if email_exists:

        message['email'] = 'That email already exists'

    return message
