
########################## GUI INCLUDE ###############################

import sys


################ DO NOT DELETE - EXE 파일 만들때 필요한 부분 ################
import os
 
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)



#########################################################

#from PySide2.QtXml import* ##중요 이거없으면 exe 안만들어짐
from PyQt5.QtWidgets import *
from PyQt5 import uic as QtUiTools 
from PyQt5.QtCore import *
from PyQt5.QtGui import*

import time
import threading

########################## SERIAL COM INCLUDE  ######################

import serial           


#######################  글로벌 변수  할당 ###################
######  GUI 쓰레드와 계측 MAIN LOOP 쓰레드간의 변수 공유######


global PORT_NUM
global LAST_PORT_NUM
global BAUD_RATE
global CHANNEL
global START_CH_SCAN
global DEVICE_NUM

global position
global capacitance
global speed
global err
global RUN

global cap
global pos
global spd

global port_scan_flag  # 스캔버튼 누르면 뜸 0 대기  1 시작 2 완료 포트 스캔 은 메인루프에서 진행
global port    # 퍼
global err_flag


err_flag = 0
port_scan_flag = 0
port = 0

BAUD_RATE = 0
DEVICE_NUM = "---"
PORT_NUM = 0
LAST_PORT_NUM = 0
CHANNEL = []
SCAN_STATUS = 0

position =0
capacitance =0
speed =0
err =0
RUN = 0

cap = 0
pos = 0
spd = 0


######################  파라미터 설정  #############################



COM_TERM = 1        #SEC : 485통신 타임아웃
SCAN_TERM = 0.05

POS_MAX = 4000
SPD_MAX = 360
SPD_MIN = 30


##########################  전역 함수 설정  #######################################


def serial_ports():   ##find serial port
    """ Lists serial port names   
       
        :raises EnvironmentError:   
            On unsupported or unknown platforms   
        :returns:   
            A list of the serial ports available on the system   
    """   
    if sys.platform.startswith('win'):   
        ports = ['COM%s' % (i + 1) for i in range(256)]   
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):   
        # this excludes your current terminal "/dev/tty"   
        ports = glob.glob('/dev/tty[A-Za-z]*')   
    elif sys.platform.startswith('darwin'):   
        ports = glob.glob('/dev/tty.*')   
    else:   
        raise EnvironmentError('Unsupported platform')   
       
    result = []   
    for port in ports:   
        try:   
            s = serial.Serial(port)   
            s.close()   
            result.append(port)   
        except (OSError, serial.SerialException):   
            pass   
    return result




def scan_ch():
    
    global ser
    global channel
   
        
    ch = ['%d' % (i) for i in range(17)]
    channel = []
    test = []

    for i in range(17):

        line= list((str(format(i,'02'))+"\r").encode('ascii'))
        test.append(line)

        
    for j in range(0,17):#initiate

        ser.write(test[j])
        result = ser.read(8)

        if(result):

            channel.append(format(j,'02'))

    ser.close()

    ser = serial.Serial(
        
            port = PORT_NUM,
            baudrate = BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout= COM_TERM

            )
            
    return channel





##########################UI  ###########################################


form = resource_path('vvc.ui')
form_class = QtUiTools.loadUiType(form)[0] #EXE 파일 만들기 위한 선언 방식

dialog = resource_path('vvc_scan.ui')
dialog_class = QtUiTools.loadUiType(dialog)[0] # EXE 파일 만들기 위한 선언 방식



