rutgers-repotools
=================
rutgers-repotools includes the set of tools used by Open System Solutions on
CentOS for the RPM package publishing process. They work in conjunction with
koji, specifically using koji's and yum's python APIs.

The tools are designed to run on a system which has read and write access to
koji's database and write access to the rutgers rpm's repositories. As of this
writing, this machine is omachi.

An imaginary koji user named 'roji' does the tagging and untagging of packages
on koji, and the emailing of the results. In order to access the koji database
and to do (un)tagging operations roji needs SSL certificates. These can be
generated via
```
     #!/bin/bash
     user=roji
     koji add-user ${user}
     koji grant-permission admin ${user}
     sudo -s
     cd /etc/pki/koji
     openssl genrsa -out certs/${user}.key 2048
     openssl req -config ssl.cnf -new -nodes -out certs/${user}.csr -key certs/${user}.key
     openssl ca -config ssl.cnf -keyfile private/koji_ca_cert.key -cert koji_ca_cert.crt \
        -out certs/${user}.crt -outdir certs -infiles certs/${user}.csr
     cat certs/${user}.crt certs/${user}.key > ${user}.pem
```
An external MySQL database needs to be created with write access to dump the package
information, which will be used by rpm2php. We typically use, as root
```
     mysql -u root -p
```
Inside mysql prompt we do:
```
     create database rpmfind;
     grant usage on *.* to roji@localhost identified by 'PASSWORD';
     grant all privileges on rpmfind.* to roji@localhost;
     exit;
```
Then the database can be accessed via
```
     mysql -uroji rpmfind -p
```
If the database is to be accessed by a remote machine (e.g. that runs rpm2php), the 
necessary privileges need to be provided.

Important:  
**Please edit the /etc/rutgers-repotools.cfg file for all options!!!**

Currently, we have 4 scripts: checkrepo, populate-rpmfind-db, pushpackage,
rebuild-repos. Their outputs are logged in `/var/log/rutgers-debuginfo/`.


checkrepo
---------
Checks the sanity of the given repo. It makes use of repoclosure output from
yum-utils. This script is run daily as a cron job. However it can be run
stond-alone, An email is sent to OSS by default if a problem, i.e. a broken
dependency is found. 

It is possible to give a list of exceptions for broken dependencies to this
script that will be ignored. This ignore list is given in file
`/etc/depcheck.ignore`. However, it is best to avoid using exceptions and fix
the broken dependencies properly. The script has the following usage:
```
     usage: checkrepo [options] <repo>

     options:
       -h, --help     show this help message and exit
       --nomail       Do not send email notification
       -v, --verbose  Verbose output
       -q, --quiet    Don't output anything
```

populate-rpmfind-db
-------------------
Updates or rebuilds from scratch the rpmfind repository, that will be accessed by
rpm2php. Rebuilding from scratch assumes the existence of a running koji server.
```
     usage: populate-rpmfind-db [options]

     options:
       -h, --help     show this help message and exit
       -v, --verbose  Verbose output
       -r, --rebuild  Cleans and rebuilds the whole database.
```

pushpackage
-----------
This main push script that does all the magic. This script takes package(s) from
a given repo (tag) and copies (tags) it to another. It does not erase
the existing tags. It also checks the dependencies of the package(s) against the
repo they are being moved to. It copies (actually, creates symlinks) packages to
the target repo and rebuilds the target repo. Moreover it takes the debuginfo
subpackages of the packages (if there are any) and forwards them to the 
rutgers-debuginfo repo. Finally, by default, it sends the results to OSS as an 
email. It has the following usage:
```
     usage: pushpackage [options] <to_repo> <package(s)>

       <to_repo>       one of: rutgers rutgers-testing rutgers-unstable
       <package(s)>    either in NVR format or: all

     options:
       -h, --help      show this help message and exit
       --nomail        Do not send email notification
       -f, --force     Do not do dependency checking
       -t, --test      Do the dependency checking and exit. No actual pushes are
       	   	       made.
       -v, --verbose   Verbose output
```

Example:
```
     $ pushpackage rutgers-testing rutgers-repotools-0.2.0-1.ru
```


pullpackage
-----------------
This is the brother of pushpackage. It is used to remove packages from the
specified repos.
```
     usage: pullpackage [options] <from_repo> <package(s)>

       <from_repo>     one of: rutgers rutgers-testing rutgers-unstable rutgers-staging
       <package(s)>    either in NVR format

     options:
       -h, --help     show this help message and exit
       --nomail       Do not send email notification
       -f, --force    Do not do dependency checking
       -t, --test     Do the dependency checking and exit. No actual pulls are
		      made.
       -v, --verbose  Verbose output
```

movepackage
-----------------
Wrapper around pullpackage and pushpackage. It just pushes the repo to
`to_repo` and pulls it from `from_repo`.
```
     usage: movepackage [options] <from_repo> <to_repo> <package(s)>

       <from_repo>     one of: rutgers rutgers-testing rutgers-unstable rutgers-staging
       <to_repo>       one of: rutgers rutgers-testing rutgers-unstable
       <package(s)>    either in NVR format or: all

     options:
       -h, --help     show this help message and exit
       --nomail       Do not send email notification
       -f, --force    Do not do dependency checking
       -t, --test     Do the dependency checking and exit. No actual pushes are
		      made.
       -v, --verbose  Verbose output
```

rebuild-repos
-------------
This has the capability of recreating all the repos we publish from scratch.
What it does is: It asks koji for the latest packages from a specific tag,
such as 'centos5-rutgers', 'centos5-rutgers-testing', 'centos5-rutgers-unstable'.
Then it creates symlinks from koji's packages directories into a temporary
repo directory. When all packages are symlinked, the repo metadata is created in
this temporary directory. Finally the old repo in `/army/rpmprivate/centos` is
replaced by the new one.
```
     usage: rebuild-repos [options] <repo(s)>

       <repo(s)>      one or more of: rutgers rutgers-testing rutgers-unstable rutgers-debuginfo
                      separated by whitespace, or simply: all.

     options:
       -h, --help     show this help message and exit
       -v, --verbose  Verbose output
```

Authors
=======
src/checkdep.py is heavily modified version of Fedora's spam-o-matic from mash
project:
http://git.fedoraproject.org/git/mash

The rest is written by Orcan Ogetbil, Jarek Sedlacek, and Kaitlin Poskaitis of Rutgers'
Open System Solutions.