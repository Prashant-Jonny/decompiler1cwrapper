#! python3
# -*- coding: utf-8 -*-
from . import __version__
from argparse import ArgumentParser
from configparser import RawConfigParser
from pathlib import Path
import tempfile
import shutil
import subprocess


class Processor:
    def __init__(self):
        self.argparser = ArgumentParser()
        self.argparser.add_argument('-v', '--version', action='version', version='%(prog)s, ver. {}'.format(
            __version__))
        self.argparser.add_argument('--debug', action='store_true', default=False,
                                    help='if this option exists then debug mode is enabled')

        settings_file_path = Path('decompiler1cwrapper.ini')
        if not settings_file_path.exists():
            settings_file_path = Path.home() / settings_file_path
            if not settings_file_path.exists():
                raise SettingsError('Settings file does not exist!')

        self.config = RawConfigParser()
        self.config.optionxform = lambda option: option
        self.config.read(str(settings_file_path), 'utf-8')
        self.general_section_name = 'General'
        self.general_section = self.config[self.general_section_name]

        self.exe_1c = Path(self.general_section['1C'])
        if not self.exe_1c.exists():
            raise SettingsError('1C:Enterprise 8 does not exist!')

        self.ib = Path(self.general_section['IB'])
        if not self.ib.exists():
            raise SettingsError('Service information base does not exist!')

        self.v8_reader = Path(self.general_section['V8Reader'])
        if not self.v8_reader.exists():
            raise SettingsError('V8Reader does not exist!')

        self.v8_unpack = Path(self.general_section['V8Unpack'])
        if not self.v8_unpack.exists():
            raise SettingsError('V8Unpack does not exist!')

        self.gcomp = Path(self.general_section['GComp'])
        if not self.gcomp.exists():
            raise SettingsError('GComp does not exist!')

    def run(self):
        pass


class Decompiler(Processor):
    def __init__(self):
        super().__init__()

        self.argparser.add_argument('input', nargs='?')
        self.argparser.add_argument('output', nargs='?')

    def perform(self, in_path: Path, out_path: Path):
        with tempfile.NamedTemporaryFile('w', encoding='cp866', suffix='.bat', delete=False) as bat_file:
            bat_file.write('@echo off\n')
            in_path_suffix_lower = in_path.suffix.lower()
            if in_path_suffix_lower in ['.epf', '.erf']:
                bat_file.write('"{}" /F"{}" /DisableStartupMessages /Execute"{}" {}'.format(
                    str(self.exe_1c),
                    str(self.ib),
                    str(self.v8_reader),
                    '/C"decompile;pathtocf;{};pathout;{};shutdown;convert-mxl2txt;"'.format(
                        str(in_path),
                        str(out_path)
                    )
                ))
            elif in_path_suffix_lower in ['.ert', '.md']:
                bat_file.write('"{}" -d -F "{}" -DD "{}"'.format(
                    str(self.gcomp),
                    str(in_path),
                    str(out_path)
                ))
        exit_code = subprocess.check_call(['cmd.exe', '/C', str(bat_file.name)])
        if not exit_code == 0:
            raise Exception('Decompiling "{}" is failed!'.format(str(in_path)))
        Path(bat_file.name).unlink()

    def run(self):
        args = self.argparser.parse_args()

        input_file = Path(args.input)
        output_folder = Path(args.output)

        self.perform(input_file, output_folder)


class Compiler(Processor):
    def __init__(self):
        super().__init__()

        self.argparser.add_argument('input', nargs='?')
        self.argparser.add_argument('output', nargs='?')

    def perform(self, input_folder: Path, output_file: Path):
        temp_source_folder = Path(tempfile.mkdtemp())
        if not temp_source_folder.exists():
            temp_source_folder.mkdir(parents=True)
        else:
            shutil.rmtree(str(temp_source_folder), ignore_errors=True)

        renames_file = input_folder / 'renames.txt'

        with renames_file.open(encoding='utf-8-sig') as file:
            for line in file:
                names = line.split('-->')

                new_path = temp_source_folder / names[0].strip()
                new_folder_path = new_path.parent

                if not new_folder_path.exists():
                    new_folder_path.mkdir(parents=True)

                old_path = input_folder / names[1].strip()

                if old_path.is_dir():
                    new_path = temp_source_folder / names[0].strip()
                    shutil.copytree(str(old_path), str(new_path))
                else:
                    shutil.copy(str(old_path), str(new_path))

        exit_code = subprocess.check_call([
            str(self.v8_unpack),
            '-B',
            str(temp_source_folder),
            str(output_file)
        ])
        if not exit_code == 0:
            raise Exception('Compiling "{}" is failed!'.format(str(output_file)))

    def run(self):
        args = self.argparser.parse_args()

        if args.debug:
            import sys
            sys.path.append('C:\\Python34\\pycharm-debug-py3k.egg')

            import pydevd
            pydevd.settrace(port=10050)

        input_folder = Path(args.input)
        output_file = Path(args.output)

        self.perform(input_folder, output_file)


class Error(Exception):
    def __init__(self, value=None):
        super(Error, self).__init__()
        self.value = value

    def __str__(self):
        return repr(self.value)


class SettingsError(Error):
    def __init__(self, message: str):
        super().__init__('{}'.format(message))


def decompile():
    # sys.path.append('C:\\Python35\\pycharm-debug-py3k.egg')
    #
    # import pydevd
    # pydevd.settrace(port=10050)

    Decompiler().run()


def compile_():
    # sys.path.append('C:\\Python35\\pycharm-debug-py3k.egg')
    #
    # import pydevd
    # pydevd.settrace(port=10050)

    Compiler().run()
