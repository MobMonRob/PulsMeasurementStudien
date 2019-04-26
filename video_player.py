import cv2
import numpy as np
import collections
import time
import datetime
from utils import average
import threading

MAX_FPS = 60


class VideoPlayer():

    def __init__(self, camera, window_name, fourcc):
        self.camera = None
        self.change_camera(camera)
        self.overlay_active = True
        self.recording = False
        self.playing = False
        self.window_name = window_name
        self.time_recording_started = None
        self.time_recording_stopped = None
        self.fourcc = fourcc
        self.run_thread = None

        # Define the font type for opencv
        self.font_type = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.55
        self.font_margin = 25
        self.font_thickness = 2
        self.font_color = (255, 0, 0)

    def __init_camera__(self, camera):
        camera.open()
        self.camera = camera
        self.width, self.height = camera.get_frame_size()
        self.camera_defect = False
        self.frame_times = collections.deque(maxlen=MAX_FPS)
        self.frames = []

    def change_camera(self, camera):
        if self.camera != None:
            self.camera.close()

        self.__init_camera__(camera)

    def toogle_overlay(self):
        self.overlay_active = not self.overlay_active

    def play(self):
        if(self.playing):
            self.stop()
        self.playing = True
        self.run_thread = threading.Thread(target=self._display_camera)
        self.run_thread.start()

    def _display_camera(self):
        failed_frames_counter = 0
        while self.playing:
            frame_start = time.time()
            ret, frame = self.camera.read()
            if ret:
                failed_frames_counter = 0
                             
                if self.recording:
                    self._record_frame(frame)

                if self.overlay_active:
                    self.add_overlay_to_frame(frame)

                cv2.imshow(self.window_name, frame)
                cv2.waitKey(1)
            
                #cap fps to MAX_FPS
                diff = 1/MAX_FPS-(time.time() - frame_start)
                time.sleep(0 if diff < 0 else diff)        

                self.frame_times.append((time.time() - frame_start))

            else:
                failed_frames_counter += 1
                if failed_frames_counter > 100:
                    self.camera_defect = True
                    break

    def add_overlay_to_frame(self, frame):
        cv2.putText(frame, 'FPS:'+str(round(1 / average(self.frame_times), 1)),
                    (self.font_margin, self.font_margin), self.font_type, self.font_scale, self.font_color, self.font_thickness, cv2.LINE_AA)
        if self.recording:
            text = 'Recording'
            text_size = cv2.getTextSize(
                text, self.font_type, self.font_scale, self.font_thickness)
            cv2.putText(frame, text,
                        (self.width-self.font_margin - text_size[0][0], self.font_margin), self.font_type, self.font_scale, self.font_color, self.font_thickness, cv2.LINE_AA)

    def _record_frame(self, frame):           
        self.frames.append(np.copy(frame))

    def _save_recording(self):
        record_time = self.time_recording_stopped - self.time_recording_started

        date = datetime.datetime.fromtimestamp(
            time.time()).strftime('%Y_%m_%d-%H_%M_%S')
        out = cv2.VideoWriter(date + '.avi', self.fourcc, int(len(self.frames)/record_time),
                              (self.width, self.height), isColor=self.camera.is_color())

        for frame in self.frames:
            out.write(frame)
        self.frames.clear()
        out.release()

    def stop(self):
        self.playing = False
        self.run_thread.join()
        self.camera.close()

    def toogle_recording(self):
        if self.recording:
            self.recording = False
            self.time_recording_stopped = time.time()
            self._save_recording()
        else:
            self.recording = True
            self.time_recording_started = time.time()
