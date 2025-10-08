import json
from datetime import datetime, timedelta
import os, os.path
import sys
import logging
from zipfile import ZipFile

def filetime_to_datetime(filetime_ticks):
    # 1 tick = 100 nanoseconds, and we need to convert to seconds.
    seconds = filetime_ticks / 10000000  # Convert ticks to seconds
    # Windows FileTime epoch: January 1, 1601
    filetime_epoch = datetime(1601, 1, 1)
    # Add the timedelta (in seconds) to the FileTime epoch
    result = filetime_epoch + timedelta(seconds=seconds)
    return result

def calculate_logouttime(logintime, playedtime):
    seconds = logintime / 10000000  # Convert ticks to seconds
    # Windows FileTime epoch: January 1, 1601
    seconds = seconds + playedtime
    filetime_epoch = datetime(1601, 1, 1)
    # Add the timedelta (in seconds) to the FileTime epoch
    result = filetime_epoch + timedelta(seconds=seconds)
    return result

def get_last_timestamp_from_logfile(logfile):
    logging.debug('retrieve timestamp information from logfile')
    if not os.path.exists(logfile):
        logging.info('logfile does not exist: ' + logfile)
        return 'logfile not available'

    with open(logfile, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        last_line = lines[-1]
        first_line = lines[0]
    
    return last_line.split(',')[0].split('(')[1], first_line.split(',')[0].split('(')[1]

def get_potions_prepared_from_logfile(logfile):
    logging.debug('retrieve potion information from logfile...')
    if not os.path.exists(logfile):
        logging.info('logfile does not exist: ' + logfile)
        return 'logfile not available'

    potions_started = 0
    potions_completed_successfully = 0
    potions_failed = 0
    potions_error = 0
    with open(logfile, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for line in lines:
            if ' Recipe ' in line:
                pot_id = line.split('Recipe (Id:')[1].strip().split(')')[0]
                state = ''
                if 'started' in line:
                    potions_started = potions_started + 1
                elif 'Success' in line:
                    potions_completed_successfully = potions_completed_successfully + 1
                elif 'Fail' in line:
                    potions_failed = potions_failed + 1
                elif 'Exit' in line:
                    potions_error = potions_error + 1
                else:
                    logging.error('invalid receipe state: ' + line)
                    continue

    return potions_started, potions_completed_successfully, potions_failed, potions_error

class TimeInformation:
    def __init__(self, timeZoneInformation, kinectTimestamp, systemTimestamp, unityTimestamp):
        self.timeZoneInformation = timeZoneInformation
        self.kinectTimestamp = kinectTimestamp
        self.systemTimestamp = systemTimestamp
        self.unityTimestamp = unityTimestamp

class ResultInformation:
    def __init__(self, loginTime, logoutTime, minFrameTimeInfo, maxFrameTimeInfo, lastTimestampInLogFile, firstTimestampInLogFile, p_started, p_completed, p_failed, p_error, potionsPrepared):
        
        self.potions_prepared = potionsPrepared
        self.p_started_log = p_started
        self.p_completed_log = p_completed
        self.p_failed_log = p_failed
        self.p_error_log = p_error

        if self.potions_prepared != self.p_completed_log:
            logging.info('potions prepared mismatch found...')
        if self.p_completed_log == 0:
            logging.info('no potion completed in this session')

        self.lastTimestampInLogFile = lastTimestampInLogFile
        self.firstTimestampInLogFile = firstTimestampInLogFile

        self.loginTime = loginTime
        self.logoutTime = logoutTime

        converted_loginTime = filetime_to_datetime(loginTime)
        self.readableLoginTime = converted_loginTime.strftime("%Y-%m-%d %H:%M:%S")
        self.readableLogoutTime = ''
        
        if self.logoutTime != '':
            converted_logoutTime = filetime_to_datetime(logoutTime)
            self.readableLogoutTime = converted_logoutTime.strftime("%Y-%m-%d %H:%M:%S")
        
        self.playedTimeSystemTimestamp = maxFrameTimeInfo.systemTimestamp - minFrameTimeInfo.systemTimestamp
        self.playedTimeLKinectTimestamp = maxFrameTimeInfo.kinectTimestamp - minFrameTimeInfo.kinectTimestamp
        self.playedTimeUnityTimestamp = maxFrameTimeInfo.unityTimestamp - minFrameTimeInfo.unityTimestamp

        logouttime_calculated = calculate_logouttime(loginTime, self.playedTimeSystemTimestamp)
        self.calculatedLogoutTimeBasedOnDurationAndLoginTime = logouttime_calculated.strftime("%Y-%m-%d %H:%M:%S")

def create_information(input_filename, logfile):
    try:
        with open(input_filename, 'r', encoding='utf-8') as file:
            data = json.load(file)

            loginTime = str(data['loginTime'])
            logoutTime = str(data['logoutTime'])
            potionsPrepared = str(data['potionsPrepared'])

            if loginTime != '':
                loginTime = int(loginTime)
            if logoutTime != '':
                logoutTime = int(logoutTime)

            frameData = data['frameData']

            if len(frameData) == 0:
                return None
            
            minFrameId = 0
            maxFrameId = 0
            firstCheck = True
            for frame in frameData:
                frameId = frame['frameDataId']
                if firstCheck:
                    minFrameId = frameId
                    maxFrameId = frameId
                    firstCheck = False
                else:
                    if frameId < minFrameId:
                        minFrameId = frameId
                    if frameId > maxFrameId:
                        maxFrameId = frameId
            
            for frame in frameData:
                label_val = frame['labels'].split(';')
                frameId = frame['frameDataId']
                if frameId == minFrameId:
                    minFrameTimeInfo = TimeInformation(label_val[3], float(label_val[4]), float(label_val[5]), float(label_val[6]))
                if frameId == maxFrameId:
                    maxFrameTimeInfo = TimeInformation(label_val[3], float(label_val[4]), float(label_val[5]), float(label_val[6]))

            lastTimeStampInLogFile, firstTimeStampInLogFile = get_last_timestamp_from_logfile(logfile)
            p_started, p_completed, p_failed, p_error = get_potions_prepared_from_logfile(logfile)

            result = ResultInformation(loginTime, logoutTime, minFrameTimeInfo, maxFrameTimeInfo, lastTimeStampInLogFile, firstTimeStampInLogFile, p_started, p_completed, p_failed, p_error, potionsPrepared)
            result_data = json.dumps(result.__dict__)
            return result_data

    except Exception as error:
        logging.info('could not load input file: ' + input_filename)
        logging.info(error)
        return None 

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    if len(sys.argv) < 2:
        sys.exit('Usage: python APPNAME DATA_FOLDER')

    path = sys.argv[1]
    logging.info('data path: ' + path)
    if not os.path.isdir(path):
        sys.exit('data folder not found: ' + path)

    # read all zip files
    zip_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.zip')]

    for zip_file in zip_files:
        logging.info('parsing ' + zip_file + '...')

        # check if the file is new
        patient_id = zip_file.split('_')[0]
        if len(patient_id) < 28:
            logging.info('file skipped (old file from feasibility study)')
            continue

        # check if the calculation is already completed for that zip file
        full_zip_file = path + '/' + zip_file
        file_key = full_zip_file[:-4]
        output_filename = file_key + '_info_v1.json'
        if os.path.isfile(output_filename):
            logging.info('calculated information for ' + full_zip_file + ' already available')
            continue

        # unzip file
        with ZipFile(full_zip_file, 'r') as zf:
            zf.extractall(path)
            logging.info('...file extracted')

        json_file = file_key + '.json'
        log_file = file_key + '.log'

        if not os.path.isfile(json_file):
            logging.info(json_file + ' does not exist!')
            continue

        if not os.path.isfile(log_file):
            logging.info(log_file + ' does not exist!')
            os.remove(json_file)
            continue

        json_result = create_information(json_file, log_file)
        if json_result != None:
                with open(output_filename, "w", encoding="utf-8") as outfile:
                    logging.info('write information file ' + output_filename)
                    outfile.write(json_result)
                    # delete data file and log file
                    os.remove(json_file)
                    os.remove(log_file)
