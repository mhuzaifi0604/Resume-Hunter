import this
from flask import *
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock, Event
import os
import docx
import PyPDF2
import re

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = '5dec1cfe7c0c2ec55c17fb44b43f7d14'
socket_ = SocketIO(app, async_mode=async_mode)

parseThread = None
parse_thread_lock = Lock()

event= Event()
def line_num_getter(filename, pattern, count2):
    num_count = 0
    length = len(pattern)
    with open(filename, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if pattern.lower() in line.lower():
                if(count2 == num_count):
                    return i
                else:
                    num_count+=1
                    continue
                
            

def Naive(text, match, file):
    # pattern must be shorter than text
    count = 0; k= 0; count2 = 0
    lines = ""
    if len(match) > len(text):
        return -1
    for i in range(len(text) - len(match) + 1):
        for j in range(len(match)):
            if text[i+j] != match[j] and text[i+j].lower() != match[j].lower():
                break
 
        if j == len(match)-1:
            if match.lower()==text[i:i+len(match)].lower():
                lineno = line_num_getter("DataFiles/"+file, text[i:i+len(match)], count2)
                if lineno != None:
                    socket_.emit('logging', {'data':f'{file}: {text[i:i+len(match)]} : found at Line: {lineno}' })
                    lines += str(lineno)
                    lines += ","
                elif lineno == None:
                    if(len(lines) > 50):
                        socket_.emit('logging', {'data':f'{file}: {text[i:i+len(match)]} : Found in either of: {lines[0:50]}' })
                    else:
                        socket_.emit('logging', {'data':f'{file}: {text[i:i+len(match)]} : Found in either of: {lines[0:len(lines)-1]}' })
                count2+=1
                count +=1
    lines = None
    socket_.emit('logging', {'data':f'"{file}"' ' Completed - No More Matches 🚫'})
    socket_.emit('logging', {'data':'Total Occcurence of 'f'"{match}" ➡️ {count}'})
    return False


def rabinKarp(text, match, file, q=101, d=256):
    new_txt = text
    text = text.lower()
    match = match.lower()
    M = len(match)
    N = len(text)
    i = 0; count2 = 0
    j = 0; lines = ""
    p = 0    # hash value for matchtern
    t = 0    # hash value for text
    h = 1
    count =  0
    # The value of h would be "pow(d, M-1)%q"
    for i in range(M-1):
        h = (h*d) % q
 
    # Calculate the hash value of matchtern and first window
    # of text
    for i in range(M):
        p = (d*p + ord(match[i])) % q
        t = (d*t + ord(text[i])) % q
 
    # Slide the matchtern over text one by one
    for i in range(N-M+1):
        # Check the hash values of current window of text and
        # matchtern if the hash values match then only check
        # for characters one by one
        if p == t:
            # Check for characters one by one
            for j in range(M):
                if text[i+j] != match[j]:
                    break
                else:
                    j += 1
 
            # if p == t and pat[0...M-1] = text[i, i+1, ...i+M-1]
            if j == M:
                if match.lower()==text[i:i+len(match)].lower():
                    lineno = line_num_getter("DataFiles/"+file, new_txt[i:i+len(match)], count2)
                    if lineno != None:
                        socket_.emit('logging', {'data':f'{file}: {new_txt[i:i+len(match)]} : found at Line: {lineno}' })
                        lines += str(lineno)
                        lines += ","
                    elif lineno == None:
                        if(len(lines) > 50):
                            socket_.emit('logging', {'data':f'{file}: {text[i:i+len(match)]} : Found in either of: {lines[0:50]}' })
                        else:
                            socket_.emit('logging', {'data':f'{file}: {text[i:i+len(match)]} : Found in either of: {lines[0:len(lines)-1]}' })
                    count2+=1
                    count +=1

        # Calculate hash value for next window of text: Remove
        # leading digit, add trailing digit
        if i < N-M:
            t = (d*(t-ord(text[i])*h) + ord(text[i+M])) % q
 
            # We might get negative values of t, converting it to
            # positive
            if t < 0:
                t = t+q
    lines = None
    socket_.emit('logging', {'data':f'"{file}"' ' Completed - No More Matches 🚫'})
    socket_.emit('logging', {'data':'Total Occcurence of 'f'"{match}" ➡️ {count}'})
    return False


def computeLPSArray(pat, M, lps):
    len = 0 
 
    lps[0]
    i = 1

    while i < M:
        if pat[i]== pat[len]:
            len += 1
            lps[i] = len
            i += 1
        else:
            if len != 0:
                len = lps[len-1]

            else:
                lps[i] = 0
                i += 1

def KMP(pat, txt, file):
    pat, txt=txt, pat
    org_pat = pat
    org_txt = txt
    M = len(pat)
    N = len(txt)
    lps = [0]*M
    j = 0; count2= 0
    k = 0; lines = ""
    computeLPSArray(org_pat.lower(), M, lps)
    count = 0
    i = 0
    while i < N:
        if org_pat[j].lower() == org_txt[i].lower():
            i += 1
            j += 1
 
        if j == M:
            lineno = line_num_getter("DataFiles/"+file, org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))], count2)
            if(ord(org_pat[0]) >= 65 and ord(org_pat[0])< 91 and ord(org_pat[0]) +32 == ord(org_txt[i-len(org_pat)])):
                if lineno != None:
                    socket_.emit('logging', {'data':f'{file} : {org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))]} : found at Line: {lineno}'})
                    lines += str(lineno)
                    lines += ","
                elif lineno == None:
                    if(len(lines)>50):
                        socket_.emit('logging', {'data':f'{file} : {org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))]} : found at either: {lines[0:50]}'})
                    else:
                        socket_.emit('logging', {'data':f'{file} : {org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))]} : found at either: {lines[0:len(lines)-1]}'})
                count+=1; count2+=1
                j= lps[j-1]

            elif(ord(org_pat[0]) >= 97 and ord(org_pat[0]) < 123 and ord(org_pat[0]) == ord(org_txt[i-len(org_pat) + 32])):
                if lineno != None:
                    socket_.emit('logging', {'data':f'{file} : {org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))]} : found at Line: {lineno}'})
                    lines += str(lineno)
                    lines += ","
                elif lineno == None:
                    if(len(lines)>50):
                        socket_.emit('logging', {'data':f'{file} : {org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))]} : found at either: {lines[0:50]}'})
                    else:
                        socket_.emit('logging', {'data':f'{file} : {org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))]} : found at either: {lines[0:len(lines)-1]}'})
                count+=1; count2+=1
                j= lps[j-1]
            else:
                if lineno != None:
                    socket_.emit('logging', {'data':f'{file} : {org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))]} : found at Line: {lineno}'})
                    lines += str(lineno)
                    lines += ","
                elif lineno == None:
                    if(len(lines)>50):
                        socket_.emit('logging', {'data':f'{file} : {org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))]} : found at either: {lines[0:50]}'})
                    else:
                        socket_.emit('logging', {'data':f'{file} : {org_txt[(i-len(org_pat)):((i-len(org_pat)) + len(org_pat))]} : found at either: {lines[0:len(lines)-1]}'})
                count+=1; count2+=1
                j= lps[j-1]
            
        elif i < N and org_pat[j].lower() != org_txt[i].lower():
            if j != 0:
                j = lps[j-1]
            else:
                i += 1
    lines = None
    socket_.emit('logging', {'data':f'"{file}"' ' Completed - No More Matches 🚫'})
    socket_.emit('logging', {'data':'Total Occcurence of 'f'"{pat}" ➡️ {count}'})
    return False
 

