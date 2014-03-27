"""
Utility for sending mail via SMTP.
"""

import sys
import smtplib

def sendmail(fromaddr, toaddrs, subject, body):
    """
    Sends a generic email report.
    """
    msg = """From: {0}
To: {1}
Subject: {2}
{3}
""".format(fromaddr, toaddrs, subject, body)

    smtp_host = app.config.get("report", "smtp_host")
    server = smtplib.SMTP(smtp_host)
    server.set_debuglevel(1)
    smtplib.stderr = sys.stdout
    try:
        server.sendmail(fromaddr, toaddrs, msg)
    except Exception, e:
        app.logger.error("Sending mail failed: " + str(e))


def sendspam(app, subject, body, scriptname="sendspam"):
    """
    Sends a Rutgers Repository Tools report via email.
    """
    fromaddr = app.config.get("report", "from_addr")
    toaddrs = app.config.get("report", "to_addr")
    distname = app.config.get("repositories", "distname_nice")
    distver = app.distver

    msg = """From: {0}
To: {1}
Subject: {2}
{3}
------------------------------------------------------------------------------

{4}

------------------------------------------------------------------------------
This report generated by {3}, a proud member of the Rutgers
Repository Tools family.

For more information, see https://github.com/oss/rutgers-repotools.
""".format(fromaddr, toaddrs, subject, scriptname, body)

    smtp_host = app.config.get("report", "smtp_host")
    server = smtplib.SMTP(smtp_host)
    server.set_debuglevel(1)
    smtplib.stderr = sys.stdout
    try:
        server.sendmail(fromaddr, toaddrs, msg)
    except Exception, e:
        app.logger.error("Sending mail failed: " + str(e))
