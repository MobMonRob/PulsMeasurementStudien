import cv2
from pypylon import pylon


class Camera:
    def __init__(self):
        self.backend = None
        self.camera = None
        self.isColor = None

    def read(self):
        raise NotImplementedError("Please Implement this method")

    def open(self):
        raise NotImplementedError("Please Implement this method")

    def close(self):
        raise NotImplementedError("Please Implement this method")

    def is_color(self):
        raise NotImplementedError("Please Implement this method")

    def get_frame_size(self):
        index = 0
        while index < 10:
            index += 1
            ret, frame = self.read()
            if ret:
                height = len(frame)
                width = len(frame[0])
                return((width, height))
        return((0, 0))

    def get_frame_position(self):
        return 0
    
    def get_frame_count(self):
        return 0


class OpenCVCamera(Camera):
    def __init__(self, backend, camera_index):
        super().__init__()
        self.backend = backend
        self.camera_index = camera_index

    def __init_camera__(self, camera_index):
        self.camera = cv2.VideoCapture(camera_index)

    def open(self):
        self.__init_camera__(self.camera_index)

    def close(self):
        if self.camera != None:
            self.camera.release()

    def read(self):
        return self.camera.read()

    def release(self):
        if(self.camera != None):
            self.camera.release()

    def is_color(self):
        if self.isColor == None:
            while True:
                ret, frame = self.read()
                if ret:
                    if len(frame.shape) == 3:
                        self.isColor = True
                        return True
                    else:
                        self.isColor = False
                        return False
        return self.isColor


class BaslerCamera(Camera):
    def __init__(self, backend, camera_index):
        super().__init__()
        self.backend = backend
        self.camera_index = camera_index
        self.camera = None
        # setting up converter to opencv bgr format
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    def __init_camera__(self):
        tlFactory = pylon.TlFactory.GetInstance()
        devices = tlFactory.EnumerateDevices()
        _camera = pylon.InstantCamera()
        _camera.Attach(tlFactory.CreateDevice(devices[self.camera_index]))
        return _camera

    def open(self):
        if self.camera == None:
            self.camera = self.__init_camera__()
        self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

    def close(self):
        if self.camera != None:
            self.camera.StopGrabbing()

    def read(self):
        if self.camera.IsGrabbing():
            grabResult = self.camera.RetrieveResult(
                5000, pylon.TimeoutHandling_Return)

            if grabResult.GrabSucceeded():
                # Access the image data
                image = self.converter.Convert(grabResult)
                img = image.GetArray()
                grabResult.Release()
                return True, img
            grabResult.Release()
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

class FileCamera(Camera):

    def __init__(self,path):
        self.backend = 'file'
        self.camera = None
        self.path = path
        self.isColor = None

    def __init_camera__(self, path):
        self.camera = cv2.VideoCapture(path)

    def open(self):
        self.__init_camera__(self.path)

    def close(self):
        if self.camera != None:
            self.camera.release()

    def read(self):
        ok,frame =  self.camera.read()
        if not ok:
            #repeat the video from the beginning
            self.camera.set(cv2.CAP_PROP_POS_FRAMES,0)
            return self.camera.read()
        return ok,frame

    def release(self):
        if(self.camera != None):
            self.camera.release()

    def get_frame_size(self):
        width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))     
        return((width, height))

    def is_color(self):
        number_of_channels = self.camera.get(cv2.CAP_PROP_CHANNEL)
        if number_of_channels == 3:
            return True
        return False

    def get_frame_position(self):
        return int(self.camera.get(cv2.CAP_PROP_POS_FRAMES))
    
    def get_frame_count(self):
        return int(self.camera.get(cv2.CAP_PROP_FRAME_COUNT))

