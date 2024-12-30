#!/usr/bin/env python
import pandas as pd
import chardet
import re

def discover_csv_encoding(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read()
    result = chardet.detect(rawdata)
    encoding = result['encoding']
    confidence = result['confidence']
    return encoding, confidence

def dms_to_decimal(degrees, minutes, seconds):
    if degrees is not None:
        # Check direction (N, S, E, W) and determine decimal degree sign
        sign = -1 #In real, it's +1; All decimal coordinate signs in Brazil are negative due to its location in the southern hemisphere and west of Greenwich.
        #if direction in ["S", "W"]:
         #   sign = -1
        # Calculates the decimal degree
        decimal = sign * (degrees + minutes/60 + seconds/3600)
        return decimal
    else:
        return None
    
def string_to_float(string):

    if '.' in string:
        float_value = float(string)
        return float_value
    
    if len(string) == 1:
        return float(string)

    if len(string) >= 2:
        if int(string[0]) > 5:
            float_value = float(f"{string[0]}.{string[1:]}")        
        else: 
            float_value = float(f"{string[0:2]}.{string[2:]}")
    
        return float_value

def convert_to_negative_float(value):

    if value is not None and value == value and isinstance(value, str):
        try:
            value = str(value)
            value = value.replace(',', '.') if ',' in value else value
            float_value = float(value)
            return float_value if float_value < 0 else -float_value
        except ValueError:
            pass
        
    return value

def extract_gc(str_text):
    if pd.isna(str_text):
        return None
    try:
        str_text = str(str_text)
        str_text = re.sub(r'\s', '', str_text)
        match = re.search(r"^[A-Z]?(\d{1,2})[o°º`\.]?(\d{1,2})['’´`\.,]{0,2}(\d+[\.,]?[\d]{0,2}).*", str_text)

        if match:
            degrees = int(match.group(1))
            minutes = int(match.group(2))
            seconds = string_to_float(match.group(3).replace(",", "."))

            if degrees is not None and minutes is not None and seconds is not None:
                return degrees, minutes, seconds
             
    except AttributeError:
        # Trate exceções aqui, se necessário
        pass
    
    return str_text

if __name__ == '__main__':

    file_path = '/home/cleyton/ProjetosGit/msc_thesis_naea_ufpa/1_DataSource/csv_files/farm_branches.csv'
    encoding, confidence = discover_csv_encoding(file_path)
    print(f"Encoding: {encoding}, Confidence: {confidence}")

    farm_branches = pd.read_csv(file_path, encoding=encoding)
    rows, cols = farm_branches.shape
    cols = ['Latitude', 'Longitude']

    for col in cols:
        for index in range(rows): 
            #Remove "°" and "°" from decimal gc
            if farm_branches[col][index] is not pd.isna(farm_branches[col][index]):
                farm_branches[col][index] = str(farm_branches[col][index]).rstrip("º").rstrip("°")

            #Transform positives in negatives 
            farm_branches[col][index] = convert_to_negative_float(farm_branches[col][index])
            gc = extract_gc(farm_branches[col][index])
            
            if gc is not None and not pd.isna(gc) and len(gc) == 3:
                decimal_cg = dms_to_decimal(gc[0], gc[1], gc[2])
                farm_branches[col][index] = decimal_cg

            else:
                farm_branches[col][index] = farm_branches[col][index]

farm_branches.to_csv('/home/cleyton/ProjetosGit/msc_thesis_naea_ufpa/2_DataProcessing/cg_farm_branches_to_decimal.csv', encoding='utf-8')
