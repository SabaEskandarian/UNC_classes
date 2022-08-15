import sys
import subprocess
import re
import time
import datetime
from bs4 import BeautifulSoup

###NOTE: to run this script, you need to do the following steps:
#1) create working_files directory next to script
#2) log in to connectcarolina on Chromium (must be a fresh login)
#3) go to course search, and press F12 to open developer tools. Click on network tab
#4) search for COMP classes in Fall 2022 with course number <=500, uncheck box about only searching for open classes
#5) right click on the resulting POST request and select copy as curl. 
#6) paste contents into COMP_search_curl.sh in SAME DIRECTORY as script

#currently output text assumes searches for fall 2022 classes numbered under 999 with meeting time on any day of week
#fails if there are too many results

#TODO: assuming class numbers don't repeat across terms. Might cause issues if they repeat across active terms.
#TODO: assumes only 1 URL per note.
#notes.txt file contains pairs of lines where first line is class number and second line is any custom notes to appear after description.
def getCustomNotes(notesFileName):
    notes = {}
    fileContents = open(notesFileName, "r")
    while True:
        classNumStr = fileContents.readline().strip()
        if not classNumStr:
            break
        note = fileContents.readline().strip()
        if not note:
            break
        url = ""
        hasURL = False
        for word in note.split():
            if "https://" in word or "http://" in word:
                hasURL = True
                url = word
        if hasURL:
            note = note.replace(url, "<a href='"+url+"'>"+url+"</a>")
        notes[classNumStr] = note
    #print(notes)
    return notes

#names.txt file contains pairs of lines where first line is class name and second line is a custom name to replace the name. Use this to give names to CS special topics classes
def getCustomNames(namesFileName):
    names = {}
    fileContents = open(namesFileName, "r")
    while True:
        classNameStr = fileContents.readline().strip()
        if not classNameStr:
            break
        newName = fileContents.readline().strip()
        if not newName:
            break
        names[classNameStr] = newName
    #print(notes)
    return names

#TODO: getContentById returns "None" for classes that are taught by multiple instructors because ConnectCarolina lists the id and the names on different lines. Fixing this shouldn't be too hard but will involve some modification of this function
def getContentById(targetId, data):
    relevantData = ""
    for line in data.splitlines():
        if targetId in line:
            relevantData = relevantData + line + "\n"
    if not relevantData:
        #don't want a crash if there is no description
        if targetId == "DERIVED_CLSRCH_DESCRLONG":
            return ""
        print("couldn't find match for id "+targetId+"!\n")

    soup = BeautifulSoup(relevantData, 'html.parser')
    return str(soup.find(id=targetId).string).replace(u'\xa0', u'&nbsp;')
    
