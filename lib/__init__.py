""" Init scripts to run our repotools """
###############################################################################
#Programmer: Orcan Ogetbil    orcan@nbcs.rutgers.edu                          #
#Date: 11/11/2010                                                             #
#Filename: __init.py__                                                        #
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
import sys
import os
import logging
import string
import time

import genrepo
import populatedb
import pull
import push
import checkdep
import sendspam
import rcommon

os.umask(002)

# Repository goes in the wrapper
# distver goes in the app handler (rcommon)

def parse_distrepo(distrepo):
    """ Parses a distribution/repository name into its constituent parts.

    Takes a full distribution and repository name like 'centos6-rutgers-staging'
    and splits it up into the appropriate parts.  If the name is badly
    formatted, this method returns (None, None, None) - that is, None for all
    parts. Otherwise, it returns a tuple containing (distname, distversion,
    repository).
    
    For simplicity's sake, this assumes that the distribution version is a
    simple number after the distrepo name; this can be changed for
    future versions."""
    # NOTE: if this becomes more complicated, feel free to replace the
    # loop with a proper regular expression.
    if distrepo is None:
        return None, None, None

    index1 = distrepo.find("-")
    if index1 == -1:
        return None, None, None

    # Find the distribution version
    for i in range(0, index1):
        if distrepo[i].isdigit():
            index2 = i
            return (distrepo[:index2], distrepo[index2:index1],
                    distrepo[index1+1:])
    else:
        return None, None, None


def add_time_run(body, timerun):
    """ Adds a line to include time run on the email to be sent """
    timerun = str(timerun)
    body += """

Time run: %s seconds

""" % (timerun)
    return body


def run_depcheck(my_config_file='/etc/rutgers-repotools.cfg'):
    """ Runs the actual script """
    os.umask(002)
    myapp = rcommon.AppHandler(verifyuser=True,config_file=my_config_file)

    versions = myapp.config.get("repositories", "alldistvers").split()
    distname = myapp.config.get("repositories", "distname")
    repos = get_publishrepos(myapp)
    repos.append("upstream")

    usage = "usage: %prog [options] <distro>-<repo>\n\n"
    usage += "  <distro>       one of: " + string.join([distname + v for v in versions], " ") + "\n"
    usage += "  <repo>         one of: " + string.join(repos, " ") + "\n"

    parser = OptionParser(usage)
    parser.add_option("--nomail",
                      action="store_true",
                      help="Do not send email notification")
    parser.add_option("-v", "--verbose",
                      default=False,
                      action="store_true",
                      help="Verbose output")
    parser.add_option("-q", "--quiet",
                      default=False,
                      action="store_true",
                      help="Don't output anything")

    (options, args) = parser.parse_args(sys.argv[1:])

    if options.nomail:
        mail = False
    else:
        mail = True

    if options.verbose:
        verbosity = logging.DEBUG
    else:
        verbosity = logging.INFO

    if len(args) != 1:
        print "Error: Invalid number of arguments: ", args
        print "Exactly one repository argument is expected."
        myapp.exit(1)

    distro, distver, check_repo = parse_distrepo(args[0])
    if distro is None or distver is None or check_repo is None:
        myapp.logger.error("Error: Badly formatted distribution, version or repository.")
        myapp.exit(1)
    if distro != distname:
        myapp.logger.error("Error: '" + distro + "' is not a valid distribution name.")
        myapp.exit(1)
    if not distver in versions:
        myapp.logger.error("Error: '" + distro + distver + "' is not a valid distribution version.")
        myapp.exit(1)
    if not check_repo in repos:
        print "Error: Invalid from_repo: ", check_repo
        myapp.exit(1)

    myapp.init_logger(verbosity, options.quiet)
    myapp.distver = distver

    results = checkdep.doit(myapp, check_repo)
    timerun = myapp.time_run()
    if results:
        if mail:
            email_subject = myapp.config.get("repositories", "distname_nice") + " - Broken dependencies"
            problem = "The routine daily check has found dependency problems.\n"
            email_body = problem + results
            email_body = add_time_run(email_body, timerun)
            myapp.logger.warning("Sending email...")
            sendspam.sendspam(myapp, email_subject, email_body, scriptname="depcheck")
        myapp.logger.error("There are broken dependencies.")

    myapp.logger.info("\nSuccess! Time run: " + str(timerun) + " s")
    myapp.exit()


