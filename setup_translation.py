#!/usr/bin/env python3
import csv
import json
import logging
import re
import shutil
import sys
import urllib.error
import urllib.request
from argparse import ArgumentParser
from pathlib import Path

logging.basicConfig(
    stream=sys.stdout,
    format='[%(levelname)s]: %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger("")

root = Path(__file__).parent.resolve()
base = root / "Base.lproj"
locale_identifiers = root / "locale-identifiers.csv"

locales = {
    row[0]: row[1] for row in csv.reader(locale_identifiers.read_text().split("\n")[1:], delimiter=",")
}

arg_parser = ArgumentParser(description="Setup a new translation")
arg_parser.add_argument("-l", "--language", type=str, choices=locales.keys(), required=True)

args = arg_parser.parse_args()


def main():
    logger.info("=== Setting up translation ===")
    logger.info("Selected language: %s" % locales[args.language])

    default_translations = get_default_translations(args.language)

    language_folder = (root / ("%s.lproj" % args.language)).resolve()

    logger.info("Creating '%s'" % str(language_folder))
    language_folder.mkdir(exist_ok=True)

    for file in base.iterdir():
        dest = language_folder / file.name
        if not dest.exists():
            logger.info("Copy '%s'" % str(file.name))
            shutil.copy(file, dest)
        else:
            logger.info("Skip '%s' (already exists)" % str(file.name))

    for file in language_folder.iterdir():
        logger.info("Setting Default Translations for '%s'" % str(file.name))
        text = file.read_text(encoding="UTF-8")

        for key, replacement in default_translations.items():
            text = re.sub(r"^\s*\"%s\"\s*=\s*\"(.| )+\";" % key, "\"%s\" = \"%s\";" % (key, replacement), text,
                          flags=re.M)

        file.write_text(text, encoding="UTF-8")

    logger.info("=== Completed ===")


def get_default_translations(language):
    # Most languages such as "sv-SE" are simply named "sv" in "martnst/localize-mainmenu"
    langshort = language[:language.rfind("-")] if "-" in language else language

    for item in {langshort, language}:
        try:
            data = urllib.request.urlopen(
                "https://raw.githubusercontent.com/martnst/localize-mainmenu/master/languages/%s.json" % item
            ).read().decode("UTF-8")

            data = data.replace("<AppName>", "Typora")

            return json.loads(data)
        except urllib.error.HTTPError:
            logger.warning("Did not find default translations for '%s'" % item)
    logger.warning("Proceeding without default translations")
    return dict()


if __name__ == '__main__':
    main()
