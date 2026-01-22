from sardana.macroserver.macro import Macro, macro, Type


@macro([
    ['roi_name', Type.String, None, 'name of the roi in Environment/LaVue'],
    ['output', Type.Boolean, True, 'output roi']
])
def roi_read(self, roi_name, output):
    """Macro roi_read"""
    rois = self.getEnv('DetectorROIs')
    try:
        roi = rois[roi_name]
        if output:
            self.output('{:s}: {:s}'.format(roi_name, str(roi[0])))
        return roi[0]
    except KeyError:
        self.error('ROI \"{:s}\" not in Environment/LaVue'.format(roi_name))
        return []


