import sys
import os
import hashlib
import base58
import ecdsa
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette

# ═══════════════════════════════════════
# SCIEZKA DO PLIKU (dziala w .app i normalnie)
# ═══════════════════════════════════════

def get_resource_path(filename):
    """Zwraca sciezke do pliku (dziala w zbudowanej .app i normalnie)"""
    if getattr(sys, 'frozen', False):
        # Zbudowana aplikacja PyInstaller
        base_path = sys._MEIPASS
    else:
        # Normalne uruchomienie python3 menu.py
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, filename)

# ═══════════════════════════════════════
# WCZYTAJ ADRESY Z PLIKU
# ═══════════════════════════════════════

def load_targets(filename="adresy.txt"):
    """Wczytuje adresy z pliku i zwraca slownik TARGETS"""
    targets = {}
    filepath = get_resource_path(filename)
    
    if not os.path.exists(filepath):
        return {"1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa": "Satoshi (fallback)"}
    
    with open(filepath, "r") as f:
        for i, line in enumerate(f, 1):
            addr = line.strip()
            if addr:
                targets[addr] = f"Target #{i}"
    
    return targets

TARGETS = load_targets("adresy.txt")

UPDATE_CO = 100_000

# ═══════════════════════════════════════
# CRYPTO
# ═══════════════════════════════════════

def private_to_address(private_key_bytes):
    sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    public_key = b'\x04' + vk.to_string()
    sha = hashlib.sha256(public_key).digest()
    ripemd = hashlib.new('ripemd160', sha).digest()
    prefix = b'\x00' + ripemd
    checksum = hashlib.sha256(hashlib.sha256(prefix).digest()).digest()[:4]
    return base58.b58encode(prefix + checksum).decode()

# ═══════════════════════════════════════
# WORKER THREAD
# ═══════════════════════════════════════

class BruteForceWorker(QThread):
    progress = pyqtSignal(int, str, float)
    found = pyqtSignal(str, str, str, int)
    status = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
    
    def run(self):
        self.running = True
        start = time.time()
        proba = 0
        
        while self.running:
            private_key = os.urandom(32)
            adres = private_to_address(private_key)
            proba += 1
            
            if adres in TARGETS:
                name = TARGETS[adres]
                self.found.emit(name, adres, private_key.hex(), proba)
            
            if proba % UPDATE_CO == 0:
                elapsed = time.time() - start
                speed = proba / elapsed if elapsed > 0 else 0
                self.progress.emit(proba, adres, speed)
        
        self.status.emit("Stopped")
    
    def stop(self):
        self.running = False

