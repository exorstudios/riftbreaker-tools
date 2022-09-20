// Copyright (C) 2016 Allegorithmic
//
// This software may be modified and distributed under the terms
// of the MIT license.  See the LICENSE file for details.

import QtQuick 2.3
import QtQuick.Layouts 1.2
import QtQuick.Dialogs 1.0
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import Qt.labs.platform 1.0
import AlgWidgets 2.0
import AlgWidgets.Style 1.0

Button {
  id: control
  antialiasing: true
  width: 32
  height: 32
  property bool saving: false
  tooltip: "EXOR Exporter"

  style: ButtonStyle {
    background: Rectangle {
      implicitWidth: control.width
      implicitHeight: control.height
      width: control.width; height: control.height
      color: control.hovered ?
        "#262626" :
        "transparent"
    }
  }

  Image {
    anchors.fill: parent
    anchors.margins: 8
    source: "icons/exor_exporter_button.png"
    fillMode: Image.PreserveAspectFit
    sourceSize.width: control.width
    sourceSize.height: control.height
    mipmap: true
    opacity: control.loading ? 0.5 : 1
  }

  FolderDialog {
    id: exportDirDialog
    title: "Please locate `textures` directory..."
    modality: Qt.ApplicationModal

    onAccepted: {
      var dir = alg.fileIO.urlToLocalFile(currentFolder.toString());
      alg.settings.setValue("exportDir", dir);

      exportDirLabel.text = dir;
    }
  }

  AlgDialog {
    id: convertDialog

    title: "Converting files..."
    width: bar.width
    height: bar.height
    modality: Qt.ApplicationModal

    property int filesCount
    function onConvertDone()
    {
      bar.value += 1;

      filesCount -= 1;
      if ( filesCount <= 0 )
        convertDialog.accept();
    }

    function onConverStart( count )
    {
        filesCount = count;

        bar.from = 0.0;
        bar.to = filesCount;

        convertDialog.show();
    }

    AlgProgressBar {
      id: bar
      height: 30
      width: 200
      indeterminate: false
    }
  }

  function createFolderInfo( layer, depth )
  {
      if ( depth < 2 && layer.layers && layer.layers.length > 0 )
      {
        var data = new Object();
        data.name = layer.name;

        if ( data.name == "default" )
          data.name = "";

        data.depth = depth;
        data.enabled = layer.enabled;
        data.folders = getFoldersFor(layer.layers, depth + 1);
        layer.enabled = false;
        return data;
      }

      return null;
  }

  function getFoldersFor(layers, depth)
  {
      var folders = []
      for ( var layerIdx in layers )
      {
        var layer = layers[layerIdx];
        var data = createFolderInfo( layer, depth );
        if ( data != null )
          folders.push( data );
      }
	  folders.reverse();
      return folders;
  }

  function buildSuffix( folders )
  {
    for ( var idx in folders )
    {
      var folder = folders[idx];
      if ( folder.enabled )
      {
        if ( folder.name != "" )
          return folder.name + "_" + buildSuffix( folder.folders );

        return buildSuffix( folder.folders );
      }
    }

    return "";
  }

  function buildConverterCommand( inputFile, convertToDDS, textureSuffix, materialName, generateMipMaps, sharpenMipMaps, isNormalMap, convertToBC5, hasAlphaChannel )
  {
    var command = "\"" + alg.plugin_root_directory + "texture_converter.exe\""
    command += generateMipMaps ? "" : " --nomipmap";

    var outputFile = inputFile.replace( "_" + materialName + "_temp_", textureSuffix ).toLowerCase();

    var format = "none";
    if ( convertToDDS )
    {
      format = !hasAlphaChannel ? "dxt1c" : "dxt5";
      if ( !isNormalMap && generateMipMaps && sharpenMipMaps ) 
        command += " --sharpen";

      if ( isNormalMap )
      {
        command += " --norm";

        if ( convertToBC5 )
        {
          format = "bc5";
        }
      }

      outputFile = outputFile.replace(".png", ".dds");
    }

    command += " --format=" + format;
    command += " --file=\"" + inputFile + "\""
    command += " --output=\"" + outputFile + "\""
    command += " --remove"

    return command;
  }

  function getSelectedMaterial()
  {
      var structure = alg.mapexport.documentStructure();
      for ( var materialIdx in structure.materials )
      {
        var material = structure.materials[ materialIdx ];
        if ( material.selected )
          return material
      }

      return null;
  }

  function buildTextureSuffix(material, multiMaterial)
  {
    var textureSuffix = "_";
    if ( multiMaterial && material.name !== "default" )
      textureSuffix += material.name + "_";
 
    for ( var stackIdx in material.stacks )
    {
      var stack = material.stacks[ stackIdx ];
      textureSuffix += buildSuffix( getFoldersFor( stack.layers, 0 ) );
    }

    return textureSuffix;
  }

  function convertTextures(maps)
  {
    if (!saving)
      return

    var structure = alg.mapexport.documentStructure();

    var commands = []
    for (var mapName in maps)
    {
      var material = structure.materials.find( function( mat ) { return mat.name == mapName; } );
      var hasOpacityChannel = material.stacks.find( function( stack )
      {
         return stack.channels.find( function( ch ) { return ch.toLowerCase() == "opacity"; } ) != undefined;
      }) != undefined;

      var textureSuffix = buildTextureSuffix(material, structure.materials.length > 1);
      alg.log.info("Texture suffix: " + textureSuffix);

      for (var fileIdx in maps[mapName])
      {
        var filePath = maps[mapName][fileIdx];
        if ( filePath === "" )
          continue;

        alg.log.info("");
        alg.log.info("******************");
        alg.log.info("File: " + filePath);

        if ( exportAsDDS.checked )
        {
          var isNormalMap = !( filePath.indexOf("normal") === -1 );
          var isAlbedo = !( filePath.indexOf("albedo") === -1 );

          var generateMipMaps = ddsGenerateMips.checked;
          var sharpenMipMaps = isAlbedo && ddsSharpenMips.checked;
          var convertToBC5 = isNormalMap && ddsNormalsBC5.checked;
          var hasOpacity = isAlbedo && hasOpacityChannel;

          alg.log.info("Sharpen mipmaps: " + sharpenMipMaps);
          alg.log.info("Is normal map: " + isNormalMap);
          alg.log.info("Has opacity: " + hasOpacityChannel);
          alg.log.info("Convert to BC5: " + convertToBC5);

          var command = buildConverterCommand( filePath, true, textureSuffix, material.name, generateMipMaps, sharpenMipMaps, isNormalMap, convertToBC5, hasOpacity )
          alg.log.info("Command: " + command );

          commands.push( command );
        }
        else
        {
          var command = buildConverterCommand( filePath, false, textureSuffix, material.name )
          alg.log.info("Command: " + command );

          commands.push( command );
        }
      }
    }

    convertDialog.onConverStart(commands.length + 1)

    for ( var idx in commands )
    {
      var command = commands[idx];
      alg.subprocess.start(command, function(e){ convertDialog.onConvertDone(); } );
    }

    convertDialog.onConvertDone();
  }

  function createListModel() {
    var materials = []

    var structure = alg.mapexport.documentStructure();
    for ( var materialIdx in structure.materials )
    {
      var material = structure.materials[ materialIdx ];
      materials.push( material.name )
    }

    return materials;
  }

  AlgDialog {
    id: dialog
    title: "EXOR Exporter"
    defaultButtonText: "Export"

    function reload() {
        exportPacked.checked = alg.project.settings.value("exportPacked", false)
        exportNormal.checked = !exportPacked.checked
        exportAsDDS.checked = alg.project.settings.value("exportAsDDS", false)
        exportAsPNG.checked = !exportAsDDS.checked;
        ddsSharpenMips.checked = alg.project.settings.value("ddsSharpenMips", false)
        ddsGenerateMips.checked = alg.project.settings.value("ddsGenerateMips", true)
        ddsNormalsBC5.checked = alg.project.settings.value("ddsNormalsBC5", true)
        exportDirLabel.text = alg.settings.value("exportDir", "");
    }

    function exportMaps() {
        var exportDir = alg.settings.value("exportDir", "")

        var preset = "EXOR Exporter - Normal"
        if ( exportPacked.checked ) {
          preset = "EXOR Exporter - Packed"
        }

        var prefix = "substanceSource/"

        var path = alg.project.url();
        path = path.substring( path.indexOf(prefix) + prefix.length )
        path = exportDir + "/textures/" + path.substring( 0, path.lastIndexOf("/") )

        control.saving = true

        var structure = alg.mapexport.documentStructure();
        for ( var matIdx in structure.materials )
        {
          var material = structure.materials[ matIdx ];
          if ( !alg.project.settings.value(material.name + ".export", true))
            continue;

          var index = alg.project.settings.value(material.name + ".index", -1)
          if ( index === -1 )
          {
            var resolution = alg.mapexport.textureSetResolution(material.name);
            index = ( 4096 / resolution[ 0 ] ) - 1;
          }

          alg.log.info("Resolution index: " + index );

          var size = Math.pow( 2, 12 - index );

          alg.log.info("Resolution: " + size + " x " + size)

          convertDialog.show();
          var maps = alg.mapexport.exportDocumentMaps( preset, path, "png", { resolution: [size,size] }, [material.name] );
          convertDialog.accept();

          convertTextures( maps );
        }

        control.saving = false
    }

    onAccepted: {
        if ( control.saving )
          return;
        alg.project.settings.setValue("exportPacked", exportPacked.checked)
        alg.project.settings.setValue("exportAsDDS", exportAsDDS.checked)
        alg.project.settings.setValue("ddsSharpenMips", ddsSharpenMips.checked)
        alg.project.settings.setValue("ddsGenerateMips", ddsGenerateMips.checked)
        alg.project.settings.setValue("ddsNormalsBC5", ddsNormalsBC5.checked)

        var exportDir = alg.settings.value("exportDir", "")
        if ( exportDir === "" || !alg.fileIO.exists(exportDir) )
        {
          exportDirDialog.open()
        }

        dialog.exportMaps()
    }

    width: 350
    height: layout.height + 50

    Flow {
      id: layout
      RowLayout {
        ColumnLayout {
          AlgGroupWidget {
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.fillWidth: true

            toggled: true
            text: "Export mode"

            RowLayout {
              Layout.leftMargin: 10
              Layout.rightMargin: 10

              AlgCheckBox {
                Layout.preferredWidth: 80

                id: exportNormal
                text: "Normal"

                onCheckedChanged: {
                  exportPacked.checked = !checked;
                }
              }

              AlgCheckBox {
                Layout.preferredWidth: 80

                id: exportPacked
                text: "Packed"

                onCheckedChanged: {
                  exportNormal.checked = !checked;
                }
              }
            }
          }

          AlgGroupWidget {
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.fillWidth: true

            toggled: true
            text: "Materials"

            RowLayout {
              Layout.leftMargin: 10
              Layout.rightMargin: 10
              Layout.fillWidth: true

              RowLayout {
                Layout.fillWidth: true

                ListModel {
                  id: materialsModel
                }

                ColumnLayout {
                  Repeater {
                    model: materialsModel

                    delegate: ColumnLayout {
                      AlgCheckBox {
                        Component.onCompleted: {
                          var structure = alg.mapexport.documentStructure();
                          var material = structure.materials[ index ];

                          text = material.name;
                          checked = alg.project.settings.value( material.name + ".export", true )
                        }

                        onCheckedChanged: {
                            var structure = alg.mapexport.documentStructure();
                            var material = structure.materials[ index ];
                            alg.project.settings.setValue( material.name + ".export", checked )
                        }
                      }
                    }
                  }
                }

                ColumnLayout {
                  Repeater {
                    model: materialsModel

                    delegate: ColumnLayout {
                      AlgComboBox {
                        model: [ "4096x4096", "2048x2048", "1024x1024", "512x512", "256x256", "128x128" ]
                        Component.onCompleted: {
                          var structure = alg.mapexport.documentStructure();
                          var material = structure.materials[ index ];

                          currentIndex = alg.project.settings.value(material.name + ".index", -1);

                          var resolution = alg.mapexport.textureSetResolution(material.name);
                          if ( currentIndex === -1 )
                            currentIndex = ( 4096 / resolution[ 0 ] ) - 1;

                          alg.project.settings.setValue( material.name + ".index", currentIndex )
                        }

                        function changeIndex(idx) {
                          var structure = alg.mapexport.documentStructure();
                          var material = structure.materials[ index ];

                          alg.project.settings.setValue( material.name + ".index", idx )
                        }

                        onActivated: {
                          changeIndex( index );
                        }
                      }
                    }
                  }
                }
              }
            }
          }

          AlgGroupWidget {
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.fillWidth: true

            toggled: true
            text: "Output format"

            RowLayout {
              ColumnLayout {
                Layout.leftMargin: 10
                Layout.rightMargin: 10
                Layout.preferredWidth: 40

                AlgCheckBox {
                  id: exportAsPNG
                  text: "PNG"

                  onCheckedChanged: {
                    exportAsDDS.checked = !checked;
                  }
                }

                AlgCheckBox {
                  id: exportAsDDS
                  text: "DDS"
                  onCheckedChanged: {
                    exportAsPNG.checked = !checked;
                  }
                }
              }

              ColumnLayout {
                Layout.leftMargin: 0

                AlgCheckBox {
                  id: ddsGenerateMips
                  enabled: exportAsDDS.checked
                  text: "Generate mipmaps"
                }

                AlgCheckBox {
                  id: ddsSharpenMips
                  enabled: exportAsDDS.checked
                  text: "Sharpen albedo mipmaps"
                }

                AlgCheckBox {
                  id: ddsNormalsBC5
                  enabled: exportAsDDS.checked
                  text: "Use BC5 for normal map"
                }
              }
            }
          }

          AlgGroupWidget {
            Layout.topMargin: 10
            Layout.leftMargin: 10
            Layout.rightMargin: 10
            Layout.fillWidth: true

            toggled: true
            text: "Export directory"

            ColumnLayout {
              Layout.leftMargin: 10
              Layout.rightMargin: 10

              AlgLabel
              {
                id: exportDirLabel
                text: ""
              }

              AlgButton {
                id: changeExportDirButton
                text: "Change"
                Layout.preferredWidth: 60

                onClicked:
                {
                  var exportDir = alg.settings.value("exportDir", "")

                  exportDirDialog.currentFolder = exportDir;
                  exportDirDialog.open()
                }
              }
            }
          }
        }
      }
    }
  }

  onClicked: {
    materialsModel.clear();

    var materials = createListModel();
    for ( var idx in materials )
    {
      materialsModel.append( { name: materials[idx] } )
    }

    dialog.open();
  }
}
