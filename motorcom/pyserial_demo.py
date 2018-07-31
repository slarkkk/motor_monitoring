# -*- coding: utf-8 -*-
import sys
import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from ui_demo_1 import Ui_Form
import os
import binascii
import crcmod.predefined
import struct
import time


#485通信OOP
class RS485data(object):
    def __init__(self):
        self.Address = '01'
        self.Function = '03'
        self.dataAddr = '0000'
        self.Numdata = '0000'
        self.CRC = '0000'

    def getAddress(self,Address):
        self.Address = Address
    def getFunction(self,Function):
        self.Function = Function
    def getdataAddr(self,dataAddr):
        self.dataAddr=dataAddr
    def getNumdata(self,Numdata):
        self.Numdata = Numdata
    def getCRC(self,CRC):
        self.CRC = CRC
    def getdata(self,data):
        self.data = data

#CRC校验oop
class CRCGenerator(object):

    def __init__(self):
        # crcmod is a module for crc algrithms in python
        # It concludes the modules like crc-8,crc-16...
        # you can refer to the website below:
        # http://crcmod.sourceforge.net/crcmod.predefined.html
        self.module = 'modbus'

    def create(self, input):
        crc16 = crcmod.predefined.Crc(self.module)
        hexData = input
        hexData = binascii.unhexlify(hexData)
        crc16.update(hexData)
        out = [hex(i)for i in struct.pack('<i',(crc16.crcValue))]
        out = str(out[0]).replace('0x','').upper().zfill(2)+" "+str(out[1]).replace('0x','').upper().zfill(2)
        return out