# ═══════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BTC Key")
        self.setMinimumSize(850, 500)
        self.resize(850, 500)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QWidget { 
                background-color: #f5f5f5; 
                color: #333; 
            }
            QLabel { background: transparent; }
            QPushButton {
                background-color: #fff; color: #9c9c9c; border: 1px solid #e5e5e5;
                border-radius: 10px; padding: 10px 15px; font-weight: 500; font-size: 13px;
            }
            QPushButton:hover { background-color: #f0f0f0; border-color: #d5d5d5; }
            QPushButton:disabled { background-color: #f9f9f9; color: #bbb; border-color: #eee; }
            QTextEdit {
                background-color: #fff; color: #666; border: 1px solid #eee;
                border-radius: 12px; padding: 12px;
                font-size: 11px; line-height: 1.6;
            }
            QTableWidget {
                background-color: #fff; border: 1px solid #eee; border-radius: 12px;
                gridline-color: #f0f0f0;
                font-size: 10px; color: #555;
            }
            QTableWidget::item { padding: 4px 8px; border: none; }
            QHeaderView::section {
                background-color: #fafafa; color: #999; border: none;
                border-bottom: 1px solid #eee; border-top-left-radius: 12px; border-top-right-radius: 12px; padding: 6px 8px; font-weight: 600;
                font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;
            }
            QScrollBar:vertical {
                background: transparent; width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #ddd; border-radius: 3px; min-height: 20px;
            }
        """)
        
        self.worker = None
        self.total_probes = 0
        self.found_count = 0
        self.setup_ui()
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(10)
        
        # Stats row
        stats_layout = QHBoxLayout()
        
        self.targets_label = QLabel(f"Targets: {len(TARGETS):,}")
        self.targets_label.setFixedWidth(180)
        self.targets_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.targets_label.setStyleSheet("color: #aaa; font-size: 15px; background: #ffffff; padding: 4px 10px; border: 1px solid #eee; border-radius: 6px;")
        stats_layout.addWidget(self.targets_label)
        
        self.probes_label = QLabel("Probes: 0")
        self.probes_label.setFixedWidth(180)
        self.probes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.probes_label.setStyleSheet("color: #aaa; font-size: 15px; background: #ffffff; padding: 4px 10px; border: 1px solid #eee; border-radius: 6px;")        
        stats_layout.addWidget(self.probes_label)
        
        self.speed_label = QLabel("Speed: 0/s")
        self.speed_label.setFixedWidth(180)
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.speed_label.setStyleSheet("color: #aaa; font-size: 15px; background: #ffffff; padding: 4px 10px; border: 1px solid #eee; border-radius: 6px;")
        stats_layout.addWidget(self.speed_label)
        
        self.hits_label = QLabel("Hits: 0")
        self.hits_label.setFixedWidth(180)
        self.hits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hits_label.setStyleSheet("color: #aaa; font-size: 15px; background: #ffffff; padding: 4px 10px; border: 1px solid #eee; border-radius: 6px;")
        stats_layout.addWidget(self.hits_label)
        
        layout.addLayout(stats_layout)
        
        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Time", "Probes", "Address"])
        self.table.setMaximumHeight(220)

        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 80)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        layout.addWidget(self.table)
        
        # Log area
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(100)
        self.log.setPlaceholderText("Key hits will appear here...")
        layout.addWidget(self.log)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Scanning")
        self.start_btn.clicked.connect(self.start_scan)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)
        
        # Footer
        footer = QLabel(f"v.1.0 KamOS · 2026")
        footer.setStyleSheet("color: #aeaeae; font-size: 10px; background: transparent;")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
    
    def start_scan(self):
        self.worker = BruteForceWorker()
        self.worker.progress.connect(self.update_progress)
        self.worker.found.connect(self.on_found)
        self.worker.status.connect(self.on_stopped)
        
        self.worker.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.table.setRowCount(0)
        self.log.clear()
        self.log.append(f"// Searching {len(TARGETS):,} addresses...\n")
    
    def stop_scan(self):
        if self.worker:
            self.worker.stop()
        self.on_stopped("Manually stopped")
    
    def update_progress(self, proba, adres, speed):
        self.total_probes = proba
        self.probes_label.setText(f"Probes: {proba:,}")
        self.speed_label.setText(f"Speed: {speed:,.0f}/s")

        row = self.table.rowCount()
        self.table.insertRow(row)

        time_item = QTableWidgetItem(datetime.now().strftime("%H:%M:%S"))
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        time_item.setForeground(QColor("#999"))
        self.table.setItem(row, 0, time_item)

        probes_item = QTableWidgetItem(f"{proba:,}")
        probes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        probes_item.setForeground(QColor("#555"))
        self.table.setItem(row, 1, probes_item)

        addr_item = QTableWidgetItem(adres)
        addr_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        addr_item.setForeground(QColor("#777"))
        self.table.setItem(row, 2, addr_item)

        self.table.scrollToBottom()

        while self.table.rowCount() > 100:
            self.table.removeRow(0)
    
    def on_found(self, owner, adres, key, proba):
        self.found_count += 1
        self.hits_label.setText(f"Hits: {self.found_count}")
        
        self.log.append(f"\n{'─'*40}")
        self.log.append(f"  KEY FOUND!")
        self.log.append(f"  Target: {owner}")
        self.log.append(f"  Address: {adres}")
        self.log.append(f"  KEY: {key}")
        self.log.append(f"  Probes: {proba:,}")
        self.log.append(f"{'─'*40}\n")
        
        with open("found.txt", "a") as f:
            f.write(f"{datetime.now()},{owner},{adres},{key},{proba}\n")
    
    def on_stopped(self, message):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log.append(f"\n// {message}")
    
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())