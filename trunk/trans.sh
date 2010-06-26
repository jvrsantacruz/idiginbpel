#!/bin/sh

# Application name (used in filenames)
APP=idiginbpel
# Source Files to translate
PY_FILES=*/*.py
# Glade ui files
GLADE_DIR=share/ui
# Glade Files to translate
GLADE_FILES=$GLADE_DIR/*.glade
# Config file with opt explanations
CONFIG_FILE=share/config.xml
# Result of glade string extraction
H_FILES=$GLADE_DIR/*.h
# Dev l10n dir
LOCALE_DIR=locale
# general translation template
POT_FILE=$LOCALE_DIR/$APP.pot
# translated templates
PO_FILES=$LOCALE_DIR/*/$APP.po
# translated binaries
MO_FILES=$LOCALE_DIR/*/LC_MESSAGES/$APP.mo

if [ ! $# -eq 1 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	echo "Usage: $0 update|binary"
	echo "          update: Update translation templates"
	echo "          binary: Generate binary versions of templates"
	exit 1
fi

# Get the new strings and update translation templates
if [ "$1" = "update" ]; then

	# Extract strings from glade and put it in .h files
	echo "Extracting glade files from $GLADE_DIR"
	for GLADE in $GLADE_FILES
	do
		intltool-extract --type="gettext/glade" $GLADE
	done

	echo "Extracting help strings from $CONFIG_FILE"
	# Extract strings from config file, filter undesired values and add it to H_FILES
	intltool-extract --type="gettext/quoted" $CONFIG_FILE
	# Only keep help string lines and the previous description line 
	fgrep 'idg.help.' $CONFIG_FILE.h -B 1 > $CONFIG_FILE.temp && mv $CONFIG_FILE.temp $CONFIG_FILE.h
	H_FILES=$H_FILES" $CONFIG_FILE.h"

	echo "Generating .pot template"
	# Generate a po template file with strings extracted from .py and .h files
	xgettext -k_ -kN_ -o $POT_FILE $PY_FILES $H_FILES

	# Change default CHARSET to UTF-8
	sed -i -e "s/CHARSET/UTF-8/" $POT_FILE

	echo "Removing used .h temp files"
	# Remove used .h files
	echo $H_FILES
	rm $H_FILES

	echo "Updating local PO templates"
	# Update existing .po translation files with new strings
	for PO in $PO_FILES 
	do
		msgmerge --update $PO $POT_FILE
	done

# Get the actual translation templates and generate binary versions
elif [ "$1" = "binary" ]; then
	echo "Generating .mo binary versions of .po template files"
	for PO in $PO_FILES
	do
		DIR_PO=$(dirname $PO)
		echo $DIR_PO
		mkdir -p $DIR_PO
		msgfmt $PO -o $DIR_PO/LC_MESSAGES/$APP.mo
	done
fi
