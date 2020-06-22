import sys
import argparse
import json

from . import __version__
from .hiera import Hiera


class Command:
    VERSION = __version__
    PROG = 'pyhiera'

    @classmethod
    def main(cls):
        try:
            sys.exit(cls().run_from_argv(sys.argv))
        except KeyboardInterrupt:
            sys.exit(1)

    def create_parser(self, prog=None):
        parser = argparse.ArgumentParser(prog=prog or getattr(self, 'PROG', None))

        parser.add_argument(
            'config_file', action='store',
            metavar='CONFIG_FILE'
        )
        # parser.add_argument(
        #     '--delimiter', '-d', action='store', default='-',
        #     help="word delimiter",
        #     )
        # parser.add_argument(
        #     '--words', '-w',
        #     action='store', type=int, default=4,
        #     help="number of words",
        #     )
        # parser.add_argument(
        #     '--min-length',
        #     action='store', type=int, default=3,
        #     help="number of words",
        #     )
        # parser.add_argument(
        #     '--max-length',
        #     action='store', type=int, default=6,
        #     help="number of words",
        #     )
        # parser.add_argument(
        #     '--vcr',
        #     action='store', default='small',
        #     choices=['random', 'small', 'medium', 'large'],
        #     help="vcr of words",
        #     )
        parser.add_argument(
            '--traceback', action='store_true',
            help="traceback on exception",
            )
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s version {}'.format(getattr(self, 'VERSION', None) or 'WIP'),
            )
        return parser

    def print_usage(self):
        parser = self.create_parser()
        parser.print_usage()

    def run_from_argv(self, argv):
        parser = self.create_parser()
        options = parser.parse_args(argv[1:])
        kwargs = options.__dict__
        args = kwargs.pop('args', [])
        return self.execute(*args, **kwargs)

    def execute(self, *args, **options):
        self.stdout = options.pop('stdout', sys.stdout)
        self.stderr = options.pop('stderr', sys.stderr)
        self.traceback = options.pop('traceback', False)
        try:
            return self.handle(*args, **options)
        except Exception as err:
            if self.traceback:
                raise
            else:
                self.stderr.write("{}: {}\n".format(type(err).__name__, err))
            sys.exit(1)

    def handle(self, *args, config_file=None, **options):
        # print("{}:{}".format(self.__class__.__module__, self.__class__.__name__))

        #//test data
        # import argparse
        # envlocal = argparse.Namespace(name={'foo': 'local'})

        context = {
            'environment': 'local',
        }
        hiera_data = Hiera.load_data(config_file, context=context)
        hiera_dict = hiera_data.flatten()

        # import pprint
        # self.stdout.write(pprint.pformat(hiera_dict))
        json.dump(hiera_dict, self.stdout, indent=2)
        self.stdout.write("\n")
