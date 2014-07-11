import zipfile
import os
import argparse
import sys
import json
import textwrap

_manifest_name = 'manifest.json'
_required_files = [_manifest_name, 'index.mustache.html']
_manifest_required_fields = ['version']

def _check_file_exists(file, parent_folder=None, raise_exception=True):
    """
    Check that the file `file` exists in the folder `folder`

    Param:
        file: the name of the file
        parent_folder: (optional) path to the folder containing the file
        raise_exception: if True(default) raise exception, else return False.

    Raise:
        IOError: if the file is not found in the folder.

    Return:
        True if file exists
    """
    if parent_folder:
        filename = os.path.join(parent_folder, file)
    else:
        filename = file

    if not os.path.isfile(filename):
        if raise_exception:
            raise IOError('Required file "{}" does not exist in given rootfolder {}'.format(file, folder))
        else:
            return False
    return True


def validate(rootfolder):
    """
    Check that the required files are present, and that the required fields are present in the manifest.

    Raise:
        IOError: if the given `rootfolder` does not point to a directory
        IOError: if any required files are missing (checked using _check_file_exists)
        ValueError: if any required field is missing from manifest.
    """
    if not os.path.isdir(rootfolder):
        raise IOError('Supplied path has to point to a directory!')

    for file in _required_files:
        _check_file_exists(file=file, parent_folder=rootfolder)

    manifest_json = open(os.path.join(rootfolder, _manifest_name)).read()
    manifest = json.loads(manifest_json)
    for field in _manifest_required_fields:
        if not field in manifest or manifest[field] == None or manifest[field] == '':
            raise ValueError("{} missing from manifest!".format(field))


def package(rootfolder, output, validate_only, force, verbose):
    """
    Package the contents of the given `rootfolder` to a single zip-archive
    """
    validate(rootfolder)
    if verbose:
        print 'Validation passed!'
    if validate_only:
        return

    if _check_file_exists(file=output, raise_exception=False):
        if force:
            os.remove(output)
            print 'deleted old {}'.format(output)
        else:
            raise IOError('outputfile "{}" already exists! (pass -f to delete it).'.format(output))

    if verbose:
        print 'Adding files to archive:'
    archive = zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED)
    root_len = len(os.path.abspath(rootfolder))
    for root, dirs, files in os.walk(rootfolder):
        archive_root = os.path.abspath(root)[root_len:]
        for f in files:
            fullpath = os.path.join(root, f)
            archive_name = os.path.join(archive_root, f)
            if verbose:
                print '\t'+archive_name
            archive.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
    archive.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate and package an mgp-html5app.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
            EXAMPLE:
                $ python mgp-html5app-compiler.py -v -a myapp.zip -p some/location/myapps/MyApp/

            Will package the contents of MyApp in an archive called 'myapp.zip' and print all
            packaged filenames to screen'''))
    parser.add_argument('-p', '--path', type=str, required=True,
        help='path to the apps root directory. This directory should contain the files'+
            '"manifest.json" and "index.mustache.html"')
    parser.add_argument('-a', '--archive-name', type=str, default='archive.zip',
        help='Specify where to place the new archive. path/to/archivename.zip')
    parser.add_argument('--no-package', action='store_true',
        help='Run validation only. Validate the app without packaging it.')
    parser.add_argument('-f', '--force', action='store_true',
        help='delete existing archivefile if given archive-name already exists')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='Print all filenames added to archive')

    args = parser.parse_args()
    try:
        package(args.path, args.archive_name, args.no_package, args.force, args.verbose)
    except IOError as e:
        print 'Failed! Given reason:\n\t{}'.format(e)
        sys.exit(-1)
    except ValueError as e:
        print 'Failed! Given reason:\n\t{}'.format(e)
        sys.exit(-1)

    print 'Done!'