#bigState 0 is normal dept, 1 is first part of big dept, 2 is second part of big dept
def makeDeptQuery(stateNum, ICSID, dept, bigState):
    number = 999
    matchDirection = "T"
    if bigState != 0:
        number = 500
    if bigState == 2:
        matchDirection = "G"
    queryString = "  --data-raw 'ICAJAX=1&ICNAVTYPEDROPDOWN=1&ICType=Panel&ICElementNum=0&ICStateNum="+str(stateNum)+"&ICAction=CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH&ICModelCancel=0&ICXPos=0&ICYPos=0&ResponsetoDiffFrame=-1&TargetFrameName=None&FacetPath=None&ICFocus=&ICSaveWarningFilter=0&ICChanged=-1&ICSkipPending=0&ICAutoSave=0&ICResubmit=0&ICSID="+ICSID+"&ICActionPrompt=false&ICPanelName=&ICFind=&ICAddCount=&ICAppClsData=&CLASS_SRCH_WRK2_INSTITUTION$31$=UNCCH&CLASS_SRCH_WRK2_STRM$35$=2229&NC_CSE_ATTR_TBL_CRSE_ATTR_VALUE$0=&SSR_CLSRCH_WRK_SUBJECT$0="+dept+"&SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$1="+matchDirection+"&SSR_CLSRCH_WRK_CATALOG_NBR$1="+str(number)+"&SSR_CLSRCH_WRK_ACAD_CAREER$2=&SSR_CLSRCH_WRK_SSR_OPEN_ONLY$chk$3=N&SSR_CLSRCH_WRK_SSR_START_TIME_OPR$4=GE&SSR_CLSRCH_WRK_MEETING_TIME_START$4=&SSR_CLSRCH_WRK_SSR_END_TIME_OPR$4=LE&SSR_CLSRCH_WRK_MEETING_TIME_END$4=&SSR_CLSRCH_WRK_INCLUDE_CLASS_DAYS$5=J&SSR_CLSRCH_WRK_MON$chk$5=Y&SSR_CLSRCH_WRK_MON$5=Y&SSR_CLSRCH_WRK_TUES$chk$5=Y&SSR_CLSRCH_WRK_TUES$5=Y&SSR_CLSRCH_WRK_WED$chk$5=Y&SSR_CLSRCH_WRK_WED$5=Y&SSR_CLSRCH_WRK_THURS$chk$5=Y&SSR_CLSRCH_WRK_THURS$5=Y&SSR_CLSRCH_WRK_FRI$chk$5=Y&SSR_CLSRCH_WRK_FRI$5=Y&SSR_CLSRCH_WRK_SAT$chk$5=Y&SSR_CLSRCH_WRK_SAT$5=Y&SSR_CLSRCH_WRK_SUN$chk$5=Y&SSR_CLSRCH_WRK_SUN$5=Y&SSR_CLSRCH_WRK_SSR_EXACT_MATCH2$6=B&SSR_CLSRCH_WRK_LAST_NAME$6=&SSR_CLSRCH_WRK_DESCR$7=&SSR_CLSRCH_WRK_CLASS_NBR$8=&SSR_CLSRCH_WRK_SSR_UNITS_MIN_OPR$9=GE&SSR_CLSRCH_WRK_UNITS_MINIMUM$9=&SSR_CLSRCH_WRK_SSR_UNITS_MAX_OPR$9=LE&SSR_CLSRCH_WRK_UNITS_MAXIMUM$9=&SSR_CLSRCH_WRK_SSR_COMPONENT$10=&SSR_CLSRCH_WRK_SESSION_CODE$11=&SSR_CLSRCH_WRK_INSTRUCTION_MODE$12=&SSR_CLSRCH_WRK_CAMPUS$13=' \\"
    return queryString

#extract class list(s)
def createSearchCommand(dept, splitSearch, ICSID):
    stateNum = 4

    if not splitSearch:
        command = open("COMP_search_curl.sh", "r").read().splitlines()
        command[-2] = makeDeptQuery(stateNum, ICSID, dept, 0)
        dept_search_file = "working_files/"+dept+"_search_curl.sh"
        new_command_file = open(dept_search_file, "w")
        for line in command:
            new_command_file.write(line+"\n")
        new_command_file.close()
    else:
        command = open("COMP_search_curl.sh", "r").read().splitlines()
        command[-2] = makeDeptQuery(stateNum, ICSID, dept, 2)
        dept_search_file = "working_files/second_"+dept+"_search_curl.sh"
        new_command_file = open(dept_search_file, "w")
        for line in command:
            new_command_file.write(line+"\n")
        new_command_file.close()

        command = open("COMP_search_curl.sh", "r").read().splitlines()
        command[-2] = makeDeptQuery(stateNum, ICSID, dept, 1)
        dept_search_file = "working_files/"+dept+"_search_curl.sh"
        new_command_file = open(dept_search_file, "w")
        for line in command:
            new_command_file.write(line+"\n")
        new_command_file.close()

    return dept_search_file
    
def logResponse(fileName, data):
    log_file = open(fileName, "w")
    log_file.write(data)
    log_file.close()

