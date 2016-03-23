""" Re-bastardized version of spam-o-matic from Fedora's mash """
###############################################################################
#Programmer: Orcan Ogetbil    orcan@nbcs.rutgers.edu                          #
#Date: 10/07/2010                                                             #
#Filename: checkdep.py                                                        #
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
#
# Library for checking package dependencies

import os
import shutil
import string
import sys
import tempfile
import re
from optparse import OptionParser
import rcommon, sendspam

from yum.constants import LETTERFLAGS
from yum.misc import getCacheDir

from repoutils import repoclosure
from repoutils import genpkgmetadata

DEPS = {}

def main():
    os.umask(002)
    myapp = rcommon.AppHandler(verifyuser=False)

    versions = myapp.config.get("repositories", "alldistvers").split()
    distname = myapp.config.get("repositories", "distname")
    repos = RUtools.get_publishrepos(myapp)
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

    mail = not options.nomail

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

    results = doit(myapp, check_repo)
    timerun = myapp.time_run()
    if results:
        myapp.logger.error("There are broken dependencies.")

        if mail:
            distname = myapp.config.get("repositories", "distname_nice")
            email_subject = "{0} {1} - Broken Dependencies".format(distname, distver)
            problem = "The routine daily check has found dependency problems.\n"
            email_body = problem + results
            email_body = RUtools.add_time_run(email_body, timerun)
            myapp.logger.warning("Sending email...")
            sendspam.sendspam(myapp, email_subject, email_body, scriptname="depcheck")

    myapp.logger.info("Time run: " + str(timerun) + " s")
    myapp.exit()


def generate_config(app, disttype, arch, tmprepodir="", removal=False):
    """ Generates a yum config file for our purposes """
    (fdesc, conffile) = tempfile.mkstemp()
    relname_nice = app.config.get("repositories", "distname_nice")
    relver = app.distver
    repodir_public = app.config.get("repositories", "repodir_public")
    repodir_private = app.config.get("repositories", "repodir_private")
    repos = get_publishrepos(app)
    distroverpkg = app.config.get("repositories", "distroverpkg")
    confheader = """
[main]
debuglevel=2
logfile=/var/log/yum.log
pkgpolicy=newest
distroverpkg=%s
reposdir=/dev/null
cachedir=/var/tmp/yum
keepcache=0

[base]
name=%s - Base
baseurl=file://%s/%s/os/%s/

[update]
name=%s - Updates
baseurl=file://%s/%s/updates/%s/

#[addons]
#name=%s - Addons
#baseurl=file://%s/%s/addons/%s/

[extras]
name=%s - Extras
baseurl=file://%s/%s/extras/%s/
""" % (distroverpkg,
       relname_nice, repodir_public, relver, arch,
       relname_nice, repodir_public, relver, arch,
       relname_nice, repodir_public, relver, arch,
       relname_nice, repodir_public, relver, arch)

    # In order to check the sanity of upstream CentOS repos:
    if disttype != "upstream":
        for repo in repos:
            if removal and repo == disttype:
                break
            confheader += """
[%s]
name=%s %s Tree
baseurl=file://%s/%s/%s/%s/
""" % (repo, relname_nice, repo,
       repodir_private, repo, relver, arch)
            if not removal and repo == disttype:
                break

    if tmprepodir != "":
        confheader += """
[candidates]
name=New packages
baseurl=file://%s

""" % (tmprepodir)

    app.logger.info("I generated a yum.conf file with the repositories that I")
    app.logger.info("will use to do the dependency checking.")
    app.logger.debug("------------------------yum.conf-----------------------")
    app.logger.debug(confheader)
    app.logger.debug("-------------------------------------------------------")
    os.write(fdesc, confheader)
    os.close(fdesc)
    return conffile


def libmunge(match):
    """ Munge sonames """
    if match.groups()[1].isdigit():
        return "%s%d" % (match.groups()[0], int(match.groups()[1])+1)
    else:
        return "%s%s" % (match.groups()[0], match.groups()[1])

def get_src_pkg(pkg):
    """ Returns the SRPM name """
    if pkg.arch == 'src':
        return pkg.name
    srpm = pkg.returnSimple('sourcerpm')
    if not srpm:
        return None
    srcpkg = string.join(srpm.split('-')[:-2],'-')
    return srcpkg

