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
            if to_repo not in pkgtags:
                # Doesn't exist in the target repository
                app.logger.error('Package {0} does not exist in {1}.'.format(package, to_repo))
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
    message = []
    packagelist = []

    # Remove the from_repo tags from the package
    for package in packages:
        app.logger.info("Untagging "+ package + " from " + from_repo)
        kojisession.untagBuildBypass(from_repo, package)
        message.append(package)
        packagelist.append(package)

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
            app.logger.debug("pullpackage triggered an error while looking for errors.")
            pass

    # Finally, prepare for the email
    distname = app.config.get("repositories", "distname_nice")
    distver = app.distver
    packagelist = ", ".join(packagelist)

    if clean == False:
        email_subject = "{0} {1} - Pull Failed - {2}".format(distname, distver, packagelist)
        email_body = "\n".join(errors)
        sendspam.sendspam(app, email_subject, email_body, scriptname="pullpackage")
        app.exit(2)
    else:
        message = '\t' + '\n\t'.join(message)
        email_subject = "{0} {1} - Pull Successful - {2}".format(distname, distver, packagelist)
        email_body = []
        email_body.append("""The following packages have been pulled by {0} from {1}:

{2}

The repositories are regenerated and the packages are ready to use.
    """.format(user, from_repo, message))
        email_body = "\n".join(email_body)
        email_body.strip()

        return [email_subject, email_body]
