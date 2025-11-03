# app/style.py
TITLE_STYLE = """
    font-size: 32px;
    font-weight: bold;
    color: #ffffff;
    background-color: transparent;
"""

BUTTON_STYLE = """
    QPushButton {
        background-color: #3498db;
        color: white;
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 18px;
    }
    QPushButton:hover {
        background-color: #2980b9;
    }
    QPushButton:pressed {
        background-color: #1f618d;
    }
"""

PROJECT_BUTTON_STYLE="""
    QPushButton {
        background-color: #000000;
        color : white;
        border-radius: 12px;
        padding: 20px 20px;
        font-size: 18px;
    }
    QPushButton:hover {
        background-color: #A9A9A9;
    }
    QPushButton:pressed {
        background-color: #808080;
    }
"""

LEAVE_BUTTON_STYLE="""
    QPushButton {
        background-color: #FF0000;
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
        background: red;
        color: white;
        border-radius: 12px;
        padding: 40px 60px;
        font-size: 30px;
    }
    QPushButton:hover {

    }
    QPushButton:pressed {
    
    }
"""

VOLUME_SLIDER="""
    QSlider::groove:horizontal{
        border: 1px solid #999999;
        height: 8px;
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
        margin: 2px 0;
    }
    QSlider::handle:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
        border: 1px solid #5c5c5c;
        width: 18px;
        margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */
        border-radius: 3px;
    }
"""

THEME_BUTTON="""
    QPushButton{
        
    }    
"""

WINDOW_STYLE = """
    background-color: #2c3e50;
"""
