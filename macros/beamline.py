from sardana.macroserver.macro import Macro, macro, imacro, Type
import tango
from time import sleep
import subprocess



@macro()
def fix(self):
    self.execMacro("laser_ready_mode")
    self.execMacro("tape_off")
    self.execMacro("target_off")


@macro()
def mte_spec_fix(self):
    mnt_grp = self.getObj(self.getEnv('ActiveMntGrp'), type_class=Type.MeasurementGroup)
    self.output('Disabled mte_spec counter')
    mnt_grp.setEnabled(False, 'mte_spec')
    self.output('Enabled again')
    mnt_grp.setEnabled(True, 'mte_spec')


@macro()
def switch_to_mte(self):
    self.output("switching to mte ccd detector...")
    # self.output("driving ccd in")
    # self.execMacro("ccd_in")
    self.output("switching measurement group to spectroscopy")
    self.execMacro("set_meas", "spectroscopy_mgmt")
    self.output("switching PiLCTimerCtrl.TriggerMode to 3")
    pilc = self.getController("PiLCTimerCtrl_spec")
    pilc.write_attribute("triggermode", 3)
    self.output(f"triggermode = %d" % pilc.read_attribute("triggermode").value)
    self.output("exporting acqconf to check mte CamTemp")
    # args are boolean: checkTape, checkTarget, checkCamTemp, startTape, stopTape, startTarget, stopTarget, autoModeLaser, darkModeLaser, autoShutterPump
    self.execMacro("acqconf", 1, 1, 1, 1, 1, 1, 1, 1, 0, 0)
    self.output("don't forget to switch\nLaVue Tango Events -> Attributes to rsxs mte")

@macro()
def switch_to_pilc_only(self):
    self.output("switching measurement group to pilc_only")
    self.execMacro("set_meas", "pilc_only")
    self.output("switching PiLCTimerCtrl.TriggerMode to 1")
    pilc = self.getController("PiLCTimerCtrl_spec")
    pilc.write_attribute("triggermode", 1)
    self.output(f"triggermode = %d" % pilc.read_attribute("triggermode").value)
    # args are boolean: checkTape, checkTarget, checkCamTemp, startTape, stopTape, startTarget, stopTarget, autoModeLaser, darkModeLaser, autoShutterPump
    self.execMacro("acqconf", 1, 1, 0, 1, 1, 1, 1, 1, 0, 0)
@macro()
def pressure_check(self):
    try:
        pressure_ccd = tango.DeviceProxy("spec/TPG261/ccd").pressure
    except:
        pressure_ccd = 9999.0
    try:
        pressure_pxs = tango.DeviceProxy("sxr/TPG261/pxs").pressure
    except:
        pressure_pxs = 9999.0
    try:
        pressure_optics = tango.DeviceProxy("spec/TPG261/optic").pressure
    except:
        pressure_optics = 9999.0


    p_pxs = 1.0e-5     # ideally 1e-5
    p_ccd = 1.0e-6     # ideally 1e-6
    p_optics = 1.0e-5  # ideally 1e-5

    self.output("pxs <%0.1e?" % p_pxs)
    self.output(pressure_pxs)
    self.output(pressure_pxs < p_pxs)
    self.output("==========")

    self.output("CCD <%0.1e?" % p_ccd)
    self.output(pressure_ccd)
    self.output(pressure_ccd < p_ccd)
    self.output("==========")

    self.output("Optics <%0.1e?" % p_optics)
    self.output(pressure_optics)
    self.output(pressure_optics < p_optics)

    if pressure_pxs < p_pxs and pressure_ccd < p_ccd and pressure_optics < p_optics:
        return True
    else:
        return False

@macro()
def start_puzzing_all(self):
    puzzi = tango.DeviceProxy("lab/roborock/puzzi")
    if puzzi.status() == 'Status:\ncharging\nState:\ndocked':
        self.output("Cleaning entire lab! Battery level: %d percent."%puzzi.battery_level)
        puzzi.start_cleaning_all()

    else:
        self.warning("Puzzi not happy :( ")
        self.warning("Status: %s"%puzzi.status())

@macro()
def stop_puzzing(self):
    puzzi = tango.DeviceProxy("lab/roborock/puzzi")
    self.output("Returning home! Battery level: %d percent."%puzzi.battery_level)
    puzzi.stop_cleaning()
    puzzi.return_to_dock()

@macro()
def sync(self):
    scanDir = self.getEnv("ScanDir")
    self.output("synchronize data to NAS")
    result = subprocess.run(
    f'rsync -r -t -g -v --progress -s {scanDir} data_ampere@nasbsxr.sxr.lab:/share/Data/henryetta.sxr.lab/spectroscopy',shell = True, stdout=subprocess.PIPE,)
    self.output(result.stdout.decode("utf-8"))


@macro()
def end_of_the_day(self):
    self.output("Running end_of_the_day in 5s:")

    for i in range(5):
        self.output((i + 1) * ".")
        sleep(1)

    self.execMacro("umv", "thindisk_laser_wp", "0")

    try:
        self.execMacro("tape_off")
        self.execMacro("target_off")
    except:
        self.warning("Tape and/or target could not be turned off!")

    try:
        self.execMacro("laser_sleep_mode")
        self.execMacro("shutter_disable")
        self.execMacro("shutter_manual")  
        self.execMacro("laser_off")
    except:
        self.warning("Shutter and/or flipmounts did not close properly! Manually disable the shutter!")

    self.output("CAUTION! PUMP BEAM MAY BE NOT BLOCKED!!!!!!!")

    try:
        self.execMacro("umv", "mag_curr_spec", "0")
    except:
        self.output("Magnet can not be turned off. CaenFastPS off?")


    try:
        self.execMacro("mte_temp_set", 19)
    except:
        self.warning("Could not contact CCD to heat to 19 degrees C")


    try:
        self.execMacro("pressure_check")
    except:
        self.warning("Could not get pressures.")

    
    try:
        self.execMacro("sync")
    except:
        self.warning("Sync data")
    
    try:
        self.execMacro("start_puzzing_all")
    except:
        self.warning("Could not contact Puzzi properly.")

    



