import subprocess
import re
import datetime
import csv
from email.mime.text import MIMEText
import smtplib

###
# -- Server Settings -- #
###
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "email"
SMTP_PASSWORD = "password"
EMAIL_FROM = "source email"
DATE_FORMAT = "%m/%d/%Y"
EMAIL_SPACE = ", "

###
# -- Functions Defined -- #
###
def email_user(recipientEmail, daysUntilExp):
    expDate = datetime.date.today() + datetime.timedelta(days=daysUntilExp)
    body = " Your account's LDAP password is set to expire in %s days which is used by various internal services inlcuding VPN access. \r\n This is an automated message alert. \r\n \r\n Please let me know if you would like any help updating your password or have any questions." % daysUntilExp
    subject = 'LDAP Password Expires On '
    msg = MIMEText(body)
    msg['Subject'] = "{0} {1}".format(subject, expDate.strftime(DATE_FORMAT))
    msg['To'] = recipientEmail # used to be EMAIL_TO
    msg['From'] = EMAIL_FROM
    mail = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    mail.starttls()
    mail.login(SMTP_USERNAME, SMTP_PASSWORD)
    mail.sendmail(EMAIL_FROM, recipientEmail, msg.as_string())
    mail.quit()


def evaluate_password_expiry(user, uid):
    #Gets the users policy length
    proc = subprocess.Popen(['/usr/bin/pwpolicy -getpolicy -u {0}'.format(user)], shell=True, stdout=subprocess.PIPE, )
    userPolicy = proc.communicate()[0]
    userPolicy = str(userPolicy)
    policyLength = re.search('129600', userPolicy).group()
    policyLength = int(policyLength)
    print(policyLength)
    # I like having prints just to watch watch for failures at certain points

    proc = subprocess.Popen(['/usr/sbin/mkpassdb -dump {0}'.format(uid)], shell=True, stdout=subprocess.PIPE, )
    passLastChanged = proc.communicate()[0]
    passLastChanged = str(passLastChanged)

    #this is the shitty regular expression to search for the exact formatting of the policy length of the user queried, this would be probably different for you

    passLastChanged = re.search('Last password change:\W+(t)([0-9]+/[0-9]+/[0-9]+[0-9]\W+[0-9]+:[0-9]+[0-9]:[0-9]+[0-9]\W+AM)', passLastChanged).group(2)
    passLastChangedTime = datetime.datetime.strptime(passLastChanged, "%m/%d/%Y %H:%M:%S %p")
    expDate = passLastChangedTime + datetime.timedelta(days=90)
    delta = expDate - datetime.datetime.now()
    daysLeft = delta.days
    daysLeft = int(daysLeft)
    print(daysLeft, "Days until PW Expiration")

    return daysLeft


f = open('test.csv', 'r') #open file
try:
    r = csv.reader(f) #init csv reader
    for row in r:
        daysLeftForUser = evaluate_password_expiry(row[2], row[0])
        if daysLeftForUser <= 10:
            email_user(row[1], daysLeftForUser)
        else:break
finally:
    f.close() #cleanup

