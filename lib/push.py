""" Library that checks dependencies of the new packages against the to_repo
and copies the corresponding debuginfo subpackages. """
###############################################################################
#Programmer: Orcan Ogetbil    orcan@nbcs.rutgers.edu                          #
#Date: 10/20/2010                                                             #
#Filename: push.py                                                            #
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

import datetime

def check_packages(app, kojisession, packages, to_repo):
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
            if not pkgtags:
                app.logger.error('Package ' +  str(package) + ' has no valid tags!')
                app.exit(3)
            if to_repo in pkgtags:
                app.logger.error("Error: " + package + " is already in the "
                                 + to_repo + " repo.")
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


def get_replaced_packages(app,kojisession,packages,to_repo):
    """Find if the package we're pushing replaces any other packages
    in the repository"""
    replaced_pkgs = []
    # set multicall to false for now so we can get results
    kojisession.multicall = False
    for pkg in packages:
        pkg_split = pkg.split("-")
        # last two fields are release and version, everything else must be name
        pkg_name = "-".join(pkg_split[:-2])
        results = kojisession.getLatestRPMS(to_repo,pkg_name)
        # returns list of lists of packages (all builds for a given package)
        for res in results:
            for build in res:
                if 'nvr' in build:
                    if 'tag_info' in build and build['tag_info'] == to_repo:
                        replaced_pkgs.append(build['nvr'])
                        break

    # set multicall back to true
    kojisession.multicall = True
    return replaced_pkgs


def push_packages(app, kojisession, packages, to_repo, user,test):
    """ Tag into the to_repo. Return a message with the results
    to be emailed """
    kojitmpsession = app.get_koji_session(ssl = False)
    kojisession.multicall = True

    message = ""
    packagelist = ""
    changelogs = ""

    # get the packages that will be replaced by this push
    replaced_pkgs = get_replaced_packages(app,kojisession,packages,to_repo)
    # untag all the pkgs, they will be replaced
    for pkg in replaced_pkgs:
        kojisession.untagBuildBypass(to_repo, pkg)

    for package in packages:
        app.logger.info("Tagging " + package + " into " + to_repo)
        if not test:
            kojisession.tagBuildBypass(to_repo, package)
        message += package+"\n"
        packagelist += package+", "
        changelogs += """
%s
%s """ % (package, "-"*len(package))
        clog = kojitmpsession.getChangelogEntries(package)
        for entry in range(min(len(clog), 3)):
            tstamp = datetime.date.fromtimestamp(
                clog[entry]["date_ts"]).strftime("%a %b %d %Y")
            author = clog[entry]["author"]
            text = clog[entry]["text"]
            changelogs += """
* %s %s
%s
""" % (tstamp, author, text)

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
    email_subject = distname_nice + " - Push Successful: " + packagelist
    if test:
        test_msg = "TEST: nothing actually applied"
    else:
        test_msg = ""
    email_body = """
%s
The following package(s) are pushed by %s to %s :

%s

The following package(s) were pulled from %s:

%s

The repos are regenerated. The package(s) are ready to use.

Changelogs:
%s
""" % (test_msg, user, to_repo, message, to_repo, '\n'.join(replaced_pkgs), changelogs)
    return [email_subject, email_body]
