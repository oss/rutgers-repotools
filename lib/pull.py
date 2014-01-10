""" Library that checks dependencies of the packages that will be removed from
the from_repo and copies the corresponding debuginfo subpackages. """
###############################################################################
#Programmer: Orcan Ogetbil    orcan@nbcs.rutgers.edu                          #
#Date: 10/20/2010                                                             #
#Filename: pull.py                                                            #
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


def check_packages(app, kojisession, packages, from_repo):
    """ Check if the given packages are really there
    If they are, return the tags associated with them"""
    clean = True

    for package in packages:
        if package.count("-") < 2 or package[0] == "-" or package[-1] == "-":
            app.logger.error("Error: Invalid NVR fromat: " + package)
            clean = False

    if clean == False:
        app.exit(2)

    pkgstags = []
    for package in packages:
        binfo = kojisession.getBuild(package)
        pkgtags = []
        if binfo:
            btag = kojisession.listTags(package)
            for tag in btag:
                pkgtags.append(tag["name"][tag["name"].find("-")+1:])
            if not from_repo in pkgtags:
                app.logger.error("Error: " + package + " is not in the "
                                 + from_repo + " repo.")
                clean = False
        else:
            app.logger.error("Error: " + package + " not found in koji.")
            clean = False
        pkgstags.append(pkgtags)

    if clean == False:
        app.exit(2)

    return pkgstags


def debug_check(app, packages):
    """ Check whether the given packages have associated debuginfo packages. """
    kojitmpsession = app.get_koji_session(ssl = False)

    for package in packages:
        build = kojitmpsession.getBuild(package)
        rpmlist = kojitmpsession.listRPMs(build["id"])
        for irpm in rpmlist:
            if irpm['name'].find("-debuginfo") != -1:
                app.logger.info("Found debuginfo packages.")
                return True

    app.logger.info("No debuginfo packages.")
    return False


def pull_packages(app, kojisession, packages, from_repo, user):
    """ Untag from the repos. Return a message with the results
    to be emailed """
    kojisession.multicall = True

    message = ""
    packagelist = ""
    # Remove the from_repo tags from the package
    for package in packages:
        app.logger.info("Untagging "+ package + " from " + from_repo)
        kojisession.untagBuildBypass(from_repo, package)
        message += package+"\n"
        packagelist += package+", "

    # Truncate the trailing comma
    packagelist = packagelist[:-2]

    # Get the results
    results = kojisession.multiCall()

    clean = True
    for i in range(len(results)):
        try:
            if results[i]['faultString']:
                app.logger.error("Error: " + results[i]['faultString'])
                clean = False
        except (KeyError, TypeError):
            pass
    if clean == False:
        app.exit(2)

    distname_nice = app.config.get("repositories", "distname_nice")
    email_subject = distname_nice + " - Pull Successful: " + packagelist
    email_body = """
The following package(s) are pulled by %s from %s :

%s

The repos are regenerated. The package(s) are ready to use.

""" % (user, from_repo, message)
    return [email_subject, email_body]
