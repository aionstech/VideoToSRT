import sys
import os
import moviepy.editor as mp
import whisper
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog, QMessageBox, QVBoxLayout, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class TranscriptionThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, video_file):
        super().__init__()
        self.video_file = video_file

    def run(self):
        try:
            # Extract audio from video
            audio_file = 'temp_audio.wav'
            video_clip = mp.VideoFileClip(self.video_file)
            video_clip.audio.write_audiofile(audio_file, codec='pcm_s16le')

            # Transcribe audio
            model = whisper.load_model("base")
            transcription = model.transcribe(audio_file)

            # Save SRT
            srt_file = os.path.splitext(self.video_file)[0] + '.srt'
            total_segments = len(transcription['segments'])
            with open(srt_file, 'w') as f:
                for i, segment in enumerate(transcription['segments']):
                    # Emit progress signal
                    progress = int((i + 1) / total_segments * 100)
                    self.progress.emit(progress)

                    start = segment['start']
                    end = segment['end']
                    text = segment['text']

                    # Formatting for SRT
                    f.write(f"{i + 1}\n")
                    f.write(f"{self.format_time(start)} --> {self.format_time(end)}\n")
                    f.write(f"{text}\n\n")

            # Emit finished signal with srt file path
            self.finished.emit(srt_file)
        except Exception as e:
            self.error.emit(str(e))

    def format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


class VideoTranscriberApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Video to SRT Transcriber')
        self.setGeometry(100, 100, 300, 150)

        # Layout
        layout = QVBoxLayout()

        # Button to select video
        self.button = QPushButton('Select Video', self)
        self.button.clicked.connect(self.select_video)
        layout.addWidget(self.button)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def select_video(self):
        options = QFileDialog.Options()
        video_file, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)", options=options)

        if video_file:
            # Start transcription in a separate thread
            self.transcription_thread = TranscriptionThread(video_file)
            self.transcription_thread.progress.connect(self.update_progress)
            self.transcription_thread.finished.connect(self.on_finished)
            self.transcription_thread.error.connect(self.on_error)
            self.transcription_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_finished(self, srt_file):
        QMessageBox.information(self, "Success", f"SRT file saved as {srt_file}")
        self.progress_bar.setValue(0)  # Reset progress bar

    def on_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.progress_bar.setValue(0)  # Reset progress bar

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transcriber = VideoTranscriberApp()
    transcriber.show()
    sys.exit(app.exec_())
