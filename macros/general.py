from sardana.macroserver.macro import imacro, macro, Type, Optional
from tango import DeviceProxy
import numpy as np


@imacro(
    [
        ["checkTape", Type.Boolean, Optional, "check tape"],
        ["checkTarget", Type.Boolean, Optional, "check target"],
        ["checkCamTemp", Type.Boolean, Optional, "check cam temp"],
        ["startTape", Type.Boolean, Optional, "start tape"],
        ["stopTape", Type.Boolean, Optional, "stop tape"],
        ["startTarget", Type.Boolean, Optional, "start target"],
        ["stopTarget", Type.Boolean, Optional, "stop target"],
        ["autoModeLaser", Type.Boolean, Optional, "auto mode laser"],
        ["darkModeLaser", Type.Boolean, Optional, "dark mode laser"],
        ["autoShutterPump", Type.Boolean, Optional, "auto shutter pump"],
        ["waitTime", Type.Float, Optional, "wait time"],
    ]
)
def acqconf(
    self,
    checkTape,
    checkTarget,
    checkCamTemp,
    startTape,
    stopTape,
    startTarget,
    stopTarget,
    autoModeLaser,
    darkModeLaser,
    autoShutterPump,
    waitTime,
):
    # run all the other configurations
    try:
        acqConf = self.getEnv("acqConf")
    except:
        acqConf = {}

    if checkTape is None:
        checkTape = self.input(
            "Check tape before acquisition:",
            data_type=Type.Boolean,
            title="check tape",
            default_value=acqConf["checkTape"],
        )

    if checkTarget is None:
        checkTarget = self.input(
            "Check target before acquisition:",
            data_type=Type.Boolean,
            title="check target",
            default_value=acqConf["checkTarget"],
        )

    if checkCamTemp is None:
        checkCamTemp = self.input(
            "Check cam temp before acquisition:",
            data_type=Type.Boolean,
            title="check cam temp",
            default_value=acqConf["checkCamTemp"],
        )

    acqConf["checkTape"] = checkTape
    acqConf["checkTarget"] = checkTarget
    acqConf["checkCamTemp"] = checkCamTemp

    if startTape is None:
        startTape = self.input(
            "Start tape before scan:",
            data_type=Type.Boolean,
            title="start tape",
            default_value=acqConf["startTape"],
        )
    if stopTape is None:
        stopTape = self.input(
            "Stop tape after scan:",
            data_type=Type.Boolean,
            title="stop tape",
            default_value=acqConf["stopTape"],
        )

    if startTarget is None:
        startTarget = self.input(
            "Start target before scan:",
            data_type=Type.Boolean,
            title="start target",
            default_value=acqConf["startTarget"],
        )

    if stopTarget is None:
        stopTarget = self.input(
            "Stop target after scan:",
            data_type=Type.Boolean,
            title="stop target",
            default_value=acqConf["stopTarget"],
        )

    acqConf["startTape"] = startTape
    acqConf["stopTape"] = stopTape
    acqConf["startTarget"] = startTarget
    acqConf["stopTarget"] = stopTarget

    if autoModeLaser is None:
        autoModeLaser = self.input(
            "Change laser mode automatically before/after scans to acquire a standard image",
            data_type=Type.Boolean,
            title="auto mode laser",
            default_value=acqConf["autoModeLaser"],
        )

    if darkModeLaser is None:
        darkModeLaser = self.input(
            "Change laser mode automatically before/after scans to acquire a dark image instead of a standard image",
            data_type=Type.Boolean,
            title="dark mode laser",
            default_value=acqConf["darkModeLaser"],
        )

    if autoShutterPump is None:
        autoShutterPump = self.input(
            "Open/close pump laser before/after movements:",
            data_type=Type.Boolean,
            title="auto shutter pump",
            default_value=acqConf["autoShutterPump"],
        )

    acqConf["autoModeLaser"] = autoModeLaser
    acqConf["darkModeLaser"] = darkModeLaser
    acqConf["autoShutterPump"] = autoShutterPump

    self.setEnv("acqConf", acqConf)

    self.execMacro("waittime", waitTime)

    # self.execMacro('powerconf')
    # self.execMacro('fluenceconf')
    # self.output('\r')
    # self.execMacro('acqrep')


