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
import time
import sendspam, rcommon, checkdep, genrepos, populatedb
from optparse import OptionParser

def main():
    """ Parses command line arguments and dispatches request to pushpackage """
    os.umask(002)
    myapp = rcommon.AppHandler(verifyuser=True)

    # Grab all the repository information from the config file
    versions = myapp.config.get("repositories", "alldistvers").split()
    distname = myapp.config.get("repositories", "distname")
    to_repos = RUtools.get_publishrepos(myapp)

    # Usage, etc.
    usage =  "usage: %prog [options] <distro>-<to_repo> <package(s)>\n\n"
    usage += "  <distro>     one of: " + string.join([distname + v for v in versions], " ") + "\n"
    usage += "  <to_repo>       one of: " + string.join(to_repos, " ") + "\n"
    usage += "  <package(s)>    A list of packages in NVR format"
    parser = OptionParser(usage)
    parser.add_option("--nomail", action="store_true",
                      help="Do not send an email notification.")
    parser.add_option("-f", "--force", action="store_true",
                      help="Do not do dependency checking.")
    parser.add_option("-t", "--test", default=False, action="store_true",
                      help="Do the dependency checking and exit. No actual pushes are made.")
    parser.add_option("-v", "--verbose", default=False, action="store_true",
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
    distro, distver, to_repo = RUtools.parse_distrepo(args[0])
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
    
    pushpackage(myapp, mail, options.test, options.force, distname, distver, 
            to_repo, packages)
    
    timerun = myapp.time_run()
    
    if options.test:
        myapp.logger.warning("End of test run. " + str(timerun) + " s")
    else:
        myapp.logger.info("Success! Time run: " + str(timerun) + " s")
    myapp.exit(0)


def pushpackage(myapp, mail, test, force, distname, distver, to_repo, packages,
                checkdep_to_repo=False):
    """ Pushes a package to the given repo by making the appropriate 
    Koji tag changes.

    Arguments:
    myapp - an instance of rcommon apphandler
    mail - if True will send an email with the results
    force - if True will not perform dependency checking
    distname - name of the distro, e.g. 'centos'. TODO: why is this needed?
    distver - version of distro, e.g. 6 for centos6
    to_repo - the repo to push the package to
    packages - a list of packages to push
    checkdep_to_repo - TODO: unused
    """
    user = myapp.username
    kojisession = myapp.get_koji_session(ssl=True)

    # Do not do dependency checking when --force flag is given
    if not force:
        if depcheck_is_necessary(kojisession, packages, to_repo):
            results = checkdep.doit(myapp, to_repo, packages)
            RUtools.depcheck_results(myapp, user, packages, results, mail)
        else:
            myapp.logger.info("The specified packages are already inherited from a parent repo.")
            myapp.logger.info("No need to do dependency checking.")

    if not test:
        errors = update_tags(myapp, kojisession, packages,
                             "{}{}-{}".format(distname, distver, to_repo))
        emaildata = prepare_email(app, packages, errors)

        if errors:
            for error in errors:
                myapp.logger.error(error)
        else:
            # We are not exposing the build repos anymore. So create our own repo
            myapp.logger.info("Next, regenerate repositories and expose.")

            dontpublishrepos = myapp.config.get("repositories",
                                            "dontpublishrepos").split()
            repostodebug = myapp.config.get("repositories", "repostodebug").split()

            dbgcheck = debug_check(myapp, packages)
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
            email_body = RUtools.add_time_run(emaildata[1], timerun)
            sendspam.sendspam(myapp, emaildata[0], email_body, scriptname="pushpackage")
    else:
        myapp.logger.info("Test of pushpackage complete.")


def depcheck_is_necessary(kojisession, packages, repo):
    """ Returns true if a depcheck is needed with this push
    
    A depcheck is needed when the package is pushed up the parent-child repo
    chain -- for example, if the package is in staging and is being pushed
    to stable. This depends on a correct ordering of repos in the config
    file """
    pkgstags = koji_get_tags(myapp, kojisession, packages, repo)
    to_repos = RUtools.get_publishrepos(myapp)

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
        if to_repos.index(repo) < index:
            return True

    return False


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

def koji_get_tags(app, kojisession, packages, repo):
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
                app.logger.error('Package {0} already exists in {1}.'.format(
                    package, repo))
                clean = False
        else:
            # Nothing found in Koji
            app.logger.error("Package {0} does not exist in Koji.".format(package))
            clean = False
        allpkgtags.append(pkgtags)

    if clean == False:
        app.exit(2)
    return allpkgtags


def koji_untag_packages(app, kojisession, repo, packages):
    for package in packages:
        app.logger.info("Tagging {} to {}".format(package, repo))
        kojisession.untagBuildBypass(repo, package)

def koji_tag_packages(app, kojisession, repo, packages):
    for package in packages:
        app.logger.info("Tagging {} to {}".format(package, repo))
        kojisession.tagBuildBypass(repo, package)

def koji_get_errors_from_result(app, results):
    return [r['faultString'] for r in results if 'faultString' in r]


def update_tags(app, kojisession, packages, to_repo):
    """ Tag into the to_repo. Returns an array of errors encountered """
    kojitmpsession = app.get_koji_session(ssl = False)
    kojisession.multicall = True

    # Untag replaced packages and tag pushed packages
    replaced_pkgs = get_replaced_packages(app, kojisession, packages, to_repo)
    koji_untag_packages(app, kojisession, to_repo, replaced_pkgs)
    koji_tag_packages(app, kojisession, to_repo, packages)

    # Apply changes to Koji
    results = kojisession.multiCall()
    errors = koji_get_errors_from_result(results)

    for error in errors:
        app.logger.error(error)

    return errors
    

def get_changelogs(kojisession, packages):
    for package in packages:
        message.append(package)
        packagelist.append(package)
        changelogs += """
%s
%s """ % (package, "-"*len(package))
        clog = kojisession.getChangelogEntries(package)
        for entry in range(min(len(clog), 3)):
            tstamp = unicode(datetime.date.fromtimestamp(
                clog[entry]["date_ts"]).strftime("%a %b %d %Y"), "utf-8")
            try:
                author = unicode(clog[entry]["author"], "utf-8")
            except TypeError:
                author = clog[entry]["author"]
            try:
                text = unicode(clog[entry]["text"], "utf-8")
            except TypeError:
                text = clog[entry]["text"]
            changelogs += """
* %s %s
%s
""" % (tstamp, author, text)

    return changelogs

def prepare_email(app, packagelist, errors):
    distname = app.config.get("repositories", "distname_nice")
    distver = app.distver
    packagelist = ", ".join(packagelist)

    if errors:
        email_subject = "{0} {1} - Push Failed - {2}".format(distname, distver, packagelist)
        email_body = "\n".join(errors)
        sendspam.sendspam(app, email_subject, email_body, scriptname="pushpackage")
        app.exit(2)
    else:
        email_subject = "{0} {1} - Push Successful - {2}".format(distname, 
                distver, packagelist)
        email_body = []

        message = '\t' + '\n\t'.join(message)
        replaced = '\t' + '\n\t'.join(replaced_pkgs) if replaced_pkgs else "\tNone!"
        if test:
            email_body.append("Test Results")
            email_body.append("(No packages have actually been pushed.)\n")

        email_body.append(u"""The following packages have been pushed by {0} to {1}:

{2}

The following packages were pulled from {1}:

{3}

The repositories are regenerated and the packages are ready to use.

Recent changes:
{4}
    """.format(user, to_repo, message, replaced, changelogs))
        email_body = u"\n".join(email_body)
        email_body.strip()

        return [email_subject, email_body]
