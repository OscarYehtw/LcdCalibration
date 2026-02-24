#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Created on 2017-04-21
This interface base on serial and modbus_tk packages
Add a threading lock for every com read/write
@author: Carl.liao
'''
import serial  
  
import modbus_tk  
import modbus_tk.defines as cst  
from modbus_tk import modbus_rtu
import threading
import logging

logger = modbus_tk.utils.create_logger("dummy",logging.INFO)
# logger = modbus_tk.utils.create_logger("console",logging.DEBUG)
class InnorevModbus(object):
    """
    Exception: Print the error code of MODBUS
        Error code stand for:
            ILLEGAL_FUNCTION = 1
            ILLEGAL_DATA_ADDRESS = 2
            ILLEGAL_DATA_VALUE = 3
            SLAVE_DEVICE_FAILURE = 4
            COMMAND_ACKNOWLEDGE = 5
            SLAVE_DEVICE_BUSY = 6
            MEMORY_PARITY_ERROR = 8 
    """
    _handle = None

    def __init__(self, port, baudrate=38400, bytesize=8, parity='N', stopbits=1,xonoff=0):
        self.master = modbus_rtu.RtuMaster(
                serial.Serial(port,baudrate, bytesize,  parity, stopbits, xonoff))
        self.lock = threading.Lock()
        self._handle = 1
    
    @staticmethod
    def getInstance(port, re_init=False):
        if re_init:
            if InnorevModbus._handle is not None:
                InnorevModbus._handle.close()
                InnorevModbus._handle = None

        if not InnorevModbus._handle:
            InnorevModbus._handle = InnorevModbus(port)
        return InnorevModbus._handle
    
    def print_exception_text(self, value):
        """
        Exception: Print the error code of MODBUS
        Error code stand for:
            ILLEGAL_FUNCTION = 1
            ILLEGAL_DATA_ADDRESS = 2
            ILLEGAL_DATA_VALUE = 3
            SLAVE_DEVICE_FAILURE = 4
            COMMAND_ACKNOWLEDGE = 5
            SLAVE_DEVICE_BUSY = 6
            MEMORY_PARITY_ERROR = 8 
        """     
        exception_text = "Unknown"
        if value == 1:
            exception_text = "Illegal function"
        if value == 2:
            exception_text = "Illegal data address "+str(value)
        if value == 3:
            exception_text = "Illegal data address "+str(value)
        if value == 4:
            exception_text = "Slave devices failure"
        if value == 5:
            exception_text = "Command acknowledge"
        if value == 6:
            exception_text = "Slave device busy"
        if value == 8:
            exception_text = "Memory parity error"
        return exception_text
    
    def InnorevOpenSerial(self):
        """
        Use modbus_rtu to Open serial to query/set modbus_rtu
        Default parameters:
            BAUDRATE = 38400 # baud rate
            BYTESIZE = 8     # number of databits
            PARITY = NONE    # enable parity checking
            STOPBITS = 1     # number of stopbits
            xonxoff=0,       # enable software flow control
        
        """        
        self.lock.acquire()
        try:
            self.master.open()
            self.master.set_timeout(0.1)
            self.master.set_verbose(True)
            return True
        except modbus_tk.modbus.ModbusError as exc:  
            logger.error("%s", self.print_exception_text(exc.get_exception_code()))
            raise Exception(self.print_exception_text(exc.get_exception_code()))
        except Exception as excpt:            
            logger.error(excpt)
            raise Exception(str(excpt))
        finally:
            self.lock.release()
    
    def close(self):
        if self.master:
            self.master.close()
        
    def InnorevReadCoil(self,slaveaddress,rigster,data_number = 1):
        """
        Read coils data.Function return value is a tuple every element of which is 0/1.
        if function return value is NULL,some error may happen 
        """
        self.lock.acquire()
        data = None
        try:
            data = self.master.execute(slaveaddress, cst.READ_COILS, rigster, data_number)
            self.lock.release()
            return data
        except modbus_tk.exceptions.ModbusError as exc:  
            logger.error("%s", self.print_exception_text(exc.get_exception_code()))
            data = self.master.execute(slaveaddress, cst.READ_COILS, rigster, data_number)
            return data
        except Exception as excpt:            
            logger.error(excpt)
            data = self.master.execute(slaveaddress, cst.READ_COILS, rigster, data_number)
            return data
        finally:
            self.lock.release()

    def InnorevReadDiscreteInput(self,slaveaddress,rigster,data_number = 1):
        """
        Read discrete input data.Function return value is a tuple.
        if function return value is NULL,some error may happen 
        """
        self.lock.acquire()
        data = None
        try:
            data = self.master.execute(slaveaddress, cst.READ_DISCRETE_INPUTS, rigster, data_number)
            self.lock.release()
            return data
        except modbus_tk.exceptions.ModbusError as exc:  
            logger.error("%s", self.print_exception_text(exc.get_exception_code()))
            data = self.master.execute(slaveaddress, cst.READ_DISCRETE_INPUTS, rigster, data_number)
            return data
        except Exception as excpt:            
            logger.error(excpt)
            data = self.master.execute(slaveaddress, cst.READ_DISCRETE_INPUTS, rigster, data_number)
            return data
        finally:
            self.lock.release()
            
    def InnorevReadHodlingRegister(self,slaveaddress,rigster,data_number = 1,out_format=""):
        """
        Read holding register input data.Function return value is a tuple.
        if return False,some error may happen   
        """
        self.lock.acquire()
        data = None
        try:
            data = self.master.execute(slaveaddress, cst.READ_HOLDING_REGISTERS, rigster, data_number,0,out_format)
            return data
        except modbus_tk.exceptions.ModbusError as exc:  
            logger.error("%s", self.print_exception_text(exc.get_exception_code()))
            data = self.master.execute(slaveaddress, cst.READ_HOLDING_REGISTERS, rigster, data_number,out_format)
            return data
        except Exception as excpt:            
            logger.error(excpt)
            data = self.master.execute(slaveaddress, cst.READ_HOLDING_REGISTERS, rigster, data_number,out_format)
            return data
        finally:
            self.lock.release()
            
    def InnorevWriteSignalCoil(self,slaveaddress,rigster,data):
        """
        write 0/1 into a coil
        if return False,some error may happen   
        """
        self.lock.acquire()
        try:
            if(0 == data or 1 == data):
                self.master.execute(slaveaddress, cst.WRITE_SINGLE_COIL, rigster, output_value=data)
                logging.info('Success to write single coil')
                return True
            else:
                logging.info('parameter must be 0/1, data = %d'%data)
                return False
        except modbus_tk.exceptions.ModbusError as exc:  
            logger.error("%s", self.print_exception_text(exc.get_exception_code()))
            if(0 == data or 1 == data):
                self.master.execute(slaveaddress, cst.WRITE_SINGLE_COIL, rigster, output_value=data)
                logging.info('Success to write single coil')
                return True
        except Exception as excpt:            
            logger.error(excpt)
            if(0 == data or 1 == data):
                self.master.execute(slaveaddress, cst.WRITE_SINGLE_COIL, rigster, output_value=data)
                logging.info('Success to write single coil')
                return True
        finally:
            self.lock.release()

    def InnorevWriteSingleRegister(self,slaveaddress,rigster,data):
        """
        write a 2 byte data into a single register
        if return False,some error may happen   
        """
        self.lock.acquire()
        try:
            da = self.master.execute(slaveaddress, cst.WRITE_SINGLE_REGISTER, rigster, output_value=data)
            return True
        except modbus_tk.exceptions.ModbusError as exc:  
            logger.error("%s=====%s====%s", self.print_exception_text(exc.get_exception_code()),str(rigster),str(data))
            self.master.execute(slaveaddress, cst.WRITE_SINGLE_REGISTER, rigster, output_value=data)
            return True
        except Exception as excpt:            
            logger.error(excpt)
            self.master.execute(slaveaddress, cst.WRITE_SINGLE_REGISTER, rigster, output_value=data)
            return True
        finally:
            self.lock.release()

    def InnorevWriteMultipleCoils(self,slaveaddress,rigster,data):
        """
        write multiple 0/1 into coils
        if return False,some error may happen   
        """
        Islegal = True
        self.lock.acquire()
        try:
            tuple_name = tuple(data)
            tuple_len = len(tuple_name)
            for length in range(0,tuple_len):
                if(not ((0 == tuple_name[length]) or (1 == tuple_name[length]))):
                    logging.info('parameter must be 0/1, data = %d , position = %d'%(tuple_name[length], length))
                    Islegal = False
            if(Islegal):
                self.master.execute(slaveaddress, cst.WRITE_MULTIPLE_COILS, rigster, output_value = tuple_name)
                logging.info('Success to write multiple coil')
                return True
            else:
                logging.info('Some parameter is not 0/1')
        except modbus_tk.exceptions.ModbusError as exc:  
            logger.error("%s", self.print_exception_text(exc.get_exception_code()))
            raise Exception(self.print_exception_text(exc.get_exception_code()))
            return False
        except Exception as excpt:            
            logger.error(excpt)
            raise Exception(str(excpt))
        finally:
            self.lock.release()

    def InnorevWriteMultipleRegister(self,slaveaddress,rigster,data):
        """
        write multiple 0/1 into coils
        if return False,some error may happen   
        """
        self.lock.acquire()
        try:
            tuple_name = tuple(data)           
            self.master.execute(slaveaddress, cst.WRITE_MULTIPLE_REGISTERS, rigster, output_value = tuple_name)
            logging.info('Success to write multiple registers.')
            return True
        except modbus_tk.exceptions.ModbusError as exc:
            logger.error("%s", self.print_exception_text(exc.get_exception_code()))
            tuple_name = tuple(data)           
            self.master.execute(slaveaddress, cst.WRITE_MULTIPLE_REGISTERS, rigster, output_value = tuple_name)
            logging.info('Success to write multiple registers.')
            return True
        except Exception as excpt:            
            logger.error(excpt)
            tuple_name = tuple(data)           
            self.master.execute(slaveaddress, cst.WRITE_MULTIPLE_REGISTERS, rigster, output_value = tuple_name)
            logging.info('Success to write multiple registers.')
            return True
        finally:
            self.lock.release()