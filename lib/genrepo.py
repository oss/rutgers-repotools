""" Library to generate Rutgers rpm repositories """
#
###############################################################################
#Programmer: Orcan Ogetbil    orcan@nbcs.rutgers.edu                          #
#Date: 09/10/2010                                                             #
#Filename: genrepo.py                                                         #
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

import os
import errno
import shutil
import string
import tempfile

from repoutils import genpkgmetadata

def main():
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

def mkdir_p(path):
    """ Creates recursive directories """
    os.umask(002)
    try:
        os.makedirs(path)
    except OSError, exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

def gen_repos(app, repos, builddebug=False):
    """ Generates the repos in a temporary location. Then replaces the old repos
    with the generated ones."""
    os.umask(002)
    tempprefix = 'tmprepodir-'
    repos_tmpdir = tempfile.mkdtemp(prefix=tempprefix)
    repos_dir = app.config.get('repositories', 'repodir_private')
    debugrepo = app.config.get('repositories', 'debugrepo')
    distver = app.distver

    kojisession = app.get_koji_session(ssl = False)
    if builddebug:
        create_debug_repo(app, kojisession, repos_tmpdir)
        app.logger.info("All done creating the debug repo.")
        app.logger.info("Now replace old repo with the new one.")
        debugpath = repos_dir + "/" + debugrepo + "/" + distver
        try:
            shutil.rmtree(debugpath)
        except OSError, exc:
            if exc.errno == errno.ENOENT:
                app.logger.warning("No such file or directory: " + debugpath)
                pass
            else:
                app.logger.error("Unexpected OS error: " + os.strerror(exc.errno))
                raise
        shutil.move(repos_tmpdir + "/debug/" + distver, repos_dir + "/" + debugrepo + "/" + distver)

    if repos:
        for repo in repos:
            create_repo(app, kojisession, repo, repos_tmpdir)
        app.logger.info("All done creating repos.")
        app.logger.info("Now replace old repos with the new ones.")
        for repo in repos:
            infopath = repos_dir + "/" + repo + "/" + distver
            try:
                shutil.rmtree(infopath)
            except OSError, exc:
                if exc.errno == errno.ENOENT:
                    app.logger.warning("No such file or directory: " + infopath)
                    pass
                elif exc.errno == errno.EACCES:
                    app.logger.error("Access permission denied to " + infopath)
                    app.logger.error("Fatal error. See stack trace for more details.")
                    app.logger.error("You should check the group permissions for " +  infopath + "and try pushing again.")
                    raise
                else:
                    app.logger.error("Unexpected OS error: " + os.strerror(exc.errno))
                    raise
            shutil.move(repos_tmpdir + "/" + repo + "/" + distver, repos_dir + "/" + repo + "/" + distver)

    app.logger.info("Cleaning up.")
    shutil.rmtree(repos_tmpdir, ignore_errors = True)


def create_debug_repo(app, kojisession, repos_tmpdir):
    """ Create debug repo. Uses the old repo metadata, if exists, for speed """
    debugrepo = app.config.get('repositories', 'debugrepo')
    relver = app.distver
    repos_dir = app.config.get('repositories', 'repodir_private')
    repo_dir = repos_dir + "/" + debugrepo + "/" + relver
    repo_tmpdir = repos_tmpdir + "/debug/" + relver
    archs = app.config.get('repositories', 'archs').split()
    relname = app.config.get('repositories', 'distname')
    repo_prefix = relname + relver + "-"

    app.logger.info("Creating temporary debug repo at " + repo_tmpdir)
    fresh = False
    for arch in archs:
        mkdir_p(repo_tmpdir + "/" + arch)
        try:
            fromdir = repo_dir + "/" + arch + "/repodata"
            todir = repo_tmpdir + "/" + arch + "/repodata"
            shutil.copytree(fromdir, todir)
        except OSError:
            fresh = True
    if fresh:
        app.logger.warning("No previous record of the debug repo. Creating from scratch.")
    else:
        app.logger.info("We will use the old debug repo metadata to speed things up.")

    repostodebug = app.config.get("repositories", "repostodebug").split()
    latest_rpms = []
    for repo in repostodebug:
        app.logger.info("Retrieving the list of latest packages for repo: " + \
                        repo)
        latest_rpms += kojisession.getLatestRPMS(repo_prefix+repo)[0]

    app.logger.info("Populating debug repo with debuginfo RPMs from: " + \
                    string.join(repostodebug, " "))

    number_of_latest_rpms = len(latest_rpms)
    rpmno = 0

    for rpm in latest_rpms:
        rpmno += 1
        if rpm['name'].find("-debuginfo") == -1:
            continue

        build = kojisession.getBuild(rpm['build_id'])
        koji_pkg_dir = app.config.get('koji','pkgdir')
        nvr_dir = koji_pkg_dir + build['name'] + "/" + build['version'] + \
                  "/" + build['release']
        filename = rpm['name'] + "-" + rpm['version'] + "-" + rpm['release'] + \
                   "." + rpm['arch'] + ".rpm"
        filepath = nvr_dir + "/" + rpm['arch'] + "/" + filename

        try:
            app.logger.debug("Symlinking: " + filename + "(" + str(rpmno) \
                             + "/" + str(number_of_latest_rpms) + ")")
            os.symlink(filepath, repo_tmpdir + "/" \
                           + rpm['arch'] + "/" + filename)
        except OSError, exc:
            # Same RPM might exist in multiple repos (stable, testing)
            if exc.errno == errno.EEXIST:
                pass
            else:
                app.logger.error("Unexpected OS error: " + os.strerror(exc.errno))
                raise

    for archdir in archs:
        if fresh:
            genpkgmetadata.main([repo_tmpdir + "/" + archdir])
        else:
            genpkgmetadata.main(["--update", repo_tmpdir + "/" + archdir])



