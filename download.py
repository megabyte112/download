# A video/audio downloader based on yt-dlp aimed at simplifying the process of downloading videos and audio.
# Runs as CLI by default, but will be run as a TUI if no arguments are provided.

# Usage is as follows:
# download.py [url] [options]

# possible cli options:
# -a --audio                    : download audio only
# -c --compatibility            : transcode to mp4/m4a (MPEG-4) for maximum compatibility
# -f [name], --folder [name]    : specify a folder to save the file(s) in
# -s --no-check                 : skip the URL check
# -h --help                     : show help menu, then close

## Config ##

# GPU hardware accelerated encoding options, change this to suit your GPU
# set to "nvidia" or "amd", or an empty string "" encode on the CPU
hwaccel = "amd"

## End Config ##

import os
import sys
import subprocess
from shutil import which
import glob

isCli = len(sys.argv) > 1

def close(isCli):
    if isCli:
        exit()
    else:
        input("Press enter to close.")
        exit()

# test for yt-dlp
if which("yt-dlp") == None:
    print("[Error] yt-dlp not found. Please install yt-dlp.")
    close(isCli)

# test for ffmpeg, but allow user to continue with a warning
if which("ffmpeg") == None:
    print("[Error] FFMPEG not found. Please install FFMPEG.")
    close(isCli)

# validate hardware acceleration choice
match hwaccel:
    case "nvidia":
        print("[Info] Hardware accelerated encoding enabled: Nvidia NVENC")
    case "amd":
        print("[Info] Hardware accelerated encoding enabled: AMD AMF")
    case "":
        pass
    case _:
        print("[Error] Unknown hardware acceleration method.")
        close(isCli)


# list of allowed options
allowedOptions = ["-a", "--audio", "-c", "--compatibility", "-f", "--folder", "-h", "--help", "-s", "--no-check"]

# check if URL is valid, don't print anything to stdout
def CheckURL(url, isCli):
    test = subprocess.run(["yt-dlp", "--no-playlist", "--flat-playlist", "--no-warnings", "--get-title", url], capture_output=True, text=True)
    if test.returncode != 0:
        if isCli:
            print("[Error] Invalid URL.")
        else:
            input("[Error] Media check failed. Check your URL and try again.")
        close(isCli)
    else:
        titles = test.stdout.strip().split("\n")
        print("Found media:")
        for i in range(len(titles)):
            print("- " + titles[i])
        print("Total: " + str(len(titles)))

def GetFilenames(url, folder, isCli, fileformat):
    test = subprocess.run(["yt-dlp", "--no-playlist", "--flat-playlist",  "--get-filename", "--restrict-filenames", "--no-warnings", "-o", folder + "/" + fileformat, url], capture_output=True, text=True)
    if test.returncode != 0:
        if isCli:
            print("[Error] Could not get filename.")
        else:
            input("[Error] Could not get filename. Check your URL and try again.")
        close(isCli)
    else:
        if isCli:
            print("Filename(s): " + test.stdout.strip())
        return test.stdout.strip().split("\n")
    
# returns true if the file has no video stream
def IsAudio(file):
    test = os.popen(f"ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 \"{file}\"").read()
    return test.strip() == ""

def FindDownloadedFile(basename):
    if os.path.exists(basename):
        return basename
    files = glob.glob(basename + ".*")
    if len(files) == 0:
        return None
    return files[0]
        
    
options = []
fileformat = "%(title)s"

