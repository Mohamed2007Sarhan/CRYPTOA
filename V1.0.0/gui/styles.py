"""
Styles — نظام التصميم الموحد للواجهة
"""

DARK_THEME = """
/* ═══════════════════════════════════════════════════════════
   AI CRYPTO TRADING PLATFORM — DARK THEME
   ═══════════════════════════════════════════════════════════ */

QWidget {
    background-color: #0D1117;
    color: #F0F6FC;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #0D1117;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: #161B22;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363D;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #00FFB2;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #161B22;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #30363D;
    border-radius: 4px;
}

/* ── Cards ── */
.card {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 16px;
}

/* ── Labels ── */
QLabel {
    color: #F0F6FC;
    font-size: 13px;
}
QLabel.title {
    font-size: 22px;
    font-weight: bold;
    color: #00FFB2;
}
QLabel.subtitle {
    font-size: 14px;
    color: #8B949E;
}
QLabel.section-title {
    font-size: 15px;
    font-weight: bold;
    color: #F0F6FC;
    border-bottom: 2px solid #00FFB2;
    padding-bottom: 4px;
}
QLabel.buy {
    color: #22C55E;
    font-weight: bold;
    font-size: 18px;
}
QLabel.sell {
    color: #EF4444;
    font-weight: bold;
    font-size: 18px;
}
QLabel.hold {
    color: #F59E0B;
    font-weight: bold;
    font-size: 18px;
}

/* ── Buttons ── */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00FFB2, stop:1 #00D4FF);
    color: #0D1117;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    min-height: 38px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00FFD4, stop:1 #00EAFF);
}
QPushButton:pressed {
    background: #00CC8F;
}
QPushButton:disabled {
    background: #30363D;
    color: #8B949E;
}
QPushButton.danger {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #EF4444, stop:1 #F97316);
    color: white;
}
QPushButton.danger:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #FF5555, stop:1 #FF8800);
}
QPushButton.secondary {
    background: #21262D;
    color: #F0F6FC;
    border: 1px solid #30363D;
}
QPushButton.secondary:hover {
    background: #30363D;
    border: 1px solid #00FFB2;
}
QPushButton.success {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #22C55E, stop:1 #16A34A);
    color: white;
}

/* ── Inputs ── */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #21262D;
    color: #F0F6FC;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #00FFB2;
    selection-color: #0D1117;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #00FFB2;
    background-color: #1C2128;
}

/* ── ComboBox ── */
QComboBox {
    background-color: #21262D;
    color: #F0F6FC;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    min-width: 120px;
}
QComboBox:focus, QComboBox:hover {
    border: 1px solid #00FFB2;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #21262D;
    color: #F0F6FC;
    border: 1px solid #30363D;
    selection-background-color: #00FFB2;
    selection-color: #0D1117;
    border-radius: 4px;
}

/* ── SpinBox ── */
QDoubleSpinBox, QSpinBox {
    background-color: #21262D;
    color: #F0F6FC;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
}
QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #00FFB2;
}

/* ── Slider ── */
QSlider::groove:horizontal {
    background: #30363D;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #00FFB2;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #00FFB2;
    border-radius: 3px;
}

/* ── CheckBox ── */
QCheckBox {
    spacing: 8px;
    color: #F0F6FC;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #30363D;
    background: #21262D;
}
QCheckBox::indicator:checked {
    background: #00FFB2;
    border: 2px solid #00FFB2;
}

/* ── Tabs ── */
QTabWidget::pane {
    border: 1px solid #30363D;
    border-radius: 8px;
    background: #161B22;
    margin-top: -1px;
}
QTabBar::tab {
    background: #21262D;
    color: #8B949E;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 8px 18px;
    margin-right: 4px;
    font-size: 13px;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00FFB2, stop:1 #00D4FF);
    color: #0D1117;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background: #30363D;
    color: #F0F6FC;
}

/* ── Tables ── */
QTableWidget {
    background-color: #161B22;
    border: none;
    gridline-color: #21262D;
    border-radius: 8px;
    alternate-background-color: #1C2128;
}
QTableWidget::item {
    padding: 6px 10px;
    border: none;
    color: #F0F6FC;
}
QTableWidget::item:selected {
    background-color: #00FFB2;
    color: #0D1117;
}
QHeaderView::section {
    background-color: #21262D;
    color: #8B949E;
    border: none;
    padding: 8px 10px;
    font-weight: bold;
    font-size: 12px;
    border-bottom: 2px solid #30363D;
}

/* ── Progress Bar ── */
QProgressBar {
    background: #21262D;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: #0D1117;
    font-weight: bold;
    height: 18px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00FFB2, stop:1 #00D4FF);
    border-radius: 6px;
}

/* ── GroupBox ── */
QGroupBox {
    border: 1px solid #30363D;
    border-radius: 10px;
    font-weight: bold;
    font-size: 13px;
    color: #F0F6FC;
    margin-top: 8px;
    padding-top: 12px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: #00FFB2;
    font-size: 12px;
}

/* ── Splitter ── */
QSplitter::handle {
    background: #30363D;
}
QSplitter::handle:horizontal {
    width: 2px;
}
QSplitter::handle:vertical {
    height: 2px;
}

/* ── ToolTip ── */
QToolTip {
    background: #21262D;
    color: #F0F6FC;
    border: 1px solid #00FFB2;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ── Status Bar ── */
QStatusBar {
    background: #161B22;
    color: #8B949E;
    border-top: 1px solid #30363D;
    font-size: 12px;
}
"""
