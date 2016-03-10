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

# Finally, run the setup
setup(name         = 'rutgers-repotools',
      version      = '0.7.14',
      description  = 'Dependency checking and publish scripts',
      author       = 'Open System Solutions',
      author_email = 'oss@oss.rutgers.edu',
      url          = 'https://github.com/oss/rutgers-repotools/',
      license      = 'GPLv2+',
      platforms    = ['linux'],
      long_description  = """This package contains Rutgers tools needed to check
        the dependencies of new packages. This also installs a daily cron job
        which checks for broken dependencies in the Rutgers tree and sends email
        to report problems.
      """,
      packages     = ['RUtools'],
      package_dir  = {'RUtools': 'lib'},
      data_files   = [('/etc', ['conf/depcheck.ignore.sample', 'conf/rutgers-repotools.cfg.sample']),
                      ('/etc/cron.daily', ['cron/daily_checks'])],
      scripts      = ['bin/depcheck',
                      'bin/koji-backup',
                      'bin/movepackage',
                      'bin/populate-rpmfind-db',
                      'bin/pullpackage',
                      'bin/pushpackage',
                      'bin/rebuild-repos',
                      'bin/repocheck',
                      'bin/rpmdb-backup'])
