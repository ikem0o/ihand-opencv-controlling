import time
import cv2
import os
import math
import numpy
import tkinter
import win32con
import win32api
import mediapipe as mp
from PIL import ImageTk, Image
# Controling box frame size.
controlingFrame = 100
# Config of camera resolution and screen resolution.
hCam, wCam, wScr, hScr = 480, 640, win32api.GetSystemMetrics(
    0), win32api.GetSystemMetrics(1)
# Config camera, gui, system variables and graphics.
handModes, handModesFolder = [], "interfaceImages/handModes"
for modePath in os.listdir(handModesFolder):
    handModes.append(cv2.imread(os.path.join(handModesFolder, modePath)))
activeModes, activeModesFolder = [], "interfaceImages/activeModes"
for modePath in os.listdir(activeModesFolder):
    activeModes.append(cv2.imread(os.path.join(activeModesFolder, modePath)))
mouseModes, mouseModesFolder = [], "interfaceImages/mouseModes"
for modePath in os.listdir(mouseModesFolder):
    mouseModes.append(cv2.imread(os.path.join(mouseModesFolder, modePath)))
cameraPort = cv2.VideoCapture(0)
activeMode, workOnceTimer, workOnceCounter = False, True, True
mainBackground = cv2.imread('interfaceImages/GUIBackground.jpg', 3)
# Create a window.
root = tkinter.Tk()
root.title('[iKEMOO] iHand - Mouse Control v2')
root.iconphoto(False, tkinter.PhotoImage(file="interfaceImages/Launcher.png"))
appWindow = tkinter.Frame(root, bg="black")
appWindow.grid()
# Create a label in the frame.
appWindow = tkinter.Label(appWindow)
appWindow.grid()


# Hand detection and segmentation system.
class handTrackingModule():
    def __init__(self, draw=True, maxHands=1):
        self.draw = draw
        self.tipIds = [4, 8, 12, 16, 20]
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(False, maxHands, 0, 0.75, 0.5)
        self.mpDraw = mp.solutions.drawing_utils

    # Collecting data from frames and return it.
    def getFrameData(self, img):
        lmList, fingers = [], []
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if self.draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS,
                                               self.mpDraw.DrawingSpec(
                                                   color=(255, 255, 255), thickness=4),
                                               self.mpDraw.DrawingSpec(
                                                   color=(255, 255, 255), thickness=2),
                                               )
            myHand = self.results.multi_hand_landmarks[0]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
            if lmList[self.tipIds[0]][1] > lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
            for id in range(1, 5):
                if lmList[self.tipIds[id]][2] < lmList[self.tipIds[id] - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)
        totalFingers = fingers.count(1)
        return img, lmList, totalFingers, fingers

    # Find the distance between points.
    def findDistance(self, p1, p2, img, lmList, draw=False, r=10, t=3):
        x1, y1 = lmList[p1][1:]
        x2, y2 = lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        length = math.hypot(x2 - x1, y2 - y1)
        return length, img, [x1, y1, x2, y2, cx, cy]


# Make a shortcut to use the module.
HTMSystem = handTrackingModule()


