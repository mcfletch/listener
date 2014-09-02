import QtQuick 1.0
/* PySide's QtQuick doesn't include the QtQuick.Layouts module?! */

Rectangle {
    signal correctionMade;
    anchors.fill: parent;
    
    color: "black";

    function setText(text) {
        correction.text = text
    }

    Text {
        id: correction
        anchors.centerIn: parent; color: "white"
    }

    MouseArea {
        anchors.fill: parent
        onClicked: correctionMade(correction.text)
    }
}
