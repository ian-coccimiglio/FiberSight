from javax.swing import JFrame, JLabel, JPanel, JButton, JRadioButton, JSpinner, SpinnerNumberModel, \
    ButtonGroup, JTextField, JDialog, JOptionPane, ImageIcon, SwingConstants, JComboBox, JCheckBox
from java.awt import GridBagConstraints as GBC, GridBagLayout, Font, Insets,\
    Color, GridLayout
from javax.swing.border import EmptyBorder
from java.awt.event import ActionListener, WindowAdapter
from javax.swing.event import ChangeListener
from java.awt import Image
from ij.io import OpenDialog
import sys

class FiberSight(WindowAdapter):
    CHANNEL_OPTIONS = ["Fiber Border", "DAPI", "Type I", "Type IIa", "Type IIx", "Type IIb", "None"]
    EXPECTED_IMAGE_FORMATS = ('.nd2','.czi','.tif','.tiff','.png')
    EXPECTED_ROI_FORMATS = ('.roi', '.zip')
    STRING_IMAGE_FORMATS = ', '.join([x for x in EXPECTED_IMAGE_FORMATS])
    STRING_ROI_FORMATS = ', '.join([x for x in EXPECTED_ROI_FORMATS])
    def __init__(self, input_image_path=None, input_roi_path=None):
        # fsIconLeft = ImageIcon(ImageIcon("/home/ian/SynologyDrive/data/results_smallCompositeCalibrated/FS_icon.png").getImage().getScaledInstance(100, 100, Image.SCALE_DEFAULT))
        # fsIconLeft = ImageIcon(ImageIcon("/home/ian/SynologyDrive/fs_Icon_right.png").getImage().getScaledInstance(150, 150, Image.SCALE_DEFAULT))
        
        self.input_image_path = input_image_path
        self.input_roi_path = input_roi_path
        self.terminated=False
        
        self.mainFrame = JDialog(JFrame("FiberSight"), True)        
        self.titleFont = Font("Sans Serif", Font.PLAIN, 16)
        
        # self.leftIcon = JLabel(fsIconLeft)
        self.mainFrame.setLayout(GridLayout(4,0))
        
        self.headerPanel = JPanel(GridBagLayout())
        self.headerPanel.setBorder(EmptyBorder(1,1,1,1))
        self._addHeader()
        
        self.middlePanel = JPanel(GridBagLayout())
        self.middlePanel.setBorder(EmptyBorder(1,1,1,1))
        self._addInputs()
        self._addImportButtons()
        
        self.bottomPanel = JPanel(GridBagLayout())
        self.bottomPanel.setBorder(EmptyBorder(1,1,1,1))
        self._addChannels()
        self._addToggleButton()
        self._addStart()
        
        self.advancedPanel = self.create_advanced_panel()
        self.advancedPanel.setVisible(False)  # Hidden by default
        gbc = GBC()
        
        self.mainFrame.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE)
        self.mainFrame.getContentPane().add(self.headerPanel, gbc)
        self.mainFrame.getContentPane().add(self.middlePanel, gbc)
        self.mainFrame.getContentPane().add(self.bottomPanel, gbc)
        self.mainFrame.getContentPane().add(self.advancedPanel, gbc)
        self.mainFrame.pack()
        self.mainFrame.setLocationRelativeTo(None) # Sets to center of the screen. Put /after/ the pack function.
        self.close_control = self.CloseControl()
        self.mainFrame.addWindowListener(self.close_control)
        self.start_button.requestFocusInWindow()
        self.mainFrame.visible = True
        self.mainFrame.getRootPane().setDefaultButton(self.start_button)


    def create_advanced_panel(self):
        panel = JPanel(GridBagLayout())
        panel.setBorder(EmptyBorder(1,1,1,1))
        gbc = GBC()
        
        # Add your advanced options here
        advanced_model_label = JLabel("Cellpose Model")
        advanced_diameter_label = JLabel("Cellpose Diameter")
        advanced_ft_label = JLabel("Fiber-Typing Thresholding")
        
        self.advanced_model = JComboBox(["cyto3", "PSR_9", "HE_30", "WGA_21"])
        self.advanced_model.createToolTip()
        self.advanced_model.setToolTipText("cyto3 model is the baseline model, others are finetuned")

        self.advanced_ft_method = JComboBox(["Huang", "Mean", "Otsu"])
        self.advanced_ft_method.createToolTip()
        self.advanced_ft_method.setToolTipText("Fiber-Typing Thresholding Method")

        self.advanced_diameter = JSpinner(SpinnerNumberModel(0, 0, 200, 1))
        self.advanced_diameter.createToolTip()
        self.advanced_diameter.setToolTipText("Diameter of 0 will auto-estimate diameter given the cyto3 model")

        self.advanced_remove = JCheckBox("Remove Small ROIs", True)
        self.advanced_remove.createToolTip()
        self.advanced_remove.setToolTipText("Removes ROIs with area below 10 pixels as mis-detections")

        self.advanced_hybrids = JCheckBox("Quantify Hybrid Fiber-Types", True)
        self.advanced_hybrids.createToolTip()
        self.advanced_hybrids.setToolTipText("Categorizes hybrid fibertypes (e.g. I/IIa, IIa/IIx, IIx/IIb)")

        self.advanced_ft_correction = JCheckBox("Pseudo Flat-Field Correction (Fiber-Typing)")
        self.advanced_ft_correction.createToolTip()
        self.advanced_ft_correction.setToolTipText("Corrects for uneven staining/fluorescence/lighting")
        
        self.advanced_overwrite_button = JCheckBox("Overwrite Existing Segmentation")
        self.advanced_overwrite_button.createToolTip()
        self.advanced_overwrite_button.setToolTipText("Will overwrite an existing segmentation in cellpose_rois directory")
        
        cellpose_listener = self.ToggleOverwrite(self.advanced_overwrite_button)
        self.advanced_model.addActionListener(cellpose_listener)
        self.advanced_diameter.addChangeListener(cellpose_listener)

        gbc.gridx = 0
        gbc.gridy = 0
        gbc.anchor = GBC.LINE_END
        gbc.weightx = 1.0
        gbc.fill = GBC.NONE
        gbc.ipadx = 15
        gbc.ipady = 5
        gbc.insets = Insets(5,2,2,5)
        panel.add(advanced_diameter_label, gbc)
        gbc.fill = GBC.HORIZONTAL
        gbc.gridx = 1
        panel.add(self.advanced_diameter, gbc)
        
        gbc.gridx = 0
        gbc.gridy = 1
        gbc.anchor = GBC.EAST
        gbc.fill = GBC.NONE
        panel.add(advanced_model_label, gbc)
        gbc.gridx = 1
        gbc.fill = GBC.HORIZONTAL
        panel.add(self.advanced_model, gbc)
        
        gbc.gridy = 2
        gbc.gridx = 0
        panel.add(advanced_ft_label, gbc)
        gbc.gridx = 1
        panel.add(self.advanced_ft_method, gbc)
        
        gbc.gridy = 0
        gbc.gridx = 2
        panel.add(self.advanced_remove, gbc)
        
        gbc.gridy = 1
        gbc.gridx = 2
        panel.add(self.advanced_hybrids, gbc)

        gbc.gridy = 0
        gbc.gridx = 3
        panel.add(self.advanced_ft_correction, gbc)
        
        gbc.gridy = 1
        gbc.gridx = 3
        panel.add(self.advanced_overwrite_button, gbc)
        
        return panel

    def _addToggleButton(self):
        gbc = GBC()
        gbc.gridy = 0
        gbc.gridx = 5
        gbc.ipady = 10
        self.advanced_toggle = JCheckBox("Show Advanced Options")
        self.advanced_toggle.addActionListener(self.toggle_advanced_options)
        self.bottomPanel.add(self.advanced_toggle, gbc)

    def toggle_advanced_options(self, event):
        self.advancedPanel.setVisible(self.advanced_toggle.isSelected())
        # self.mainFrame.pack()  # Resize frame to fit new content

    def _addChannels(self):
        self.channels = []
        channels_1 = self._place_channel_dropdown(self.bottomPanel, "DAPI", 1)
        channels_2 = self._place_channel_dropdown(self.bottomPanel, "Fiber Border", 2)
        channels_3 = self._place_channel_dropdown(self.bottomPanel, "None", 3)
        channels_4 = self._place_channel_dropdown(self.bottomPanel, "None", 4)
        self.channels.extend([channels_1, channels_2, channels_3, channels_4])
        
    def _place_channel_dropdown(self, panel, selected_item, height):
        gbc=GBC()
        channel_labels = JLabel("Channel {}".format(height))
        channel_chooser = JComboBox(self.CHANNEL_OPTIONS)
        channel_chooser.setSelectedItem(selected_item)
        panel.add(channel_labels, gbc)
        gbc.anchor = GBC.CENTER
        gbc.insets = Insets(5,2,2,5)
        gbc.gridx = height-1
        gbc.anchor = GBC.WEST
        panel.add(channel_chooser, gbc)
        return channel_chooser

    def _set_image_path(self, path, fp_field, field_type, expectedFormats):
        self.image_field.setText(path)
        self._validate_file_path(fp_field, field_type, expectedFormats)

    def _set_roi_path(self, path, fp_field, field_type, expectedFormats):
        self.roi_field.setText(path)
        self._validate_file_path(fp_field, field_type, expectedFormats)

    def _addStart(self):
        self.start_button = JButton("Start FiberSight", actionPerformed=self._start_FiberSight)
        gbc = GBC()
        gbc.anchor = GBC.EAST
        gbc.ipady = 10
        gbc.gridy = 1
        gbc.gridx = 5
        gbc.insets = Insets(5,2,2,5)
        self.bottomPanel.add(self.start_button, gbc)
    
    def _addIcon(self, icon):
        gbc = GBC()
        if (icon == self.leftIcon):
            gbc.gridx = 0
        elif (icon == self.rightIcon):
            gbc.gridx = 2
        gbc.gridy = 0
        gbc.gridheight = 1
        gbc.gridwidth = 1
        gbc.fill = GBC.NONE
        gbc.weightx = 1
        gbc.insets = Insets(5,2,2,5)
        gbc.anchor = GBC.CENTER
        self.headerPanel.add(icon, gbc)
    
    def _addHeader(self):
        main_Header = JLabel("""<html><center>FiberSight <br>
        A Tool for Muscle Fiber Measurement and Microscope Image Analysis <br> 
        Developed at the Rossi Lab @ UBC </center></html>""")
        
        main_Header.setFont(self.titleFont)
        main_Header.setHorizontalTextPosition(JLabel.RIGHT)
        gbc = GBC()
        gbc.gridx = 1
        gbc.gridheight = 1
        gbc.gridwidth = 1
        gbc.fill = GBC.NONE
        gbc.weightx = 1
        gbc.insets = Insets(5,2,2,5)
        gbc.anchor = GBC.CENTER
        self.headerPanel.add(main_Header, gbc)
    
    def _addInputs(self):
        imageLabel = JLabel("Import Image")
        roiLabel = JLabel("Import Fiber ROIs?")
        textfield_size = 50
        
        self.image_field = JTextField(textfield_size)
        if self.input_image_path is not None:
            self._set_image_path(self.input_image_path, self.image_field, "Image", self.EXPECTED_IMAGE_FORMATS)
        self.image_field.createToolTip()
        self.image_field.setToolTipText('Some known image formats include: ' + self.STRING_IMAGE_FORMATS + '. Others may not work or may not be calibrated.')
        
        self.roi_field = JTextField(textfield_size)
        if self.input_roi_path is not None:
            self._set_roi_path(self.input_roi_path, self.roi_field, "ROI", self.EXPECTED_ROI_FORMATS)

        self.roi_field.editable = False
        self.roi_field.createToolTip()
        self.roi_field.setToolTipText('Supported ROI formats include: ' + self.STRING_ROI_FORMATS)

        self.browse_button_imp = JButton("Browse")
        self.browse_button_imp.addActionListener(self.FileChoiceListener(self, self.image_field, dialog_name="Image selection", field_type="Image",expectedFormats=self.EXPECTED_IMAGE_FORMATS))
                
        self.browse_button_roi = JButton("Browse")
        self.browse_button_roi.addActionListener(self.FileChoiceListener(self, self.roi_field, dialog_name="ROI Selection", field_type="ROI", expectedFormats=self.EXPECTED_ROI_FORMATS))
        self.browse_button_roi.setEnabled(False)
        
        gbc = GBC()
        gbc.gridx = 0
        gbc.ipady = 5
        gbc.ipadx = 5
        gbc.insets = Insets(5,0,0,5)
        gbc.anchor = GBC.WEST
        
        for obj in [imageLabel, self.image_field, self.browse_button_imp]:
            self.middlePanel.add(obj, gbc)
            gbc.gridx += 1
        gbc.gridx = 0
        for obj in [roiLabel, self.roi_field, self.browse_button_roi]:
            self.middlePanel.add(obj, gbc)
            gbc.gridx += 1
    
    def _addImportButtons(self):
        self.importRadioButton = JRadioButton(text = "Import ROIs (Optional)")

        self.noImportRadioButton = JRadioButton(text = "Don't Import ROIs")
        self.noImportRadioButton.setSelected(True)
        
        button_Group = ButtonGroup()
        button_Group.add(self.importRadioButton)
        button_Group.add(self.noImportRadioButton)

        toggle_listener = self.ToggleImport(self.importRadioButton, self.roi_field, self.browse_button_roi)
        self.importRadioButton.addActionListener(toggle_listener)
        self.noImportRadioButton.addActionListener(toggle_listener)
        
        gbc = GBC()
        gbc.gridx = 0
        gbc.anchor = GBC.WEST
        gbc.weightx = 0.5
        for obj in [self.importRadioButton, self.noImportRadioButton]:    
            self.middlePanel.add(obj, gbc)
            gbc.gridx += 1
            
    def _start_FiberSight(self, event):
        if (self.image_field.text != ""):
            print 'Starting FiberSight'
            self.mainFrame.dispose()
        else:
            self.image_field.setBackground(Color.red)
            JOptionPane().showMessageDialog(None, "Please enter an image file")
    
    def get_cellpose_model(self):
        return self.advanced_model.getSelectedItem()
    
    def get_threshold_method(self):
        return self.advanced_ft_method.getSelectedItem()
    
    def get_cellpose_diameter(self):
        return self.advanced_diameter.getValue()

    def get_overwrite_button(self):
        return self.advanced_overwrite_button.isSelected()

    def get_remove_small(self):
        return self.advanced_hybrids.isSelected()
        
    def get_ft_hybrid(self):
        return self.advanced_hybrids.isSelected()

    def get_flat_field(self):
        return self.advanced_ft_correction.isSelected()

    def get_image_path(self):
        return self.image_field.text
        
    def get_roi_button(self):
        return self.importRadioButton.isSelected()
    
    def get_roi_path(self):
        return None if self.roi_field.text == "" else self.roi_field.text

    def get_channel(self, channel_number):
        if 0 <= channel_number < len(self.channels):
            return self.channels[channel_number].getSelectedItem()
        return None

    def _validate_file_path(self, fp_field, field_type, expectedFormats):
        VERY_LIGHT_GREEN = Color(102,255,102)
        YELLOW = Color.yellow
        RED = Color.red
        if (field_type == "ROI"):
            fp_field.setBackground(Color.white)
            if fp_field.text.endswith(expectedFormats):
                fp_field.setBackground(VERY_LIGHT_GREEN)
            else:
                fp_field.setBackground(RED)
                JOptionPane().showMessageDialog(None, "ROI files end in " + ', '.join([x for x in expectedFormats]))
        elif (field_type == "Image"):
            fp_field.setBackground(Color.white)
            if fp_field.text.endswith(expectedFormats):
                fp_field.setBackground(VERY_LIGHT_GREEN)
            else:
                fp_field.setBackground(YELLOW)
    
    class ToggleImport(ActionListener):
        def __init__(self, importOnButton, roi_field, roi_button):
            self.importOnButton = importOnButton
            self.roi_field = roi_field
            self.roi_button = roi_button
    
        def actionPerformed(self, event):
            if self.importOnButton.isSelected():
                # Enable components
                self.roi_field.editable = True
                self.roi_button.setEnabled(True)
            else:
                # Disable components
                self.roi_field.editable = False
                self.roi_field.text = ""
                self.roi_button.setEnabled(False)

    class ToggleOverwrite(ChangeListener, ActionListener):
        def __init__(self, overwrite_button):
            self.overwrite_button = overwrite_button
    
        def stateChanged(self, event):
            event.getSource().getValue()
            self.updateCheckbox()
            
        def actionPerformed(self, event):
            event.getSource().getSelectedItem()
            self.updateCheckbox()
        
        def updateCheckbox(self):
            self.overwrite_button.setSelected(True)

    class FileChoiceListener(ActionListener):
        def __init__(self, gui, fp_field, field_type, dialog_name, expectedFormats):
            self.field_type = field_type
            self.gui = gui
            self.fp_field = fp_field
            self.expectedFormats = expectedFormats
            self.dialog_name = dialog_name
        def actionPerformed(self, event):
            od = OpenDialog(self.dialog_name)
            filename = od.getFileName()
            if filename is None:
                print "User canceled dialog"
            elif self.fp_field.isEditable():
                directory = od.getDirectory()
                fp = directory + filename
                self.fp_field.text = fp
                self.gui._validate_file_path(self.fp_field, self.field_type, self.expectedFormats)
            else:
                pass
    
    class CloseControl(WindowAdapter):
        def __init__(self):
            self.terminated=False
        def windowClosing(self, event):
            self.terminated=True
            event.getSource().dispose() # close the JFrame

if (__name__ == '__main__'):
    fs = FiberSight()