# parse arguments
if len(sys.argv) > 1:
    url = sys.argv[1]
    options = sys.argv[2:]

    # close if unknown options are specified, ignoring the option following folder
    for i in range(len(options)):
        if options[i] not in allowedOptions:
            if options[i-1] == "-f" or options[i-1] == "--folder":
                continue
            else:
                print("Unknown option: " + options[i])
                close(isCli)

    # check if help is requested
    if "-h" in sys.argv or "--help" in sys.argv:
        print("Usage: download.py [url] [options]")
        print("Options:")
        print("-a, --audio                  : save audio only")
        print("-c, --compatibility          : transcode to mp4/m4a (MPEG-4) for maximum compatibility")
        print("-f [name], --folder [name]   : specify a folder to save the file(s) in")
        print("-s, --no-check               : skip the URL check")
        print("-h, --help                   : show this help menu, then close")
        print()
        print("If no options are specified, the text user interface is launched.")
        close(isCli)
    
    args = ["--restrict-filenames", "--no-playlist"]

    if "-a" in options or "--audio" in options:
        args.insert(0, "-x")
    args.insert(0, "--progress")
    if "-c" in options or "--compatibility" in options:
        fileformat += "-download-%(id)s"
    if "-f" in options or "--folder" in options:
        folder = options[options.index("-f") + 1] if "-f" in options else options[options.index("--folder") + 1]
        args.append("-o")
        args.append("\"" + folder + "/" + fileformat + "\"")
    else:
        folder = ""
        args.append("-o")
        args.append("\"" + fileformat + "\"")
    if "-s" in options or "--no-check" in options:
        skipCheck = True
    else:
        skipCheck = False
else:
    # text user interface
    isCli = False
    skipCheck = False
    url=input("Enter URL\n> ")

    args = ["--restrict-filenames", "--no-playlist", "--progress"]

    # ask for audio only
    audio=input("Download audio only? (y/N)\n> ")
    if audio.lower() == "y":
        args.insert(0, "-x")

    # compatibility mode
    compatibility=input("Compatibility mode? (y/N)\n> ")
    if compatibility.lower() == "y":
        options.append("-c")
        fileformat += "-download-%(id)s"

    # folder
    folder=input("Enter folder name (leave blank for current directory)\n> ")
    if folder != "":
        args.append("-o")
        args.append("\"" + folder + "/" + fileformat + "\"")
    else:
        args.append("-o")
        args.append("\"" + fileformat + "\"")
    

# remove ampersands from url and everything after
url = url.split("&")[0]

# check if url is valid
if not skipCheck:
    print("Checking media...")
    CheckURL(url, isCli)

if "-c" in options:
    # get filename(s) without extension
    filenames = GetFilenames(url, folder, isCli, fileformat)

# wrap URL in quotes
url = "\"" + url + "\""

# add url to args
args.insert(0, url)


# download, making note of whether it is successful
print("Downloading...")
test = os.system("yt-dlp " + " ".join(args))
if test != 0:
    if isCli:
        print("[Error] Download failed.")
    else:
        input("[Error] Download failed. Restart the program and try again.")
    close(isCli)
else:
    print("Success!")

# transcode to mp4/m4a if compatibility mode is enabled
if "-c" in options:
    for i in range(len(filenames)): 
        # find downloaded file
        if folder != "":
            filenames[i] = FindDownloadedFile(filenames[i])
        else:
            filenames[i] = FindDownloadedFile(filenames[i])
        if filenames[i] == None:
            print(f"[Error] Could not find downloaded file for {filenames[i]}.")
            close(isCli)
        finalname = '.'.join(filenames[i].split('-download-')[:-1])
        if IsAudio(filenames[i]):
            print("Transcoding audio...")
            test = os.system(f"ffmpeg -i \"{filenames[i]}\" -vn -c:a aac -y \"{finalname}.m4a\"")
        else:
            if hwaccel == "nvidia":
                print("Transcoding with NVENC...")
                test = os.system(f"ffmpeg -i \"{filenames[i]}\" -c:v h264_nvenc -c:a aac -y \"{finalname}.mp4\"")
            elif hwaccel == "amd":
                print("Transcoding with AMF..")
                test = os.system(f"ffmpeg -i \"{filenames[i]}\" -c:v h264_amf -c:a aac -y \"{finalname}.mp4\"")
            else:
                print("Transcoding...")
                test = os.system(f"ffmpeg -i \"{filenames[i]}\" -c:v libx264 -c:a aac -y \"{finalname}.mp4\"")
        try:
            os.remove(filenames[i])
        except:
            print(f"[Warn] Could not delete {filenames[i]}! Is it open in another program?")
        if test != 0:
            if isCli:
                print("[Error] Transcoding failed.")
            else:
                input("[Error] An error occurred during transcoding.")
                close(isCli)
close(isCli)