def startClassList(dept_search_file):
    #use curl to get class list
    classListData = subprocess.run(["bash", dept_search_file], capture_output=True).stdout.decode("utf-8")
    #print("result of command: \n" + classListData)
    #classListData = open("class_list_res.html", "r").read()
    #save classListData to a temp file in working_files directory
    logResponse("working_files/dept_response.txt", classListData)

    #extract number of classes
    numClasses = 0
    for line in classListData.splitlines():
        if "class section(s) found" in line:
            numClasses = int(re.sub("[^0-9]", "", line))
            break
    print("number of classes: " + str(numClasses))

    #abort if fail
    if numClasses == 0:
        print("wasn't able to find any classes")
        sys.exit(1)

    return numClasses

def addClassEntry(dept_search_file, ICSID, i, notes, names):
    #form a class_search_curl.sh file by copying info from the dept search headers/cookies and modifying data
    class_search = open(dept_search_file, "r").read().splitlines()
    StateNum = 5
    class_search[-2] = "  --data-raw 'ICAJAX=1&ICNAVTYPEDROPDOWN=1&ICType=Panel&ICElementNum=0&ICStateNum="+str(StateNum)+"&ICAction=MTG_CLASS_NBR%24"+str(i)+"&ICModelCancel=0&ICXPos=0&ICYPos=0&ResponsetoDiffFrame=-1&TargetFrameName=None&FacetPath=None&ICFocus=&ICSaveWarningFilter=0&ICChanged=-1&ICSkipPending=0&ICAutoSave=0&ICResubmit=0&ICSID="+ICSID+"&ICActionPrompt=false&ICBcDomData=&ICPanelName=&ICFind=&ICAddCount=&ICAppClsData=' \\"

    #write the class search to a file
    class_file_name = "working_files/class_search_curl.sh"
    class_file = open(class_file_name, "w")
    for line in class_search:
        class_file.write(line+"\n")
    class_file.close()

    #run query
    count = 0
    classRawData = ""
    while classRawData == "" and count < 5:
        classRawData = subprocess.run(["bash", class_file_name], capture_output=True).stdout.decode("utf-8")
        if classRawData == "":
            time.sleep(0.1)
            print("couldn't get classRawData, trying again\n")
            count += 1
    
    #save classRawData to a temp file in working_files directory
    logResponse("working_files/class_response.txt", classRawData)

    #print(classRawData)
    #parse class data, output html
    classNum = getContentById("SSR_CLS_DTL_WRK_CLASS_NBR", classRawData)
    className = getContentById("DERIVED_CLSRCH_DESCR200", classRawData)
    if className in names:
        className = names[className]
    classTime = getContentById("MTG_SCHED$0", classRawData)
    instructor = getContentById("MTG_INSTR$0", classRawData)
    room = getContentById("MTG_LOC$0", classRawData)
    enrollment = getContentById("SSR_CLS_DTL_WRK_ENRL_TOT", classRawData)
    enrollmentMax = getContentById("SSR_CLS_DTL_WRK_ENRL_CAP", classRawData)
    waitlist = getContentById("SSR_CLS_DTL_WRK_WAIT_TOT", classRawData)
    waitlistMax = getContentById("SSR_CLS_DTL_WRK_WAIT_CAP", classRawData)
    description = getContentById("DERIVED_CLSRCH_DESCRLONG", classRawData)
    units = getContentById("SSR_CLS_DTL_WRK_UNITS_RANGE", classRawData)

    #if meeting time is TBA, instructor is Staff, and nobody's enrolled, this is probably not a real class
    #NOTE: this is a heuristic, but I think it's a good choice for making the results less cluttered
   #NOTE: commenting this out now that the search query itself does a better job of decluttering
   #if classTime == "TBA" and instructor == "Staff" and int(enrollment) == 0:
    #    return ""

    #add html
    enrollmentTD = "<td>"
    #if class is full, make the enrollment red
    if int(enrollment) >= int(enrollmentMax):
        enrollmentTD = "<td style='color:red'>"

    tableLines = "<tr><td>"+classNum+"</td><td>"+className+"</td><td>"+classTime+"</td><td>"+instructor+"</td><td>"+room+"</td>"+enrollmentTD+enrollment+"/"+enrollmentMax+"</td><td>"+waitlist+"/"+waitlistMax+"</td></tr>\n<tr class='expandable'><td colspan=7><strong>Description: </strong>"+description+" "+units+"."

    if classNum in notes:
        tableLines = tableLines + "\n<br /><strong>Notes:</strong> "+notes[classNum]

    tableLines = tableLines + "</td></tr>\n"

    return tableLines



