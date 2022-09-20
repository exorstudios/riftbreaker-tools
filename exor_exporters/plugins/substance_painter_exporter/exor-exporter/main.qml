import QtQuick 2.2
import Painter 1.0

PainterPlugin {
    // starts a timer that will trigger the 'onTick' callback at regular interval
    tickIntervalMS: -1 // -1 mean disabled (default value)

    // starts a JSON server on the given port:
    // you send javascript that will be evaluated and you get the result in JSON format
    jsonServerPort: -1 // -1 mean disabled (default value)

    QtObject {
        id: internal

        property QtObject button
    }

    Component.onCompleted: {
        internal.button = alg.ui.addWidgetToPluginToolBar("exporter.qml");
    }
}