Rutgers Repository Tools
========================
Rutgers Repository Tools is a set of tools used by Open System Solutions on
CentOS machines for the RPM package publishing process. These tools work in
conjunction with Koji and uses it's Python API. It also relies on some Python
code in yum-utils.

To change any configuration options, simply edit the configuration file, which
by default is stored at `/etc/rutgers-repotools.cfg`.

Prerequisites
-------------
In summary, an imaginary Koji user `roji` does the tagging and
untagging of packages on Koji, sending email with the results of its operations.

These tools are designed to run on a system which has read and write access to
the Koji PostgreSQL database, as well as write access to the Rutgers RPM
repositories.  In order to access the Koji database and perform tagging
operations, `roji` needs SSL certificates generated and installed in the Koji
certificate directory (typically `/etc/pki/koji`).

An external MySQL database also needs to be created with write access to dump
the package information, which will be used by rpm2python.  If the database is
to be accessed by a remote machine (e.g. that runs rpm2python), the necessary
privileges need to be provided. As of this writing, this suite of tools lives on
omachi.

Publishing Scripts
------------------
Scripts for publishing to repositories.

### pushpackage
The main publishing script. This takes packages from a repository (tag) and
copies it (tags it) to a given target repository. Note that this does not erase
existing tags. This also checks the dependencies of the packages against the
repository they are being moved to with the depcheck script. At the end of the
push, mail is sent, indicating success or failure.

An example:

     $ pushpackage centos6-rutgers-testing rutgers-repotools-0.7.0-1.ru6

### pullpackage
This script does the opposite of pushpackage: it takes a package from a
repository and untags it. Before this occurs, it does dependency checking to
make sure that an existing package does not depend on the removed one.

The pullpackage script takes arguments in the same style as pushpackage.

### movepackage
Moves a package from one repository to another. This is merely a convenience
script that runs pullpackage on the package from its original repository and
then pushes it to the new target.

Note that there is no restriction on moving packages between different
versions - for example, you can pull a package from CentOS 5 and push it to
CentOS 6.

Other Scripts
-------------
These scripts do dependency checking, regenerate repositories, perform backups,
and so on.

### depcheck
Does dependency checking on a given repository. This is a hack that uses
repoclosure from the yum-utils package. Essentially, it pretends that our
repository is a Yum repository, then has Yum do the dependency checking for us.

This script is run as part of the daily checks cron job; it call also be run by
hand if desired. Mail is sent if broken dependencies are found.

It's possible to give a list of exceptions for broken dependencies that this
script will ignore. By default, the list is installed at `/etc/depcheck.ignore`.
However, it's best to avoid using exceptions and fix the broken dependencies
properly. 

### repocheck
Does sanity checks on the repositories for a given distribution version. More
specifically, it checks to make sure that there are no packages newer in stable
than in testing (and, optionally, newer in testing than in unstable).

### populate-rpmfind-db
Updates or rebuilds from scratch the RPM database. This information is then used
by rpm2python to display repository and package information in the Rutgers web
interface.

Note that rebuilding from scratch assumes the existence of a running Koji server.

### rebuild-repos
This script can recreate all of the publish repositories from scratch. This uses
the Koji API to get the latest packages from a specific tag/repository. Then,
this creates symlinks from Koji's packages directory into a temporary directory.
Finally, this then creates repository metadata in the temporary directory. The
new repository is then transfered from the temporary location into the actual
repository.

For more information about where these directories are located, see the
configuration file.

### rpmdb-backup
This is a simple rotating backup script for the rpmfind database. The location
of the backups and the total number of backups to keep should be specified on
the command line; however, the cron job pulls this information from the config
file and runs it automatically. You can run it by hand if you know what you're
doing!

### koji-backup
This dumps the PostgreSQL Koji database and saves it as a backup. Like the
rpmdb-backup script, it takes its arguments from the command line, but the cron
job automatically uses information from the configuration file by default.

Authors
=======
The dependency checking script depcheck.py is a heavily modified version of
Fedora's spam-o-matic from the mash project. You can find them at
http://pkgs.fedoraproject.org/cgit/mash.git/.

The rest is written by Orcan Ogetbil, Jarek Sedlacek, Kaitlin Poskaitis, and
Kyle Suarez of Rutgers University Open System Solutions.

For a list of recent changes, see the CHANGELOG.

License
=======
This software is licensed under the GNU General Public License. See LICENSE
for more info.
