import cv2


def average(lst):
    if len(lst) > 0:
        return sum(lst) / len(lst)
    return 1


def draw_rect(frame, rect, col=(0, 255, 0)):
    x, y, w, h = rect
    cv2.rectangle(frame, (x, y), (x + w, y + h), col, 1)
