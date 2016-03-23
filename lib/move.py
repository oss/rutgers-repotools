from optparse import OptionParser
import rcommon


def main():
    """ Wrapper function around pullpackage and pushpackage."""
    myapp = rcommon.AppHandler(verifyuser=True,config_file=my_config_file)

    # Repository information
    # Note that you may pull from the staging repository but not pull from it
    versions = myapp.config.get("repositories", "alldistvers").split()
    distname = myapp.config.get("repositories", "distname")
    from_repos = myapp.config.get("repositories", "allrepos").split()
    to_repos = get_publishrepos(myapp)

    usage =  "usage: %prog [options] <distro>-<from_repo> <distro>-<to_repo> <package(s)>\n\n"
    usage += "  <distro>        one of: " + string.join([distname + v for v in versions], " ") + "\n"
    usage += "  <from_repo>     one of: " + string.join(from_repos, " ") + "\n"
    usage += "  <to_repo>       one of: " + string.join(to_repos, " ") + "\n"
    usage += "  <package(s)>    A list of packages in NVR format"
    parser = OptionParser(usage)
    parser.add_option("--nomail",
                      action="store_true",
                      help="Do not send email notification")
    parser.add_option("-f", "--force",
                      action="store_true",
                      help="Do not do dependency checking")
    parser.add_option("-t", "--test",
                      default=False,
                      action="store_true",
                      help="Do the dependency checking and exit. No actual pushes are made.")
    parser.add_option("-v", "--verbose",
                      default=False,
                      action="store_true",
                      help="Verbose output")

    (options, args) = parser.parse_args(sys.argv[1:])
    myapp.create_lock()

    if options.verbose:
        verbosity = logging.DEBUG
    else:
        verbosity = logging.INFO
    myapp.init_logger(verbosity)

    if len(args) < 3:
        myapp.logger.error("Error: Too few arguments: " + str(args))
        myapp.logger.error("Run with --help to see correct usage")
        myapp.exit(1)

    if options.nomail:
        mail = False
    else:
        mail = True

    if options.test:
        mail = False
        myapp.logger.warning("This is a test run. No packages will be moved. No emails will be sent.")

    # Examine the arguments
    packages = args[2:]
    from_distro, from_distver, from_repo = parse_distrepo(args[0])
    to_distro, to_distver, to_repo = parse_distrepo(args[1])

    # Sanity checks
    if from_distro is None or from_distver is None or from_repo is None:
        myapp.logger.error("Error: Badly formatted source distribution, version or repository.")
        myapp.exit(1)
    if to_distro is None or to_distver is None or to_repo is None:
        myapp.logger.error("Error: Badly formatted destination distribution, version or repository.")
        myapp.exit(1)
    if from_distro != distname or to_distro != distname:
        myapp.logger.error("Error: Source and/or destination distributions are not valid.")
        myapp.exit(1)
    if not from_distver in versions:
        myapp.logger.error("Error: '" + from_distro + from_distver + "' is not a valid distribution version.")
        myapp.exit(1)
    if not to_distver in versions:
        myapp.logger.error("Error: '" + to_distro + to_distver + "' is not a valid distribution version.")
        myapp.exit(1)
    if not from_repo in from_repos:
        myapp.logger.error("Error: Invalid from_repo: " + from_repo)
        myapp.exit(1)
    if not to_repo in to_repos:
        myapp.logger.error( "Error: Invalid to_repo: " + to_repo)
        myapp.exit(1)
    if from_repo == to_repo:
        myapp.logger.error("Error: from_repo cannot be equal to to_repo.")
        myapp.exit(1)

    myapp.distver = to_distver
    pushpackage(myapp, mail, options.test, options.force, to_distro, to_distver, to_repo, packages, True)
    myapp.distver = from_distver
    pullpackage(myapp, mail, options.test, options.force, from_distro, from_distver, from_repo, packages, True)

    timerun = myapp.time_run()
    if options.test:
        myapp.logger.warning("End of test run. " + str(timerun) + " s")
    else:
        myapp.logger.info("Success! Time run: " + str(timerun) + " s")

    myapp.exit(0) 
