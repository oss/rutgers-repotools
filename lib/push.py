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
import sendspam

def check_packages(app, kojisession, packages, to_repo):
    """ Check if the given packages are really there
    If they are, return the tags associated with them"""
    clean = True

    # NOTE: This should be replaced by a more sophisticated check
    for package in packages:
        if package.count("-") < 2 or package[0] == "-" or package[-1] == "-":
            app.logger.error("Error: Invalid NVR fromat: " + package)
            clean = False

    if clean == False:
        app.exit(2)

    allpkgtags = []
    for package in packages:
        # Get the build information from Koji
        buildinfo = kojisession.getBuild(package)
        pkgtags = []
        if buildinfo:
            # Find all tags associated with this package
            tags = kojisession.listTags(package)
            for tag in tags:
                pkgtags.append(tag["name"])

            if not pkgtags:
                # Contains no Koji tags
                app.logger.error('Package {0} has no valid tags!'.format(package))
                clean = False
            if to_repo in pkgtags:
                # Already exists in the target repository
                app.logger.error('Package {0} already exists in {1}.'.format(package, to_repo))
                clean = False
        else:
            # Nothing found in Koji
            app.logger.error("Package {0} does not exist in Koji.".format(package))
            clean = False
        allpkgtags.append(pkgtags)

    if clean == False:
        app.exit(2)
    return allpkgtags

def debug_check(app, packages):
    """ Check whether the given packages have associated debuginfo packages. """
    kojitmpsession = app.get_koji_session(ssl=False)

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


def push_packages(app, kojisession, packages, to_repo, user, test):
    """ Tag into the to_repo. Return a message with the results
    to be emailed """
    # NOTE: This could use some cleanup in the future
    kojitmpsession = app.get_koji_session(ssl = False)
    kojisession.multicall = True
    message = []
    packagelist = []
    changelogs = ""

    # get the packages that will be replaced by this push
    replaced_pkgs = get_replaced_packages(app,kojisession,packages,to_repo)

    # untag all the pkgs, they will be replaced
    for pkg in replaced_pkgs:
        kojisession.untagBuildBypass(to_repo, pkg)

    for package in packages:
        app.logger.info("Tagging " + package + " into " + to_repo)
        if not test:
            # This does the actual Koji "pushing" if it's not a test
            kojisession.tagBuildBypass(to_repo, package)

        message.append(package)
        packagelist.append(package)
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

    # Get the results
    results = kojisession.multiCall()

    # Look for errors
    clean = True
    errors = []
    for i in range(len(results)):
        try:
            if results[i]['faultString']:
                app.logger.error("Error: " + results[i]['faultString'])
                errors.append("Error: " + results[i]['faultString'])
                clean = False
        except (KeyError, TypeError):
            app.logger.debug("pushpackage triggered an error while looking for errors")
            pass

    # Prepare for the email
    distname = app.config.get("repositories", "distname_nice")
    distver = app.distver
    packagelist = ", ".join(packagelist)

    if clean == False:
        email_subject = "{0} {1} - Push Failed - {2}".format(distname, distver, packagelist)
        email_body = "\n".join(errors)
        sendspam.sendspam(app, email_subject, email_body, scriptname="pushpackage")
        app.exit(2)
    else:
        email_subject = "{0} {1} - Push Successful - {2}".format(distname, distver, packagelist)
        email_body = []

        message = '\t' + '\n\t'.join(message)
        replaced = '\t' + '\n\t'.join(replaced_pkgs) if replaced_pkgs else "None!"
        if test:
            email_body.append("Test Results")
            email_body.append("(No packages have actually been pushed.)\n")

        email_body.append("""The following packages have been pushed by {0} to {1} :

{2}

The following packages were pulled from {1}:

{3}

The repositories are regenerated and the packages are ready to use.

Recent changes:
{4}
    """.format(user, to_repo, message, replaced, changelogs))
        email_body = "\n".join(email_body)
        email_body.strip()

        return [email_subject, email_body]
