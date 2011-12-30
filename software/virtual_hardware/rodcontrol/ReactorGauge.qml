import QtQuick 1.0

Item
{
    width: parent.width; height: parent.height
    id: reactorGauge
    
    // Treat these as servos for npw
    property int value: 128
    property int uValue: 1500

    function setPosition(pos)
    {
        value = pos
        valueText.text = value
    }
    function setUSec(pos)
    {
        uValue = pos
        value = uValue-1000*(1000/255)
        valueText.text = uValue + "uS"
    }

    Rectangle
    {
        id: container
        width: parent.width; height: parent.height
        color: "#dddddd"
        border.color: "black"
        border.width: 2


        Column
        {
            width: parent.width; height: parent.height
            // Gauge face, actually a circle (go figure why rectangle is used to make one...)
            Rectangle
            {
                id: face
                anchors.horizontalCenter: parent.horizontalCenter
                width: (parent.width<parent.height?parent.width:parent.height) * 0.85
                height: width
                color: "red"
                border.color: "black"
                border.width: 1
                radius: width/2
                
                // Gauge dial
                Rectangle
                {
                    anchors.horizontalCenter: parent.horizontalCenter
                    id: dial
                    width: 5
                    height: parent.height*0.9/2
                    color: "black"
                    y: face.y+face.height/2-height
                    transform: Rotation
                    {
                        origin.x: dial.width/2
                        origin.y: dial.height
                        angle: 180/255*reactorGauge.value
                    }
                }
            }
            Rectangle
            {
                width: parent.width; height: parent.height*0.15
                color: "transparent"
                Text
                {
                    id: valueText
                    anchors.centerIn: parent
                    font.pixelSize: parent.height/3
                    text: reactorGauge.value
                }
            }
        }
    }
    
    
}