@macro()
def acqrep(self):
    acqConf = self.getEnv("acqConf")
    self.output(
        "Gen. Settings:\nWaittime = %.2f s | check tape: %r | check target: %r | check cam temp: %r\nstart tape: %r | stop tape: %r |start target: %r | stop target: %r\nauto mode laser: %r",
        acqConf["waitTime"],
        acqConf["checkTape"],
        acqConf["checkTarget"],
        acqConf["checkCamTemp"],
        acqConf["startTape"],
        acqConf["stopTape"],
        acqConf["startTarget"],
        acqConf["stopTarget"],
        acqConf["autoModeLaser"],
    )
    #self.execMacro("powerrep")
    #self.execMacro("fluencerep")


@imacro([["time", Type.Float, Optional, "time in seconds"]])
def waittime(self, time):
    """Macro waittime"""
    acqConf = self.getEnv("acqConf")

    if time is None:
        label, unit = "Waittime", "s"
        time = self.input(
            "Wait time before every acqisition?",
            data_type=Type.Float,
            title="Waittime Amplitude",
            key=label,
            unit=unit,
            default_value=acqConf["waitTime"],
            minimum=0.0,
            maximum=100,
        )

    acqConf["waitTime"] = time
    self.setEnv("acqConf", acqConf)
    self.output("waittime set to %.2f s", time)


@imacro(
    [
        ["pumpHor", Type.Float, Optional, "pumpHor"],
        ["pumpVer", Type.Float, Optional, "pumpVer"],
        ["refl", Type.Float, Optional, "reflectivity"],
        ["repRate", Type.Float, Optional, "repetition rate"],
    ]
)
def fluenceconf(self, pumpHor, pumpVer, refl, repRate):
    fluencePM = DeviceProxy("pm/fluencectrl/1")
    try:
        lastPumpHor = fluencePM.pumpHor
        lastPumpVer = fluencePM.pumpVer
        lastRefl = fluencePM.refl
        lastRepRate = fluencePM.repRate
    except:
        lastPumpHor = 100
        lastPumpVer = 100
        lastRefl = 0
        lastRepRate = 3000

    if pumpHor is None:
        label, unit = "hor", "um"
        pumpHor = self.input(
            "Set the horizontal beam diameter (FWHM):",
            data_type=Type.Float,
            title="Horizontal beam diameter",
            key=label,
            unit=unit,
            default_value=lastPumpHor,
            minimum=0.0,
            maximum=100000,
        )
    if pumpVer is None:
        label, unit = "ver", "um"
        pumpVer = self.input(
            "Set the vertical beam diameter (FWHM):",
            data_type=Type.Float,
            title="Vertical beam diameter",
            key=label,
            unit=unit,
            default_value=lastPumpVer,
            minimum=0.0,
            maximum=100000,
        )
    if refl is None:
        label, unit = "refl", "%"
        refl = self.input(
            "Set the sample reflectivity:",
            data_type=Type.Float,
            title="Sample reflectivity",
            key=label,
            unit=unit,
            default_value=lastRefl,
            minimum=0.0,
            maximum=100,
        )
    if repRate is None:
        label, unit = "repRate", "Hz"
        repRate = self.input(
            "Set the laser repetition rate:",
            data_type=Type.Float,
            title="Laser repetition rate",
            key=label,
            unit=unit,
            default_value=lastRepRate,
            minimum=0.0,
            maximum=10000,
        )

    fluencePM.pumpHor = pumpHor
    fluencePM.pumpVer = pumpVer
    fluencePM.refl = refl
    fluencePM.repRate = repRate

    power = self.getPseudoMotor("power")
    fluence = self.getPseudoMotor("fluence")
    minPower, maxPower = power.getPositionObj().getLimits()

    trans = 1 - (refl / 100)
    minFluence = (
        minPower
        * trans
        / (repRate / 1000 * np.pi * pumpHor / 10000 / 2 * pumpVer / 10000 / 2)
    )
    maxFluence = (
        maxPower
        * trans
        / (repRate / 1000 * np.pi * pumpHor / 10000 / 2 * pumpVer / 10000 / 2)
    )
    self.info("Update limits of pseudo motor fluence")
    fluence.getPositionObj().setLimits(minFluence, maxFluence)

    self.execMacro("fluencerep")


