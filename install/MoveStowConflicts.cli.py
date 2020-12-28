#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
######################################################################
# @author      : benfair (benfair@Bens-MacBook-Air.local)
# @file        : cli
# @created     : Saturday Dec 26, 2020 16:47:20 EST
#
# @description : 
######################################################################
"""
Helper script move existing dotfiles which are not symlinks, which may conflict with installing new dotfiles with stow, into a new directory.

use MoveStowConflictFilesToDir to move existing dotfiles to new directory. This is useful if you want to install all my dotfiles on a new computer (by cloning my dotfiles repo and then using stow to make symlinks from the dotfiles repo to home folder) but there already exists dotfiles in the home folder that you want to move out of the way without permanently deleting them. Use this command to move all those old dotfiles to a folder to make room for new dotfiles. Symlinks will not be moved with this command. Moving symlinks isn't necessary anyway because stow has a parameter which allows overwriting symlinks.

If you have already used MoveStowConflictFilesToDir command and you want to safely move all those files back to the home dir, use MoveFilesToDirSafely command to move files in an existing directory into a target (ie your home folder). If an existing file already exists in the home directory, this will not overwrite it unless it is a symlink.
"""
__author__ = "Benjamin Fair"
__version__ = "0.1.0"
__license__ = "MIT"

import sys
import os
import argparse
import logging

# If running from interactive interpreter with prompt, keep logging at DEBUG
try:
    if(sys.ps1):
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
except: pass

class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    """
    intialize a parser object with argparse.Args(formatter_class=CustomFormatter) to inherit best of both formats
    """
    pass

def cmdline_args(Args=None):
    # create the top-level parser, p
    p = argparse.ArgumentParser(description=__doc__, formatter_class=CustomFormatter, add_help=True )
    # create a similar parent parser so subparsers can inherit some common options
    parent = argparse.ArgumentParser(description=__doc__, formatter_class=CustomFormatter , add_help=True)
    parent.add_argument('--version', action='version', version='%(prog)s {version}'.format(version=__version__))
    parent.add_argument('-v', '--verbose', action='count', dest='verbosity', default=0, help="verbose output (repeat for increased verbosity)")
    parent.add_argument('-q', '--quiet', action='store_const', const=-1, default=0, dest='verbosity', help="quiet output (show errors only)")
    parent.add_argument("-n", "--dryrun", action='store_true')
    subparsers = p.add_subparsers(title='subcommands', help='Choose a subcommand and run with -h for more help. Subcommands listed below:', dest="sub_command")
    # create the parser_a for the first command
    parser_a = subparsers.add_parser("MoveStowConflictFilesToDir", add_help=False, parents=[parent], formatter_class=CustomFormatter, help="Find which files in subtrees of source dir (i.e. a stow dir) would conflict if they were to be moved (or symlink 'stowed') into a target dir. Move those files into a NewDir to allow stowing without conflicts")
    parser_a.add_argument("--SourceDir", help="Source stow directory. In the example use case, this would be the dotfiles stow directory", metavar="<Path/To/Directory>", default="./")
    parser_a.add_argument("--TargetDir", help="Target stow directory. In the example use case, this would be the home directory where you want to later create symlinks in place of the existing dotfiles", metavar="<Path/To/Directory>", default="../")
    parser_a.add_argument("--NewDir", help="New directory. In the example use case, this would be something like Dir/To/Keep/OldDotfiles", metavar="<Path/To/Directory>", default="PreStowConflictFiles/")
    parser_a.add_argument("--SubtreeDirs", help="""Sub directory(s) in source directory to check for stow conflicts. This is equivalent to package directories for stow. In the example use case, this would be something like git vim. Glob pattern expansions, are acceptable """, metavar="<SubDirInSourceDirectory>", nargs='+', required=True)
    # create the parser_b for the next command
    parser_b = subparsers.add_parser("MoveFilesToDirSafely", parents=[parent], add_help=False, formatter_class=CustomFormatter, help="Move files in source dir into a target dir")
    parser_b.add_argument("--TargetDir", help="Target directory where you want files to be moved to. In the example use case, this would be your home directory", metavar="<Path/To/Directory>",  required=True)
    parser_b.add_argument("--SourceDir", help="Source directory with files you want to move. In the example use case, this would be the directory where you put all your old dotfiles and now you want to move those same files back to home", metavar="<Path/To/Directory>",  required=True)
    return(p.parse_args(Args))

