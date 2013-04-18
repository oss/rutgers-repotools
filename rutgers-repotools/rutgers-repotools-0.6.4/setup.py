#!/usr/bin/env python

from distutils.core import setup
from distutils import dir_util, file_util
import sys

args = sys.argv[1:]
buildroot = ""
for arg in range(len(args)):
    if args[arg] == "--root":
        buildroot = args[arg+1]

if "install" in args:
    dir_util.mkpath(buildroot + '/var/log/rutgers-repotools')
    #file_util.write_file(buildroot + '/var/log/rutgers-repotools/checkrepo.log', "")
    #file_util.write_file(buildroot + '/var/log/rutgers-repotools/populate-rpmfind-db.log', "")
    #file_util.write_file(buildroot + '/var/log/rutgers-repotools/pushpackage.log', "")
    #file_util.write_file(buildroot + '/var/log/rutgers-repotools/rebuild-repos.log', "")

setup(name         = 'rutgers-repotools',
      version      = '0.6.5',
      description  = 'Dependency check and publish scripts',
      author       = 'Orcan Ogetbil',
      author_email = 'oss@oss.rutgers.edu',
      url          = 'http://cvs.rutgers.edu/cgi-bin/viewvc.cgi/trunk/orcan/rutgers-repotools/',
      license      = 'GPLv2+',
      platforms    = ['linux'],
      long_description  = """This package contains the tools we use to check the dependencies of
                             new packages. This also installs a daily cron job which checks
                             the dependency situation in the rutgers tree and sends an email
                             if there is anything broken.""",
      packages     = ['RUtools'],
      package_dir  = {'RUtools': 'lib'},
      data_files   = [('/etc', ['conf/depcheck.ignore', 'conf/rutgers-repotools.cfg', 'conf/rutgers-repotools-centos6.cfg', 'conf/depcheck6.ignore']),
                      ('/etc/cron.daily', ['cron/depcheck_rutgers', 'cron/depcheck_rutgers6'])],
      scripts      = ['bin/checkrepo',
                      'bin/checkrepo6',
                      'bin/populate-rpmfind-db',
                      'bin/movepackage',
                      'bin/pullpackage',
                      'bin/pushpackage',
                      'bin/rebuild-repos',
                      'bin/populate-rpmfind-db6',
                      'bin/movepackage6',
                      'bin/pullpackage6',
                      'bin/pushpackage6',
                      'bin/rebuild-repos6']
     )
