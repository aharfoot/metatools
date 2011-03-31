# -*- coding: utf-8 -*-

#******************************************************************************
#
# Metatools
# ---------------------------------------------------------
# Metadata browser/editor
#
# Copyright (C) 2011 NextGIS (info@nextgis.ru)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/copyleft/gpl.html>. You can also obtain it by writing
# to the Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.
#
#******************************************************************************

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from PyQt4.QtXmlPatterns import *

from qgis.core import *
from qgis.gui import *

import sys, os, codecs, shutil

from license_editor_dialog import LicenseEditorDialog
from license_template_manager import LicenseTemplateManager

from workflow_editor_dialog import WorkflowEditorDialog
from workflow_template_manager import WorkflowTemplateManager

from organization_editor_dialog import OrganizationEditorDialog
from organization_template_manager import OrganizationTemplateManager

from ui_apply_templates import Ui_ApplyTemplatesDialog

from standard import MetaInfoStandard
import utils

currentPath = os.path.abspath( os.path.dirname( __file__ ) )

class ApplyTemplatesDialog( QDialog, Ui_ApplyTemplatesDialog ):
  def __init__( self, iface ):
    QDialog.__init__( self )
    self.setupUi( self )
    self.iface = iface

    self.layers = []

    self.licenseTemplateManager = LicenseTemplateManager( currentPath )
    self.workflowTemplateManager = WorkflowTemplateManager( currentPath )
    path = os.path.join( currentPath, "templates/institutions.xml" )
    self.orgsTemplateManager = OrganizationTemplateManager( path )

    self.btnApply = QPushButton( self.tr( "Apply" ) )
    self.btnClose = QPushButton( self.tr( "Close" ) )
    self.buttonBox.clear()
    self.buttonBox.addButton( self.btnApply, QDialogButtonBox.AcceptRole )
    self.buttonBox.addButton( self.btnClose, QDialogButtonBox.RejectRole )

    QObject.connect( self.chkExternalFiles, SIGNAL( "stateChanged( int )" ), self.toggleExternalFiles )
    QObject.connect( self.lstLayers, SIGNAL( "itemSelectionChanged()" ), self.updateLayerList )

    QObject.connect( self.btnSelectDataFiles, SIGNAL( "clicked()" ), self.selectExternalFiles )
    QObject.connect( self.btnManageLicenses, SIGNAL( "clicked()" ), self.manageLicenses )
    QObject.connect( self.btnManageOrgs, SIGNAL( "clicked()" ), self.manageOrganizations )
    QObject.connect( self.btnManageWorkflows, SIGNAL( "clicked()" ), self.manageWorkflows )
    QObject.connect( self.btnSelectLogFile, SIGNAL( "clicked()" ), self.selectLogFile )

    QObject.disconnect( self.buttonBox, SIGNAL( "accepted()" ), self.accept )
    QObject.connect( self.btnApply, SIGNAL( "clicked()" ), self.applyTemplates )

    self.manageGui()

  def manageGui( self ):
    # populate layer list
    self.lstLayers.addItems( utils.getRasterLayerNames() )

    # populate comboboxes with templates
    self.updateLicenseTemplatesList()
    self.updateWorkflowTemplatesList()
    self.updateOrgsTemplatesList()

    # disable Apply button when there are no layers
    if len( self.layers ) == 0:
      self.btnApply.setEnabled( False )

  def toggleExternalFiles( self ):
    self.btnApply.setEnabled( False )
    if self.chkExternalFiles.isChecked():
      #self.lstLayers.setEnabled( False )
      self.lstLayers.clear()
      self.lstLayers.setSelectionMode( QAbstractItemView.NoSelection )
      self.btnSelectDataFiles.setEnabled( True )
      self.layers = []
    else:
      #self.lstLayers.setEnabled( True )
      self.lstLayers.clear()
      self.lstLayers.setSelectionMode( QAbstractItemView.ExtendedSelection )
      self.lstLayers.addItems( utils.getRasterLayerNames() )
      self.btnSelectDataFiles.setEnabled( False )
      self.updateLayerList()

  def selectExternalFiles( self ):
    files = QFileDialog.getOpenFileNames( self, self.tr( "Select files" ), ".", self.tr( "All files (*.*)" ) )

    if files.isEmpty():
      return

    self.layers = files
    self.lstLayers.addItems( files )
    self.btnApply.setEnabled( True )

  def manageLicenses( self ):
    oldValue = self.cmbLicense.currentText()

    dlg = LicenseEditorDialog()
    dlg.exec_()

    self.updateLicenseTemplatesList()

    # try to restore previous value
    index = self.cmbLicense.findText( oldValue )
    if index != -1:
      self.cmbLicense.setCurrentIndex( index )

  def manageWorkflows( self ):
    oldValue = self.cmbWorkflow.currentText()

    dlg = WorkflowEditorDialog()
    dlg.exec_()

    self.updateWorkflowTemplatesList()

    # try to restore previous value
    index = self.cmbWorkflow.findText( oldValue )
    if index != -1:
      self.cmbWorkflow.setCurrentIndex( index )

  def manageOrganizations( self ):
    oldValue = self.cmbOrganization.currentText()

    dlg = OrganizationEditorDialog()
    dlg.exec_()

    self.orgsTemplateManager.reloadTemplates()
    self.updateOrgsTemplatesList()

    # try to restore previous value
    index = self.cmbOrganization.findText( oldValue )
    if index != -1:
      self.cmbOrganization.setCurrentIndex( index )

  def selectLogFile( self ):
    # TODO: need to save last dir and set it in dialog
    logFileName = QFileDialog.getOpenFileName( self, self.tr( "Select log file" ), ".", self.tr( "Text files (*.txt);;Log files (*.log);;All files (*)" ), None, QFileDialog.ReadOnly )
    self.leLogFile.setText( logFileName )
    self.leLogFile.setToolTip( logFileName )

  def updateLicenseTemplatesList( self ):
    self.cmbLicense.clear()
    self.cmbLicense.addItems( self.licenseTemplateManager.getTemplateList() )

  def updateWorkflowTemplatesList( self ):
    self.cmbWorkflow.clear()
    self.cmbWorkflow.addItems( self.workflowTemplateManager.getTemplateList() )

  def updateOrgsTemplatesList( self ):
    self.cmbOrganization.clear()
    self.cmbOrganization.addItems( self.orgsTemplateManager.tempalateNames() )

  def updateLayerList( self ):
    self.layers = []
    selection = self.lstLayers.selectedItems()
    for item in selection:
      layer = utils.getRasterLayerByName( item.text() )
      self.layers.append( layer.source() )

    if len( self.layers ) != 0:
      self.btnApply.setEnabled( True )

  def applyTemplates( self ):
    # TODO: check if there are some templates selected

    # get profile from settings
    settings = QSettings( "NextGIS", "metatools" )
    profile = settings.value( "iso19115/defaultProfile", QVariant( "" ) ).toString()
    if profile.isEmpty():
      QMessageBox.warning( self, self.tr( "No profile" ), self.tr( "No profile selected. Please set default profile in plugin settings" ) )
      return

    profilePath = str( QDir.toNativeSeparators( os.path.join( currentPath, "xml_profiles", str( profile ) ) ) )

    try:
      for layer in self.layers:
        # get metadata file path
        metaFilePath = utils.mdPathFromLayerPath( layer )

        # check if metadata file exists and create it if necessary
        if not os.path.exists( metaFilePath ):
          try:
            shutil.copyfile( profilePath, metaFilePath )
          except:
            QMessageBox.warning( self, self.tr( "Metatools" ), self.tr( "Metadata file can't be created: ") + str( sys.exc_info()[ 1 ] ) )
            continue

        # check metadata standard
        standard = MetaInfoStandard.tryDetermineStandard( metaFilePath )
        if standard != MetaInfoStandard.ISO19115:
          QMessageBox.warning( self, self.tr( "Metatools" ),
                               self.tr( "File %1 has unsupported metadata standard! Only ISO19115 supported now!" )
                               .arg( layer ) )
          continue

        # load metadata file
        file = QFile( metaFilePath )
        metaXML = QDomDocument()
        metaXML.setContent( file )

        # apply templates (BAD version - change to applier with standard)
        self.applyInstitutionTemplate( metaXML )
        self.applyLicenseTemplate( metaXML )
        self.applyWorkflowTemplate( metaXML )
        self.applyLogFile( metaXML )

        # save metadata file (hmm.. why not QFile?)
        metafile = codecs.open( metaFilePath, "w", encoding="utf-8" )
        metafile.write( unicode( metaXML.toString().toUtf8(), "utf-8" ) )
        metafile.close()

      QMessageBox.information( self, self.tr( "Metatools" ), self.tr( "Templates successfully applied!" ) )
      # clear selection and disable Apply button
      self.lstLayers.clearSelection()
      self.layers = []
      self.btnApply.setEnabled( False )
    except:
      QMessageBox.warning( self, self.tr( "Metatools" ), self.tr( "Templates can't be applied: " ) + str( sys.exc_info()[ 1 ] ) )

  # ----------- Appliers -----------
  
  def applyInstitutionTemplate( self, metaXML ):
    # TODO: make more safe
    if self.cmbOrganization.currentIndex() == -1:
      return
    
    template = self.orgsTemplateManager.organizations[ self.cmbOrganization.currentText() ]
    
    root = metaXML.documentElement()
    mdContact = self.getOrCreateChild( root, "contact" )
    mdResponsibleParty = self.getOrCreateChild( mdContact, "CI_ResponsibleParty" )
    
    # individualName
    mdIndividualName = self.getOrCreateChild( mdResponsibleParty, "individualName" )
    mdCharStringElement = self.getOrCreateChild( mdIndividualName, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.person )
    
    # organisationName
    mdOrganisationName = self.getOrCreateChild( mdResponsibleParty, "organisationName" )
    mdCharStringElement = self.getOrCreateChild( mdOrganisationName, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.name )
    
    # positionName
    mdPositionName = self.getOrCreateChild( mdResponsibleParty, "positionName" )
    mdCharStringElement = self.getOrCreateChild( mdPositionName, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.position )
    
    # go deeper... fill contactInfo
    mdContactInfo = self.getOrCreateChild( mdResponsibleParty, "contactInfo" )
    mdCIContact = self.getOrCreateChild( mdContactInfo, "CI_Contact" )
    
    # hours of service
    mdHours = self.getOrCreateChild( mdCIContact, "hoursOfService" )
    mdCharStringElement = self.getOrCreateChild( mdHours, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.hours )
    
    # fill phones
    mdPhone = self.getOrCreateChild( mdCIContact, "phone" )
    mdCIPhone = self.getOrCreateChild( mdPhone, "CI_Telephone" )
    
    mdVoice = self.getOrCreateChild( mdCIPhone, "voice" )
    mdCharStringElement = self.getOrCreateChild( mdVoice, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.phone )
    
    mdFacsimile = self.getOrCreateChild( mdCIPhone, "facsimile" )
    mdCharStringElement = self.getOrCreateChild( mdFacsimile, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.phone )
    
    # fill address
    mdAddress = self.getOrCreateChild( mdCIContact, "address" )
    mdCIAddress = self.getOrCreateChild( mdAddress, "CI_Address" )
    
    # deliveryPoint
    mdDeliveryPoint = self.getOrCreateChild( mdCIAddress, "deliveryPoint" )
    mdCharStringElement = self.getOrCreateChild( mdDeliveryPoint, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.deliveryPoint )
    
    # city
    mdCity = self.getOrCreateChild( mdCIAddress, "city" )
    mdCharStringElement = self.getOrCreateChild( mdCity, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.city )
    
    # administrativeArea
    mdAdminArea = self.getOrCreateChild( mdCIAddress, "administrativeArea" )
    mdCharStringElement = self.getOrCreateChild( mdAdminArea, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.adminArea )
    
    # postalCode
    mdPostalCode = self.getOrCreateChild( mdCIAddress, "postalCode" )
    mdCharStringElement = self.getOrCreateChild( mdPostalCode, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.postalCode )
    
    # country
    mdCountry = self.getOrCreateChild( mdCIAddress, "country" )
    mdCharStringElement = self.getOrCreateChild( mdCountry, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.country )
    
    # email
    mdEmail = self.getOrCreateChild( mdCIAddress, "electronicMailAddress" )
    mdCharStringElement = self.getOrCreateChild( mdEmail, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( template.email )

  def applyLicenseTemplate( self, metaXML ):
    # TODO: make more safe
    if self.cmbLicense.currentIndex() == -1:
      return

    licenseTemplate = self.licenseTemplateManager.loadTemplate( self.cmbLicense.currentText() )

    root = metaXML.documentElement()

    mdIdentificationInfo = self.getOrCreateChild( root, "identificationInfo" )
    mdDataIdentification = self.getOrCreateChild( mdIdentificationInfo, "MD_DataIdentification" )

    mdResourceConstraints = self.getOrIsertAfterChild( mdDataIdentification, "resourceConstraints", [ "resourceSpecificUsage", "descriptiveKeywords", "resourceFormat", "graphicOverview", "resourceMaintenance", "pointOfContact", "status", "credit", "purpose", "abstract" ] )
    mdLegalConstraintsElement = self.getOrCreateChild( mdResourceConstraints, "MD_LegalConstraints" )

    # useLimitation
    mdUseLimitationElement = self.getOrCreateChild( mdLegalConstraintsElement, "useLimitation" )
    mdCharStringElement = self.getOrCreateChild( mdUseLimitationElement, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( licenseTemplate.stringRepresentation() )

    # useConstraints
    mdUseConstraintsElement = self.getOrCreateChild( mdLegalConstraintsElement, "useConstraints" )
    mdRestrictionCodeElement = self.getOrCreateChild( mdUseConstraintsElement, "MD_RestrictionCode" )

    mdRestrictionCodeElement.setAttribute( "codeList", "http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/Codelist/ML_gmxCodelists.xml#MD_RestrictionCode" )
    mdRestrictionCodeElement.setAttribute( "codeListValue", "license" )

    textNode = self.getOrCreateTextChild( mdRestrictionCodeElement )
    textNode.setNodeValue( "license" )

  def applyWorkflowTemplate( self, metaXML ):
    # TODO: make more safe
    if self.cmbWorkflow.currentIndex() == -1:
        return

    workflowTemplate = self.workflowTemplateManager.loadTemplate( self.cmbWorkflow.currentText() )

    root = metaXML.documentElement()

    mdDataQualityInfo = self.getOrIsertAfterChild( root, "dataQualityInfo", [ "distributionInfo", "contentInfo", "identificationInfo" ] )
    mdDQData = self.getOrCreateChild( mdDataQualityInfo, "DQ_DataQuality" )

    # check requirements (not need for workflow)
    if mdDQData.firstChildElement( "scope" ).isNull():
      mdScope = self.getOrIsertTopChild( mdDQData, "scope" )
      mdDQScope = self.getOrCreateChild( mdScope, "DQ_Scope" )
      mdLevel = self.getOrIsertTopChild( mdDQScope, "level" )
      mdScopeCode = self.getOrCreateChild( mdLevel, "MD_ScopeCode" )

      mdScopeCode.setAttribute( "codeList", "http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/Codelist/ML_gmxCodelists.xml#MD_ScopeCode" )
      mdScopeCode.setAttribute( "codeListValue", "dataset" )

      textNode = self.getOrCreateTextChild( mdScopeCode )
      textNode.setNodeValue( "dataset" )

    mdLineage = self.getOrCreateChild( mdDQData, "lineage" )
    mdLiLineage = self.getOrCreateChild( mdLineage, "LI_Lineage" )
    mdStatement = self.getOrIsertTopChild( mdLiLineage, "statement" )

    mdCharStringElement = self.getOrCreateChild( mdStatement, "gco:CharacterString" )

    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( workflowTemplate.stringRepresentation() )

  def applyLogFile( self, metaXML ):
    # TODO: make more safe
    if self.leLogFile.text().isEmpty():
      return

    logFile = codecs.open( self.leLogFile.text(), "r", encoding="utf-8" )
    logFileContent = logFile.read()
    logFile.close()

    root = metaXML.documentElement()

    mdDataQualityInfo = self.getOrIsertAfterChild( root, "dataQualityInfo", [ "distributionInfo", "contentInfo", "identificationInfo" ] )
    mdDQData = self.getOrCreateChild( mdDataQualityInfo, "DQ_DataQuality" )

    # check requirements (not need for log file)
    if mdDQData.firstChildElement( "scope" ).isNull():
      mdScope = self.getOrIsertTopChild( mdDQData, "scope" )
      mdDQScope = self.getOrCreateChild( mdScope, "DQ_Scope" )
      mdLevel = self.getOrIsertTopChild( mdDQScope, "level" )
      mdScopeCode = self.getOrCreateChild( mdLevel, "MD_ScopeCode" )

      mdScopeCode.setAttribute( "codeList", "http://standards.iso.org/ittf/PubliclyAvailableStandards/ISO_19139_Schemas/resources/Codelist/ML_gmxCodelists.xml#MD_ScopeCode" )
      mdScopeCode.setAttribute( "codeListValue", "dataset" )
      textNode = self.getOrCreateTextChild( mdScopeCode )
      textNode.setNodeValue( "dataset" )

    mdLineage = self.getOrCreateChild( mdDQData, "lineage" )
    mdLiLineage = self.getOrCreateChild( mdLineage, "LI_Lineage" )

    mdProcessStep = self.getOrCreateChild( mdLiLineage, "processStep" )
    mdLIProcessStep = self.getOrCreateChild( mdProcessStep, "LI_ProcessStep" )
    mdDescription = self.getOrIsertTopChild( mdLIProcessStep, "description" )
    mdCharStringElement = self.getOrCreateChild( mdDescription, "gco:CharacterString" )
    textNode = self.getOrCreateTextChild( mdCharStringElement )
    textNode.setNodeValue( logFileContent )

  def applyOrganisationTemplate( self, metaXML ):
    pass

  # ----------- XML Helpers -----------

  def getOrCreateChild( self, element, childName ):
    child = element.firstChildElement( childName )
    if child.isNull():
      child = element.ownerDocument().createElement( childName )
      element.appendChild( child )
    return child

  def getOrIsertAfterChild( self, element, childName, prevChildsName ):
    child = element.firstChildElement( childName )
    if child.isNull():
      child = element.ownerDocument().createElement( childName )

      # search previous element
      for elementName in prevChildsName:
        prevElement = element.firstChildElement( elementName )
        if not prevElement.isNull():
          element.insertAfter( child, prevElement )
          return child

      # if not found, simply append
      element.appendChild( child )
    return child

  def getOrIsertTopChild( self, element, childName ):
    child = element.firstChildElement( childName )
    if child.isNull():
      child = element.ownerDocument().createElement( childName )
      element.insertBefore( child, QDomNode() )
    return child

  def getOrCreateTextChild( self, element ):
    childTextNode = element.childNodes().at( 0 ) # bad! need full search and type checker
    if childTextNode.isNull():
      childTextNode = element.ownerDocument().createTextNode( "" )
      element.appendChild( childTextNode )
    return childTextNode