def run_populate_rpmfind_db(my_config_file='/etc/rutgers-repotools.cfg'):
    """ Utility to update rpmfind database """
    os.umask(002)
    myapp = rcommon.AppHandler(verifyuser=True,config_file=my_config_file)
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-r", "--rebuild",
                      default=False,
                      action="store_true",
                      help="Cleans and rebuilds the whole database.")
    parser.add_option("-v",
                      "--verbose",
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

    distname = myapp.config.get("repositories", "distname_nice")
    alldistvers = myapp.config.get("repositories", "alldistvers").split()
    for distver in alldistvers:
        myapp.distver = distver
        myapp.logger.info("Populating rpmfind database for {0} {1}...".format(
            distname, distver))
        populatedb.update_db(myapp, options.rebuild, options.rebuild)

    timerun = myapp.time_run()
    myapp.logger.info("\nSuccess! Time run: " + str(timerun) + " s")

    myapp.exit()


def run_pullpackage(my_config_file='/etc/rutgers-repotools.cfg'):
    """ Wrapper function to remove packages from repos. """
    os.umask(002)
    myapp = rcommon.AppHandler(verifyuser=True,config_file=my_config_file)

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
    distro, distver, from_repo = parse_distrepo(args[0])
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


def pullpackage(myapp, mail, test, force, distname, distver, from_repo,
                packages, checkdep_from_repo=False):
    """ The actual puller."""
    from_repos = myapp.config.get("repositories", "allrepos").split()
    user = myapp.username
    kojisession = myapp.get_koji_session(ssl = True)
    pkgstags = pull.check_packages(myapp, kojisession, packages, from_repo)

    # We only need to depcheck the from_repo if it does not inherit
    # from parent repos that the packages are tagged with

    from_indices = []
    for pkgtags in pkgstags:
        indices = []
        for tag in pkgtags:
            indices.append(from_repos.index(tag))
        from_indices.append(min(indices))

    for index in from_indices:
        if from_repos.index(from_repo) <= index:
            checkdep_from_repo = True

    # Do not do dependency checking when --force flag is given
    if not force:
        if checkdep_from_repo:
            results = checkdep.doit(myapp, from_repo, packages, True)
            depcheck_results(myapp, user, packages, results, mail)
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


def run_movepackage(my_config_file='/etc/rutgers-repotools.cfg'):
    """ Wrapper function around pullpackage and pushpackage."""
    myapp = rcommon.AppHandler(verifyuser=True,config_file=my_config_file)

    # Repository information
    # Note that you may pull from the staging repository but not pull from it
    versions = myapp.config.get("repositories", "alldistvers").split()
    distname = myapp.config.get("repositories", "distname")
    from_repos = myapp.config.get("repositories", "allrepos").split()
    to_repos = get_publishrepos(myapp)

    usage =  "usage: %prog [options] <distro>-<from_repo> <distro>-<to_repo> <package(s)>\n\n"
    usage += "  <distro>        one of: " + string.join([distname + v for v in versions], " ") + "\n"
    usage += "  <from_repo>     one of: " + string.join(from_repos, " ") + "\n"
    usage += "  <to_repo>       one of: " + string.join(to_repos, " ") + "\n"
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
                      help="Do the dependency checking and exit. No actual pushes are made.")
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

    if len(args) < 3:
        myapp.logger.error("Error: Too few arguments: " + str(args))
        myapp.logger.error("Run with --help to see correct usage")
        myapp.exit(1)

    if options.nomail:
        mail = False
    else:
        mail = True

    if options.test:
        mail = False
        myapp.logger.warning("This is a test run. No packages will be moved. No emails will be sent.")

    # Examine the arguments
    packages = args[2:]
    from_distro, from_distver, from_repo = parse_distrepo(args[0])
    to_distro, to_distver, to_repo = parse_distrepo(args[1])

    # Sanity checks
    if from_distro is None or from_distver is None or from_repo is None:
        myapp.logger.error("Error: Badly formatted source distribution, version or repository.")
        myapp.exit(1)
    if to_distro is None or to_distver is None or to_repo is None:
        myapp.logger.error("Error: Badly formatted destination distribution, version or repository.")
        myapp.exit(1)
    if from_distro != distname or to_distro != distname:
        myapp.logger.error("Error: Source and/or destination distributions are not valid.")
        myapp.exit(1)
    if not from_distver in versions:
        myapp.logger.error("Error: '" + from_distro + from_distver + "' is not a valid distribution version.")
        myapp.exit(1)
    if not to_distver in versions:
        myapp.logger.error("Error: '" + to_distro + to_distver + "' is not a valid distribution version.")
        myapp.exit(1)
    if not from_repo in from_repos:
        myapp.logger.error("Error: Invalid from_repo: " + from_repo)
        myapp.exit(1)
    if not to_repo in to_repos:
        myapp.logger.error( "Error: Invalid to_repo: " + to_repo)
        myapp.exit(1)
    if from_repo == to_repo:
        myapp.logger.error("Error: from_repo cannot be equal to to_repo.")
        myapp.exit(1)

    myapp.distver = to_distver
    pushpackage(myapp, mail, options.test, options.force, to_distro, to_distver, to_repo, packages, True)
    myapp.distver = from_distver
    pullpackage(myapp, mail, options.test, options.force, from_distro, from_distver, from_repo, packages, True)

    timerun = myapp.time_run()
    if options.test:
        myapp.logger.warning("End of test run. " + str(timerun) + " s")
    else:
        myapp.logger.info("Success! Time run: " + str(timerun) + " s")

    myapp.exit(0)


