# resizecbz
Python script to resize all images inside a CBZ (Comic Book Zip)

Usage: python resizecbz.py file1 file2 ....

file1 can contain wildcards such as "*.cbz", "abc?.cbz", etc.  

For example:
   python resizecbz.py d:\mycollection1\*.cbz d:\mycollection2\xyz*.cbz"
   
Only files with the extension .cbz will be processed.  Any error will be logged into the file "resizecbz.error.log.txt" 

The script needs python 3 and you need to install pillow module with "pip3 install pillow"

You can control the maximum size of the images, the destination directory, and the extesion of the resized file via a configuration file.  A sample configuration file ".resizecbz.cfg.sample" will be created the first time you run the script without any parameters. You can edit this file and then rename it to ".resizecbz.cfg" and it will be loaded by the script.  You can put .resizecbz.cfg in the direcotory where you run the script (so you can have a different resize parameters for each direcotory), the same direcotory as the script, in your home directory, or in ~/config/resizecbz.

By default the maximum width in landscape mode is 1366, the maximum height in portrait mode is 1080, the directory is a subdirectory "resized" underneath the source directory, and the default extension is "resized.cbz".

There is a pre-built Windows executable for users who don't have Python installed.  The executable can be found [here](https://github.com/tsaost/resizecbz/releases) and you have to look for it under "Assets"

The autogenerate project web page is [here](https://tsaost.github.io/resizecbz/)