class MyWindow(QMainWindow, form_class):

    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("VVC CONTROLLER")

  
        self.timer = QTimer(self)            
        self.timer.start(100)
        self.timer.timeout.connect(self.inquiry) #1초마다 inquiry가 호출됨

        self.label_14.setText("●")
        
        
        self.pushButton_1.clicked.connect(self.pushButton_1Function)
        self.pushButton_2.clicked.connect(self.pushButton_2Function)
        self.pushButton_3.clicked.connect(self.pushButton_3Function)
        self.pushButton_4.clicked.connect(self.pushButton_4Function)
        self.pushButton_5.clicked.connect(self.pushButton_5Function)
        self.pushButton_6.clicked.connect(self.pushButton_6Function)

        #self.listWidget.itemDoubleClicked.connect(self.select_ch)

        self.lineEdit_1.setValidator(QDoubleValidator(0,9999,1,self))
        self.lineEdit_2.setValidator(QIntValidator(0,9999,self))
        self.lineEdit_3.setValidator(QIntValidator(0,9999,self))

        self.lineEdit_1.returnPressed.connect(self.pushButton_3Function)
        self.lineEdit_2.returnPressed.connect(self.pushButton_4Function)
        self.lineEdit_3.returnPressed.connect(self.pushButton_5Function)


        ###### tool tip #######

        self.lineEdit_1.setToolTip("11.6 ~ 241.9")
        self.lineEdit_2.setToolTip("0 ~ 5400")
        self.lineEdit_3.setToolTip("30 ~ 360")
   



        ###### message box ######
        
        self.msgbox = QDialog()
        self.msgbox_label = QLabel(self.msgbox)
        self.msgbox.setWindowTitle('알림')
        self.msgbox.setWindowModality(Qt.NonModal)
        self.msgbox.resize(200, 80)

        self.msgbox_label.setText("Indexing...")  
        self.msgbox_label.setAlignment(Qt.AlignCenter)
        font2 = self.msgbox_label.font()
        font2.setPointSize(20)
        self.msgbox_label.setFont(font2)
        self.msgbox_label.move (20,15)


        ###### message box ######
        
        self.scaning = QDialog()
        self.scaning_label = QLabel(self.scaning)
        self.scaning.setWindowTitle('알림')
        self.scaning.setWindowModality(Qt.NonModal)
        self.scaning.resize(200, 80)

        self.scaning_label.setText("Scaning...")  
        self.scaning_label.setAlignment(Qt.AlignCenter)
        font1 = self.scaning_label.font()
        font1.setPointSize(20)
        self.scaning_label.setFont(font1)
        self.scaning_label.move (20,15)


        ###### message box ######
        
        self.loading = QDialog()
        self.loading_label = QLabel(self.loading)
        self.loading.setWindowTitle('알림')
        self.loading.setWindowModality(Qt.NonModal)
        self.loading.resize(200, 80)

        self.loading_label.setText("loading...")  
        self.loading_label.setAlignment(Qt.AlignCenter)
        font3 = self.loading_label.font()
        font3.setPointSize(20)
        self.loading_label.setFont(font3)
        self.loading_label.move (20,15)



              

    def pushButton_1Function(self) : #스캔

        global ser
        global port_scan_flag
        
        if LAST_PORT_NUM:

            ser.close()

        port_scan_flag = 1
        self.loading.show()
        
    

    def pushButton_2Function(self) : #오리진

        global RUN

        RUN = 4



    def pushButton_3Function(self): #CAP SET


        global RUN
        global cap

        
        cap = float(format(float(self.lineEdit_1.text()), ".1f"))

        cap = int(cap*10)
        RUN = 1      
        

    def pushButton_4Function(self): #POS SET

        global RUN
        global pos

        pos = int(self.lineEdit_2.text())


        if (pos < 0):
            pos = 0
            RUN = 2


        elif  (POS_MAX < pos):
            pos = POS_MAX
            RUN = 2

        else :
            
            RUN = 2




    def pushButton_5Function(self): #SPEED SET

        global RUN
        global spd
        
        spd = int(self.lineEdit_3.text())


        if (spd < SPD_MIN):
            spd = SPD_MIN
            RUN = 3


        elif  (SPD_MAX < spd):
            spd = SPD_MAX
            RUN = 3

        else :
            
            RUN = 3




    def pushButton_6Function(self): #ch select


        global DEVICE_NUM
        global position
        global capacitance
        global speed
        global err
        global RUN 

        DEVICE_NUM = self.listWidget.currentItem().text() ## 더블클릭
        self.lineEdit_1.clear()
        self.lineEdit_2.clear()
        self.lineEdit_3.clear()
        

        INF = list((DEVICE_NUM+"INF?"+"\r").encode('ascii'))

        ser.write(INF)
        k=ser.readline()

        if not k[6] - 48 :

            RUN = 4

        position = (k[13]-48)*1000+(k[14]-48)*100+(k[15]-48)*10+k[16]-48
        capacitance = ((k[19]-48)*1000+(k[20]-48)*100+(k[21]-48)*10+k[22]-48)/10
        speed = (k[26]-48)*100+(k[27]-48)*10+(k[28]-48)
        err = k[8]-48

    def closeEvent(self, event): # 창닫기 이벤트

         sys.exit()

    def msgboxcloseEvent(msgbox, event): # 창닫기 이벤트

         event.ignore()

    
         
    def inquiry(self) : # 1초마다 gui 업데이트 내용

        global SCAN_STATUS
        global DEVICE_NUM
        global RUN
        global port_scan_flag
        global err_flag

    
        self.LCD_1.display(DEVICE_NUM)

        if port_scan_flag == 2:

            self.loading.close()
            port_scan_flag = 0
            
            subwindow = Config_Dialog()
            subwindow.exec_() 
        

        if DEVICE_NUM == "---":
            self.pushButton_2.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.pushButton_5.setEnabled(False)

            if not CHANNEL :
                self.pushButton_6.setEnabled(False)
                
  

            self.LCD_2.display("---")
            self.LCD_3.display("---")
            self.LCD_4.display("---")

            self.lineEdit_1.setEnabled(False)
            self.lineEdit_2.setEnabled(False)
            self.lineEdit_3.setEnabled(False)



        if (SCAN_STATUS == 1):
            
            self.scaning.show()
            self.pushButton_1.setEnabled(False)
            self.pushButton_2.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.pushButton_5.setEnabled(False)

            

            self.LCD_2.display("---")
            self.LCD_3.display("---")
            self.LCD_4.display("---")

            
     

        if (SCAN_STATUS == 2):
            self.listWidget.clear()
            self.listWidget.addItems(CHANNEL)
            self.pushButton_1.setEnabled(True)
            SCAN_STATUS = 0
            
            DEVICE_NUM = "---"
            self.LCD_2.display("---")
            self.LCD_3.display("---")
            self.LCD_4.display("---")
            
            self.scaning.close()

            self.lineEdit_1.clear()
            self.lineEdit_2.clear()
            self.lineEdit_3.clear()

            self.pushButton_6.setEnabled(True)

            if not CHANNEL:
                QMessageBox.information(self,"알림"," 검색된 채널이 없습니다 \n 포트 재설정 필요 ")
                
    

        if not DEVICE_NUM == "---":
            if not SCAN_STATUS : 
                self.pushButton_1.setEnabled(True)
                self.pushButton_2.setEnabled(True)
                self.pushButton_3.setEnabled(True)
                self.pushButton_4.setEnabled(True)
                self.pushButton_5.setEnabled(True)


                self.LCD_2.display(str(capacitance))
                self.LCD_3.display(str(position))
                self.LCD_4.display(str(speed))

                """


                if not capacitance<=999 :##채널 중복 탐지
                    
                    err_flag = 2
                    DEVICE_NUM = "---"


                """

                


                if not 0<=position<=9999 :
                    
                    err_flag = 2
                    DEVICE_NUM = "---"


                if not 30<=speed<=9999:

                    err_flag = 2
                    DEVICE_NUM = "---"

                
            

       

        if (RUN == 0) :#대기
            if not DEVICE_NUM == "---":

                self.statusBar().showMessage("상태 : 대기"  + "  포트 : " + str (PORT_NUM))
                self.lineEdit_1.setEnabled(True)
                self.lineEdit_2.setEnabled(True)
                self.lineEdit_3.setEnabled(True)

        if (RUN == 1) :#CAP

            
            self.pushButton_1.setEnabled(False)
            self.pushButton_2.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.pushButton_5.setEnabled(False)


            self.statusBar().showMessage("상태 : 동작"  + "  포트 : " + str (PORT_NUM))

        if (RUN == 2) :#POS

            self.pushButton_1.setEnabled(False)
            self.pushButton_2.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.pushButton_5.setEnabled(False)

            self.statusBar().showMessage("상태 : 동작"  + "  포트 : " + str (PORT_NUM))


        if (RUN == 4) :#ORG

    
            self.msgbox.show()
            self.pushButton_1.setEnabled(False)
            self.pushButton_2.setEnabled(False)
            self.pushButton_3.setEnabled(False)
            self.pushButton_4.setEnabled(False)
            self.pushButton_5.setEnabled(False)
            
            self.lineEdit_1.setEnabled(False)
            self.lineEdit_2.setEnabled(False)
            self.lineEdit_3.setEnabled(False)

            self.LCD_2.display("---")
            self.LCD_3.display("---")
            self.LCD_4.display("---")
    
            self.statusBar().showMessage("상태 : Indexing"  + "  포트 : " + str (PORT_NUM))

        if (RUN == 5 ) :#ORG 완료

            self.msgbox.close()
            self.lineEdit_1.clear()
            self.lineEdit_2.clear()
            self.lineEdit_3.clear()
            RUN = 0



        if err_flag == 1 :# 통신 에러

            err_flag = 0
            

            QMessageBox.information(self,"알림","통신에러")

        if err_flag == 2 :# 통신 에러

            err_flag = 0
            self.pushButton_1.setEnabled(True)

            QMessageBox.information(self,"알림"," 채널 중복 발견 \n 채널 설정 요망 ")

        if err == 0 :
            self.label_14.setStyleSheet("color: #41E881; border-style: solid;")## 초록색 41E881

        if err == 1:
            self.label_14.setStyleSheet("color: #FF5733; border-style: solid;")## 빨간색 FF5733

    

        
                        
    