def printable_req(pkg, dep):
    """ Returns a human readable dependency string """
    (name, depflag, version) = dep
    req = '%s' % name
    if depflag:
        flag = LETTERFLAGS[depflag]
        req = '%s %s' % (req, flag)
    if version:
        req = '%s %s' % (req, version)
    return "%s requires %s" % (pkg, req,)

def assign_blame(resolver, dep):
    """ Given a dep, find potential responsible parties """
    def __addpackages(sack):
        """ Adds providing source packages to sack """
        for package in sack.returnPackages():
            providing_pkg = get_src_pkg(package)
            deplist.append(providing_pkg)

    deplist = []

    # The dep itself
    deplist.append(dep)

    # Something that provides the dep
    __addpackages(resolver.whatProvides(dep, None, None))

    # Libraries: check for variant in soname
    if re.match("lib.*\.so\.[0-9]+", dep):
        new = re.sub("(lib.*\.so\.)([0-9])+", libmunge, dep)
        __addpackages(resolver.whatProvides(new, None, None))
        libname = dep.split('.')[0]
        __addpackages(resolver.whatProvides(libname, None, None))

    return deplist

def generate_spam(pkgname, treename):
    """ Returns the body of the failure email message """
    package = DEPS[pkgname]

    for key in package.keys():
        subpackage = package[key]
        for arch in subpackage.keys():
            brokendeps = subpackage[arch]

    data = """

%s has broken dependencies in the %s tree:
""" % (pkgname, treename)

    for key in package.keys():
        subpackage = package[key]
        for arch in subpackage.keys():
            data = data + "On %s:\n" % (arch)
            brokendeps = subpackage[arch]
            for dep in brokendeps:
                data = data + "\t%s\n" % printable_req(dep[0], dep[1])

    return data


def filterout(app, baddeps):
    """ Filter out the bad dependencies specified in depcheck_ignore file """
    depcheck_ignore = app.config.get("repositories", "depcheck_ignorefile")
    di_file = open(depcheck_ignore, 'r')
    inputtext = di_file.readlines()
    di_file.close()
    ignorelist = []
    for line in range(len(inputtext)):
        if inputtext[line][0] != "#" and inputtext[line] != "\n":
            ignoreitem = inputtext[line].split()
            if len(ignoreitem) == 3:
                ignorelist.append(ignoreitem)
            else:
                app.logger.warning("Could not parse {0}, line {1}".format(depcheck_ignore, line))
                app.logger.warning("\t"+inputtext[line])
                # Bad! We need to quit
                return -1

    pkgs = baddeps.keys()
    for pkg in pkgs:
        remove = 0
        for (name, depflag, version) in baddeps[pkg]:
            if filterrules(ignorelist, pkg.name, name, depflag, version):
                remove = 1
        if remove == 1:
            baddeps.pop(pkg)
    return baddeps

def str_to_regex(expression):
    """ convert str to regex expression """
    r_string = string.replace(expression, ".", "\.")
    r_string = string.replace(r_string, "*", ".*")
    r_string = string.replace(r_string, "+", "\+")
    r_string = string.replace(r_string, "(", "\(")
    r_string = string.replace(r_string, ")", "\)")
    return r_string

def filterrules(ignorelist, name, requires, compare, version):
    """ checks if the broken dep matches anything in the ignorelist"""
    # TODO: We don't do anything with the compare flags yet. This is to be
    # implemented
    for ignoreitem in range(len(ignorelist)):
        myname = ignorelist[ignoreitem][0]
        myrequires = ignorelist[ignoreitem][1]
        myversion = ignorelist[ignoreitem][2]

        if string.find(ignorelist[ignoreitem][0], "*") > -1:
            ignore_regex_name = re.compile(str_to_regex(
                                              ignorelist[ignoreitem][0]
                                           ))
            if ignore_regex_name.match(name):
                myname = name
        if string.find(ignorelist[ignoreitem][1], "*") > -1:
            ignore_regex_requires = re.compile(str_to_regex(
                                              ignorelist[ignoreitem][1]
                                           ))
            if ignore_regex_requires.match(requires):
                myrequires = requires
        # Version may not be given, in which case it is a None type object
        if string.find(ignorelist[ignoreitem][2], "*") > -1:
            ignore_regex_version = re.compile(str_to_regex(
                                              ignorelist[ignoreitem][2]
                                           ))
            if version == None:
                myversion = version
            elif ignore_regex_version.match(version):
                myversion = version

        if name == myname and requires == myrequires and version == myversion:
            return True
    return False

