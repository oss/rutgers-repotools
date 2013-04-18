""" Application handler class that contains common functions to use in our 
scripts """
###############################################################################
#Programmer: Orcan Ogetbil    orcan@nbcs.rutgers.edu                          #
#Date: 10/21/2010                                                             #
#Filename: rcommon.py                                                         #
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

import os
import sys
import grp
import getpass
import inspect
import time
import ConfigParser
import koji
import logging
import rlogger

class AppHandler:
    """ Repotool application handler class """
    def __init__(self, verifyuser = True, config_file='/etc/rutgers-repotools.cfg'):
        self.config = None
        self.load_config(config_file)
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
	    #print "We were called from " + self._callername 

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

    def get_koji_session(self, ssl = False):
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
            print "Error: Please do not run this script as root."
            sys.exit(1)

        members = grp.getgrnam(self.groupowner)[3]
        if not self.username in members:
            print "Error: The user who runs this script must belong to the group: " + self.groupowner
            sys.exit(1)

    def load_config(self, config_file):
        """ Load configuration from file """
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_file)
        
    def time_run(self):
        """ Calculate time run """
        return round(time.time() - self._start_time, 3)

    def check_lock(self):
        """ Stop if there is a lock file for this application """
        if self._lockfilename == None:
            print "No lockfile specified in the configuration for the application"
            sys.exit(1)
        if os.path.isfile(self._lockfilename): 
            if is_running():
                remove_lock()
            else:
                print "Process is currently running. Please wait for it to finish"
        lockers = self.config.options('locks')
        for locker in lockers:
            lockfilename = self.config.get('locks', locker)
            if os.path.isfile(lockfilename):
                if is_running():
                    remove_lock()
                else:
                    print "Process is currently running. Please wait for it to finish"    
                    sys.exit(1)

    def create_lock(self):
        """ Create a lock file for this application """
        self.check_lock()
        lockfile = open(self._lockfilename, "w")
        lockfile.write(os.getpid())
        
    def remove_lock(self):
        """ Delete the lock file of this application """
        if os.path.isfile(self._lockfilename):
            os.remove(self._lockfilename)
    
    def is_running(self):
        lockfile = open(self._lockfilename, "r")
        try:
            os.kill(lockfile.readline(), 0)
            lockfile.close()
            return 1
        except:
            lockfile.close()
            return 0

    def exit(self, status=0):
        """ Exit from application gracefully """
        if self._lockfilename:
            self.remove_lock()

        gid = grp.getgrnam(self.groupowner)[2]
        private_dir = self.config.get('repositories', 'repodir_private')
        if os.stat(private_dir)[5] != gid:
            self.logger.info("Chowning " + private_dir + " to group " + self.groupowner)
            # Recursively chown private_dir
            for root, dirs, files in os.walk(private_dir):
                for path in dirs:
                    os.chown(os.path.join(root, path), -1, gid, follow_symlinks=false)
                for path in files:
                    os.chown(os.path.join(root, path), -1, gid, follow_symlinks=false)
                    

        # Make sure the log file ends up with the right group owner:
        if self._logfile:
            if os.stat(self._logfile)[5] != gid:
                os.chown(self._logfile, -1, gid)
        sys.exit(status)
