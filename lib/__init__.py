"""
A suite of tools for managing Rutgers repositories.
"""

import ConfigParser
import getpass
import grp
import inspect
import koji
import logging
import os
import rlogger
import sys
import time

class UserError(Exception):
    """
    Errors caused by the user doing something invalid.
    """
    pass


class DependencyError(Exception):
    """
    Occurs when a broken dependency is detected.
    """
    pass


class ConfigurationError(Exception):
    """
    Occurs if the configuration file is malformed or invalid.
    """
    pass


class AppHandler:
    """
    An application helper class.
    """
    def __init__(self, verifyuser=True, config_file='/etc/rutgers-repotools.cfg'):
        """
        Initializes loggers, reads the config file and begins timing.
        """
        # Read the config file
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_file)

        # Examine this user's credentials
        self.username = getpass.getuser()
        self.groupowner = self.config.get("repositories", "groupowner")
        if verifyuser:
            self.verify_user()

        # what script is calling this function?
        self._callerfile = inspect.stack()[-1][1]
        self._callername = self._callerfile.split("/")[-1]
        try:
            self._lockfilename = self.config.get("locks", self._callername)
        except ConfigParser.NoOptionError:
            self._lockfilename = None

        self._start_time = time.time()
        self.logger = None
        self._logfile = None
        self._kojisession_with_ssl = None

    def init_logger(self, level=logging.INFO, quiet=False):
        """ Initialize loggers """
        self._logfile = self.config.get("logs", self._callername)
        the_suspect = self.config.get("report","user")+"-" + self.username
        rlogger.init(self._logfile, the_suspect, self.config, level, quiet)
        self.logger = logging.getLogger(the_suspect)

    def get_koji_session(self, ssl=False):
        """ Get a koji session with or without SSL access"""
        if self._kojisession_with_ssl and ssl:
            return self._kojisession_with_ssl

        hub = self.config.get('koji','hub')
        kojisession = koji.ClientSession(hub)
        if ssl:
            clientcert = self.config.get('koji','clientcert')
            clientca = self.config.get('koji','clientca')
            serverca = self.config.get('koji','serverca')
            kojisession.ssl_login(clientcert, clientca, serverca)
            self._kojisession_with_ssl = kojisession
        return kojisession

    def verify_user(self):
        """ See if we want to run our application for this user """
        if self.username == "root":
            raise UserException("User should not be root.")

        members = grp.getgrnam(self.groupowner)[3]
        if not self.username in members:
            raise UserException(
                    "User is not a member of group {}.".format(self.groupowner))

    def time_run(self):
        """ Calculate time run """
        return round(time.time() - self._start_time, 3)

    def check_lock(self):
        """ Stop if there is a lock file for this application """
        if self._lockfilename is None:
            raise ConfigurationError("No lock file specified in configuration.")

        lockers = self.config.options('locks')
        for locker in lockers:
            lockfilename = self.config.get('locks', locker)
            if os.path.isfile(lockfilename):
                if not AppHandler.is_running(lockfilename):
                    AppHandler.remove_lock(lockfilename)
                else:
                    raise UserError("Another process is already running.")

    def create_lock(self):
        """ Create a lock file for this application """
        self.check_lock()
        lockfile = open(self._lockfilename, "w")
        lockfile.write(str(os.getpid()))

    @staticmethod
    def remove_lock(lockfilename):
        """ Delete the lock file of this application """
        if os.path.isfile(lockfilename):
            os.remove(lockfilename)

    @staticmethod
    def is_running(lockfilename):
        lockfile = open(lockfilename, "r")
        try:
            os.kill(int(lockfile.readline()), 0)
            lockfile.close()
            return True
        except:
            lockfile.close()
            return False

    def exit(self, status=0):
        """ Exit from application gracefully """
        if self.logger:
            self.logger.debug("Beginning exit and cleanup.")
        else:
            print "Warning: Exiting, but logger has not been initialized."

        if self._lockfilename:
            AppHandler.remove_lock(self._lockfilename)

        gid = grp.getgrnam(self.groupowner)[2]
        private_dir = self.config.get('repositories', 'repodir_private')

        # Check to make sure current process is in correct group
        allgroups = os.getgroups()
        if not gid in allgroups:
            self.logger.warning("Current process is not in the proper group ({0}).".format(gid))

        if os.stat(private_dir)[5] != gid:
            self.logger.info("Chowning " + private_dir + " to group " + self.groupowner)
            # Recursively chown private_dir
            for root, dirs, files in os.walk(private_dir):
                for path in dirs:
                    os.chown(os.path.join(root, path), -1, gid, follow_symlinks=False)
                for path in files:
                    os.chown(os.path.join(root, path), -1, gid, follow_symlinks=False)
        else:
            self.logger.debug("Group ID is {0}: all systems go.".format(gid))

        # Make sure the log file ends up with the right group owner:
        if self._logfile:
            if os.stat(self._logfile)[5] != gid:
                os.chown(self._logfile, -1, gid)
        sys.exit(status)


def parse_distrepo(distrepo):
    """
    Parses a distribution/repository name into its constituent parts.

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
