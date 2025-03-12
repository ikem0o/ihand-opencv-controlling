import time
import cv2
import os
import tkinter
import serial
import win32api
import mediapipe as mp
from PIL import ImageTk, Image
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
lampModes, lampModesFolder = [], "interfaceImages/lampModes"
for modePath in os.listdir(lampModesFolder):
    lampModes.append(cv2.imread(os.path.join(lampModesFolder, modePath)))
cameraPort = cv2.VideoCapture(0)
clickMode, activeMode, workOnceTimer, workOnceCounter = True, False, True, True
mainBackground = cv2.imread('interfaceImages/GUIBackground.jpg', 3)
mainBackground[252:252+109, 692:692+113] = lampModes[0]
# Config and connect to the arduino port.
port = serial.Serial("COM20", 9600, timeout=0)
stat = False
time.sleep(2)
# Create a window.
root = tkinter.Tk()
root.title('[iKEMOO] iHand - Smart Home Control v2')
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


# Make a shortcut to use the module.
HTMSystem = handTrackingModule()


def getContentFrame():
    global clickMode, activeMode, workOnceTimer, firstActiveMode, workOnceCounter
    # Get image and skip errors.
    _, camImg = cameraPort.read()
    # Get hand detection data from image and draw the virtual screen frame.
    camImg, lmList, totalFingers, fingers = HTMSystem.getFrameData(camImg)
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
        clickMode = True
    pointsXY = []
    if lmList:
        # Get x and y for every point.
        [pointsXY.append([lmList[point][1], lmList[point][2]])
         for point in [4, 8]]
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
                        clickMode = False
                    else:
                        mainBackground[248:248+117, 691:691 +
                                       115] = activeModes[int(time.time()) - firstActiveMode]
            else:
                workOnceCounter = True
                workOnceTimer = True
            # If Sec. fingers are up turn on realy.
            if fingers == [0, 1, 0, 0, 0] and clickMode:
                port.write("on".encode())
                mainBackground[252:252+109, 692:692+113] = lampModes[1]
                clickMode = False
                workOnceTimer = True
            # If first finger are up turn off realy.
            elif fingers == [1, 0, 0, 0, 0] and clickMode:
                port.write("off".encode())
                mainBackground[252:252+109, 692:692+113] = lampModes[0]
                clickMode = False
                workOnceTimer = True
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
                        clickMode = False
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