def setup_logging(verbosity):
    """
    with base_loglevel=30...
    verbosity =-1 => ERROR
    verbosity = 0 => WARNING
    verbosity = 1 => INFO
    verbosity = 2 => DEBUG
    """
    base_loglevel = 30
    verbosity = min(verbosity, 2)
    loglevel = base_loglevel - (verbosity * 10)
    logging.basicConfig(level=loglevel,
                        format='%(message)s')

def MoveStowConflictFilesToDir(TargetDir="../",  SourceDir="", SubtreeDirs=[''], NewDir="PreStowConflictFiles", dryrun=False, **kwargs):
    TargetDir = os.path.expanduser(TargetDir.strip('/') + '/')
    SourceDir = os.path.expanduser(SourceDir.strip('/') + '/')
    NewDir = os.path.expanduser(NewDir.strip('/') + '/')
    logging.debug(SubtreeDirs)
    SubtreeDirs = [SourceDir + SubDir for SubDir in SubtreeDirs]
    if not os.path.exists(NewDir):
        logging.warning('Making {} directory...'.format(NewDir))
        if not dryrun:
            os.mkdir(NewDir)
            logging.info('  ...Success.')
    for Dir in SubtreeDirs:
        logging.info("Looking for conflicting stow target files in {}...".format(Dir))
        AllTargets = os.listdir(Dir)
        logging.debug(AllTargets)
        for fn in AllTargets:
            target_fn = os.path.expanduser(TargetDir + fn)
            logging.debug("  Found {}".format(target_fn))
            # If file exists and isn't smylink
            if not os.path.islink(target_fn) and os.path.exists(target_fn):
                #Something here
                New_fn = NewDir + fn
                logging.info( "  Potenetial stow conflict found: {}".format(target_fn) )
                logging.warning( "    Moving {} => {}".format( target_fn, New_fn) )
                if not dryrun:
                    if not os.path.exists(New_fn):
                        os.rename( target_fn, New_fn )
                        logging.info( "    ...Success." )
                    else:
                        logging.warning("    ...Failure. {} already exists. Did not overwrite.".format(New_fn))

# MoveStowConflictFilesToDir(TargetDir="~/", SourceDir="~/dotfiles", NewDir = "~/TempDotfiles", SubtreeDirs=['git', 'bash'], dryrun=True)

def MoveFilesToDirSafely(SourceDir=None, TargetDir=None, dryrun=False, **kwargs):
    SourceDir = os.path.expanduser(SourceDir.strip('/') + '/')
    TargetDir = os.path.expanduser(TargetDir.strip('/') + '/')
    fn_list = os.listdir(SourceDir)
    if not fn_list:
        logging.info("No files found in SourceDir to move")
    for fn in fn_list:
        logging.debug(fn)
        logging.info("found {} in {}...".format(fn, SourceDir))
        TargetLocation = os.path.expanduser(TargetDir + fn)
        SourceLocation = SourceDir + fn
        # Move to target location only if won't overwrite an existing file.
        # Overwriting symlinks are ok
        if (not os.path.exists(TargetLocation)) or (os.path.islink(TargetLocation)):
            logging.warning(  "Moving {} => {}".format(SourceLocation, TargetLocation) )
            os.rename( SourceLocation, TargetLocation )
            logging.info("  ...Success." ) 

def main(**parsed_args):
    if parsed_args['sub_command'] == "MoveStowConflictFilesToDir":
        MoveStowConflictFilesToDir(**parsed_args)
    elif parsed_args['sub_command'] == "MoveFilesToDirSafely":
        MoveFilesToDirSafely(**parsed_args)

if __name__ == '__main__':
    try:
        if(sys.ps1):
            Args = ['MoveStowConflictFilesToDir', '~', '~', 'git',]
            args = cmdline_args(Args=Args)
    except:
        args = cmdline_args()
    # print(vars(args))
    setup_logging(args.verbosity)
    main(**vars(args))