def create_tmp_repo(app, packages, arch, removalfromrepo = ""):
    """ Creates a temporary repo with the specified packages and arch """
    kojisession = app.get_koji_session(ssl = False)
    tempprefix = 'tmprepo-'+arch+'-'
    tempdir = tempfile.mkdtemp(prefix=tempprefix)

    if removalfromrepo:
        # We need to hack this through since there is no suitable Python API for
        # the "cp a/* b/" command
        os.rmdir(tempdir)
        app.logger.info("Populating temporary repo " + tempdir +
                        " with candidate packages removed from " + removalfromrepo)
        app.logger.info("Copying the original repo to the temporary location")
        distver = app.distver
        repodir_org = app.config.get("repositories", "repodir_private") + "/" + \
                      removalfromrepo + "/" + distver + "/" + arch
        shutil.copytree(repodir_org, tempdir, symlinks=True)
        removal_list = []
        add_list = []
        for package in packages:
            buildinfo = kojisession.getBuild(package)
            bid = buildinfo["id"]
            rmlst = kojisession.listRPMs(bid)
            for rpm in rmlst:
                if string.find(rpm['name'], "-debuginfo") == -1 and rpm['arch'] in [arch, "noarch"]:
                    removal_list.append(rpm['nvr'] + "." + rpm['arch'] + ".rpm")

            next_largest_build_id = -1
            next_largest_build = None
            tagname = app.config.get("repositories", "distname") + distver + "-" + removalfromrepo
            allbuilds = kojisession.listTagged(tagname, package=buildinfo["name"])
            for build in allbuilds:
                if build["build_id"] > next_largest_build_id and build["build_id"] != buildinfo["id"]:
                    next_largest_build_id = build["build_id"]
                    next_largest_build = build
            if next_largest_build_id == -1:
                addlst = []
            else:
                addlst = kojisession.listRPMs(next_largest_build_id)
            for rpm in addlst:
                if string.find(rpm['name'], "-debuginfo") == -1 and rpm['arch'] in [arch, "noarch"]:
                    packagedir = app.config.get("koji", "pkgdir") + '/' + \
                         next_largest_build['name'] + '/' + next_largest_build['version'] + \
                         '/' + next_largest_build['release'] + '/' + rpm['arch']
                    add_list.append([packagedir, rpm['nvr'] + "." + rpm['arch'] + ".rpm"])

        app.logger.info("Remove the subject packages from the temporary repo")
        for item in removal_list:
            app.logger.info("Removing: " + item)
            os.remove(tempdir + "/" + item)

        app.logger.info("Add next most recent builds to the temporary repo, if there are any")
        if add_list == []:
            app.logger.info("Nope... No other build for this package")
        for item in add_list:
            app.logger.info("Adding: " + item[1])
            os.symlink(item[0] + "/" + item[1], tempdir + "/" + item[1])

        app.logger.info("Writing metadata")
        genpkgmetadata.main(["--update", tempdir])

    else:
        app.logger.info("Populating temporary repo " + tempdir +
                        " with candidate packages.")
        for package in packages:
            buildinfo = kojisession.getBuild(package)
            packagedir = app.config.get("koji", "pkgdir") + '/' + \
                         buildinfo['name'] + '/' + buildinfo['version'] + \
                         '/' + buildinfo['release']
            # First copy arch specific RPM's
            # TODO the arch thing so it looks cooler and not dumb
            try:
                rpmfiles = os.listdir(packagedir+'/'+arch)
                for rpmfile in rpmfiles:
                    if (rpmfile.endswith('.rpm') and string.find(rpmfile, 'debuginfo')) == -1:
                        app.logger.info("Adding " + rpmfile)
                        os.symlink(packagedir + "/" + arch + "/" + rpmfile,
                                   tempdir + "/" + rpmfile)
            except OSError, ex:
                app.logger.warning("Source package " + package +
                                   " does not produce " + arch + " RPM's.")
                app.logger.debug(str(type(ex))+str(ex))
            # Next copy noarch RPM's
            if os.path.isdir(packagedir+'/noarch'):
                try:
                    rpmfiles = os.listdir(packagedir+'/noarch')
                    for rpmfile in rpmfiles:
                        if rpmfile.endswith('.rpm'):
                            app.logger.info("Adding " + rpmfile)
                            os.symlink(packagedir + "/noarch/" + rpmfile,
                                       tempdir + "/" + rpmfile)
                except IOError, ex:
                    app.logger.debug(str(type(ex))+str(ex))
        app.logger.info("Writing metadata")
        genpkgmetadata.main([tempdir])
    return tempdir

