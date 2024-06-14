import sys
import time
import numpy as np
import sounddevice as sd
import pyaudio
import wave
import mss
import cv2
import os
import subprocess
import qtawesome as qta
from screeninfo import get_monitors
from moviepy.editor import VideoFileClip, AudioFileClip
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QComboBox, QPushButton, QLineEdit, QTextEdit, QWidget, QGridLayout, QHBoxLayout, QCheckBox, QSlider, QProgressBar, QTabWidget, QShortcut
from PyQt5.QtGui import QPixmap, QImage, QFont, QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from threading import Thread
import win32api
import win32gui
import win32con
import win32ui

# Configurar logging
import logging
logging.basicConfig(filename='app.log', filemode='w', level=logging.DEBUG)

class Communicate(QObject):
    log_signal = pyqtSignal(str)
    update_timer_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)
    update_mic_progress_signal = pyqtSignal(int)

class ScreenRecorderApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.comm = Communicate()
        self.comm.log_signal.connect(self.log)
        self.comm.update_timer_signal.connect(self.update_timer)
        self.comm.update_progress_signal.connect(self.update_progress)
        self.comm.update_mic_progress_signal.connect(self.update_mic_progress)

        # Variables de grabación
        self.recording = False
        self.processing = False
        self.mic_testing = False
        self.selected_screen = None
        self.selected_mic = None
        self.selected_button = None
        self.filepath = "grabaciones"
        self.fps = 15
        self.device_info = sd.query_devices(kind='input')
        self.monitors = get_monitors()

        # Configuración del atajo de teclado
        self.shortcut = None

        # Crear la carpeta de grabaciones si no existe
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)
        self.tmp_filepath = os.path.join(self.filepath, "tmp")
        if not os.path.exists(self.tmp_filepath):
            os.makedirs(self.tmp_filepath)

        # Configuración de la interfaz
        self.init_ui()

    def update_mic_progress(self, value):
        self.mic_progress_bar.setValue(value)

    def init_ui(self):
        self.setWindowTitle("Screen Recorder Pro")
        self.resize(800, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: Arial, sans-serif;
            }
            QLabel {
                font-size: 14px;
                color: #ecf0f1;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                text-align: center;
                font-size: 12px;
                margin: 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #555;
            }
            QComboBox, QLineEdit {
                padding: 5px;
                font-size: 12px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #34495e;
                color: #ecf0f1;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                background-color: #34495e;
                color: #ecf0f1;
            }
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 5px;
                text-align: center;
                background-color: #34495e;
                color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 20px;
            }
            QCheckBox {
                font-size: 12px;
                color: #ecf0f1;
            }
            QSlider {
                background-color: #34495e;
            }
            QTabWidget::pane {
                border: 1px solid #34495e;
            }
            QTabBar::tab {
                background: #34495e;
                color: #ecf0f1;
                padding: 8px;
                font-size: 14px;
                min-width: 120px;
                min-height: 30px;
                margin: 0 2px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)

        main_layout = QVBoxLayout()

        header = QLabel("Screen Recorder Pro")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 20))
        main_layout.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(self.create_recording_tab(), "Recording")
        tabs.addTab(self.create_settings_tab(), "Settings")
        tabs.addTab(self.create_logs_tab(), "Logs")
        main_layout.addWidget(tabs)

        self.setLayout(main_layout)

        # Ventana reducida para grabación
        self.mini_window = QWidget()
        self.mini_window.setWindowTitle("Recording")
        self.mini_window.setFixedSize(400, 150)
        self.mini_window.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: Arial, sans-serif;
            }
            QLabel {
                font-size: 18px;
                color: #ecf0f1;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                text-align: center;
                font-size: 12px;
                margin: 4px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #555;
            }
        """)

        mini_layout = QVBoxLayout()
        self.mini_timer_label = QLabel("00:00:00")
        self.mini_timer_label.setAlignment(Qt.AlignCenter)
        self.mini_timer_label.setFont(QFont("Arial", 18))
        mini_layout.addWidget(self.mini_timer_label)

        button_layout = QHBoxLayout()
        self.mini_stop_button = QPushButton("Stop Recording")
        self.mini_stop_button.setFixedSize(150, 40)
        self.mini_stop_button.setIcon(qta.icon('fa.stop-circle'))
        self.mini_stop_button.setIconSize(QtCore.QSize(24, 24))
        self.mini_stop_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.mini_stop_button)

        self.show_main_button = QPushButton("Open Main Window")
        self.show_main_button.setFixedSize(150, 40)
        self.show_main_button.setIcon(qta.icon('fa.window-restore'))
        self.show_main_button.setIconSize(QtCore.QSize(24, 24))
        self.show_main_button.clicked.connect(self.show_main_window)
        button_layout.addWidget(self.show_main_button)

        mini_layout.addLayout(button_layout)
        self.mini_window.setLayout(mini_layout)

        self.show()

    def show_main_window(self):
        self.mini_window.hide()
        self.show()

    def create_recording_tab(self):
        recording_tab = QWidget()
        layout = QVBoxLayout()

        screen_selection_layout = QVBoxLayout()
        screen_selection_label = QLabel("Select Screen to Record:")
        screen_selection_layout.addWidget(screen_selection_label)

        self.screen_grid = QGridLayout()
        self.screen_buttons = []
        screen_width = self.size().width() - 40  # Allow some padding
        screen_height = int(screen_width * 9 / 16)  # Assuming a 16:9 aspect ratio

        for i, monitor in enumerate(self.monitors):
            screenshot = self.capture_screen(monitor)
            btn = QPushButton()
            btn.setIcon(QtGui.QIcon(screenshot))
            btn.setIconSize(QtCore.QSize(screen_width // 2 - 20, screen_height // 2 - 20))
            btn.setStyleSheet("background: transparent; border: none;")
            btn.clicked.connect(lambda _, m=monitor, b=btn: self.select_screen(m, b))
            btn.setToolTip(f"Select {monitor.name}")
            self.screen_buttons.append(btn)
            self.screen_grid.addWidget(btn, i // 2, i % 2)
        screen_selection_layout.addLayout(self.screen_grid)
        layout.addLayout(screen_selection_layout)

        recording_controls = QHBoxLayout()
        self.record_button = QPushButton("Start Recording")
        self.record_button.setFixedSize(150, 40)
        self.record_button.setIcon(qta.icon('fa.play-circle'))
        self.record_button.setIconSize(QtCore.QSize(24, 24))
        self.record_button.clicked.connect(self.toggle_recording)
        recording_controls.addWidget(self.record_button, alignment=Qt.AlignCenter)

        self.open_mini_button = QPushButton("Minimize")
        self.open_mini_button.setFixedSize(150, 40)
        self.open_mini_button.setIcon(qta.icon('fa.window-minimize'))
        self.open_mini_button.setIconSize(QtCore.QSize(24, 24))
        self.open_mini_button.clicked.connect(self.show_mini_window)
        recording_controls.addWidget(self.open_mini_button, alignment=Qt.AlignCenter)

        layout.addLayout(recording_controls)

        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFont(QFont("Arial", 18))
        self.timer_label.setVisible(False)
        layout.addWidget(self.timer_label, alignment=Qt.AlignCenter)

        self.loading_label = QLabel("Processing...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label, alignment=Qt.AlignCenter)

        recording_tab.setLayout(layout)
        return recording_tab

    def show_mini_window(self):
        if self.recording:
            self.mini_stop_button.setText("Stop Recording")
            self.mini_stop_button.setIcon(qta.icon('fa.stop-circle'))
        else:
            self.mini_stop_button.setText("Start Recording")
            self.mini_stop_button.setIcon(qta.icon('fa.play-circle'))
        self.hide()
        self.mini_window.show()

    def create_settings_tab(self):
        settings_tab = QWidget()
        form_layout = QVBoxLayout()

        location_layout = QHBoxLayout()
        self.location_button = QPushButton("Select Storage Location")
        self.location_button.setIcon(qta.icon('fa.folder-open'))
        self.location_button.setIconSize(QtCore.QSize(24, 24))
        self.location_button.clicked.connect(self.select_location)
        location_layout.addWidget(self.location_button)
        
        self.open_location_button = QPushButton("Open Recordings Folder")
        self.open_location_button.setIcon(qta.icon('fa.folder'))
        self.open_location_button.setIconSize(QtCore.QSize(24, 24))
        self.open_location_button.clicked.connect(self.open_location)
        location_layout.addWidget(self.open_location_button)
        form_layout.addLayout(location_layout)

        name_and_extension_layout = QGridLayout()
        self.filename_label = QLabel("File Name:")
        name_and_extension_layout.addWidget(self.filename_label, 0, 0)
        self.filename_input = QLineEdit("recording")
        name_and_extension_layout.addWidget(self.filename_input, 0, 1)
        self.extension_combo = QComboBox()
        self.extension_combo.addItems([".mp4", ".avi", ".mov"])
        name_and_extension_layout.addWidget(self.extension_combo, 0, 2)
        form_layout.addLayout(name_and_extension_layout)

        audio_and_cursor_layout = QGridLayout()
        self.record_system_audio_checkbox = QCheckBox("Record System Audio")
        self.record_system_audio_checkbox.setChecked(False)
        self.record_system_audio_checkbox.stateChanged.connect(self.toggle_system_audio_volume_slider)
        audio_and_cursor_layout.addWidget(self.record_system_audio_checkbox, 0, 0)

        self.system_audio_volume_slider = QSlider(Qt.Horizontal)
        self.system_audio_volume_slider.setRange(0, 1000)
        self.system_audio_volume_slider.setValue(700)
        self.system_audio_volume_slider.setEnabled(False)
        audio_and_cursor_layout.addWidget(self.system_audio_volume_slider, 0, 1)

        self.show_cursor_checkbox = QCheckBox("Show Cursor")
        self.show_cursor_checkbox.setChecked(True)
        audio_and_cursor_layout.addWidget(self.show_cursor_checkbox, 0, 2)

        self.cursor_style_combo = QComboBox()
        self.cursor_style_combo.addItems(["Default", "White Circle", "Red Circle", "Green Circle", "Blue Circle", "Cross"])
        audio_and_cursor_layout.addWidget(self.cursor_style_combo, 0, 3)

        form_layout.addLayout(audio_and_cursor_layout)

        mic_settings_layout = QGridLayout()
        self.mic_recording_checkbox = QCheckBox("Record Microphone Audio")
        self.mic_recording_checkbox.setChecked(True)
        self.mic_recording_checkbox.stateChanged.connect(self.toggle_mic_controls)
        mic_settings_layout.addWidget(self.mic_recording_checkbox, 0, 0)

        self.mic_combo = QComboBox()
        self.mic_devices = [d for d in sd.query_devices() if d['max_input_channels'] > 0]
        self.mic_combo.addItems([d['name'] for d in self.mic_devices])
        self.mic_combo.setEnabled(True)
        mic_settings_layout.addWidget(self.mic_combo, 0, 1)

        self.mic_volume_slider = QSlider(Qt.Horizontal)
        self.mic_volume_slider.setRange(0, 3000)
        self.mic_volume_slider.setValue(1000)
        self.mic_volume_slider.setEnabled(True)
        mic_settings_layout.addWidget(self.mic_volume_slider, 0, 2)

        self.test_mic_button = QPushButton("Test")
        self.test_mic_button.setIcon(qta.icon('fa.microphone'))
        self.test_mic_button.setIconSize(QtCore.QSize(24, 24))
        self.test_mic_button.clicked.connect(self.toggle_mic_test)
        self.test_mic_button.setEnabled(True)
        mic_settings_layout.addWidget(self.test_mic_button, 1, 0)

        self.mic_progress_bar = QProgressBar()
        self.mic_progress_bar.setMaximum(100)
        mic_settings_layout.addWidget(self.mic_progress_bar, 1, 1, 1, 2)

        form_layout.addLayout(mic_settings_layout)

        # Add shortcut setting
        shortcut_layout = QHBoxLayout()
        self.shortcut_label = QLabel("Set Shortcut for Start/Stop Recording:")
        shortcut_layout.addWidget(self.shortcut_label)
        self.shortcut_input = QLineEdit()
        self.shortcut_input.setPlaceholderText("Press a key combination")
        self.shortcut_input.setReadOnly(True)
        self.shortcut_input.setFocusPolicy(Qt.StrongFocus)
        self.shortcut_input.keyPressEvent = self.set_shortcut
        shortcut_layout.addWidget(self.shortcut_input)
        form_layout.addLayout(shortcut_layout)

        # Add minimize on start option
        self.minimize_on_start_checkbox = QCheckBox("Minimize on Start Recording")
        self.minimize_on_start_checkbox.setChecked(True)
        form_layout.addWidget(self.minimize_on_start_checkbox)

        settings_tab.setLayout(form_layout)
        return settings_tab

    def create_logs_tab(self):
        logs_tab = QWidget()
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        logs_tab.setLayout(layout)
        return logs_tab

    def log(self, message):
        self.log_text.append(f"{time.strftime('%H:%M:%S')}: {message}")
        logging.info(message)

    def update_timer(self, time_string):
        self.timer_label.setText(time_string)
        self.mini_timer_label.setText(time_string)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def capture_screen(self, monitor):
        bbox = {'left': monitor.x, 'top': monitor.y, 'width': monitor.width, 'height': monitor.height}
        sct_img = mss.mss().grab(bbox)
        img = QImage(sct_img.rgb, sct_img.width, sct_img.height, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(img)
        pixmap = pixmap.scaled(360, 202, Qt.KeepAspectRatio)  # Increased size for better visibility
        return pixmap

    def select_screen(self, monitor, button):
        self.selected_screen = monitor
        self.log(f"Selected screen: {monitor.name}")
        if self.selected_button:
            self.selected_button.setStyleSheet("background: transparent; border: none;")
        self.selected_button = button
        self.selected_button.setStyleSheet("background: transparent; border: 2px solid #007ACC;")

    def select_location(self):
        self.filepath = QFileDialog.getExistingDirectory(self, "Select Storage Location")
        if self.filepath:
            self.tmp_filepath = os.path.join(self.filepath, "tmp")
            if not os.path.exists(self.tmp_filepath):
                os.makedirs(self.tmp_filepath)
            self.log(f"Selected location: {self.filepath}")

    def open_location(self):
        if os.path.isdir(self.filepath):
            self.log(f"Opening recordings location: {self.filepath}")
            if sys.platform == 'win32':
                os.startfile(self.filepath)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', self.filepath])
            else:
                subprocess.Popen(['xdg-open', self.filepath])
        else:
            self.log(f"The path {self.filepath} is not a valid directory.")

    def toggle_system_audio_volume_slider(self):
        self.system_audio_volume_slider.setEnabled(self.record_system_audio_checkbox.isChecked())

    def toggle_mic_controls(self):
        mic_enabled = self.mic_recording_checkbox.isChecked()
        self.mic_combo.setEnabled(mic_enabled)
        self.test_mic_button.setEnabled(mic_enabled)
        self.mic_volume_slider.setEnabled(mic_enabled)
        self.mic_progress_bar.setVisible(True)  # Always visible

    def toggle_mic_test(self):
        if self.mic_testing:
            self.stop_mic_test()
        else:
            self.start_mic_test()

    def start_mic_test(self):
        self.log("Testing microphone...")
        self.mic_progress_bar.setValue(0)
        self.mic_testing = True
        self.test_mic_button.setText("Stop")

        def callback(indata, frames, time, status):
            volume_norm = np.linalg.norm(indata) * 10
            self.comm.update_mic_progress_signal.emit(min(100, int(volume_norm)))
            self.comm.log_signal.emit(f"Microphone volume level: {volume_norm}")

        self.mic_stream = sd.InputStream(callback=callback)
        self.mic_stream.start()

    def stop_mic_test(self):
        self.mic_stream.stop()
        self.mic_stream.close()
        self.mic_testing = False
        self.test_mic_button.setText("Test")
        self.comm.log_signal.emit("Microphone test ended.")
        self.mic_progress_bar.setValue(0)

    def toggle_recording(self):
        if self.recording:
            self.recording = False
            self.record_button.setText("Start Recording")
            self.record_button.setIcon(qta.icon('fa.play-circle'))
            self.mini_stop_button.setText("Start Recording")
            self.mini_stop_button.setIcon(qta.icon('fa.play-circle'))
            self.timer_label.setVisible(False)
            self.comm.log_signal.emit("Recording stopped.")
            self.show_main_window()
        else:
            if self.selected_screen is None:
                self.comm.log_signal.emit("Error: No screen selected.")
                QtWidgets.QMessageBox.warning(self, "Screen Not Selected", "Please select a screen to record before starting.")
                return
            output_name = f"{self.filepath}/{self.filename_input.text()}{self.extension_combo.currentText()}"
            if os.path.exists(output_name):
                reply = QtWidgets.QMessageBox.question(self, 'File Exists',
                                                    f"The file '{output_name}' already exists. Replace it?",
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
                if reply == QtWidgets.QMessageBox.No:
                    self.comm.log_signal.emit("Recording cancelled by user.")
                    return
            
            self.recording = True
            self.record_button.setText("Stop Recording")
            self.record_button.setIcon(qta.icon('fa.stop-circle'))
            self.mini_stop_button.setText("Stop Recording")
            self.mini_stop_button.setIcon(qta.icon('fa.stop-circle'))
            self.timer_label.setVisible(True)
            self.comm.log_signal.emit("Starting recording...")
            if self.minimize_on_start_checkbox.isChecked():
                self.hide()
                self.mini_window.show()
            Thread(target=self.record).start()
            self.comm.log_signal.emit("Recording started.")

    
    def capture_cursor(self):
        cursor_info = win32gui.GetCursorInfo()
        cursor_handle = cursor_info[1]

        hdc = win32gui.GetDC(0)
        hdc_mem = win32ui.CreateDCFromHandle(hdc)
        hdc_compatible = hdc_mem.CreateCompatibleDC()
        hbitmap = win32ui.CreateBitmap()
        hbitmap.CreateCompatibleBitmap(hdc_mem, 32, 32)
        hdc_compatible.SelectObject(hbitmap)

        icon_info = win32gui.GetIconInfo(cursor_handle)
        win32gui.DrawIconEx(hdc_compatible.GetHandleOutput(), 0, 0, cursor_handle, 32, 32, 0, 0, win32con.DI_NORMAL)

        bmpinfo = hbitmap.GetInfo()
        bmpstr = hbitmap.GetBitmapBits(True)

        cursor_img = np.frombuffer(bmpstr, dtype='uint8')
        cursor_img = cursor_img.reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))

        hdc_compatible.DeleteDC()
        hdc_mem.DeleteDC()
        win32gui.ReleaseDC(0, hdc)
        win32gui.DeleteObject(hbitmap.GetHandle())

        return cursor_img, icon_info[1], icon_info[2]  # Return cursor image and its hot spot



    def record(self):
        screen_name = os.path.join(self.tmp_filepath, "screen.avi")
        audio_name = os.path.join(self.tmp_filepath, "audio.wav")

        # Crear la carpeta de grabaciones si no existe
        if not os.path.exists(self.filepath):
            os.makedirs(self.filepath)
        if not os.path.exists(self.tmp_filepath):
            os.makedirs(self.tmp_filepath)

        # Inicializar mss dentro del hilo
        sct = mss.mss()

        # Configuración de audio
        p = pyaudio.PyAudio()
        audio_format = pyaudio.paInt16
        rate = 44100

        # Obtener el índice del micrófono seleccionado
        mic_index = self.mic_combo.currentIndex()
        mic_device = self.mic_devices[mic_index]
        mic_name = mic_device['name']

        # Comprobar el número de canales admitidos
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['name'] == mic_name:
                max_input_channels = info['maxInputChannels']
                break

        channels = 2 if max_input_channels >= 2 else 1

        # Ajustar el tamaño del buffer de frames
        frames_per_buffer = 2048

        stream = p.open(format=audio_format, channels=channels, rate=rate,
                        input=True, input_device_index=i, frames_per_buffer=frames_per_buffer)

        # Configuración de video
        bbox = {'top': self.selected_screen.y, 'left': self.selected_screen.x, 'width': self.selected_screen.width, 'height': self.selected_screen.height}
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(screen_name, fourcc, self.fps, (bbox['width'], bbox['height']))

        audio_frames = []
        start_time = time.time()
        frame_interval = 1.0 / self.fps
        next_frame_time = start_time + frame_interval

        def capture_audio():
            system_volume = self.system_audio_volume_slider.value() / 1000.0
            mic_volume = self.mic_volume_slider.value() / 1000.0
            max_value = 32767  # Maximum value for int16
            threshold = 0.8 * max_value  # Threshold for normalization and compression

            while self.recording:
                data = stream.read(frames_per_buffer)
                audio_data = np.frombuffer(data, dtype=np.int16)

                # Normalizing
                max_amplitude = np.max(np.abs(audio_data))
                if max_amplitude > threshold:
                    normalization_factor = threshold / max_amplitude
                    audio_data = audio_data * normalization_factor

                # Apply volume and clipping
                audio_data = np.clip(audio_data * mic_volume, -max_value, max_value)

                audio_frames.append(audio_data.astype(np.int16).tobytes())

        audio_thread = None
        if self.mic_recording_checkbox.isChecked():
            audio_thread = Thread(target=capture_audio)
            audio_thread.start()

        while self.recording:
            current_time = time.time()
            if current_time >= next_frame_time:
                # Captura de pantalla
                img = sct.grab(bbox)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # Mostrar cursor si está seleccionado
                if self.show_cursor_checkbox.isChecked():
                    cursor_pos = win32api.GetCursorPos()
                    cursor_style = self.cursor_style_combo.currentText()
                    cursor_x = cursor_pos[0] - bbox['left']
                    cursor_y = cursor_pos[1] - bbox['top']

                    if cursor_style == "White Circle":
                        cv2.circle(frame, (cursor_x, cursor_y), 10, (255, 255, 255), 2)
                    elif cursor_style == "Red Circle":
                        cv2.circle(frame, (cursor_x, cursor_y), 10, (0, 0, 255), 2)
                    elif cursor_style == "Green Circle":
                        cv2.circle(frame, (cursor_x, cursor_y), 10, (0, 255, 0), 2)
                    elif cursor_style == "Blue Circle":
                        cv2.circle(frame, (cursor_x, cursor_y), 10, (255, 0, 0), 2)
                    elif cursor_style == "Cross":
                        cv2.line(frame, (cursor_x - 10, cursor_y), (cursor_x + 10, cursor_y), (0, 0, 0), 2)
                        cv2.line(frame, (cursor_x, cursor_y - 10), (cursor_x, cursor_y + 10), (0, 0, 0), 2)
                    else:
                        cursor_img, hotspot_x, hotspot_y = self.capture_cursor()
                        for i in range(cursor_img.shape[0]):
                            for j in range(cursor_img.shape[1]):
                                if cursor_img[i, j, 3] > 0:  # alpha channel check
                                    frame[cursor_y - hotspot_y + i, cursor_x - hotspot_x + j] = cursor_img[i, j, :3]

                out.write(frame)
                next_frame_time += frame_interval

                # Actualizar el temporizador
                elapsed_time = current_time - start_time
                self.comm.update_timer_signal.emit(time.strftime('%H:%M:%S', time.gmtime(elapsed_time)))

        self.recording = False
        if audio_thread:
            audio_thread.join()

        # Detener y guardar la grabación de audio
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Guardar audio
        if self.mic_recording_checkbox.isChecked():
            with wave.open(audio_name, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(audio_format))
                wf.setframerate(rate)
                wf.writeframes(b''.join(audio_frames))

        out.release()

        # Procesar grabación
        self.processing = True
        self.loading_label.setVisible(True)
        self.record_button.setEnabled(False)

        self.combine_audio_video(screen_name, audio_name)

    def combine_audio_video(self, video_file, audio_file):
        output_name = f"{self.filepath}/{self.filename_input.text()}{self.extension_combo.currentText()}"

        video_clip = VideoFileClip(video_file)
        if self.mic_recording_checkbox.isChecked():
            audio_clip = AudioFileClip(audio_file)
            video_with_audio = video_clip.set_audio(audio_clip)
        else:
            video_with_audio = video_clip

        video_with_audio.write_videofile(output_name, codec='libx264', audio_codec='aac')

        self.comm.log_signal.emit(f"Recording saved to: {output_name}")

        # Eliminar archivos temporales
        os.remove(video_file)
        if self.mic_recording_checkbox.isChecked():
            os.remove(audio_file)

        self.loading_label.setVisible(False)
        self.record_button.setEnabled(True)
        self.processing = False


    def set_shortcut(self, event):
        key_sequence = QKeySequence(event.key() + int(event.modifiers()))
        self.shortcut_input.setText(key_sequence.toString())
        self.set_global_shortcut(key_sequence)

    def set_global_shortcut(self, key_sequence):
        if self.shortcut:
            self.shortcut.setEnabled(False)
        self.shortcut = QShortcut(key_sequence, self)
        self.shortcut.activated.connect(self.record_button.click)
        self.log(f"Shortcut set to: {key_sequence.toString()}")

if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication(sys.argv)
        recorder = ScreenRecorderApp()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Main execution error: {e}")
        print(f"Error: {e}")
