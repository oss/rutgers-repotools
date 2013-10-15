""" Sends OSS the results of the pushpackage process. """
###############################################################################
#Programmer: Orcan Ogetbil    orcan@nbcs.rutgers.edu                          #
#Date: 08/12/2010                                                             #
#Filename: sendspam.py                                                        #
#                                                                             #
#                                                                             #
#       Copyright 2010 Orcan Ogetbil                                          #
#                                                                             #
#    This program is free software; you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation; either version 2 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
###############################################################################

import sys
import smtplib

def sendspam(app, subject, body):
    """ spam us baby """
    fromaddr = app.config.get("report", "from_addr")
    toaddrs = app.config.get("report", "to_addr")

    msg = """From: %s
To: %s
Subject: %s

%s

""" % (fromaddr, toaddrs, subject, body)

    smtp_host = app.config.get("report", "smtp_host")
    server = smtplib.SMTP(smtp_host)
    server.set_debuglevel(1)
    smtplib.stderr = sys.stdout
    try:
        server.sendmail(fromaddr, toaddrs, msg)
    except:
        app.logger.error('sending mail failed')