def run_pushpackage(my_config_file="/etc/rutgers-repotools.cfg"):
    """ Wrapper function to publish packages. """
    os.umask(002)
    myapp = rcommon.AppHandler(verifyuser=True,config_file=my_config_file)

    # Grab all the repository information from the config file
    versions = myapp.config.get("repositories", "alldistvers").split()
    distname = myapp.config.get("repositories", "distname")
    to_repos = get_publishrepos(myapp)

    # Usage, etc.
    usage =  "usage: %prog [options] <distro>-<to_repo> <package(s)>\n\n"
    usage += "  <distro>     one of: " + string.join([distname + v for v in versions], " ") + "\n"
    usage += "  <to_repo>       one of: " + string.join(to_repos, " ") + "\n"
    usage += "  <package(s)>    A list of packages in NVR format"
    parser = OptionParser(usage)
    parser.add_option("--nomail",
                      action="store_true",
                      help="Do not send an email notification.")
    parser.add_option("-f", "--force",
                      action="store_true",
                      help="Do not do dependency checking.")
    parser.add_option("-t", "--test",
                      default=False,
                      action="store_true",
                      help="Do the dependency checking and exit. No actual pushes are made.")
    parser.add_option("-v", "--verbose",
                      default=False,
                      action="store_true",
                      help="Verbose output.")

    # Parse the command line arguments
    (options, args) = parser.parse_args(sys.argv[1:])
    if len(args) < 2:
        myapp.logger.error("Error: Too few arguments: " + str(args))
        myapp.logger.error("Run with --help to see correct usage")
        myapp.exit(1)

    # Create the lock file
    myapp.create_lock()

    # Set the logger and other options
    verbosity = logging.DEBUG if options.verbose else logging.INFO
    myapp.init_logger(verbosity)
    mail = not options.nomail
    if options.test:
        mail = False
        myapp.logger.warning("This is a test run. No packages will be pushed. No emails will be sent.")

    # Examine the arguments
    packages = args[1:]
    distro, distver, to_repo = parse_distrepo(args[0])
    if (distro is None or distver is None or to_repo is None):
        myapp.logger.error("Error: Badly formatted distribution, version or repository.")
        myapp.exit(1)

    # Sanity checks for the distro name, version, repository, etc.
    if distro != distname:
        myapp.logger.error("Error: '" + distro + "' is not a valid distribution name.")
        myapp.exit(1)
    if not distver in versions:
        myapp.logger.error("Error: '" + distro + distver + "' is not a valid distribution version.")
        myapp.exit(1)
    if not to_repo in to_repos:
        myapp.logger.error( "Error: Invalid to_repo: " + to_repo)
        myapp.exit(1)

    myapp.distver = distver

    # Run the script and time it
    localtime = time.asctime(time.localtime(time.time()))
    myapp.logger.info("Push started on", localtime)
    pushpackage(myapp, mail, options.test, options.force, distname, distver, to_repo, packages)
    timerun = myapp.time_run()
    if options.test:
        myapp.logger.warning("End of test run. " + str(timerun) + " s")
    else:
        myapp.logger.info("Success! Time run: " + str(timerun) + " s")

    myapp.exit(0)