def doit(app, repotype, packages = [], removal = False):
    """Check the dependencies of the package repo
    
    This is done with repoclosure, which is from the yum python module. Given
    a yum configuration file, repoclosure is able to process the metadata
    of the repo and calculate dependencies. We create a temporary directory,
    copy the repo files to the temp directory, and generate a yum config
    file for the directory so repoclosure can do its thing.

    Arguments:
    app - an instance of the rcommon apphandler
    repotype - 
    packages - 
    removal - 
    """

    i_am_broken = False

    archs = app.config.get("repositories", "archs").split()
    for arch in archs:
        app.logger.info("Arch: " + arch)
        if packages != []:
            if removal:
                tmprepodir = create_tmp_repo(app, packages, arch, repotype)
            else:
                tmprepodir = create_tmp_repo(app, packages, arch)
        else:
            tmprepodir = ""

        conffile = generate_config(app, repotype, arch, tmprepodir, removal)
        if not conffile:
            continue
        if arch == 'i386':
            carch = 'i686'
        elif arch == 'ppc':
            carch = 'ppc64'
        elif arch == 'sparc':
            carch = 'sparc64v'
        else:
            carch = arch
        app.logger.info("I will next calculate the dependency chains.")
        myrc = repoclosure.RepoClosure(config = conffile, arch = [carch])
        cachedir = getCacheDir(reuse=False)
        myrc.repos.setCacheDir(cachedir)
        app.logger.info("Processing metadata returned from repoclosure...")
        myrc.readMetadata()
        app.logger.info("Now calculate the dependencies...")
        app.logger.info("It might take a minute or two.")
        baddeps = myrc.getBrokenDeps(newest = True)
        baddeps = filterout(app, baddeps)
        if baddeps == -1:
            return "baddep"
        pkgs = baddeps.keys()
        tmplist = [(x.returnSimple('name'), x) for x in pkgs]
        tmplist.sort()
        pkgs = [x for (key, x) in tmplist]
        if len(pkgs) > 0:
            i_am_broken = True
            app.logger.warning("Broken deps for %s" % (arch))
            app.logger.warning("----------------------------------------------")
        else:
            app.logger.info("We are clean. No broken dependencies.")
        for pkg in pkgs:
            srcpkg = get_src_pkg(pkg)

            if not DEPS.has_key(srcpkg):
                DEPS[srcpkg] = {}

            pkgid = "%s-%s" % (pkg.name, pkg.printVer())

            if not DEPS[srcpkg].has_key(pkgid):
                DEPS[srcpkg][pkgid] = {}

            broken = []
            for (name, depflag, version) in baddeps[pkg]:
                app.logger.warning("\t%s" % printable_req(pkg, (name, depflag, version)))
                blamelist = assign_blame(myrc, name)
                broken.append( (pkg, (name, depflag, version), blamelist) )

                DEPS[srcpkg][pkgid][arch] = broken

        if tmprepodir != "":
            app.logger.info("Clean up: removing the temporary repo dir: " +
                           tmprepodir)
            shutil.rmtree(tmprepodir, ignore_errors = True)
        os.unlink(conffile)
        app.logger.info("Clean up: removing the cachedir: "+ cachedir)
        shutil.rmtree(cachedir, ignore_errors = True)
        app.logger.info("Done!\n\n")

    pkglist = DEPS.keys()

    spamdata = ""
    for pkg in pkglist:
        spamdata += generate_spam(pkg, repotype)

    if i_am_broken == True:
        return spamdata
    else:
        return ""


def get_publishrepos(app):
    to_repos = app.config.get("repositories", "allrepos").split()
    for drepo in app.config.get("repositories","dontpublishrepos").split():
        if drepo in to_repos:
            to_repos.remove(drepo)
    return to_repos
