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

from optparse import OptionParser
import time
import rcommon, sendspam


def main():
    """ Wrapper function to remove packages from repos. """
    os.umask(002)
    myapp = rcommon.AppHandler(verifyuser=True)

    # Grab repository information
    versions = myapp.config.get("repositories", "alldistvers").split()
    distname = myapp.config.get("repositories", "distname")
    from_repos = myapp.config.get("repositories", "allrepos").split()

    usage =  "usage: %prog [options] <distro>-<from_repo> <package(s)>\n\n"
    usage += "  <distro>     one of: " + string.join([distname + v for v in versions], " ") + "\n"
    usage += "  <from_repo>     one of: " + string.join(from_repos, " ") + "\n"
    usage += "  <package(s)>    A list of packages in NVR format"
    parser = OptionParser(usage)
    parser.add_option("--nomail",
                      action="store_true",
                      help="Do not send email notification")
    parser.add_option("-f", "--force",
                      action="store_true",
                      help="Do not do dependency checking")
    parser.add_option("-t", "--test",
                      default=False,
                      action="store_true",
                      help="Do the dependency checking and exit. No actual pulls are made.")
    parser.add_option("-v", "--verbose",
                      default=False,
                      action="store_true",
                      help="Verbose output")

    (options, args) = parser.parse_args(sys.argv[1:])
    myapp.create_lock()

    if options.verbose:
        verbosity = logging.DEBUG
    else:
        verbosity = logging.INFO
    myapp.init_logger(verbosity)


    if len(args) < 2:
        myapp.logger.error("Error: Too few arguments: " + str(args))
        myapp.logger.error("Run with --help to see correct usage")
        myapp.exit(1)

    if options.nomail:
        mail = False
    else:
        mail = True

    if options.test:
        mail = False
        myapp.logger.warning("This is a test run. No packages will be pulled. No emails will be sent.")

    # Examine the command line arguments
    packages = args[1:]
    distro, distver, from_repo = RUtools.parse_distrepo(args[0])
    if (distro is None or distver is None or from_repo is None):
        myapp.logger.error("Error: Badly formatted distribution, version or repository.")
        myapp.exit(1)

    # Lots of checks
    if distro != distname:
        myapp.logger.error("Error: '" + distro + "' is not a valid distribution name.")
        myapp.exit(1)
    if not distver in versions:
        myapp.logger.error("Error: '" + distro + distver + "' is not a valid distribution version.")
        myapp.exit(1)
    if not from_repo in from_repos:
        myapp.logger.error("Error: Invalid from_repo: " + from_repo)
        myapp.exit(1)

    myapp.distver = distver

    # Run the script and time it
    localtime = time.asctime(time.localtime(time.time()))
    myapp.logger.info("Pull started on", localtime)
    pullpackage(myapp, mail, options.test, options.force, from_repo, packages)
    timerun = myapp.time_run()
    if options.test:
        myapp.logger.warning("End of test run. " + str(timerun) + " s")
    else:
        myapp.logger.info("Success! Time run: " + str(timerun) + " s")

    myapp.exit(0)


def pullpackage(myapp, mail, test, force, from_repo, packages, checkdep_from_repo=False):
    """ The actual puller."""
    # Data
    user = myapp.username
    distver = myapp.distver
    distname = myapp.config.get("repositories", "distname")
    from_repos = myapp.config.get("repositories", "allrepos").split()

    # Get the full names of the repositories
    from_repo_full = "{0}{1}-{2}".format(distname, distver, from_repo)
    full_repos = ["{0}{1}-{2}".format(distname, distver, x) for x in from_repos]

    # Find all of the tags associated with the packages
    kojisession = myapp.get_koji_session(ssl=True)
    pkgstags = pull.check_packages(myapp, kojisession, packages, from_repo_full)

    # We only need to depcheck the from_repo if it does not inherit
    # from parent repos that the packages are tagged with

    # This algorithm assumes that the repositories are placed in a standard
    # order (most general to most specific). If we are pushing upwards, we must
    # do dependency checking; otherwise we skip it

    # If there exists a tag in pkgtags that does not exist in full_repos, emit a
    # warning instead of crashing.

    from_indices = []
    for pkgtags in pkgstags:
        indices = []
        for tag in pkgtags:
            try:
                indices.append(full_repos.index(tag))
            except ValueError:
                myapp.logger.warning(
                        "Tag {0} is not one of {1}".format(tag, full_repos))
        from_indices.append(min(indices))

    for index in from_indices:
        if from_repos.index(from_repo) <= index:
            checkdep_from_repo = True

    # Do not do dependency checking when --force flag is given
    if not force:
        if checkdep_from_repo:
            results = checkdep.doit(myapp, from_repo, packages, True)
            depcheck_results(myapp, user, packages, results, mail, action="pull")
        else:
            myapp.logger.info("The specified packages are already inherited from a parent repo.")
            myapp.logger.info("No need to do dependency checking.")

    if test:
        myapp.logger.info("Test of pullpackage complete.")
    else:
        pullresults = pull.pull_packages(myapp, kojisession, packages,
                                         distname + distver + "-" + from_repo,
                                         user)

        # We are not exposing the build repos anymore. So create our own repo
        myapp.logger.info("Next, regenerate repositories and expose.")

        dontpublishrepos = myapp.config.get("repositories",
                                            "dontpublishrepos").split()
        repostodebug = myapp.config.get("repositories", "repostodebug").split()

        dbgcheck = pull.debug_check(myapp, packages)
        debugrepo_built = False
        repo_built = False

        if not from_repo in dontpublishrepos:
            if from_repo in repostodebug and dbgcheck == True:
                debugrepo_built = True
            genrepo.gen_repos(myapp, [from_repo], debugrepo_built)
            repo_built = True

        if repo_built:
            populatedb.update_db(myapp, False, False)

        if mail:
            timerun = myapp.time_run()
            myapp.logger.info("Finally, sending email.")
            email_body = add_time_run(pullresults[1], timerun)
            sendspam.sendspam(myapp, pullresults[0], email_body, scriptname="pullpackage")

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
