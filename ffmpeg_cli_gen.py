import sys
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QLineEdit, QComboBox, QListWidget)
import ffmpeg
import re

class ProcessRunner(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()
        self.process = None
        self.stderr_output = ""
        self.queue = []
        self.current_command_index = 0

    def init_ui(self):
        self.layout = QVBoxLayout()

        # Input File
        input_layout = QHBoxLayout()
        self.input_file_label = QLabel("Input File:")
        self.input_file_line_edit = QLineEdit()
        self.input_file_line_edit.setPlaceholderText("Input File")
        input_layout.addWidget(self.input_file_label)
        input_layout.addWidget(self.input_file_line_edit)
        self.layout.addLayout(input_layout)

        # Resolution
        resolution_layout = QHBoxLayout()
        self.resolution_label = QLabel("Resolution:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["2560x1440", "1920x1080"])
        resolution_layout.addWidget(self.resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        self.layout.addLayout(resolution_layout)

        # Bitrate
        bitrate_layout = QHBoxLayout()
        self.bitrate_label = QLabel("Bitrate:")
        self.bitrate_line_edit = QLineEdit()
        self.bitrate_line_edit.setPlaceholderText("e.g., 8M")
        self.bitrate_line_edit.setText("8M")  # Default value
        bitrate_layout.addWidget(self.bitrate_label)
        bitrate_layout.addWidget(self.bitrate_line_edit)
        self.layout.addLayout(bitrate_layout)

        # Max Bitrate
        max_bitrate_layout = QHBoxLayout()
        self.max_bitrate_label = QLabel("Max Bitrate:")
        self.max_bitrate_line_edit = QLineEdit()
        self.max_bitrate_line_edit.setPlaceholderText("e.g., 10M")
        self.max_bitrate_line_edit.setText("10M")  # Default value
        max_bitrate_layout.addWidget(self.max_bitrate_label)
        max_bitrate_layout.addWidget(self.max_bitrate_line_edit)
        self.layout.addLayout(max_bitrate_layout)

        # Buffer Size
        bufsize_layout = QHBoxLayout()
        self.bufsize_label = QLabel("Buffer Size:")
        self.bufsize_line_edit = QLineEdit()
        self.bufsize_line_edit.setPlaceholderText("e.g., 16M")
        self.bufsize_line_edit.setText("16M")  # Default value
        bufsize_layout.addWidget(self.bufsize_label)
        bufsize_layout.addWidget(self.bufsize_line_edit)
        self.layout.addLayout(bufsize_layout)

        # Output File
        output_layout = QHBoxLayout()
        self.output_file_label = QLabel("Output File:")
        self.output_file_line_edit = QLineEdit()
        self.output_file_line_edit.setPlaceholderText("Output File")
        output_layout.addWidget(self.output_file_label)
        output_layout.addWidget(self.output_file_line_edit)
        self.layout.addLayout(output_layout)

        # Add to Queue Button
        self.add_to_queue_button = QPushButton("Add to Queue")
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        self.layout.addWidget(self.add_to_queue_button)

        # Queue List Widget
        self.queue_list_widget = QListWidget()
        self.layout.addWidget(self.queue_list_widget)

        # Start Button
        self.start_button = QPushButton("Start Rendering the queue")
        self.start_button.clicked.connect(self.start_process)
        self.layout.addWidget(self.start_button)

        # Status Label
        self.status_label = QLabel("Status: No errors")
        self.layout.addWidget(self.status_label)

        # Output Text Edit
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        self.layout.addWidget(self.output_text_edit)

        self.setLayout(self.layout)
        self.setWindowTitle('QProcess Example')
        self.resize(600, 400)

    def build_ffmpeg_command(self, input_file, output_file):
        resolution = self.resolution_combo.currentText()
        bitrate = self.bitrate_line_edit.text()
        max_bitrate = self.max_bitrate_line_edit.text()
        bufsize = self.bufsize_line_edit.text()

        command = [
            "ffmpeg", "-i", input_file,
            "-vf", f"scale={resolution}",
            "-c:v", "h264_amf",
            "-b:v", bitrate,
            "-maxrate", max_bitrate,
            "-bufsize", bufsize,
            output_file
        ]
        return command

    def add_to_queue(self):
        input_file = self.input_file_line_edit.text()
        output_file = self.output_file_line_edit.text()

        if not input_file or not output_file:
            self.status_label.setText("Status: Please provide input and output files.")
            return

        command = self.build_ffmpeg_command(input_file, output_file)
        command_str = " ".join(command)
        self.queue_list_widget.addItem(command_str)
    
    def start_process(self):
        if self.queue_list_widget.count() == 0:
            self.status_label.setText("Status: No commands in the queue.")
            return

        self.queue = [self.queue_list_widget.item(i).text() for i in range(self.queue_list_widget.count())]
        self.current_command_index = 0
        self.start_next_process()

    def start_next_process(self):
        if self.current_command_index >= len(self.queue):
            self.status_label.setText("Status: All processes finished.")
            return

        command_str = self.queue[self.current_command_index]
        command_parts = command_str.split()

        self.current_name = command_parts[13]
        
        self.frame_count, self.vid_duration = self.get_video_info(command_parts[2])

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        self.process.start(command_parts[0], command_parts[1:])

    def get_video_info(self, path):
        probe = ffmpeg.probe(path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)

        if video_stream is None:
            raise ValueError("No video stream found")

        # Extract frame count and duration
        frame_count = int(video_stream['nb_frames'])
        duration = float(video_stream['duration'])

        return frame_count, duration
    
    def handle_stdout(self):
        output = self.process.readAllStandardOutput().data().decode()
        self.output_text_edit.append(f"STDOUT: {output}")

    def handle_stderr(self):
        error = self.process.readAllStandardError().data().decode()
        self.stderr_output += error

        # Update the status label with the last line from stderr
        lines = self.stderr_output.splitlines()
        cur_frame = self.get_frame(lines[-1])
        if cur_frame != None and self.frame_count != None:
            
            new_message = f"progress = {round((float) (cur_frame / self.frame_count)* 100, 2)}% "
            new_message += lines[-1]
            self.status_label.setText(f"Status: {new_message}")




    def get_frame(self, message):
        match = re.search(r'frame=\s*(\d+)', message)
        if match:
            return int(match.group(1))
        return 0

    def process_finished(self):
        self.output_text_edit.append(f"{self.current_name} finished.")
        self.stderr_output = ""  # Clear stderr output for the next process
        self.current_command_index += 1
        self.start_next_process()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProcessRunner()
    window.show()
    sys.exit(app.exec())