def getContentFrame():
    global activeMode, workOnceTimer, firstActiveMode, workOnceCounter
    # Get image and skip errors.
    _, camImg = cameraPort.read()
    # Get hand detection data from image and draw the virtual screen frame.
    camImg, lmList, totalFingers, fingers = HTMSystem.getFrameData(camImg)
    cv2.rectangle(camImg, (controlingFrame, controlingFrame),
                  (wCam - controlingFrame, hCam - controlingFrame), (17, 102, 255), 2)
    cv2.putText(mainBackground, str(wScr), (707, 456),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (17, 102, 255), 2, cv2.LINE_AA)
    cv2.putText(mainBackground, str(hScr), (707, 496),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (17, 102, 255), 2, cv2.LINE_AA)
    # Disply number of fingers in gui.
    if totalFingers > 0:
        mainBackground[129:129+116, 679:679+136] = handModes[totalFingers]
    else:
        # Disply no hand in all options.
        mainBackground[129:129+116, 679:679+136] = handModes[0]
        mainBackground[254:254+109, 692:692+115] = mouseModes[2]
    pointsXY = []
    if lmList:
        # Get x and y for every point.
        [pointsXY.append([lmList[point][1], lmList[point][2]])
         for point in [4, 8, 12]]
        # Draw red points to debug and know the points.
        [cv2.circle(camImg, (x, y), 4, (17, 102, 255), cv2.FILLED)
         for x, y in pointsXY]
        # Check if system are activated or not.
        if activeMode:
            # IF two finger are up activate the system.
            if fingers == [1, 1, 0, 0, 0]:
                if workOnceCounter:
                    # Start counting the 3 sec.
                    if workOnceTimer:
                        firstActiveMode = int(time.time())
                        workOnceTimer = False
                    if int(time.time()) - firstActiveMode >= 3:
                        mainBackground[248:248+117,
                                       691:691+115] = activeModes[4]
                        activeMode = False
                        workOnceTimer = True
                        workOnceCounter = False
                    else:
                        mainBackground[248:248+117, 691:691 +
                                       115] = activeModes[int(time.time()) - firstActiveMode]
            else:
                workOnceCounter = True
                workOnceTimer = True
            x1, y1 = lmList[8][1:]
            # Convert from camera resolution to screen resolution.
            x3 = numpy.interp(
                x1, (controlingFrame, wCam - controlingFrame), (0, wScr))
            y3 = numpy.interp(
                y1, (controlingFrame, hCam - controlingFrame), (0, hScr))
            # If one finger are up move the mouse pointer.
            if fingers == [0, 1, 0, 0, 0]:
                # Change gui mode option to move mode.
                mainBackground[254:254+109, 692:692+115] = mouseModes[1]
                # Define mouse pointer postion to move.
                win32api.SetCursorPos((int(wScr - x3), int(y3)))
            # If two fingers are up and touched click the mouse left button.
            if fingers == [0, 1, 1, 0, 0]:
                # Change gui mode option to click mode.
                mainBackground[254:254+109, 692:692+115] = mouseModes[0]
                # Get the length between fingers to get click action.
                length, camImg, _ = HTMSystem.findDistance(
                    8, 12, camImg, lmList, False)
                target, camImg, _ = HTMSystem.findDistance(
                    8, 7, camImg, lmList, False)
                # If fingers touched.
                if length < target+20:
                    # Click down the mouse left button and release it.
                    win32api.mouse_event(
                        win32con.MOUSEEVENTF_LEFTDOWN, int(wScr - x3), int(y3), 0, 0)
                    win32api.mouse_event(
                        win32con.MOUSEEVENTF_LEFTUP, int(wScr - x3), int(y3), 0, 0)
                    time.sleep(0.2)
        else:
            # IF two finger are up deactivate the system.
            if fingers == [1, 1, 0, 0, 0]:
                if workOnceCounter:
                    # Start counting the 3 sec.
                    if workOnceTimer:
                        firstActiveMode = int(time.time())
                        workOnceTimer = False
                    if int(time.time()) - firstActiveMode >= 3:
                        mainBackground[248:248+117,
                                       691:691+115] = activeModes[5]
                        activeMode = True
                        workOnceTimer = True
                        workOnceCounter = False
                    else:
                        mainBackground[248:248+117, 691:691 +
                                       115] = activeModes[int(time.time()) - firstActiveMode]
            else:
                workOnceTimer = True
                workOnceCounter = True
                mainBackground[248:248+117, 691:691+115] = activeModes[4]
    else:
        if activeMode:
            mainBackground[248:248+117, 691:691+115] = activeModes[5]
        else:
            mainBackground[248:248+117, 691:691+115] = activeModes[4]
    # Adding camera frame to gui window.
    mainBackground[30:30+480, 30:30+640] = camImg
    imgtk = ImageTk.PhotoImage(image=Image.fromarray(
        cv2.cvtColor(mainBackground, cv2.COLOR_BGR2RGBA)))
    # Update gui window.
    appWindow.imgtk = imgtk
    appWindow.configure(image=imgtk)
    appWindow.after(1, getContentFrame)


getContentFrame()
root.mainloop()