def pushpackage(myapp, mail, test, force, distname, distver, to_repo, packages,
                checkdep_to_repo=False):
    """ The actual pusher. """
    to_repos = get_publishrepos(myapp)
    user = myapp.username
    kojisession = myapp.get_koji_session(ssl = True)
    pkgstags = push.check_packages(myapp, kojisession, packages, to_repo)

    to_indices = []
    for pkgtags in pkgstags:
        indices = []
        for tag in pkgtags:
            try:
                indices.append(to_repos.index(tag))
            except ValueError:
                # May be in the staging repo
                indices.append(99)

        to_indices.append(min(indices))

    for index in to_indices:
        if to_repos.index(to_repo) < index:
            checkdep_to_repo = True

    # Do not do dependency checking when --force flag is given
    if not force:
        if checkdep_to_repo:
            results = checkdep.doit(myapp, to_repo, packages)
            depcheck_results(myapp, user, packages, results, mail)
        else:
            myapp.logger.info("The specified packages are already inherited from a parent repo.")
            myapp.logger.info("No need to do dependency checking.")

    if test:
        myapp.logger.info("Test of pushpackage complete.")
    else:
        pushresults = push.push_packages(myapp, kojisession, packages,
                                     distname + distver + "-" + to_repo,
                                     user,test)

        # We are not exposing the build repos anymore. So create our own repo
        myapp.logger.info("Next, regenerate repositories and expose.")

        dontpublishrepos = myapp.config.get("repositories",
                                            "dontpublishrepos").split()
        repostodebug = myapp.config.get("repositories", "repostodebug").split()

        dbgcheck = push.debug_check(myapp, packages)
        debugrepo_built = False
        repo_built = False

        if not to_repo in dontpublishrepos:
            if debugrepo_built or not to_repo in repostodebug:
                dbgcheck = 0
            genrepo.gen_repos(myapp, [to_repo], dbgcheck)
            repo_built = True

        if repo_built:
            populatedb.update_db(myapp, False, False)

        if mail:
            timerun = myapp.time_run()
            myapp.logger.info("Finally, sending email.")
            email_body = add_time_run(pushresults[1], timerun)
            sendspam.sendspam(myapp, pushresults[0], email_body, scriptname="pushpackage")


