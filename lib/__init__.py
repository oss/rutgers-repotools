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
import _mysql
import _mysql_exceptions
from MySQLdb.constants import FIELD_TYPE

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

DEFAULT_CONFIG_PATH = "/etc/rutgers-repotools.cfg"

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

def get_publishrepos(app):
    """ Calculates the list of repos to be published."""
    to_repos = app.config.get("repositories", "allrepos").split()
    for drepo in app.config.get("repositories","dontpublishrepos").split():
        if drepo in to_repos:
            to_repos.remove(drepo)
    return to_repos


def add_time_run(body, timerun):
    """ Adds a line to include time run on the email to be sent """
    timerun = str(timerun)
    body += "\n\nTime run: {0} seconds\n".format(timerun)
    return body


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


def depcheck_results(myapp, user, packages, results, mail, action="push"):
    """ Emails the results of the dependency check if something is broken. """
    distver = myapp.distver
    distname = myapp.config.get("repositories", "distname_nice")
    if not results in ["", "baddep"]:
        guilt = "{0} attempted and failed to {1} the following packages to {2} {3}:".format(user, action, distname, distver)
        for package in packages:
            guilt += "\t" + package + "\n"
        timerun = myapp.time_run()
        if mail:
            email_subject = "{0} {1} - Broken Dependencies".format(distname, distver)
            email_body = guilt + add_time_run(results, timerun)
            myapp.logger.warning("Sending email...")
            script = "{0}package".format(action)
            sendspam.sendspam(myapp, email_subject, email_body, scriptname=script)
        myapp.logger.error(guilt)
        myapp.logger.error("There are broken dependencies. We stop here.")
        myapp.logger.info("\nTime run: " + str(timerun) + " s")
        myapp.exit(2)
    elif results == "baddep":
        myapp.exit(1)



