"""
This solution is based on the answer at link:
    https://stackoverflow.com/questions/21928368/login-to-facebook-using-python-requests

Attributes:
    parser (TYPE): Description
"""
import requests
import argparse
from datetime import datetime, timedelta
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import sys
from lxml import html
import encrypt_password

if sys.version_info[0] < 3:
    import ConfigParser
else:
    import configparser as ConfigParser


parser = argparse.ArgumentParser()


def load_configuration(section, config_name):
    """
    Description: load configuration from setting file using ConfigParser

    Args:
        section (str): name of section in setting file
        config_name (str): name of configuration

    Returns:
        STR: value of configuration

    No Longer Raises:
        IOError: Description

    """

    config = ConfigParser.ConfigParser()
    config.read('setting.ini')
    return config.get(section, config_name)


def send_email(sender, password, recipients, subject, message):
    """Summary

    Args:
        sender (TYPE): Description
        password (TYPE): Description
        recipients (TYPE): Description
        username (TYPE): Description
        url (TYPE): Description
    """
    # create message object instance
    msg = MIMEMultipart()

    # setup the parameters of the message
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject

    # add in the message body
    msg.attach(MIMEText(message, 'plain'))

    # create server
    server = smtplib.SMTP('smtp.gmail.com: 587')

    server.starttls()

    # Login Credentials for sending the mail
    server.login(msg['From'], password)

    # send the message via the server.
    server.sendmail(msg['From'], recipients, msg.as_string())

    server.quit()

    print("successfully sent email to %s" % (msg['To']))


def get_session(email_fb, password_fb):
    session = requests.session()
    cookies = login(session, email_fb, password_fb)
    print('cookies:', cookies)
    return session, cookies


def login(session, email, password):
    '''
    Attempt to login to Facebook. Returns cookies given to a user
    after they successfully log in.

    Args:
        session (TYPE): Description
        email (TYPE): Description
        password (TYPE): Description

    Returns:
        TYPE: Description
    '''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
    }
    url = 'https://m.facebook.com/login.php'
    login_data = {
        'email': email,
        'pass': password
    }

    # Attempt to login to Facebook
    response = session.post(url, data=login_data, headers=headers,
                            allow_redirects=False)

    assert response.status_code == 302
    assert 'c_user' in response.cookies
    return response.cookies


def check_url_response(session, cookies, check_url):
    response = session.get(check_url, cookies=cookies,
                           allow_redirects=False)
    with open('check_url.html', 'w') as f:
        f.write(response.text)

    tree = html.fromstring(response.text)
    home_button = list(set(tree.xpath(
        '//a[contains(@href,"https://www.facebook.com/?ref=tn_tnmn")]/text()'
    )))
    login_failed = True
    if len(home_button) > 0:
        if home_button[0] in ['Home', 'Trang chủ']:
            login_failed = False
    return login_failed, response


def is_deactivated(response):
    """Summary

    Args:
        response (TYPE): Description

    Returns:
        TYPE: Description
    """
    check_text = "Sorry, this content isn&#039;t available at the moment"
    return response.text.find(check_text) >= 0


def check_account_activated(args):
    """Summary

    Args:
        args (TYPE): Description
    """
    # load setting.ini
    section_name = 'SectionCommon'
    secret_key = args.secret_key
    email_fb = load_configuration(section_name, 'EmailFacebook')
    password_fb = encrypt_password.decode(
        secret_key,
        load_configuration(section_name, 'PasswordFacebook'))
    email = load_configuration(section_name, 'Email')
    password_email = encrypt_password.decode(
        secret_key,
        load_configuration(section_name, 'PasswordEmail'))
    recipients = load_configuration(section_name, 'Recipients')
    recipients = [x.strip() for x in recipients.split(',')]
    delay_minutes = int(load_configuration(section_name, 'DelayMinutes'))
    # print(email_fb, password_fb)
    # print(email, password_email)
    print('Recipients:', recipients)
    # print(delay_minutes)

    # start checking
    username = args.username
    check_url = 'https://www.facebook.com/%s' % username

    session, cookies = get_session(email_fb, password_fb)

    # check if user activate or not every 5 minutes
    ending_date = datetime.now() + timedelta(days=int(args.days))
    print('checking will be end in %s' % ending_date)
    current_activated = True
    while datetime.now() < ending_date:

        login_failed, response = check_url_response(
            session, cookies, check_url)

        if login_failed:
            # try to re-login
            session, cookies = get_session(email_fb, password_fb)
            login_failed, response = check_url_response(
                session, cookies, check_url)
            if login_failed:
                # notify yourself if you cannot log in
                subject = 'login failed'
                message = 'cannot login'
                send_email(email, password_email, [email], subject, message)
                break

        if is_deactivated(response):
            print('username=%s has deactivated' % username)
            if current_activated:
                current_activated = False
                with open('evidence_deactivated.html', 'w') as f:
                    f.write(response.text)

                subject = 'Alert deactivate FB Account %s' % username
                message = "User %s has deactivated. Follow this link to check %s" % (
                    username, check_url)
                send_email(email, password_email, recipients, subject, message)

        else:
            print('username=%s has activated' % username)
            if current_activated is False:
                current_activated = True
                # send email
                with open('evidence_activated.html', 'w') as f:
                    f.write(response.text)

                subject = 'Alert activate FB Account %s' % username
                message = "User %s has activated. Follow this link to check %s" % (
                    username, check_url)
                send_email(email, password_email, recipients, subject, message)

        # Delay in X minute
        time.sleep(delay_minutes * 60)


if __name__ == '__main__':
    parser.add_argument('username', help='username will be checked')

    parser.add_argument(
        'days', help='number of days that checking function runs')

    parser.add_argument('secret_key', help='secret key to decrypt password')

    args = parser.parse_args()
    check_account_activated(args)