def run_rebuild_repos(my_config_file='/etc/rutgers-repotools.cfg'):
    """ Rebuilds rutgers rpm repos """
    os.umask(002)
    myapp = rcommon.AppHandler(verifyuser=True,config_file=my_config_file)

    versions = myapp.config.get("repositories", "alldistvers").split()
    distname = myapp.config.get("repositories", "distname")
    debugrepo = myapp.config.get("repositories", "debugrepo")
    repos = get_publishrepos(myapp)
    repos.append(debugrepo)
    repos.append("")

    usage = "usage: %prog [options] <distro>-<repo> ... \n\n"
    usage += "  <distro>    one of: " + string.join([distname + v for v in versions], " ") + "\n"
    usage += "  <repo>      one of: " + string.join(repos, " ") + "\n\n"
    usage += "You may specify several <distro>-<repo> arguments by separating by whitespace.\n"
    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose",
                      default=False,
                      action="store_true",
                      help="Verbose output")

    (options, args) = parser.parse_args(sys.argv[1:])
    myapp.create_lock()

    # Set logger verbosity
    if options.verbose:
        verbosity = logging.DEBUG
    else:
        verbosity = logging.INFO
    myapp.init_logger(verbosity)

    if len(args) < 1:
        print "Error: Too few arguments. We need at least one repo."
        myapp.exit(1)

    to_rebuild = dict([(v, []) for v in versions])

    # Do sanity checks on the repos and sort them according to version
    for dr in [parse_distrepo(x) for x in args]:
        dname, dist, repo = dr
        if dname is None or dist is None or repo is None:
            myapp.logger.error("Error: Badly formatted distribution, version, or repository.")
            myapp.exit(1)
        elif dname != distname:
            myapp.logger.error("Error: " + dname + " is not valid.")
            myapp.exit(1)
        elif repo not in repos and repo != "all":
            myapp.logger.error("Error: Invalid repo: " + repo)
            myapp.exit(1)
        elif dist not in versions:
            myapp.logger.error("Error: centos" + repo + " is not a valid distribution version.")
            myapp.exit(1)
        else:
            to_rebuild[dist].append(repo)

    # Finally, do the actual genrepo call
    for dist, buildrepos in to_rebuild.iteritems():
        myapp.distver = dist
        if len(buildrepos) <= 0:
            continue
        elif "all" in buildrepos:
            builddebug = True
            buildrepos = repos[:]
            buildrepos.remove(debugrepo)
            buildrepos.remove("")
        elif debugrepo in buildrepos:
            builddebug = True
            buildrepos.remove(debugrepo)
        else:
            builddebug = False
        genrepo.gen_repos(myapp, buildrepos, builddebug)

    timerun = myapp.time_run()
    myapp.logger.info("\nSuccess! Time run: " + str(timerun) + " s")
    myapp.exit()


def depcheck_results(myapp, user, packages, results, mail):
    """ Emails the results of the dependency check if something is broken. """
    distver = myapp.distver
    if not results in ["", "baddep"]:
        guilt = "The push attempt of " + user
        guilt += " with the following package(s) failed on " + myapp.config.get("repositories","distname_nice") + distver + ":\n"
        for package in packages:
            guilt += package + "\n"
        timerun = myapp.time_run()
        if mail:
            email_subject = myapp.config.get("repositories", "distname_nice") \
                            + distver + " - Broken dependencies"
            email_body = guilt + add_time_run(results, timerun)
            myapp.logger.warning("Sending email...")
            sendspam.sendspam(myapp, email_subject, email_body, scriptname="depcheck")
        myapp.logger.error(guilt)
        myapp.logger.error("There are broken dependencies. We stop here.")
        myapp.logger.info("\nTime run: " + str(timerun) + " s")
        myapp.exit(2)
    elif results == "baddep":
        myapp.exit(1)


def get_publishrepos(app):
    """ Calculates the list of repos to be published."""
    to_repos = app.config.get("repositories", "allrepos").split()
    for drepo in app.config.get("repositories","dontpublishrepos").split():
        if drepo in to_repos:
            to_repos.remove(drepo)
    return to_repos