###########################통신설정 서브 다이얼로그###########################################



class Config_Dialog(QDialog, dialog_class):


    def __init__(self) :

        
        
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("SCAN")


        self.cb1.addItems(port)
        self.cb2.addItem("9600")
        
        
        if LAST_PORT_NUM : 
            self.cb1.setCurrentText(LAST_PORT_NUM)


        self.btnOK.clicked.connect(self.onOKButtonClicked)

        

        
    def onOKButtonClicked(self):


        global SCAN_STATUS
        global PORT_NUM
        global LAST_PORT_NUM
        global BAUD_RATE
        global ser


        LAST_PORT_NUM = self.cb1.currentText()
        PORT_NUM = self.cb1.currentText()
        BAUD_RATE = int(self.cb2.currentText())

            
        ser = serial.Serial(
        
            port = PORT_NUM,
            baudrate = BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout= SCAN_TERM

            )
        SCAN_STATUS = 1
    
        self.accept()
        


    def closeEvent(self, event): # 창닫기 이벤트


        global ser
            
        if LAST_PORT_NUM:
            ser.open()
        
        


#########################  통신 클래스  설정  ########################################



##########################  INIT_UI    ########################


def UI_Thread():

    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())

def start_UI_Thread():
    
    thread = threading.Thread(target=UI_Thread)
    thread.daemon = True
    thread.start()

