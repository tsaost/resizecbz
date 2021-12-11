"""Resize images inside CBZ (Comic Book Zip) files so that the file is smaller.
As a bonus the images should also load faster in your favorite CBZ reader"""

import os
import sys
import io
import glob
import configparser
import zipfile
from PIL import Image


def appendToErrorLog(text):
    """Append text to error log text file"""
    # https://stackoverflow.com/questions/230751/how-can-i-flush-the-output-of-the-print-function-unbuffer-python-output
    print(text, flush=True)
    # Must open in text mode or there will be an error:
    # TypeError: a bytes-like object is required, not 'str'
    #
    # https://docs.python.org/3/library/functions.html#open
    # When writing output to the stream if newline is None, any '\n' characters
    # written are translated to the system default line separator, os.linesep.
    # If newline is '' or '\n', no translation takes place.
    with open("resizecbz.error.log.txt", 'at',
              newline='', encoding='utf8') as output:
        output.write(text)
        output.write('\n')


def resize(inputZip, outputZip, resizeLandscape, resizePortrait):
    """Resize images inside inputZip and save the new images into outputZip"""
    infoList = inputZip.infolist()
    i = 1
    total = len(infoList)
    for info in infoList:
        filename = info.filename
        _, ext = os.path.splitext(filename)
        if not ext.lower() in (".jpg", ".jpeg", ".png", ".gif"):
            outputZip.writestr(info, inputZip.read())
            continue

        with Image.open(inputZip.open(filename)) as img:
            # https://stackoverflow.com/questions/29367990/what-is-the-difference-between-image-resize-and-image-thumbnail-in-pillow-python
            # Note: No shrinkage will occur unless ONE of the dimension is
            #       bigger than 1080. Aspect ratio is always kept
            #
            # https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-filters
            #           Performance    Downscale Quality
            # BOX       ****           *
            # BILINEAR  ***            *
            # HAMMING   ***            **
            # BICUBIC   **             ***
            # LANCZOS   *              ****
            #
            # ANTIALIAS is a alias for LANCZOS for backward compatibility
            oldSize = img.size
            img.thumbnail(resizeLandscape if img.size[0] > img.size[1]
                          else resizePortrait, Image.LANCZOS)
            print(f"{i}/{total} {img.format} {oldSize}->{img.size} {filename}")
            i = i + 1
            buffer = io.BytesIO()
            img.save(buffer, format=img.format)
            outputZip.writestr(info, buffer.getvalue())
            sys.stdout.flush()
            # output.getvalue()
            # img.show()


def resizeZippedImages(inputPath, outputPath, configParameters):
    """Resize images in file inputPath and save the new images in outputPath"""
    print(f"Resizing: {inputPath} -> {outputPath}")
    value = int(configParameters['resize_landscape'])
    resizeLandscape = (value, value)
    value = int(configParameters['resize_portrait'])
    resizePortrait = (value, value)
    tempPath = outputPath + ".0bd15818604b995cd9c00825a4c692d5d.temp"
    try:
        directory, _ = os.path.split(outputPath)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with zipfile.ZipFile(inputPath) as inZip:
            with zipfile.ZipFile(tempPath, 'w', zipfile.ZIP_STORED) as outZip:
                resize(inZip, outZip, resizeLandscape, resizePortrait)
            os.rename(tempPath, outputPath)
    except ValueError as err:
        appendToErrorLog(f"{inputPath}: {err}")
    except BaseException as err:
        # stackoverflow.com/questions/7160983/catching-all-exceptions-in-python
        #
        # https://docs.python.org/3/whatsnew/3.8.html
        # f-strings support = for self-documenting expressions and debugging
        # An f-string such as f'{expr=}' will expand to the text of the expr,
        # an equal sign, then the representation of the evaluated expression
        appendToErrorLog(f"{inputPath}: Unexpected {err}, {type(err)}")
        if os.path.exists(tempPath):
            os.remove(tempPath)
        if os.path.exists(outputPath):
            os.remove(outputPath)
        raise


def resizeCbz(path, configParameters):
    """resize the CBZ path with configuration specified in configParameters"""
    if not os.path.isfile(path):
        raise ValueError(f"{path} is not a file")

    name, ext = os.path.splitext(path)
    if int(configParameters['ext_zip_or_cbz']) != 0:
        if ext.lower() not in (".cbz", ".zip"):
            # Just print a warning without calling appendToErrorLog,
            # so that user can specify directory/* to resize
            # all the .cbz and .zip files in there.
            print(f"{path} does not have extension .cbz or .zip")
            return

    resizedFileExt = configParameters['resized_file_ext']
    if not resizedFileExt.startswith('.'):
        raise ValueError(f"resized_file_ext({resizedFileExt}) " +
                         "does not start with period")
    resizedFileExt = resizedFileExt + ext

    if path.endswith(resizedFileExt):
        raise ValueError(f"{path} has extension same ext({resizedFileExt})")

    outputPath = name + resizedFileExt
    outputDirectory = configParameters['output_directory']
    if outputDirectory:
        outputPath = os.path.join(outputDirectory,
                                  os.path.basename(outputPath))

    if os.path.exists(outputPath):
        # Not an error, just give a warning
        print(f"output {outputPath} already exists")
    else:
        resizeZippedImages(path, outputPath, configParameters)