stringMatching={
    'n':Naive,
    'rk':rabinKarp,
    'kmp':KMP
}

def parseResumes(path, match, algorithm='Naive'):
    global parseThread

    if os.path.exists(path)==False:
        socket_.emit('logging',{'data':'Invalid Path :('})
    else:
        flag=False
        for file in os.listdir(path):
            if event.is_set():
                break
            f=os.path.join(path, file)
            if os.path.isfile(f):
                socket_.emit('logging', {'data':f'Scanning {file}'})
                if f[-5:]=='.docx':
                    flag=True
                    doc=docx.document(f)
                    text=''
                    for para in doc.paragraphs:
                        text+=para.text
                elif f[-4:]=='.pdf':
                    flag=True
                    with open(f, 'rb') as pdfFile:
                        pdfReader=PyPDF2.PdfFileReader(pdfFile)
                        pageObj=pdfReader.getPage(0)
                        text=pageObj.extractText()
                elif f[-4:]=='.txt':
                    flag=True
                    with open(f, 'r', encoding='utf8') as txtFile:
                        text=txtFile.read()

                if flag:
                    stringMatching[algorithm](text, match, file)

        if not flag:
            socket_.emit('logging', {'data':'No resumes found in the specified path'})
    parseThread=None

@app.route('/')
def index():
    return render_template('index.html', async_mode=socket_.async_mode)

@socket_.on('stop')
def stop(data):
    event.set()
    emit('logging', {'data':'Stopping the process'})

@socket_.on('parse')
def parse(data):
    message=data['data']
    global parseThread
    with parse_thread_lock:
        if parseThread is None:
            path=message['path']
            match=message['match']
            algo=message['algorithm']
            print(algo)

            parseThread = socket_.start_background_task(parseResumes, path, match, algo)
            emit('logging', {'data': 'Started parsing'})
        else:
            emit('logging', {'data': 'Process already running'})

if __name__ == '__main__':
    socket_.run(app, debug=True)