start_UI_Thread()  #init UI THREAD


########################  INIT_MAINLOOP  ##################################


def main_loop():

    global CHANNEL
    global SCAN_STATUS

    global position
    global capacitance
    global speed

    global err
    global RUN

    global port_scan_flag
    global port

    global err_flag


    if port_scan_flag == 1:

        port = serial_ports()
        port_scan_flag = 2
        

    if (SCAN_STATUS == 1) :

        CHANNEL = scan_ch()
        SCAN_STATUS = 2


    if RUN == 1 :

        CAP = list((DEVICE_NUM+"CAP"+format(cap,'05')+"\r").encode('ascii'))
        INF = list((DEVICE_NUM+"INF?"+"\r").encode('ascii'))

        ser.write(CAP)
        k = ser.readline()

        while True:
            ser.write(INF)
            k=ser.readline()
            
            if k :
                position = (k[13]-48)*1000+(k[14]-48)*100+(k[15]-48)*10+k[16]-48
                capacitance = ((k[19]-48)*1000+(k[20]-48)*100+(k[21]-48)*10+k[22]-48)/10
                speed = (k[26]-48)*100+(k[27]-48)*10+(k[28]-48)
                err = k[8]-48
                if (k[7] == 48): #motor stop
                    RUN = 0
                    break


            else :
                err_flag = 1
                RUN = 0
                break

    if RUN == 2 :

        POS = list((DEVICE_NUM+"POS"+format(pos,'05')+"\r").encode('ascii'))
        INF = list((DEVICE_NUM+"INF?"+"\r").encode('ascii'))

        ser.write(POS)
        k = ser.readline()

        while True:
            ser.write(INF)
            k=ser.readline()

            if k :
                position = (k[13]-48)*1000+(k[14]-48)*100+(k[15]-48)*10+k[16]-48
                capacitance = ((k[19]-48)*1000+(k[20]-48)*100+(k[21]-48)*10+k[22]-48)/10
                speed = (k[26]-48)*100+(k[27]-48)*10+(k[28]-48)
                err = k[8]-48
                if (k[7] == 48): #motor stop
                    RUN = 0
                    break

            else :
                err_flag = 1
                RUN = 0
                break

            

    if RUN == 3 :

        SPD = list((DEVICE_NUM+"SPD"+format(spd,'05')+"\r").encode('ascii'))
        INF = list((DEVICE_NUM+"INF?"+"\r").encode('ascii'))
 
        ser.write(SPD)
        k = ser.readline()

        while True:
            ser.write(INF)
            k=ser.readline()

            if k:
                position = (k[13]-48)*1000+(k[14]-48)*100+(k[15]-48)*10+k[16]-48
                capacitance = ((k[19]-48)*1000+(k[20]-48)*100+(k[21]-48)*10+k[22]-48)/10
                speed = (k[26]-48)*100+(k[27]-48)*10+(k[28]-48)
                err = k[8]-48
                if (k[7] == 48): #motor stop
                    RUN = 0
                    break

            else :
                err_flag = 1
                RUN = 0
                break




    if RUN == 4 :

        ORG = list((DEVICE_NUM+"ORG"+"\r").encode('ascii'))
        INF = list((DEVICE_NUM+"INF?"+"\r").encode('ascii'))

        ser.write(ORG)  # INITIATE ORIGIN
        k = ser.readline()

        if k :

            while True:

                ser.write(INF)
                k=ser.readline()
               
                if len(k) == 31:

                    if (k[6] == 49):  ### 인덱싱 끝낫음  1 (응답 시작)
                        position = (k[13]-48)*1000+(k[14]-48)*100+(k[15]-48)*10+k[16]-48
                        capacitance = ((k[19]-48)*1000+(k[20]-48)*100+(k[21]-48)*10+k[22]-48)/10
                        speed = (k[26]-48)*100+(k[27]-48)*10+(k[28]-48)
                        err = k[8]-48
                        RUN = 5
                        break

        else :

            err_flag = 1
            RUN = 0
            


############################init main loop ######################

while(1):
    main_loop()








