import cv2

from camera import FileCamera, OpenCVCamera


class CameraFinder(object):

    @staticmethod
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
                camera = cv2.VideoCapture(index + apival)
                if camera.isOpened():
                    cameras.append(OpenCVCamera(camera.getBackendName(), index + apival))
                    index += 1
                    camera.release()
                    continue
                else:
                    break

        print('Found {} opencv cameras'.format(len(cameras)))
        return cameras

    @staticmethod
    def get_available_cameras():
        cameras = []

        # search for opencv cameras
        cameras.extend(CameraFinder.getAvailableOpenCVCameras())

        return cameras

    @staticmethod
    def create_file_camera(path):
        camera = FileCamera(path)
        return camera
