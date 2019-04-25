import cv2
from pypylon import pylon
import numpy as np
import time
import collections
import datetime


class Camera:
    def __init__(self):
        self.backend = None
        self.camera = None

    def read(self):
        raise NotImplementedError("Please Implement this method")


class OpenCVCamera(Camera):
    def __init__(self, backend, camera_index):
        super().__init__()
        self.backend = backend
        self.camera_index = camera_index

    def __init_camera__(self, camera_index):
        self.camera = cv2.VideoCapture(camera_index)

    def open(self):
        self.__init_camera__(self.camera_index)

    def read(self):
        return self.camera.read()

    def release(self):
        if(self.camera != None):
            self.camera.release()

    def is_color(self):
        while True:
            ret, frame = self.read()
            if ret:
                if len(frame.shape) == 3:
                    return True
                else:
                    return False

    def get_frame_size(self):
        width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return((width, height))


class BaslerCamera(Camera):
    def __init__(self, backend, camera_index):
        super().__init__()
        self.backend = backend
        self.camera_index = camera_index
        self.camera = self.__init_camera__()
        # setting up converter to opencv bgr format
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def __init_camera__(self):
        tlFactory = pylon.TlFactory.GetInstance()
        devices = tlFactory.EnumerateDevices()
        _camera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice())
        _camera.Attach(tlFactory.CreateDevice(devices[self.camera_index]))
        _camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
        return _camera

    def open(self):
        # basler cams are initialzed in the constructor
        return None

    def read(self):
        grabResult = self.camera.RetrieveResult(
            500, pylon.TimeoutHandling_ThrowException)

        if grabResult.GrabSucceeded():
            # Access the image data
            image = self.converter.Convert(grabResult)
            img = image.GetArray()
            return True, img
        return False, None

    def release(self):
        if(self.camera != None):
            self.camera.StopGrabbing()

    def is_color(self):
        while True:
            ret, frame = self.read()
            if ret:
                if len(frame.shape) == 3:
                    return True
                else:
                    return False

    def get_frame_size(self):
        while True:
            ret, frame = self.read()
            if ret:
                height = len(frame)
                width = len(frame[0])
                return((width, height))


def getAvailableOpenCVCameras():
    print('Scanning for opencv cameras...')

    cameras = []

    captureAPIs = {
        'V4L': 200,
        'FIREWIRE': 300,
        'QT': 500,
        'UNICAP': 600,
        'DSHOW': 700,
        'PVAPI': 800,
        'OPENNI': 900,
        'OPENNI_ASUS': 910,
        'ANDROID': 1000,
        'XIAPI': 1100,
        'AVFOUNDATION': 1200,
        'GIGANETIX': 1300,
        'MSMF': 1400,
        'WINRT': 1410,
        'INTELPERC': 1500,
        'OPENNI2': 1600,
        'OPENNI2_ASUS': 1610,
        'GPHOTO2': 1700,
        'GSTREAMER': 1800,
        'FFMPEG': 1900,
        'IMAGES': 2000,
        'ARAVIS': 2100,
        'OPENCV_MJPEG': 2200,
        'INTEL_MFX': 2300,
        'XINE': 2400
    }
    # search for cameras
    for _, apival in captureAPIs.items():
        index = 0
        while True:
            camera = cv2.VideoCapture(index+apival)
            if camera.isOpened():
                cameras.append(OpenCVCamera(
                    camera.getBackendName(), index+apival))
                index += 1
                camera.release()
                continue
            else:
                break

    print('Found {} opencv cameras'.format(len(cameras)))
    return cameras


def get_available_basler_cameras():
    print('Scanning for pylon cameras...')

    cameras = []
    apikey = 'pylon'

    tlFactory = pylon.TlFactory.GetInstance()
    devices = tlFactory.EnumerateDevices()

    for camera_index in range(len(devices)):
        cameras.append(BaslerCamera(apikey, camera_index))

    print('Found {} pylon cameras'.format(len(cameras)))
    return cameras


def get_available_cameras():
    cameras = []

    # search for opencv cameras
    cameras.extend(getAvailableOpenCVCameras())

    # search for basler cameras
    cameras.extend(get_available_basler_cameras())

    return cameras

def show_camera(cameras):
    #initialize window
    WINDOW_NAME = 'Cameras'
    cv2.namedWindow(WINDOW_NAME,cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 640,480)

    #select camera to use
    cam_index = 0
    camera = cameras[0]
    width, height = camera.get_frame_size()

    #conditional variables
    recording = False
    overlay = True

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')

    # Define the font type for opencv
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    font_margin = 25
    font_thickness = 2
    font_color = (255, 0, 0)  

    # Queue to calculate average frame rate later
    frame_times = collections.deque(maxlen=20)

    #counter to detect defect cameras            
    failed_frame_counter = 0
    out = None
    while(True):
        frame_start = time.time()
        ret, frame = camera.read()
        if ret:
            failed_frame_counter = 0
            if recording:
                out.write(frame)

            if overlay:
                cv2.putText(frame, 'FPS:'+str(round(1 / average(frame_times), 1)),
                            (font_margin, font_margin), font, font_scale, font_color, font_thickness, cv2.LINE_AA)
                if recording:
                    text = 'Recording'
                    text_size = cv2.getTextSize(text,font,font_scale,font_thickness)
                    cv2.putText(frame, text,
                                (width-font_margin - text_size[0][0], font_margin), font, font_scale, font_color, font_thickness, cv2.LINE_AA)
            cv2.imshow(WINDOW_NAME, frame)
            #calculate frame time
            frame_times.append((time.time() - frame_start))
        else:
            #cam not working
            failed_frame_counter +=1
            if failed_frame_counter > 100:
                #this is garbage we have to create a class to handle this
                if recording:
                    out.release()
                    recording = False
                #remove the malfunctionig camera
                cameras.remove(camera)
                camera = cameras[cam_index % len(cameras)]
                
                #reinit camera specific values
                width, height = camera.get_frame_size()
                frame_times.clear()

        #handle input
        key_pressed = cv2.waitKey(1)
        if key_pressed == 32:  # space (start/stop recording)
            if recording:
                out.release()
            else:
                date = datetime.datetime.fromtimestamp(
                    time.time()).strftime('%Y_%m_%d-%H_%M_%S')
                out = cv2.VideoWriter(date + '.avi', fourcc, int(1 / average(frame_times)),
                                        (width, height), isColor=camera.is_color())
            recording = not recording
        elif key_pressed == 111:  # 'o' (toogle overlay)
            overlay = not overlay
        elif key_pressed == 113:  # 'q' (quit)
            break
        elif key_pressed == 9: # 'tab' (next camera)
            if recording:
                out.release()
                recording = False
            cam_index += 1
            camera = cameras[cam_index % len(cameras)]
            #reinit camera specific values
            width, height = camera.get_frame_size()
            frame_times.clear()

    # Release everything
    if out != None:
        out.release()
    cv2.destroyAllWindows()


def average(lst):
    if len(lst) > 0:
        return sum(lst) / len(lst)
    return 1


if __name__ == '__main__':
    cameras = get_available_cameras()
    
    for camera in cameras:
        camera.open()

    show_camera(cameras)