@macro()
def fluencerep(self):
    fluencePM = DeviceProxy("pm/fluencectrl/1")

    pumpHor = fluencePM.pumpHor
    pumpVer = fluencePM.pumpVer
    refl = fluencePM.refl
    repRate = fluencePM.repRate

    self.output(
        "Fluence Settings: pumpHor = %.2f um | pumpVer = %.2f um |"
        "refl = %.2f %% | repRate = %.2f Hz",
        pumpHor,
        pumpVer,
        refl,
        repRate,
    )

    fluence = self.getPseudoMotor("fluence")
    [minFluence, maxFluence] = fluence.getPositionObj().getLimits()

    self.output(
        "Fluence Limits  : min = %.3f mJ/cm^2 | max = %.3f mJ/cm^2",
        minFluence,
        maxFluence,
    )


@imacro(
    [
        ["P0", Type.Float, Optional, "P0"],
        ["Pm", Type.Float, Optional, "Pm"],
        ["offset", Type.Float, Optional, "offset"],
        ["period", Type.Float, Optional, "period"],
    ]
)
def powerconf(self, P0, Pm, offset, period):
    """This sets the parameters of the power pseudo motor"""
    power = DeviceProxy("pm/powerctrl/1")

    if P0 is None:
        label, unit = "P0", "W"
        P0 = self.input(
            "Set the minimum power:",
            data_type=Type.Float,
            title="Minimum Power",
            key=label,
            unit=unit,
            default_value=power.P0,
            minimum=0.0,
            maximum=100000,
        )

    if Pm is None:
        label, unit = "Pm", "W"
        Pm = self.input(
            "Set the maximum power:",
            data_type=Type.Float,
            title="Maximum Power",
            key=label,
            unit=unit,
            default_value=power.Pm,
            minimum=0.0,
            maximum=100000,
        )

    if offset is None:
        label, unit = "offset", "deg"
        offset = self.input(
            "Set the radial offset:",
            data_type=Type.Float,
            title="Radial Offset",
            key=label,
            unit=unit,
            default_value=power.offset,
            minimum=-45,
            maximum=45,
        )

    if period is None:
        label, unit = "period", ""
        period = self.input(
            "Set the radial period:",
            data_type=Type.Float,
            title="Radial Period",
            key=label,
            unit=unit,
            default_value=power.period,
            minimum=0,
            maximum=2,
        )

    self.info("Update parameters of pseudo motor power")
    power.offset = offset
    power.period = period
    power.P0 = P0
    power.Pm = Pm

    self.execMacro("set_lim", "power", P0, (Pm + P0))
    self.execMacro("powerrep")


@macro()
def powerrep(self):
    # return all powerconf values
    power = DeviceProxy("pm/powerctrl/1")
    self.output(
        "Power Settings  : P0 = %.4f W | Pm = %.4f W |"
        "offset = %.2f deg | period = %.2f",
        power.P0,
        power.Pm,
        power.offset,
        power.period,
    )


@macro()
def init_sardana(self):
    """initalising Sardana"""
    self.output("Energy to 707:")
    self.execMacro("umv", "energy", 707)
    self.execMacro("loadcrystal")


@macro()
def roirep(self):
    """Macro to print the Rois"""
    self.execMacro("genv", "DetectorROIs")
