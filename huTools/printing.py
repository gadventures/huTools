#!/usr/bin/env python
# encoding: utf-8
"""
printing.py simple minded toolkit for printing on CUPS.

Created by Maximillian Dornseif on 2006-11-19. BSD Licensed.
"""
from __future__ import unicode_literals

from builtins import str
import os
import os.path
import subprocess
import warnings

__revision__ = "$Revision$"


def print_file(filename, jobname=None, printer=None, copies=1):
    """Print a file."""

    if not os.path.exists(filename):
        return

    warnings.warn("hutools.printing is deprecated", DeprecationWarning, stacklevel=2)
    args = ['/usr/local/bin/lpr', '-#%d' % copies]
    if printer:
        args.append('-P%s' % str(printer))
    args.append('"%s"' % filename)
    subprocess.call(args)


def print_data(data, jobname=None, printer=None, copies=1, printserver='printserver.local.hudora.biz'):
    """Print a datastream."""
    warnings.warn("hutools.printing is deprecated", DeprecationWarning, stacklevel=2)
    args = ['/usr/local/bin/lpr', '-#%d' % copies]
    if printer:
        args.append('-P%s' % str(printer))

    #if printserver:
    #    args.append('-H %s' % printserver)
    if jobname:
        args.append('-J %s  ' % jobname.replace("'\";./ ", "_"))

    pipe = subprocess.Popen(args, shell=False, stdin=subprocess.PIPE).stdin
    pipe.write(data)
    pipe.close()
