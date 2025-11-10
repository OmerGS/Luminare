TITLE_STYLE = """
    font-size: 32px;
    font-weight: bold;
    color: white;
    background-color: transparent;
"""

BUTTON_STYLE = """
    QPushButton {
        background-color: #3d3d3d;
        color: white;
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 18px;
    }
    QPushButton:hover {
        background-color: #4c4c4c;
    }
    QPushButton:pressed {
        background-color: #5f5f5f;
    }
"""

PROJECT_BUTTON_STYLE="""
    QPushButton {
        background-color: #000000;
        color : white;
        border-radius: 12px;
        padding: 20px 20px;
        font-size: 18px;
        max-width: 100%;
        max-height: 100%;
        height: 100%;
        width: 100%;
    }
    QPushButton:hover {
        background-color: #1f1f1f;
    }
    QPushButton:pressed {
        background-color: #272727;
    }
"""

LEAVE_BUTTON_STYLE="""
    QPushButton {
        background-color: #8b2222;
        color : white;
        border-radius: 12px;
        padding : 12px 24px;
        font-size: 18px;
    }
    QPushButton:hover {
        background-color : #D10000;
    }
    QPushButton:pressed {
        background-color: #C91E1E;
    }
"""

CREATE_PROJECT_BUTTON_STYLE="""
    QPushButton{
        background: #41e5e5;
        color: white;
        border-radius: 12px;
        padding: 60px 60px;
        font-size: 30px;
    }
    QPushButton:hover {
        background: #2ed1d2;
    }
    QPushButton:pressed {
        background: #1ae5e6;
    }
"""

VOLUME_SLIDER="""
    QSlider{
    }
    QSlider::groove:horizontal{
        border: 1px solid #999999;
        height: 20px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
        margin: 2px 2px;
    }
    QSlider::handle:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
        border: 1px solid #5c5c5c;
        width: 20px;
        margin: -2px 0; 
        border-radius: 3px;
    }
"""

CHANGE_FOLDER_BUTTON="""
    QPushButton {
        background-color: #a0a0a0;
        color : black;
        border-radius: 12px;
        padding : 12px 24px;
        font-size: 16px;
        max-width: 200%;    
    }
    QPushButton:hover {
        background-color : #808080;
    }
    QPushButton:pressed {
        background-color: #666666;
    }

"""

THEME_BUTTON="""
    QPushButton{
        
    }    
"""

# Modifié pour un fond sombre
WINDOW_STYLE = """
    QWidget {
        background-color: #1f1f1f;
    }
    
    QLabel {
        background-color: #1f1f1f;
        color: white; 
        max-height: 50%;
        padding-top: 25px;
    }
"""

