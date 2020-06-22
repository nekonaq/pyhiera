import sys
import argparse
import json
from .yaml import dump_yaml

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
        parser.set_defaults(output_handler=self.output_json)

        parser.add_argument(
            'config_file', action='store',
            metavar='CONFIG_FILE'
        )
        parser.add_argument(
            '--json', '-j', action='store_const', dest='output_handler',
            const=self.output_json,
            )
        parser.add_argument(
            '--yaml', '-y', action='store_const', dest='output_handler',
            const=self.output_yaml,
            )
        parser.add_argument(
            '--environment', '-e', action='store', default='local',
            )
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


    def handle(self, *args,
               config_file=None,
               environment=None,
               output_handler=None,
               **options):

        context = {
            'environment': environment,
        }
        hiera_data = Hiera.load_data(config_file, context=context)
        hiera_dict = hiera_data.flatten()

        output_handler(hiera_dict)

    def output_json(self, data, outfile=None):
        outfile = outfile or self.stdout
        json.dump(data, outfile, indent=2)
        outfile.write("\n")

    def output_yaml(self, data, outfile=None):
        outfile = outfile or self.stdout
        dump_yaml(data, stream=outfile, explicit_start=True)
