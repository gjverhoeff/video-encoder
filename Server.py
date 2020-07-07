import subprocess
import multiprocessing
import json
import os
from datetime import datetime
import time
import shutil


class Encoder():
    def Encode(self, videofilename):

        # Run Sound and video encoding
        if self._LUFSTrueFalse:
            try:
                self.Loudness_Encoding(videofilename, self._Tempfolder)
            finally:
                self.Video_Encoding(videofilename, self._Tempfolder)
                # Remove the temp file after use
                os.remove(self._Tempfolder + videofilename)
        else:
            self.Video_Encoding(videofilename, self._MediaFolder)

    def Video_Encoding(self, videofilename, tempfolder):
        try:
            subprocess.check_output('ffmpeg\\bin\\ffmpeg.exe -y -i ' + '\"' + tempfolder + videofilename + '\"' +
                                    ' -vcodec ' + self._Vcodec +
                                    ' -x264-params "nal-hrd=cbr"' +
                                    ' -b:v ' + self._VideoBitrate +
                                    ' -minrate ' + self._VideoBitrate +
                                    ' -maxrate ' + self._VideoBitrate +
                                    ' -bufsize ' + self._VideoBitrateBuffer +
                                    ' -filter:v "scale=' + self._Resolution + ', fps=fps=' + self._Fps + '"' +
                                    ' -acodec ' + self._Acodec +
                                    ' -b:a ' + self._AudioBitrate +
                                    ' \"' + self._MediaDestFolder + os.path.splitext(videofilename)[0] + '.mp4' + '\"')

        except subprocess.CalledProcessError as e:
            raise Exception('Video_Encoding Error: {}'.format(e))

    def Loudness_Encoding(self, videofilename, tempfolder):
        try:
            TARGET_I = self._TARGET_I
            TARGET_TP = self._TARGET_TP
            TARGET_LRA = self._TARGET_LRA

            ffArgs = ('ffmpeg\\bin\\ffmpeg.exe -hide_banner -i ' +
                      '\"' + self._MediaFolder + videofilename + '\"' +
                      ' -af loudnorm=I=%s:TP=%s:LRA=%s:print_format=json' % (TARGET_I, TARGET_TP, TARGET_LRA) +
                      ' -f null -')

            output = subprocess.check_output(ffArgs, stderr=subprocess.STDOUT)
            # Read the last 12 lines of the output which is where the data is.
            outputJson = ''.join(str(e) for e in (output.splitlines()[-12:]))
            # Remove random text from the outbit
            outputJson = outputJson.replace('b\'', '')
            outputJson = outputJson.replace('\'', '')
            outputJson = outputJson.replace('\\t', '')
            measured = json.loads(outputJson)

            ffArg_with_LUFS = ('ffmpeg\\bin\\ffmpeg.exe -y -hide_banner -i \"' +
                               self._MediaFolder + videofilename + '\"' +
                               ' -af loudnorm=I=%s:TP=%s:LRA=%s' % (TARGET_I, TARGET_TP, TARGET_LRA) +
                               ':measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s' % (
                               measured['input_i'], measured['input_tp'], measured['input_lra'],
                               measured['input_thresh'], measured['target_offset']) +
                               ':linear=true:print_format=summary \"' +
                               tempfolder + videofilename + '\"')

            subprocess.check_call(ffArg_with_LUFS)
        except subprocess.CalledProcessError as e:
            raise Exception('Loudness_Encoding Error: {}'.format(e))

    # The names in the json file has to be same as in this method else an error occur.
    def Read_Config(self):
        try:
            with open('Config.json') as f:
                data = json.load(f)
            self._Vcodec = data["VideoEncoder"]["Vcodec"]
            self._Fps = data["VideoEncoder"]["Fps"]
            self._Resolution = data["VideoEncoder"]["Resolution"]
            self._VideoBitrate = data["VideoEncoder"]["Bitrate"]
            self._VideoBitrateBuffer = data["VideoEncoder"]["Buffer"]

            self._Acodec = data["AudioEncoder"]["Acodec"]
            self._AudioBitrate = data["AudioEncoder"]["Bitrate"]
            self._LUFSTrueFalse = data["AudioEncoder"]["LUFS Encoding"]
            self._TARGET_I = data["AudioEncoder"]["Integrated Loudness"]
            self._TARGET_TP = data["AudioEncoder"]["Maximum True Peak"]
            self._TARGET_LRA = data["AudioEncoder"]["Maximum loudness range"]

            self._MediaFolder = data["Folder"]["Media Folder"]
            self._MediaDestFolder = data["Folder"]["Media Destination Folder"]
            self._GarbageFolder = data["Folder"]["Garbage Folder"]
            self._Extension = data["Aproved Extension"]["Extension"]

        except Exception as e:
            raise Exception('Read_Config Error: {}'.format(e))

    # Finde all files in the media folder with the aproved extension.
    # Use "Extension", "Media Folder"
    def Find_All_Files(self):
        try:
            filenames = [fn for fn in os.listdir(self._MediaFolder) if fn.split(".")[-1] in self._Extension]
            return filenames
        except Exception as e:
            raise Exception('Find_All_Files Error: {}'.format(e))

    def Move_File_To_Garbage(self, File):
        try:
            shutil.move(str(self._MediaFolder + File), str(self._GarbageFolder + File))
            # os.replace(str(self._MediaFolder+File), str(self._GarbageFolder+File))
        except Exception as e:
            raise Exception('Move_File_To_Garbage Error: {}'.format(e))

    # Create and wirte to the log
    def Log(self, text):
        # timestamp = datetime.timestamp(datetime.now())
        log = open("Log.txt", "a")
        log.writelines(str(" -- " + text + "\n"))
        log.close()

    def Create_Folders(self):
        try:
            if not os.path.exists(self._MediaDestFolder):
                os.makedirs(self._MediaDestFolder)
            if not os.path.exists(self._GarbageFolder):
                os.makedirs(self._GarbageFolder)
            if not os.path.exists(self._MediaFolder):
                os.makedirs(self._MediaFolder)
            # Create a temp folder for the LUFS encoding
            self._Tempfolder = self._MediaDestFolder + "temp/"
            if not os.path.exists(self._Tempfolder):
                os.makedirs(self._Tempfolder)

        except Exception as e:
            raise Exception('Create_Folders Error: {}'.format(e))

    # Use the first file in the filelist and then it is beeing encoded
    def Execute_An_Encoder(self):
        try:
            List_Of_Files = self.Find_All_Files()
            if (len(List_Of_Files) > 0):
                self.Encode(List_Of_Files[0])
                self.Move_File_To_Garbage(List_Of_Files[0])
                self.Log(str(List_Of_Files[0] + " - Was Encoded"))

        except Exception as e:
            self.Log(str(e))
            self.Log(str(List_Of_Files[0] + " - Error - Was Not Encoded"))
            self.Move_File_To_Garbage(List_Of_Files[0])

    def clear(self):
        # for windows
        if os.name == 'nt':
            _ = os.system('cls')
            # for mac and linux(here, os.name is 'posix')
        else:
            _ = os.system('clear')

            # Load the config file

    # When Debugmode is set to False, the terminal will be cleaned.
    def Start(self, debugmode):
        try:
            self.Log("Starting")
            self.Read_Config()
            self.Create_Folders()
            while True:
                self.Execute_An_Encoder()
                if not debugmode:
                    self.clear()
                    print("waiting for a file!")
                    time.sleep(5)
                    self.clear()
                else:
                    time.sleep(5)
        except Exception as e:
            self.Log(str(e))
            exit()


def proc_start():
    debugmode = True
    e = Encoder()
    p_to_start = multiprocessing.Process(target=e.Start, args=(debugmode,))
    p_to_start.start()
    return p_to_start


def proc_stop(p_to_stop):
    p_to_stop.kill()


# Main
if __name__ == '__main__':
    proc = proc_start()
    exit = False
    while not exit:
        r = input("")
        if r == 'q':
            print("Exit")
            exit = True
            proc_stop(proc)
        elif r == 'restart' or r == 'rest':
            print("Restarting")
            proc_stop(proc)
            time.sleep(5)
            proc = proc_start()
        else:
            print('invalid input: {}. Press"q" for quit or "rest" for restart'.format(r))