#界面OOP
class Pyqt5_Serial(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(Pyqt5_Serial, self).__init__()
        self.setupUi(self)
        self.init()
        self.setWindowTitle("串口小助手")
        self.ser = serial.Serial()
        self.port_check()

        # 接收数据和发送数据数目置零
        self.data_num_received = 0
        self.lineEdit.setText(str(self.data_num_received))
        self.data_num_sended = 0
        self.lineEdit_2.setText(str(self.data_num_sended))

    def init(self):
        # 串口检测按钮
        self.s1__box_1.clicked.connect(self.port_check)

        # 串口信息显示
        self.s1__box_2.currentTextChanged.connect(self.port_imf)

        # 打开串口按钮
        self.open_button.clicked.connect(self.port_open)

        # 关闭串口按钮
        self.close_button.clicked.connect(self.port_close)


        #监控信息1按钮
        self.s3__send_button_3.clicked.connect(self.readinfo_1)

        # 发送数据按钮
        self.send_SET.clicked.connect(self.send_set)

        # 定时器接收数据
        self.timer = QTimer(self)
       # self.timer.timeout.connect(self.data_receive)

        # 定时发送数据
        self.timer_send = QTimer()
        self.timer_send.timeout.connect(self.readinfo_1)
        self.polling.stateChanged.connect(self.data_send_polling)


    # 串口检测
    def port_check(self):
        # 检测所有存在的串口，将信息存储在字典中
        self.Com_Dict = {}
        port_list = list(serial.tools.list_ports.comports())
        self.s1__box_2.clear()
        for port in port_list:
            self.Com_Dict["%s" % port[0]] = "%s" % port[1]
            self.s1__box_2.addItem(port[0])
        if len(self.Com_Dict) == 0:
            self.state_label.setText(" 无串口")

    # 串口信息
    def port_imf(self):
        # 显示选定的串口的详细信息
        imf_s = self.s1__box_2.currentText()
        if imf_s != "":
            self.state_label.setText(self.Com_Dict[self.s1__box_2.currentText()])

    # 打开串口
    def port_open(self):
        self.ser.port = self.s1__box_2.currentText()
        self.ser.baudrate = int(self.s1__box_3.currentText())
        self.ser.bytesize = int(self.s1__box_4.currentText())
        self.ser.stopbits = int(self.s1__box_6.currentText())
        self.ser.parity = self.s1__box_5.currentText()
        self.ser.timeout=0.5
        try:
            self.ser.open()
        except:
            QMessageBox.critical(self, "Port Error", "此串口不能被打开！")
            return None

        # 打开串口接收定时器，周期为2ms
        self.timer.start(2)

        if self.ser.isOpen():
            self.open_button.setEnabled(False)
            self.close_button.setEnabled(True)
            self.formGroupBox1.setTitle("串口状态（已开启）")

    # 关闭串口
    def port_close(self):
        self.timer.stop()
        self.timer_send.stop()
        try:
            self.ser.close()
        except:
            pass
        self.open_button.setEnabled(True)
        self.close_button.setEnabled(False)
        self.pollingtime.setEnabled(True)
        # 接收数据和发送数据数目置零
        self.data_num_received = 0
        self.lineEdit.setText(str(self.data_num_received))
        self.data_num_sended = 0
        self.lineEdit_2.setText(str(self.data_num_sended))
        self.formGroupBox1.setTitle("串口状态（已关闭）")

    #CRC校验
    def send_check(self):
        try:
            input_s =  self.s3__send_text.toPlainText()
            if input_s !="":
                input_data = input_s.replace(' ','')
                crc = CRCGenerator()
                check_data=crc.create(input_data)
            self.lineEdit_5.setText(str(check_data))
        except:
            QMessageBox.critical(self, "CRC Error", "校验失败,请检查是否是十六进制")
            return None

    #发送配置信息
    def send_set(self):
        if self.ser.isOpen():
            crc=CRCGenerator()
            input_s = self.Identity.text()
            if input_s == "":
                QMessageBox.critical(self, 'information lost', '请输入设备号')
            else:
                input_s = input_s+'102000000F10'
            input_s = input_s+hex(int(self.lineEdit_7.text())).replace('0x','').zfill(4)
            input_s = input_s+hex(int(self.lineEdit_6.text())*100).replace('0x','').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_4.text())*100).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_8.text())*10).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_9.text()) * 10).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_10.text()) * 10).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_11.text()) * 10).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_12.text()) * 10).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_13.text()) * 10).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_14.text()) * 100).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_15.text()) * 100).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_16.text())).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_17.text())).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_18.text())).replace('0x', '').zfill(4)
            input_s = input_s + hex(int(self.lineEdit_19.text())).replace('0x', '').zfill(4)
            docrc = input_s
            input_s = input_s + " " + crc.create(docrc)
            input_s = input_s.strip()
            send_list = []
            while input_s != '':
                try:
                    num = int(input_s[0:2], 16)
                except ValueError:
                    QMessageBox.critical(self, 'wrong data', '数据有误')
                    return None
                input_s = input_s[2:].strip()
                send_list.append(num)
            input_s = bytes(send_list)
            num = self.ser.write(input_s)
            self.data_num_sended += num
            self.lineEdit_2.setText(str(self.data_num_sended))
        else:
            QMessageBox.critical(self,'port error','请打开串口')
            return None
    #监控信息1
    def readinfo_1(self):
        if self.ser.isOpen():
            crc = CRCGenerator()
            ALL_data = RS485data()
            for send_i in range(0,9):
                if send_i == 0:
                    input_s = self.Identity.text()
                    if input_s == "":
                        QMessageBox.critical(self, 'information lost', '请输入设备号')
                    else:
                        input_s = input_s + " 03 21 09 00 04"
                        docrc = input_s.replace(' ','')
                        input_s = input_s +" " + crc.create(docrc)
                        input_s = input_s.strip()
                        send_list = []
                        while input_s != '':
                            try:
                                num = int(input_s[0:2], 16)
                            except ValueError:
                                QMessageBox.critical(self, 'wrong data', '数据有误')
                                return None
                            input_s = input_s[2:].strip()
                            send_list.append(num)
                        input_s = bytes(send_list)
                        num = self.ser.write(input_s)
                        self.data_num_sended += num
                        self.lineEdit_2.setText(str(self.data_num_sended))
                    try:
                        time.sleep(0.05)
                        num_r = self.ser.inWaiting()
                    except:
                        self.port_close()
                        return None
                    if num_r > 0:
                        data = self.ser.read(num_r)
                        num_r = len(data)
                        out_s = ''
                        for i in range(0, len(data)):
                            out_s = out_s + '{:02X}'.format(data[i]) + ' '
                        # 统计接收字符的数量
                        self.data_num_received += num_r
                        self.lineEdit.setText(str(self.data_num_received))
                        try:
                            info_list = out_s.split(' ')

                            ALL_data.getAddress(info_list[0])
                            ALL_data.getFunction(info_list[1])
                            ALL_data.getNumdata(info_list[2])
                            ALL_data.getCRC(info_list[num_r - 2] + " " + info_list[num_r - 1])
                            if ALL_data.Function == '03':
                                length = int(ALL_data.Numdata)
                                data_address = []
                                checkdata = ''
                                for i in range(0, length):
                                    if (i + 1) % 2 == 0:
                                        data_address.append(info_list[2 + i] + info_list[3 + i])
                                for i in range(0, len(info_list) - 3):
                                    checkdata = checkdata + info_list[i]
                                crc_1 = CRCGenerator()
                                if crc_1.create(checkdata) != ALL_data.CRC:
                                    QMessageBox.critical(self, 'crc wrong', '数据传输有误!')
                                # 将电机信息填入
                                try:
                                    self.max_cur.setText('%.1f' % (int(data_address[0], 16) / 10))
                                    self.max_volt.setText(str(int(data_address[1], 16)))
                                    self.max_temper.setText(str(int(data_address[2], 16)))
                                    self.min_volt.setText(str(int(data_address[3], 16)))

                                except:
                                    QMessageBox.critical(self, 'print wrong', '填入出错了!')
                                    return None
                            else:
                                pass
                        except:
                            QMessageBox.critical(self, 'print wrong', '数据显示出错了!')
                            return None
                    else:
                        QMessageBox.critical(self, 'receive wrong', '本次发送没有接受到返回信息!')
                        return None
                elif send_i == 1:
                    input_s = self.Identity.text()
                    if input_s == "":
                        QMessageBox.critical(self, 'information lost', '请输入设备号')
                    else:
                        input_s = input_s + " 03 21 10 00 08"
                        docrc = input_s.replace(' ','')
                        input_s = input_s +" " + crc.create(docrc)
                        input_s = input_s.strip()
                        send_list = []
                        while input_s != '':
                            try:
                                num = int(input_s[0:2], 16)
                            except ValueError:
                                QMessageBox.critical(self, 'wrong data', '数据有误')
                                return None
                            input_s = input_s[2:].strip()
                            send_list.append(num)
                        input_s = bytes(send_list)
                        num = self.ser.write(input_s)
                        self.data_num_sended += num
                        self.lineEdit_2.setText(str(self.data_num_sended))
                    try:
                        time.sleep(0.05)
                        num_r = self.ser.inWaiting()
                    except:
                        self.port_close()
                        return None
                    if num_r > 0:
                        data = self.ser.read(num_r)
                        num_r = len(data)
                        out_s = ''
                        for i in range(0, len(data)):
                            out_s = out_s + '{:02X}'.format(data[i]) + ' '
                        # 统计接收字符的数量
                        self.data_num_received += num_r
                        self.lineEdit.setText(str(self.data_num_received))
                        try:
                            info_list = out_s.split(' ')
                            ALL_data.getAddress(info_list[0])
                            ALL_data.getFunction(info_list[1])
                            ALL_data.getNumdata(int(info_list[2],16))
                            ALL_data.getCRC(info_list[num_r - 2] + " " + info_list[num_r - 1])
                            if ALL_data.Function == '03':
                                length = int(ALL_data.Numdata)
                                data_address = []
                                checkdata = ''
                                for i in range(0, length):
                                    if (i + 1) % 2 == 0:
                                        data_address.append(info_list[2 + i] + info_list[3 + i])
                                for i in range(0, len(info_list) - 3):
                                    checkdata = checkdata + info_list[i]
                                crc_1 = CRCGenerator()
                                if crc_1.create(checkdata) != ALL_data.CRC:
                                    QMessageBox.critical(self, 'crc wrong', '数据传输有误!')
                                # 将电机信息填入
                                try:
                                    self.setFreq.setText('%.2f' % (int(data_address[0], 16) / 100))
                                    self.outFreq.setText('%.2f' %(int(data_address[1], 16)/100))
                                    self.outCur_2.setText('%.1f' %(int(data_address[2], 16)/10))
                                    self.inVolt.setText(str(int(data_address[3], 16)))
                                    self.outVolt.setText(str(int(data_address[4],16)))
                                    self.motorspd_t.setText('%.1f' %(int(data_address[5],16)/10))
                                    self.busVolt.setText(str(int(data_address[6],16)))
                                    self.outPower.setText('%.1f' %(int(data_address[7], 16)/10))
                                except:
                                    QMessageBox.critical(self, 'print wrong', '填入出错了!')
                                    return None
                            else:
                                pass
                        except:
                            QMessageBox.critical(self, 'print wrong', '数据显示出错了!')
                            return None
                    else:
                        QMessageBox.critical(self, 'receive wrong', '本次发送没有接受到返回信息!')
                elif send_i == 2:
                    input_s = self.Identity.text()
                    if input_s == "":
                        QMessageBox.critical(self, 'information lost', '请输入设备号')
                    else:
                        input_s = input_s + " 03 21 18 00 06"
                        docrc = input_s.replace(' ', '')
                        input_s = input_s + " " + crc.create(docrc)
                        input_s = input_s.strip()
                        send_list = []
                        while input_s != '':
                            try:
                                num = int(input_s[0:2], 16)
                            except ValueError:
                                QMessageBox.critical(self, 'wrong data', '数据有误')
                                return None
                            input_s = input_s[2:].strip()
                            send_list.append(num)
                        input_s = bytes(send_list)
                        num = self.ser.write(input_s)
                        self.data_num_sended += num
                        self.lineEdit_2.setText(str(self.data_num_sended))
                    try:
                        time.sleep(0.05)
                        num_r = self.ser.inWaiting()
                    except:
                        self.port_close()
                        return None
                    if num_r > 0:
                        data = self.ser.read(num_r)
                        num_r = len(data)
                        out_s = ''
                        for i in range(0, len(data)):
                            out_s = out_s + '{:02X}'.format(data[i]) + ' '
                        # 统计接收字符的数量
                        self.data_num_received += num_r
                        self.lineEdit.setText(str(self.data_num_received))
                        print(out_s)
                        try:
                            info_list = out_s.split(' ')
                            ALL_data.getAddress(info_list[0])
                            ALL_data.getFunction(info_list[1])
                            ALL_data.getNumdata(int(info_list[2],16))
                            ALL_data.getCRC(info_list[num_r - 2] + " " + info_list[num_r - 1])
                            if ALL_data.Function == '03':
                                length = int(ALL_data.Numdata)
                                data_address = []
                                checkdata = ''
                                for i in range(0, length):
                                    if (i + 1) % 2 == 0:
                                        data_address.append(info_list[2 + i] + info_list[3 + i])
                                for i in range(0, len(info_list) - 3):
                                    checkdata = checkdata + info_list[i]
                                crc_1 = CRCGenerator()
                                if crc_1.create(checkdata) != ALL_data.CRC:
                                    QMessageBox.critical(self, 'crc wrong', '数据传输有误!')
                                # 将电机信息填入
                                try:
                                    self.temper1.setText(str(int(data_address[0], 16) ))
                                    self.temper2.setText(str (int(data_address[1], 16) ))
                                    self.setTor.setText(str(int(data_address[2], 16) ))
                                    self.outTor.setText(str(int(data_address[3], 16)))
                                    self.setPID.setText('%.1f'%(int(data_address[4], 16)/10))
                                    self.backPID.setText('%.1f' % (int(data_address[5], 16) / 10))
                                except:
                                    QMessageBox.critical(self, 'print wrong', '填入出错了!')
                                    return None
                            else:
                                pass
                        except:
                            QMessageBox.critical(self, 'print wrong', '数据显示出错了!')
                            return None
                    else:
                        QMessageBox.critical(self, 'receive wrong', '本次发送没有接受到返回信息!')
                elif send_i == 3:
                    input_s = self.Identity.text()
                    if input_s == "":
                        QMessageBox.critical(self, 'information lost', '请输入设备号')
                    else:
                        input_s = input_s + " 03 21 1E 00 06"
                        docrc = input_s.replace(' ', '')
                        input_s = input_s + " " + crc.create(docrc)
                        input_s = input_s.strip()
                        send_list = []
                        while input_s != '':
                            try:
                                num = int(input_s[0:2], 16)
                            except ValueError:
                                QMessageBox.critical(self, 'wrong data', '数据有误')
                                return None
                            input_s = input_s[2:].strip()
                            send_list.append(num)
                        input_s = bytes(send_list)
                        num = self.ser.write(input_s)
                        self.data_num_sended += num
                        self.lineEdit_2.setText(str(self.data_num_sended))
                    try:
                        time.sleep(0.05)
                        num_r = self.ser.inWaiting()
                    except:
                        self.port_close()
                        return None
                    if num_r > 0:
                        data = self.ser.read(num_r)
                        num_r = len(data)
                        out_s = ''
                        for i in range(0, len(data)):
                            out_s = out_s + '{:02X}'.format(data[i]) + ' '
                        # 统计接收字符的数量
                        self.data_num_received += num_r
                        self.lineEdit.setText(str(self.data_num_received))
                        try:
                            info_list = out_s.split(' ')
                            ALL_data.getAddress(info_list[0])
                            ALL_data.getFunction(info_list[1])
                            ALL_data.getNumdata(int(info_list[2],16))
                            ALL_data.getCRC(info_list[num_r - 2] + " " + info_list[num_r - 1])
                            if ALL_data.Function == '03':
                                length = int(ALL_data.Numdata)
                                data_address = []
                                checkdata = ''
                                for i in range(0, length):
                                    if (i + 1) % 2 == 0:
                                        data_address.append(info_list[2 + i] + info_list[3 + i])
                                for i in range(0, len(info_list) - 3):
                                    checkdata = checkdata + info_list[i]
                                crc_1 = CRCGenerator()
                                if crc_1.create(checkdata) != ALL_data.CRC:
                                    QMessageBox.critical(self, 'crc wrong', '数据传输有误!')
                                # 将电机信息填入
                                try:
                                    self.xState.setText(str(int(data_address[0], 16) ))
                                    self.yState.setText(str (int(data_address[1], 16) ))
                                    self.AI_1.setText('%.2f'%(int(data_address[2], 16)/100))
                                    self.AI_2.setText('%.2f'%(int(data_address[3], 16)/100))
                                    self.AI_3.setText('%.2f'%(int(data_address[4], 16)/100))
                                    self.HDO.setText('%.3f'%(int(data_address[5], 16)/1000))
                                except:
                                    QMessageBox.critical(self, 'print wrong', '填入出错了!')
                                    return None
                            else:
                                pass
                        except:
                            QMessageBox.critical(self, 'print wrong', '数据显示出错了!')
                            return None
                    else:
                        QMessageBox.critical(self, 'receive wrong', '本次发送没有接受到返回信息!')
                elif send_i == 4:
                    input_s = self.Identity.text()
                    if input_s == "":
                        QMessageBox.critical(self, 'information lost', '请输入设备号')
                    else:
                        input_s = input_s + " 03 21 27 00 04"
                        docrc = input_s.replace(' ', '')
                        input_s = input_s + " " + crc.create(docrc)
                        input_s = input_s.strip()
                        send_list = []
                        while input_s != '':
                            try:
                                num = int(input_s[0:2], 16)
                            except ValueError:
                                QMessageBox.critical(self, 'wrong data', '数据有误')
                                return None
                            input_s = input_s[2:].strip()
                            send_list.append(num)
                        input_s = bytes(send_list)
                        num = self.ser.write(input_s)
                        self.data_num_sended += num
                        self.lineEdit_2.setText(str(self.data_num_sended))
                    try:
                        time.sleep(0.05)
                        num_r = self.ser.inWaiting()
                    except:
                        self.port_close()
                        return None
                    if num_r > 0:
                        data = self.ser.read(num_r)
                        num_r = len(data)
                        out_s = ''
                        for i in range(0, len(data)):
                            out_s = out_s + '{:02X}'.format(data[i]) + ' '
                        # 统计接收字符的数量
                        self.data_num_received += num_r
                        self.lineEdit.setText(str(self.data_num_received))
                        try:
                            info_list = out_s.split(' ')
                            ALL_data.getAddress(info_list[0])
                            ALL_data.getFunction(info_list[1])
                            ALL_data.getNumdata(int(info_list[2],16))
                            ALL_data.getCRC(info_list[num_r - 2] + " " + info_list[num_r - 1])
                            if ALL_data.Function == '03':
                                length = int(ALL_data.Numdata)
                                data_address = []
                                checkdata = ''
                                for i in range(0, length):
                                    if (i + 1) % 2 == 0:
                                        data_address.append(info_list[2 + i] + info_list[3 + i])
                                for i in range(0, len(info_list) - 3):
                                    checkdata = checkdata + info_list[i]
                                crc_1 = CRCGenerator()
                                if crc_1.create(checkdata) != ALL_data.CRC:
                                    QMessageBox.critical(self, 'crc wrong', '数据传输有误!')
                                # 将电机信息填入
                                try:
                                    self.counter1.setText(str(int(data_address[0], 16) ))
                                    self.runTime.setText('%.1f'% (int(data_address[1], 16)/10))
                                    self.runTimeAll.setText(str(int(data_address[2], 16)))
                                    self.runTimeAll_1.setText(str(int(data_address[3], 16)))

                                except:
                                    QMessageBox.critical(self, 'print wrong', '填入出错了!')
                                    return None
                            else:
                                pass
                        except:
                            QMessageBox.critical(self, 'print wrong', '数据显示出错了!')
                            return None
                    else:
                        QMessageBox.critical(self, 'receive wrong', '本次发送没有接受到返回信息!')
                elif send_i == 5:
                    input_s = self.Identity.text()
                    if input_s == "":
                        QMessageBox.critical(self, 'information lost', '请输入设备号')
                    else:
                        input_s = input_s + " 03 21 2B 00 04"
                        docrc = input_s.replace(' ', '')
                        input_s = input_s + " " + crc.create(docrc)
                        input_s = input_s.strip()
                        send_list = []
                        while input_s != '':
                            try:
                                num = int(input_s[0:2], 16)
                            except ValueError:
                                QMessageBox.critical(self, 'wrong data', '数据有误')
                                return None
                            input_s = input_s[2:].strip()
                            send_list.append(num)
                        input_s = bytes(send_list)
                        num = self.ser.write(input_s)
                        self.data_num_sended += num
                        self.lineEdit_2.setText(str(self.data_num_sended))
                    try:
                        time.sleep(0.05)
                        num_r = self.ser.inWaiting()
                    except:
                        self.port_close()
                        return None
                    if num_r > 0:
                        data = self.ser.read(num_r)
                        num_r = len(data)
                        out_s = ''
                        for i in range(0, len(data)):
                            out_s = out_s + '{:02X}'.format(data[i]) + ' '
                        # 统计接收字符的数量
                        self.data_num_received += num_r
                        self.lineEdit.setText(str(self.data_num_received))
                        try:
                            info_list = out_s.split(' ')
                            ALL_data.getAddress(info_list[0])
                            ALL_data.getFunction(info_list[1])
                            ALL_data.getNumdata(info_list[2])
                            ALL_data.getCRC(info_list[num_r - 2] + " " + info_list[num_r - 1])
                            if ALL_data.Function == '03':
                                length = int(ALL_data.Numdata)
                                data_address = []
                                checkdata = ''
                                for i in range(0, length):
                                    if (i + 1) % 2 == 0:
                                        data_address.append(info_list[2 + i] + info_list[3 + i])
                                for i in range(0, len(info_list) - 3):
                                    checkdata = checkdata + info_list[i]
                                crc_1 = CRCGenerator()
                                if crc_1.create(checkdata) != ALL_data.CRC:
                                    QMessageBox.critical(self, 'crc wrong', '数据传输有误!')
                                # 将电机信息填入
                                try:
                                    self.powerLevel.setText('%.1f' % (int(data_address[0], 16)/10))
                                    self.voltLevel.setText(str(int(data_address[1], 16)))
                                    self.curLevel.setText('%.1f'%(int(data_address[2], 16)/10))
                                    self.version.setText(str(int(data_address[3], 16)))

                                except:
                                    QMessageBox.critical(self, 'print wrong', '填入出错了!')
                                    return None
                            else:
                                pass
                        except:
                            QMessageBox.critical(self, 'print wrong', '数据显示出错了!')
                            return None
                    else:
                        QMessageBox.critical(self, 'receive wrong', '本次发送没有接受到返回信息!')
                elif send_i == 6:
                    input_s = self.Identity.text()
                    if input_s == "":
                        QMessageBox.critical(self, 'information lost', '请输入设备号')
                    else:
                        input_s = input_s + " 03 21 2F 00 08"
                        docrc = input_s.replace(' ', '')
                        input_s = input_s + " " + crc.create(docrc)
                        input_s = input_s.strip()
                        send_list = []
                        while input_s != '':
                            try:
                                num = int(input_s[0:2], 16)
                            except ValueError:
                                QMessageBox.critical(self, 'wrong data', '数据有误')
                                return None
                            input_s = input_s[2:].strip()
                            send_list.append(num)
                        input_s = bytes(send_list)
                        num = self.ser.write(input_s)
                        self.data_num_sended += num
                        self.lineEdit_2.setText(str(self.data_num_sended))
                    try:
                        time.sleep(0.05)
                        num_r = self.ser.inWaiting()
                    except:
                        self.port_close()
                        return None
                    if num_r > 0:
                        data = self.ser.read(num_r)
                        num_r = len(data)
                        out_s = ''
                        for i in range(0, len(data)):
                            out_s = out_s + '{:02X}'.format(data[i]) + ' '
                        # 统计接收字符的数量
                        self.data_num_received += num_r
                        self.lineEdit.setText(str(self.data_num_received))
                        try:
                            info_list = out_s.split(' ')
                            ALL_data.getAddress(info_list[0])
                            ALL_data.getFunction(info_list[1])
                            ALL_data.getNumdata(int(info_list[2],16))
                            ALL_data.getCRC(info_list[num_r - 2] + " " + info_list[num_r - 1])
                            if ALL_data.Function == '03':
                                length = int(ALL_data.Numdata)
                                data_address = []
                                checkdata = ''
                                for i in range(0, length):
                                    if (i + 1) % 2 == 0:
                                        data_address.append(info_list[2 + i] + info_list[3 + i])
                                for i in range(0, len(info_list) - 3):
                                    checkdata = checkdata + info_list[i]
                                crc_1 = CRCGenerator()
                                if crc_1.create(checkdata) != ALL_data.CRC:
                                    QMessageBox.critical(self, 'crc wrong', '数据传输有误!')
                                # 将电机信息填入
                                try:
                                    self.excite.setText('%.1f' % (int(data_address[0], 16)/10))
                                    self.PGback.setText('%.2f'%(int(data_address[1], 16)/100))
                                    self.motorTor.setText(str(int(data_address[2], 16)))
                                    self.setTension.setText(str(int(data_address[3], 16)))
                                    self.rollNow.setText(str(int(data_address[4],16)))
                                    self.spdNow.setText('%.1f'%(int(data_address[5],16)/10))
                                    self.firstRollTime.setText(str(int(data_address[6],16)))
                                    self.rollInit.setText(str(int(data_address[7],16)))
                                except:
                                    QMessageBox.critical(self, 'print wrong', '填入出错了!')
                                    return None
                            else:
                                pass
                        except:
                            QMessageBox.critical(self, 'print wrong', '数据显示出错了!')
                            return None
                    else:
                        QMessageBox.critical(self, 'receive wrong', '本次发送没有接受到返回信息!')
                elif send_i == 7:
                    input_s = self.Identity.text()
                    if input_s == "":
                        QMessageBox.critical(self, 'information lost', '请输入设备号')
                    else:
                        input_s = input_s + " 03 21 00 00 03"
                        docrc = input_s.replace(' ', '')
                        input_s = input_s + " " + crc.create(docrc)
                        input_s = input_s.strip()
                        send_list = []
                        while input_s != '':
                            try:
                                num = int(input_s[0:2], 16)
                            except ValueError:
                                QMessageBox.critical(self, 'wrong data', '数据有误')
                                return None
                            input_s = input_s[2:].strip()
                            send_list.append(num)
                        input_s = bytes(send_list)
                        num = self.ser.write(input_s)
                        self.data_num_sended += num
                        self.lineEdit_2.setText(str(self.data_num_sended))
                    try:
                        time.sleep(0.05)
                        num_r = self.ser.inWaiting()
                    except:
                        self.port_close()
                        return None
                    if num_r > 0:
                        data = self.ser.read(num_r)
                        num_r = len(data)
                        out_s = ''
                        for i in range(0, len(data)):
                            out_s = out_s + '{:02X}'.format(data[i]) + ' '
                        # 统计接收字符的数量
                        self.data_num_received += num_r
                        self.lineEdit.setText(str(self.data_num_received))
                        try:
                            info_list = out_s.split(' ')
                            ALL_data.getAddress(info_list[0])
                            ALL_data.getFunction(info_list[1])
                            ALL_data.getNumdata(info_list[2])
                            ALL_data.getCRC(info_list[num_r - 2] + " " + info_list[num_r - 1])
                            if ALL_data.Function == '03':
                                length = int(ALL_data.Numdata)
                                data_address = []
                                checkdata = ''
                                for i in range(0, length):
                                    if (i + 1) % 2 == 0:
                                        data_address.append(info_list[2 + i] + info_list[3 + i])
                                for i in range(0, len(info_list) - 3):
                                    checkdata = checkdata + info_list[i]
                                crc_1 = CRCGenerator()
                                if crc_1.create(checkdata) != ALL_data.CRC:
                                    QMessageBox.critical(self, 'crc wrong', '数据传输有误!')
                                # 将电机信息填入
                                try:
                                    if int(data_address[0])==0:
                                        self.runState.setText('运行中')
                                    elif int(data_address[0])==1:
                                        self.runState.setText('反向运行')
                                    elif int(data_address[0])==2:
                                        self.runState.setText('变频器准备好')
                                    elif int(data_address[0])==3:
                                        self.runState.setText('故障')
                                    elif int(data_address[0])==4:
                                        self.runState.setText('点动状态')
                                    elif int(data_address[0])==5:
                                        self.runState.setText('预报警')
                                    elif int(data_address[0])==6:
                                        self.runState.setText('自学习中')
                                    else:
                                        self.runState.setText('NC')
                                    if int(data_address[1])==1:
                                        self.faultType.setText('运行欠压')
                                    elif int(data_address[1])==2:
                                        self.faultType.setText('输出短路')
                                    elif int(data_address[1])==3:
                                        self.faultType.setText('输出过电流')
                                    elif int(data_address[1])==4:
                                        self.faultType.setText('主回路过压')
                                    elif int(data_address[1])==5:
                                        self.faultType.setText('散热器过热 95度')
                                    elif int(data_address[1])==6:
                                        self.faultType.setText('散热器过热 105度')
                                    elif int(data_address[1])==7:
                                        self.faultType.setText('电机过载')
                                    elif int(data_address[1])==8:
                                        self.faultType.setText('变频器过载')
                                    elif int(data_address[1])==9:
                                        self.faultType.setText('电流超限故障')
                                    elif int(data_address[1],16)==10:
                                        self.faultType.setText('来自485的外部故障')
                                    elif int(data_address[1],16)==11:
                                        self.faultType.setText('来自端子的故障输入')
                                    elif int(data_address[1],16)==12:
                                        self.faultType.setText('输入缺相')
                                    elif int(data_address[1],16)==13:
                                        self.faultType.setText('输出缺相')
                                    elif int(data_address[1],16)==14:
                                        self.faultType.setText('485通讯故障')
                                    elif int(data_address[1],16)==15:
                                        self.faultType.setText('自学习失败故障')
                                    elif int(data_address[1],16)==16:
                                        self.faultType.setText('存储器故障')
                                    elif int(data_address[1],16)==17:
                                        self.faultType.setText('LC1输出零电流故障')
                                    elif int(data_address[1],16)==18:
                                        self.faultType.setText('反馈传感器故障')
                                    else :
                                        self.faultType.setText('无')
                                    data_fault = bin(int(data_address[2],16)).replace('0b','').zfill(12)
                                    if data_fault[11]==1:
                                        self.faultInfo.setText('Uu')
                                    elif data_fault[10]==1:
                                        self.faultInfo.setText('ou')
                                    elif data_fault[9]==1:
                                        self.faultInfo.setText('OH1')
                                    elif data_fault[8]==1:
                                        self.faultInfo.setText('OC1')
                                    elif data_fault[7]==1:
                                        self.faultInfo.setText('BB')
                                    elif data_fault[6]==1:
                                        self.faultInfo.setText('EF')
                                    elif data_fault[5]==1:
                                        self.faultInfo.setText('LC1 零电流报警')
                                    elif data_fault[4]==1:
                                        self.faultInfo.setText('CALL ')
                                    elif data_fault[3]==1:
                                        self.faultInfo.setText('OH3 来自端子过热报警')
                                    elif data_fault[2]==1:
                                        self.faultInfo.setText('CE 通讯报警')
                                    elif data_fault[1]==1:
                                        self.faultInfo.setText('欠转矩报警')
                                    elif data_fault[0]==1:
                                        self.faultInfo.setText('PID反馈丢失报警')
                                    else:
                                        self.faultInfo.setText('无')

                                except:
                                    QMessageBox.critical(self, 'print wrong', '填入出错了!')
                                    return None
                            else:
                                pass
                        except:
                            QMessageBox.critical(self, 'print wrong', '数据显示出错了!')
                            return None
                    else:
                        QMessageBox.critical(self, 'receive wrong', '本次发送没有接受到返回信息!')
        else:
            QMessageBox.critical(self, 'com close', '请打开串口')
            return None



    # 轮询发送
    def data_send_polling(self):
        if self.polling.isChecked():
            self.timer_send.start(int(self.pollingtime.text()))
            self.pollingtime.setEnabled(False)
        else:
            self.timer_send.stop()
            self.pollingtime.setEnabled(True)

if __name__ == '__main__':
    mifo = RS485data()
    app = QtWidgets.QApplication(sys.argv)
    myshow = Pyqt5_Serial()
    myshow.show()
    sys.exit(app.exec_())

