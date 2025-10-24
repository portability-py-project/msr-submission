import io
import logging
import os
import sys

from collections import deque
from contextlib import redirect_stdout
from datetime import datetime
from unittest.mock import patch

from trafilatura import cli, cli_utils
from trafilatura.downloads import add_to_compressed_dict, fetch_url
from trafilatura.settings import DEFAULT_CONFIG

import signal

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
RESOURCES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'resources')

# Define constants for SIGHUP and SIGKILL to maintain portability
SIGHUP = getattr(signal, 'SIGHUP', None)
SIGKILL = getattr(signal, 'SIGKILL', None)

def test_parser():
    '''test argument parsing for the command-line interface'''
    testargs = ['', '-fvv', '--xmltei', '--notables', '-u', 'https://www.example.org']
    with patch.object(sys, 'argv', testargs):
        args = cli.parse_args(testargs)
    assert args.fast is True
    assert args.verbose == 2
    assert args.notables is False and args.no_tables is False
    assert args.xmltei is True
    assert args.URL == 'https://www.example.org'
    args = cli.map_args(args)
    assert args.output_format == 'xmltei'
    testargs = ['', '-out', 'csv', '--no-tables', '-u', 'https://www.example.org']
    with patch.object(sys, 'argv', testargs):
        args = cli.parse_args(testargs)
    assert args.fast is False
    assert args.verbose == 0
    assert args.output_format == 'csv'
    assert args.no_tables is False
    # test args mapping
    testargs = ['', '--xml', '--nocomments']
    with patch.object(sys, 'argv', testargs):
        args = cli.parse_args(testargs)
    args = cli.map_args(args)
    assert args.output_format == 'xml' and args.no_comments is False
    args.xml, args.csv = False, True
    args = cli.map_args(args)
    assert args.output_format == 'csv'
    args.csv, args.json = False, True
    args = cli.map_args(args)
    assert args.output_format == 'json'
    testargs = ['', '--with-metadata']
    with patch.object(sys, 'argv', testargs):
        args = cli.parse_args(testargs)
    args = cli.map_args(args)
    assert args.only_with_metadata is True
    # process_args
    args.inputdir = '/dev/null'
    args.verbose = 1
    args.blacklist = os.path.join(RESOURCES_DIR, 'list-discard.txt')
    cli.process_args(args)
    assert len(args.blacklist) == 2
    # filter
    testargs = ['', '-i', 'resources/list-discard.txt', '--url-filter', 'test1', 'test2']
    with patch.object(sys, 'argv', testargs):
        args = cli.parse_args(testargs)
    assert args.inputfile == 'resources/list-discard.txt'
    assert args.url_filter == ['test1', 'test2']
    args.inputfile = os.path.join(RESOURCES_DIR, 'list-discard.txt')
    args.blacklist = os.path.join(RESOURCES_DIR, 'list-discard.txt')
    f = io.StringIO()
    with redirect_stdout(f):
        cli.process_args(args)
    assert len(f.getvalue()) == 0

# Rest of the code remains the same