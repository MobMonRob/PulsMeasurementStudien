import cv2
import numpy as np
import collections
import time
import datetime
from gen_utils import average, draw_rect
import threading
from tensorflow_face_detection.tensorflow_face_detection import TensoflowFaceDector
from pulse_measure import PulseMeasurement


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
        self.detect_faces = False
        #self.face_detection = TensoflowFaceDector()
        self.measure_pulse = False
        self.pulse_processor = PulseMeasurement()
        self.tracker = None

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
        self.roi_width = self.width*0.3
        self.roi_height = self.height*0.15
        self.roi = (int(self.width/2-self.roi_width/2), int(self.height /
                                                            3-self.roi_height/2), int(self.roi_width), int(self.roi_height))

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
                frame = cv2.flip(frame, 1)

                if len(frame.shape) != 3:
                    frame = cv2.merge((frame, frame, frame))

                if self.measure_pulse:
                    if self.tracker == None:
                        print('Tracking initialized')
                        self.tracker = cv2.TrackerKCF_create()
                        self.tracker.init(frame, self.roi)
                        self.pulse_processor.buffer_size = round(
                            1 / average(self.frame_times))*3
                    else:
                        ok, self.roi = self.tracker.update(frame)
                        self.roi = [int(x) for x in self.roi]
                        if ok:
                            x, y, w, h = self.roi
                            pulse_visualized = self.pulse_processor.run(
                                frame[y:y+h, x:x+w, :])                           
                            frame[y:y+h, x:x+w, :] = pulse_visualized
                        else:
                            print('Tracking failed...')

                if self.recording:
                    self._record_frame(frame)

                if self.overlay_active:
                    self.add_overlay_to_frame(frame)

                # frame[:, :, 0] = 0#blue
                # frame[:, :, 1] = 0#green
                # frame[:, :, 2] = 0#red
                cv2.imshow(self.window_name, frame)
                # cv2.waitKey(1)

                # cap fps to MAX_FPS
                diff = 1/MAX_FPS-(time.time() - frame_start)
                time.sleep(0 if diff < 0 else diff)

                self.frame_times.append((time.time() - frame_start))

            else:
                failed_frames_counter += 1
                if failed_frames_counter > 100:
                    self.camera_defect = True
                    break

    def add_overlay_to_frame(self, frame):
        draw_rect(frame, self.roi)
        self.print_heart_beat(frame)
        cv2.putText(frame, 'FPS:'+str(round(1 / average(self.frame_times), 1)),
                    (self.font_margin, self.font_margin), self.font_type, self.font_scale, self.font_color, self.font_thickness, cv2.LINE_AA)
        if self.recording:
            text = 'Recording'
            text_size = cv2.getTextSize(
                text, self.font_type, self.font_scale, self.font_thickness)
            cv2.putText(frame, text,
                        (self.width-self.font_margin - text_size[0][0], self.font_margin), self.font_type, self.font_scale, self.font_color, self.font_thickness, cv2.LINE_AA)

    def print_heart_beat(self, frame):
        col = (100, 255, 100)
        percent = len(self.pulse_processor.data_buffer) / \
            self.pulse_processor.buffer_size

        if percent < 1:
            text = "Initializing...%0.1f %% (bpm %0.1f)" % (
                percent*100, self.pulse_processor.bpm)
        else:
            text = "(est: %0.1f bpm)" % (self.pulse_processor.bpm)

        text_size = cv2.getTextSize(
            text, self.font_type, self.font_scale, self.font_thickness)
        cv2.putText(frame, text,
                    (self.width//2 - text_size[0][0]//2, self.font_margin), self.font_type, self.font_scale, self.font_color, self.font_thickness, cv2.LINE_AA)

    def _record_frame(self, frame):
        self.frames.append(np.copy(frame))

    def _save_recording(self):
        print('Saving recording...')
        record_time = self.time_recording_stopped - self.time_recording_started

        date = datetime.datetime.fromtimestamp(
            time.time()).strftime('%Y_%m_%d-%H_%M_%S')
        out = cv2.VideoWriter(date + '.avi', self.fourcc, int(len(self.frames)/record_time),
                              (self.width, self.height), isColor=True)  # self.camera.is_color())

        for frame in self.frames:
            out.write(frame)
        self.frames.clear()
        out.release()
        print('Video saved!')

    def stop(self):
        self.playing = False
        self.run_thread.join()
        self.camera.close()

    def toogle_face_detection(self):
        self.detect_faces = not self.detect_faces

    def toogle_recording(self):
        if self.recording:
            self.recording = False
            self.time_recording_stopped = time.time()
            self._save_recording()
        else:
            self.recording = True
            self.time_recording_started = time.time()

    def toogle_pulse_measure(self):
        self.pulse_processor.reset()
        self.measure_pulse = not self.measure_pulse
        self.tracker = None
        self.roi = (int(self.width/2-self.roi_width/2), int(self.height /
                                                            3-self.roi_height/2), int(self.roi_width), int(self.roi_height))