term = "fall 2022"
term_folder = "fall2022"
dept_search_file = "COMP_search_curl.sh"
notes_file = "notes.txt"
names_file = "names.txt"
notes = getCustomNotes(notes_file)
names = getCustomNames(names_file)

#extract ICSID from the curl used for the dept search
dept_search = open(dept_search_file, "r").read().splitlines()
dept_search_data = dept_search[-2]
start_ICSID = dept_search_data.find("ICSID=")
end_ICSID = dept_search_data.find("&", start_ICSID)
ICSID = dept_search_data[start_ICSID+6: end_ICSID]
print("retrieved ICSID "+ICSID+"\n")

#Can include any dept where there are <130 courses listed with a number under 999
#COMP needs to be first or there will be issues
dept_list = ["COMP", "AAAD", "AMST", "BIOS", "COMM", "DRAM", "EDUC", "HIST", "MATH", "STOR", "WGST"]
#any department where there are <130 courses under 500 and another <130 listed over 500
#needs to go in both dept_list and large_dept_list
large_dept_list = ["HIST","MATH"]

for dept in dept_list:

    bigDept = False
    if dept in large_dept_list:
        bigDept = True

    print("starting to get data for "+dept)

    dept_search_file = createSearchCommand(dept, bigDept, ICSID)

    numClasses = startClassList(dept_search_file)

    #open/read the HTML template into a string.
    html = open("page_template.html", "r").read()

    #text at top of page

    html = html + "<h1>"+dept+" Courses</h1>\n\n"

    html = html + "<p>Here is information about "+dept+" class enrollment for <strong>"+term+"</strong>. Classes with no meeting time listed are not shown. Feel free to <a href='https://cs.unc.edu/~saba'>contact me</a> with any questions/comments/issues.</p>\n\n"

    html = html + "<p><strong>Click <a id='show'>here</a> to show class descriptions</strong>. Click <a id='hide'>here</a> to hide them.</p>\n\n"

    html = html + "<script src='../choose_term.js'></script>\n"

    html = html + "<p> Data also available for: <a href='index.html'>COMP</a>"

    for item in dept_list:
        if item == "COMP":
            continue
        html = html + ", <a href='"+item+"_classes.html'>"+item+"</a>"

    html = html + "</p>\n"

    #get timestamp for start of search
    timestamp = datetime.datetime.now()
    html = html + "<p>Data last updated: "+str(timestamp)+"</p>\n"

    #beginning of table
    html = html + "<table>\n<tr>\n<th>Class Number</th>\n<th>Class</th>\n<th>Meeting Time</th>\n<th>Instructor</th>\n<th>Room</th>\n<th>Enrollment</th>\n<th>Wait List</th>\n</tr>\n"

    #for each class
    for i in range(numClasses):
        time.sleep(.1) #avoid too many queries in a rush
        html = html + addClassEntry(dept_search_file, ICSID, i, notes, names)

    #if this is a big dept, we need to repeat some of this work for the second file
    if bigDept:
        #messy
        dept_search_file = "working_files/second_"+dept+"_search_curl.sh"
        numClasses = startClassList(dept_search_file)
        #for each class
        for i in range(numClasses):
            time.sleep(.1) #avoid too many queries in a rush
            html = html + addClassEntry(dept_search_file, ICSID, i, notes, names)

        #if i % 10 == 0:
        #    print("processed class number " + str(i))

    #add HTML end stuff and write to file
    html = html + "\n</table>\n</body>\n</html>"
    outFileName = "index.html"
    if dept != "COMP":
        outFileName = dept+"_classes.html"
    outFile = open("working_files/"+outFileName, "w")
    outFile.write(html)
    outFile.close()

    subprocess.run(["cp", "working_files/"+outFileName, "/afs/cs.unc.edu/home/saba/public_html/COMP_classes/"+term_folder+"/"+outFileName])
    print("done with "+dept+"!")
print("done!")
