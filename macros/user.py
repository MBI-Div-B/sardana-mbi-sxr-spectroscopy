from sardana.macroserver.macro import Macro, macro, Type
from time import sleep
from tango import DeviceProxy

from dirsync import sync
import os
import subprocess


@macro()
def user_pre_acq(self):
    """Macro user_pre_acq"""

    acqConf = self.getEnv("acqConf")
    try:
        waittime = acqConf["waitTime"]
    except:
        self.warning("env variable acqConf/waitTime not found!")
        waittime = 0

    try:
        check_tape = acqConf["checkTape"]
    except:
        self.warning("env variable acqConf/checkTape not found!")
        check_tape = False

    try:
        check_cam_temp = acqConf["checkCamTemp"]
    except:
        self.warning("env variable acqConf/checkCamTemp not found!")
        check_cam_temp = False

    if check_tape:
        self.execMacro("tape_check")

    if check_cam_temp:
        self.execMacro("ccd_check")

    if waittime > 0:
        sleep(waittime)
        self.debug("waiting for %.2f s", waittime)


@macro()
def user_pre_scan(self):
    """Macro user_pre_scan"""
    acqConf = self.getEnv("acqConf")

    try:
        start_tape = acqConf["startTape"]
    except:
        self.warning("env variable acqConf/startTape not found!")
    if start_tape:
        self.execMacro("tape_on")

    try:
        start_target = acqConf["startTarget"]
    except:
        self.warning("env variable acqConf/startTarget not found!")
    if start_tape:
        self.execMacro("target_on")

    try:
        dark_mode_laser = acqConf["darkModeLaser"]
    except:
        self.warning("env variable acqConf/darkModeLaser not found!")
    if dark_mode_laser:
        self.execMacro("laser_dark_mode")
    else:
        try:
            auto_mode_laser = acqConf["autoModeLaser"]
        except:
            self.warning("env variable acqConf/autoModeLaser not found!")
        if auto_mode_laser:
            self.execMacro("laser_scan_mode")

    self.execMacro("acqrep")


# @macro()
# def dark_image_prep(self):
#    """Macro to prepare for dark image"""
#
#    self.execMacro('laser_sleep_mode')
#    self.execMacro('shutter_disable')
#    self.execMacro('shutter_external')
#    self.execMacro('probe_off')
#    self.execMacro('laser_on')
#    sleep(0.4)
#    self.execMacro('shutter_enable')
#    self.execMacro('tape_on')


@macro()
def user_post_scan(self):
    """Macro user_pre_scan"""

    acqConf = self.getEnv("acqConf")

    try:
        stop_tape = acqConf["stopTape"]
    except:
        self.warning("env variable acqConf/stopTape not found!")
        stop_tape = False

    if stop_tape:
        self.execMacro("tape_off")

    try:
        stop_target = acqConf["stopTarget"]
    except:
        self.warning("env variable acqConf/stopTarget not found!")
        stop_target = False

    if stop_target:
        self.execMacro("target_off")

    try:
        auto_mode_laser = acqConf["autoModeLaser"]
    except:
        self.warning("env variable acqConf/autoModeLaser not found!")

    if auto_mode_laser:
        self.execMacro("laser_ready_mode")


@macro()
def user_post_scan_sync(self):
    scanDir = self.getEnv("ScanDir")

    #    sync_cmd = ["sshpass", "-p", "'cV4mBBpS2StpqBP'", "rsync", "-r", "-t", "-g", "-v", "--progress", "-s", "/home/labuser/Data", "data_ampere@nasbsxr.sxr.lab:/share/Data/henryetta.sxr.lab/spectroscopy"]

    if scanDir is not "" and scanDir is not None:
        self.output("Mirroring on NAS initiated...")
        result = subprocess.run(
            f'rsync -r -t -g -v --progress -s --include="*_[0-9][0-9][0-9][0-9].h5" --exclude="*.h5" {scanDir} data_ampere@nasbsxr.sxr.lab:/share/Data/henryetta.sxr.lab/spectroscopy',
            shell=True,
            stdout=subprocess.PIPE,
        )
        self.output(result.stdout.decode("utf-8"))
        self.output("End of mirroring.")
    else:
        self.output("ScanDir is not set, please check the save path.")


#    ScanDir = self.getEnv('ScanDir')
#    RemoteScanDir = self.getEnv('RemoteScanDir')
#
#    if os.path.exists(RemoteScanDir):
#        self.info('Syncing data from %s to %s', ScanDir, RemoteScanDir)
#        sync(ScanDir, RemoteScanDir, 'sync', create=True)
#    else:
#        self.warning('RemoteScanDir %s does not exist - no folder syncing', RemoteScanDir)


@macro()
def user_pre_move(self):
    """Macro user_pre_move"""

    # self.info('In user pre move')

    acqConf = self.getEnv("acqConf")

    try:
        auto_shutter_pump = acqConf["autoShutterPump"]
    except:
        self.warning("env variable acqConf/autoShutterPump not found!")
        auto_shutter_pump = False

    if auto_shutter_pump:
        parent = self.getParentMacro()
        if parent:
            # check if we need to close the shutter or not
            close_pump_shutter = False
            for mot in parent.motors:
                self.output(mot)
                if mot.name.lower().strip() in ["h", "k", "l", "th", "tth", "q", "thc"]:
                    close_pump_shutter = True
            if close_pump_shutter:
                # check if the pump shutter is open
                proxy = DeviceProxy("laser/ThorlabsMFF100/pump")
                mirror_state = proxy.mffstate
                while mirror_state not in [0, 1]:
                    sleep(0.1)
                    mirror_state = proxy.mffstate
                if mirror_state == 1:
                    self.setEnv("autoClosePump", True)
                    self.execMacro("pump_off")


@macro()
def user_post_move(self):
    """Macro user_post_move"""

    # self.info('In user post move')

    acqConf = self.getEnv("acqConf")

    try:
        auto_shutter_pump = acqConf["autoShutterPump"]
    except:
        self.warning("env variable acqConf/autoShutterPump not found!")
        auto_shutter_pump = False

    if auto_shutter_pump:
        parent = self.getParentMacro()
        if parent:
            if self.getEnv("autoClosePump"):
                # shutter was automatically close in pre-move
                # check if we really need to open the shutter or not
                open_pump_shutter = False
                for mot in parent.motors:
                    if mot.name.lower().strip() in [
                        "h",
                        "k",
                        "l",
                        "th",
                        "tth",
                        "q",
                        "thc",
                    ]:
                        open_pump_shutter = True

                if open_pump_shutter:
                    # check if the pump shutter is closed
                    proxy = DeviceProxy("laser/ThorlabsMFF100/pump")
                    mirror_state = proxy.mffstate
                    while mirror_state not in [0, 1]:
                        sleep(0.1)
                        mirror_state = proxy.mffstate
                    if mirror_state == 0:
                        self.setEnv("autoClosePump", False)
                        self.execMacro("pump_on")
