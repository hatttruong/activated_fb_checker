"""
This solution is based on the answer at link:
    https://stackoverflow.com/questions/21928368/login-to-facebook-using-python-requests

Attributes:
    parser (TYPE): Description

TODO:
resolve the problem of language. Currently, the result is in Vietnamese
"""
import os
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

LASTEST_STATUS_LOG = 'lastest_status.log'


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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        "Accept-Language": "en-US,en;q=0.5"
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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Cache-Control': 'no-cache',
        "Accept-Language": "en-US,en;q=0.5"
    }
    response = session.get(check_url,
                           cookies=cookies,
                           headers=headers,
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


def get_status_from_response(response):
    """Summary

    Args:
        response (TYPE): Description

    Returns:
        TYPE: Description
    """
    new_status = 'a'
    with open('evidence.html', 'w') as f:
        f.write(response.text)
    check_texts = ['Sorry, this content isn&#039;t available at the moment',
                   'Rất tiếc, nội dung này hiện không khả dụng']
    for check_text in check_texts:
        if response.text.find(check_text) >= 0:
            new_status = 'd'
            break

    # log the current status to file
    with open(LASTEST_STATUS_LOG, 'w') as f:
        f.write('%s;%s' % (new_status,
                           datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    return new_status


def load_lastest_status():
    lastest_status = 'a'
    if os.path.isfile(LASTEST_STATUS_LOG):
        with open(LASTEST_STATUS_LOG, 'r') as f:
            content = f.read()
            print('log file content: %s' % content)
            info = content.split(';')
            if len(info) >= 2:
                print('Status of user %s, at %s: %s' %
                      (args.username, info[1], info[0]))
                lastest_status = info[0].strip()
    return lastest_status


def check_account_activated(args):
    """Summary

    Args:
        args (TYPE): Description
    """
    # get the lastest user status
    if args.status is None:
        # load status from file
        args.status = load_lastest_status()

    # set current status
    current_status = args.status

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
    print('Current status: ',
          'activated' if current_status == 'a' else 'deactivated')
    print('Recipients:', recipients)
    # print(delay_minutes)

    # start checking
    username = args.username
    check_url = 'https://www.facebook.com/%s' % username

    session, cookies = get_session(email_fb, password_fb)

    # check if user activate or not every 5 minutes
    ending_date = datetime.now() + timedelta(days=int(args.days))
    print('checking will be end in %s' % ending_date)
    message_pattern = "User %s has %s. Follow this link to check %s"
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

        new_status = get_status_from_response(response)
        if new_status == current_status:
            new_status_full = 'deactivating'
            if new_status == 'a':
                new_status_full = 'activating'
            print('%s: username=%s has been still %s' %
                  (datetime.now(), username, new_status_full))
        else:
            current_status = new_status
            new_status_full = 'deactivated'
            if new_status == 'a':
                new_status_full = 'activated'
            print('%s: username=%s has %s' %
                  (datetime.now(), username, new_status_full))
            with open('evidence_%s.html' % new_status_full, 'w') as f:
                f.write(response.text)

            subject = '[Alert] FB Account %s status has %s' % (
                username, new_status_full)
            message = message_pattern % (username, new_status_full, check_url)
            send_email(email, password_email, recipients, subject, message)

        print('Wait %s minutes for next check...' % delay_minutes)
        # Delay in X minute
        time.sleep(delay_minutes * 60)


parser = argparse.ArgumentParser()


if __name__ == '__main__':
    parser.add_argument('username', help='username will be checked')
    parser.add_argument(
        'days', help='number of days that checking function runs')
    parser.add_argument('secret_key', help='secret key to decrypt password')
    parser.add_argument(
        '-s', '--status', choices=['a', 'd'],
        help='current status of user (a: activated, d: deactivated)')

    args = parser.parse_args()
    check_account_activated(args)
