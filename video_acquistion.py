import cv2
import numpy as np
import sys

from camera_finder import CameraFinder
from video_player import VideoPlayer

if __name__ == '__main__':
    # Initialize window
    WINDOW_NAME = 'Cameras'
    cv2.startWindowThread()
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 640, 480)

    start_frame = np.ones((480, 640))*255
    cv2.imshow(WINDOW_NAME, start_frame)
    cv2.waitKey(1)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'FFV1')
    
    
    #if video file input
    if len(sys.argv) > 1:
        cameras = [CameraFinder.create_file_camera(sys.argv[1])]

    # else scan for available cameras
    else:       
        cameras = CameraFinder.get_available_cameras()
        print('Found {} cameras.'.format(len(cameras)))

    if len(cameras) > 0:
        # index of the currently active camera
        cam_index = 0

        # initialize video player
        player = VideoPlayer(cameras[cam_index], WINDOW_NAME, fourcc)
        player.play()

        while player.playing:
            if player.camera_defect:
                print('ERROR: Camera not responding. Removing it from the list.')
                print('ERROR: CAMERA_BACKEND:',
                      cameras[cam_index % len(cameras)].backend)
                player.stop()
                # remove the malfunctioning camera
                cameras.remove(cameras[cam_index % len(cameras)])
                player.change_camera(cameras[cam_index % len(cameras)])
                player.play()

            # handle input
            key_pressed = cv2.waitKey(1)
            # print(key_pressed)
            if key_pressed == 32:  # space (start/stop recording)
                print('PRESSED: space')
                player.toogle_recording()
            elif key_pressed == 111:  # 'o' (toogle overlay)
                print('PRESSED: o')
                player.toogle_overlay()
            elif key_pressed == 9:  # 'tab' (next camera)
                print('PRESSED: tab')
                cam_index += 1
                player.stop()
                player.change_camera(cameras[cam_index % len(cameras)])
                player.play()
            elif key_pressed == 113:  # 'q' (quit)
                print('PRESSED: q')
                player.stop()
            elif key_pressed == 102:  # 'f' (toogle freeze frame)
                print('PRESSED: f')
                player.toogle_pause()
            elif key_pressed == 112:  # 'p' (toogle pulse measure)
                print('PRESSED: p')
                player.toogle_pulse_measure()
            elif key_pressed == 82:  # up_key (move roi up)
                print('PRESSED: up')
                player.roi.move_up()
            elif key_pressed == 84:  # down_key (move roi down)
                print('PRESSED: down')
                player.roi.move_down()
            elif key_pressed == 81:  # left_key (move roi left)
                print('PRESSED: left')
                player.roi.move_left()
            elif key_pressed == 83:  # right_key (move roi right)
                print('PRESSED: right')
                player.roi.move_right()
            elif key_pressed == 43:  # right_key (increase roi size)
                print('PRESSED: plus')
                player.roi.increase_size()
            elif key_pressed == 45:  # right_key (decrease roi size)
                print('PRESSED: minus')
                player.roi.decrease_size()         

    cv2.destroyAllWindows()