def create_repo(app, kojisession, repo, repos_tmpdir):
    """ Create a repo. Uses the old repo metadata, if exists, for speed """
    # Uncomment this to strip out those RPMs that are in the parent repos
    # already
    # publishrepos = get_publishrepos(app)
    relver = app.distver
    repos_dir = app.config.get('repositories', 'repodir_private')
    relname = app.config.get('repositories', 'distname')
    repo_prefix = relname + relver + "-"
    repo_dir = repos_dir + "/" + repo + "/" + relver
    repo_tmpdir = repos_tmpdir + "/" + repo + "/" + relver
    archs = app.config.get('repositories', 'archs').split()
    app.logger.info("Creating temporary repo at " + repo_tmpdir)
    fresh = False
    for arch in archs + ["SRPMS"]:
        mkdir_p(repo_tmpdir + "/" + arch)
        try:
            shutil.copytree(repo_dir + "/" + arch + "/repodata",
                            repo_tmpdir + "/" + arch + "/repodata")
        except OSError:
            fresh = True
    if fresh:
        app.logger.warning("No previous record of this repo. Creating from scratch.")
    else:
        app.logger.info("We will use the old repo metadata to speed things up.")

    app.logger.info("Retrieving the list of latest packages for repo: " + repo)
    latest_rpms = kojisession.getLatestRPMS(repo_prefix+repo)[0]
    number_of_latest_rpms = len(latest_rpms)
    rpmno = 0

    app.logger.info("Populating repo: " + repo)
    for rpm in latest_rpms:
        rpmno += 1
        if rpm['name'].find("-debuginfo") > 0:
            # These are handled elsewhere
            continue
        taginfo = kojisession.listTags(rpm['build_id'])
        tags = []
        for info in taginfo:
            tags.append(info['name'])
        if not repo_prefix+repo in tags:
            continue

        # Uncomment this part to strip out those RPMs that are in the parent
        # repos already
        #
        #parentrepos = []
        #index = 0
        #while publishrepos[index] != repo:
        #    parentrepos.append(publishrepos[index])
        #    index += 1
        #rpm_in_a_parent_repo = False
        #for parentrepo in parentrepos:
        #    if repo_prefix+parentrepo in tags:
        #        rpm_in_a_parent_repo = True
        #        break
        #if rpm_in_a_parent_repo:
        #    continue

        build = kojisession.getBuild(rpm['build_id'])
        koji_pkg_dir = app.config.get('koji','pkgdir')
        nvr_dir = koji_pkg_dir + build['name'] + "/" + build['version'] + \
                  "/" + build['release']
        filename = rpm['name'] + "-" + rpm['version'] + "-" + rpm['release'] + \
                   "." + rpm['arch'] + ".rpm"
        filepath = nvr_dir + "/" + rpm['arch'] + "/" + filename

        app.logger.debug("Symlinking: " + filename + "(" + str(rpmno) + "/" + \
                             str(number_of_latest_rpms) + ")")
        if rpm['arch'] == 'noarch':
            for arch in archs:
                os.symlink(filepath, repo_tmpdir + "/" + arch + "/" + filename)
        elif rpm['arch'] == 'src':
            os.symlink(filepath, repo_tmpdir + "/SRPMS/" + filename)
        else:
            os.symlink(filepath, repo_tmpdir + "/" + rpm['arch'] + \
                       "/" + filename)

    for archdir in archs + ["SRPMS"]:
        if fresh:
            genpkgmetadata.main([repo_tmpdir + "/" + archdir])
        else:
            genpkgmetadata.main(["--update", repo_tmpdir + "/" + archdir])


def get_publishrepos(app):
    to_repos = app.config.get("repositories", "allrepos").split()
    for drepo in app.config.get("repositories","dontpublishrepos").split():
        if drepo in to_repos:
            to_repos.remove(drepo)
    return to_repos