def readConfigurationFile(arg0):
    """Read configuration file from a series of possible directories"""
    cmdDirectory, _ = os.path.split(arg0)
    home = os.path.expanduser("~")
    homeConfig = os.path.join(home, ".config")
    homeConfigApp = os.path.join(homeConfig, "resizecbz")
    configFilename = ".resizecbz.cfg"

    # print(f"cmdDirectory({cmdDirectory})")
    config = configparser.ConfigParser()
    configParameters = None
    for directory in os.curdir, homeConfigApp, homeConfig, home, cmdDirectory:
        path = os.path.abspath(os.path.join(directory, configFilename))
        # print(f"Trying to open config file {path}")
        if os.path.exists(path):
            with open(path, encoding='utf8') as file:
                config.read_file(file)
                configParameters = config['resize.cbz']
                print(f'Reading parameters from "{path}": ')
                break

    if not configParameters:
        # Create a sample config file so that user can change it
        config['resize.cbz'] = {}
        configParameters = config['resize.cbz']
        # Output directory can be an absolute or relative path.
        # If set to None or '' then the resized files will be
        # in the same directory as the source
        configParameters['output_directory'] = 'resized'

        # Play around with these two parameters to to get the size that is most
        # pleasing for your eyes with the display.  In general you want them
        # to be a bit larger than your display so that there is no upscaling.
        #
        # If you are using a tablet (or any device that can be rotated to
        # display in # portrait mode) then you should set both of them to
        # the same value.
        # For example, on a older tablet with only a 1080x768 resolution both
        # values should be set to (1080, 1080) or (1366, 1366).
        # Obviously larger values means a larger file size
        configParameters['resize_landscape'] = '1366'
        configParameters['resize_portrait'] = '1080'

        # Can be anything, but must start with '.' and must end with '.cbz'
        configParameters['resized_file_ext'] = '.resized'
        # By default, will only process files with extension ".zip" or ".cbz"
        configParameters['ext_zip_or_cbz'] = '1'

        if os.name == 'nt':
            # For Windows, create sample in the app's directory
            parentDir = cmdDirectory
        else:
            # For Linux/Mac, create in ~/config/xxx if it exits, else in ~/
            if os.path.isdir(homeConfig):
                parentDir = homeConfigApp
            else:
                parentDir = home

        # print(f"configuration file parent: {parent}")
        if parentDir and not os.path.isdir(parentDir):
            os.makedirs(parentDir)
        samplePath = os.path.abspath(os.path.join(parentDir,
                                                  configFilename + ".sample"))
        print(f'samplePath: "{samplePath}"')
        if not os.path.exists(samplePath):
            print(f"Create sample config file {samplePath}")
            with open(samplePath, 'w', encoding='utf8') as output:
                config.write(output)
        print(f"Rename {samplePath} to {configFilename}\n" +
              "and edit it if you want to change the default value\n" +
              "No user specified config, use default parameters")

    return configParameters


if __name__ == '__main__':

    def main(argv):
        """main(arg)"""
        # Turn off "DecompressionBombWarning:
        # Image size (xxxxpixels) exceeds limit..."
        Image.MAX_IMAGE_PIXELS = None
        arg0 = argv[0]
        configParameters = readConfigurationFile(arg0)
        for key in configParameters:
            print(f"{key}={configParameters[key]}")

        if len(argv) > 1:
            for x in argv[1:]:
                for path in glob.glob(x) if '*' in x or '?' in x else [x]:
                    try:
                        resizeCbz(path, configParameters)
                    except ValueError as err:
                        appendToErrorLog(f"{path}: {err}")
        else:
            inputPath = "testcbz.cbz"
            outputPath = "testcbz.resized.cbz"
            if os.path.isfile(inputPath):
                if os.path.isfile(outputPath):
                    os.remove(outputPath)
                resizeZippedImages(inputPath, outputPath, configParameters)
            else:
                cmd = os.path.basename(arg0)
                print(f"\nUsage: {cmd} file1 file2...\n" +
                      "file1 can contain wildcards such as '*' and '?'\n\n" +
                      "For example: {cmd} d:\\mycollection\\*.cbz xyz\\??.cbz")


main(sys.argv)
