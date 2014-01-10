#!/usr/bin/env python
"""
This script checks the sanity of the Rutgers repository structure. In
particular, it makes sure there is no package newer in stable than testing, or
newer in testing than unstable."""

import sys,os,re,mx.Tools
import smtplib
from email.MIMEText import MIMEText
# For comparing versions and releases sanely and easily
from pkg_resources import parse_version

#send mail if things are broken?
SEND_MAIL=1

MAILTO="oss@oss.rutgers.edu"
MAILFROM="repo-check@omachi.rutgers.edu"
CENTOS_VERSION="5"
if "--version=6" in sys.argv:
    CENTOS_VERSION="6"


#location of the repos
STABLE_REPO="/army/rpmprivate/centos/rutgers/rutgers/" + CENTOS_VERSION
TESTING_REPO="/army/rpmprivate/centos/rutgers/rutgers-testing/" + CENTOS_VERSION
UNSTABLE_REPO="/army/rpmprivate/centos/rutgers/rutgers-unstable/" + CENTOS_VERSION


def send_mail(msg):
    msg = ""
    msg += "From: " + MAILFROM + "\r\n"
    msg += "To: " + MAILTO + "\r\n"
    msg += "Subject: CentOS " + CENTOS_VERSION + " Repo Check\r\n"
    msg += output
    s = smtplib.SMTP('localhost')
    s.sendmail(MAILFROM,[MAILTO],msg)
    s.quit



def checkRepo(olderRepo, newerRepo,oldRepoName,newRepoName):

    output = ""
    test_srpms = {}
    #put all rpms in our newer repo into the dictionary
    for filename in os.listdir(newerRepo+ "/SRPMS/"):
        
        if filename.endswith(".src.rpm"):
            filename = filename.replace(".src.rpm","")
            parts = filename.split("-")
            # last 2 fields are version #, rest are package name
            packagename =  "-".join(parts[:-2])
            packageversion =  "-".join(parts[-2:])
            test_srpms[packagename] = packageversion
    #how many packages are newer in oldRepoName than newRepoName?
    numProblems =0              
    #check all packages in oldRepoName to see if there is an older version in newRepoName   
    for filename in os.listdir(olderRepo+ "/SRPMS/"):
        if filename.endswith(".src.rpm"):
            filename = filename.replace(".src.rpm","")
            parts = filename.split("-")
            packagename =  "-".join(parts[:-2])
            packageversion =  "-".join(parts[-2:])
            #if this package is in the newRepoName repo, see if its older
            if packagename in test_srpms:
                if parse_version(packageversion) > parse_version(test_srpms[packagename]):
                    output += packagename + " is version " + packageversion + " in " + oldRepoName+ ", which is newer than " + test_srpms[packagename] + " in " + newRepoName + "\n"
                    numProblems +=1
    return (numProblems, output)


if __name__=="__main__":
    if "--no-mail" in sys.argv:
        SEND_MAIL=0 
    numProblems,output = checkRepo(STABLE_REPO,TESTING_REPO,"stable","testing")
    otherProblems,otherOutput = checkRepo(TESTING_REPO,UNSTABLE_REPO,"testing","unstable")
    numProblems += otherProblems
    output += otherOutput
    #get rid of trailing newline
    output = output.strip()
    if numProblems == 0:
        print "CentOS " + CENTOS_VERSION + " repos are sane"
    else:
        output = "The following CentOS " + CENTOS_VERSION + " packages have problems:\n" + output
        if(SEND_MAIL):
            send_mail(output)
        else:
            print output
