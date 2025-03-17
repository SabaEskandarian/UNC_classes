import sys
import subprocess
import re
import time
import datetime
from bs4 import BeautifulSoup

###NOTE: to run this script, you need to do the following steps:
#1) create working_files directory next to script
#2) log in to connectcarolina on Chromium (or use an existing session)
#3) go to course search, and press F12 to open developer tools. Click on network tab
#4) select the current term on the term dropdown at the top of the search.
#5) right click on the resulting POST request and select copy as curl. 
#6) paste contents into COMP_search_curl.sh in SAME DIRECTORY as script
### you can also call the repeat.sh script to have this script run in a loop

#fails if there are too many results
    
def getColoredTD(enrollmentFractionString):
    nums = enrollmentFractionString.split('/')
    tdString = "<td>"
    if enrollmentFractionString == "Seats filled":
        tdString = "<td style='color:red'>"
    if len(nums) < 2:
        return tdString
    if int(nums[1]) > 0 and float(nums[0]) / float(nums[1]) > .85:
        tdString = "<td style='color:orange'>"
    if int(nums[1]) > 0 and int(nums[0]) >= int(nums[1]):
        tdString = "<td style='color:red'>"
    return tdString

#switch string from open/total format to enrollment/total format
def correctEnrollment(enrollmentString):
    nums = enrollmentString.split('/')
    if len(nums) < 2:
        return enrollmentString
    return str(int(nums[1])-int(nums[0]))+"/"+nums[1]

def getContentById(targetId, data):
    relevantData = ""
    lines = data.splitlines();
    count = 0;
    while count < len(lines):
        line = lines[count]
        if targetId in line:
            relevantData = relevantData + line + "\n"
            while not ("/span" in line):
                count = count + 1
                line = lines[count]
                relevantData = relevantData + line + "\n"
        count = count + 1
    if not relevantData:
        #don't want a crash if there is no description or notes
        if targetId == "DERIVED_CLSRCH_DESCRLONG" or targetId == "SSR_CLS_DTL_WRK_CLASS_NBR" or targetId == "DERIVED_CLSRCH_SSR_CLASSNOTE_LONG":
            return ""
        print("couldn't find match for id "+targetId+"!\n")
    
    soup = BeautifulSoup(relevantData, 'html.parser')
    if targetId == "MTG_INSTR$0":
        retString = str(soup.find(id=targetId).get_text()).replace(",", ",<br />")
    elif targetId == "DERIVED_CLSRCH_SSR_CLASSNOTE_LONG":
        #print(relevantData+"\n")
        retString = soup.find(id=targetId).get_text(separator='\n')+"\n"
    else:
        retString = str(soup.find(id=targetId).string).replace(u'\xa0', u'&nbsp;')
    
    return retString
    
#bigState 0 is normal dept, 1 is first part of big dept, 2 is second part of big dept
def makeDeptQuery(term, stateNum, ICSID, dept, bigState, cutoff = 500):
    number = 999
    matchDirection = "T"
    if bigState != 0:
        number = cutoff
    if bigState == 2:
        matchDirection = "G"
    queryString = "  --data-raw 'ICAJAX=1&ICNAVTYPEDROPDOWN=1&ICType=Panel&ICElementNum=0&ICStateNum="+str(stateNum)+"&ICAction=CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH&ICModelCancel=0&ICXPos=0&ICYPos=0&ResponsetoDiffFrame=-1&TargetFrameName=None&FacetPath=None&ICFocus=&ICSaveWarningFilter=0&ICChanged=-1&ICSkipPending=0&ICAutoSave=0&ICResubmit=0&ICSID="+ICSID+"&ICActionPrompt=false&ICPanelName=&ICFind=&ICAddCount=&ICAppClsData=&CLASS_SRCH_WRK2_INSTITUTION$31$=UNCCH&CLASS_SRCH_WRK2_STRM$35$="+term+"&NC_CSE_ATTR_TBL_CRSE_ATTR_VALUE$0=&SSR_CLSRCH_WRK_SUBJECT$0="+dept+"&SSR_CLSRCH_WRK_SSR_EXACT_MATCH1$1="+matchDirection+"&SSR_CLSRCH_WRK_CATALOG_NBR$1="+str(number)+"&SSR_CLSRCH_WRK_ACAD_CAREER$2=&SSR_CLSRCH_WRK_SSR_OPEN_ONLY$chk$3=N&SSR_CLSRCH_WRK_SSR_START_TIME_OPR$4=GE&SSR_CLSRCH_WRK_MEETING_TIME_START$4=&SSR_CLSRCH_WRK_SSR_END_TIME_OPR$4=LE&SSR_CLSRCH_WRK_MEETING_TIME_END$4=&SSR_CLSRCH_WRK_INCLUDE_CLASS_DAYS$5=J&SSR_CLSRCH_WRK_MON$chk$5=Y&SSR_CLSRCH_WRK_MON$5=Y&SSR_CLSRCH_WRK_TUES$chk$5=Y&SSR_CLSRCH_WRK_TUES$5=Y&SSR_CLSRCH_WRK_WED$chk$5=Y&SSR_CLSRCH_WRK_WED$5=Y&SSR_CLSRCH_WRK_THURS$chk$5=Y&SSR_CLSRCH_WRK_THURS$5=Y&SSR_CLSRCH_WRK_FRI$chk$5=Y&SSR_CLSRCH_WRK_FRI$5=Y&SSR_CLSRCH_WRK_SAT$chk$5=Y&SSR_CLSRCH_WRK_SAT$5=Y&SSR_CLSRCH_WRK_SUN$chk$5=Y&SSR_CLSRCH_WRK_SUN$5=Y&SSR_CLSRCH_WRK_SSR_EXACT_MATCH2$6=B&SSR_CLSRCH_WRK_LAST_NAME$6=&SSR_CLSRCH_WRK_DESCR$7=&SSR_CLSRCH_WRK_CLASS_NBR$8=&SSR_CLSRCH_WRK_SSR_UNITS_MIN_OPR$9=GE&SSR_CLSRCH_WRK_UNITS_MINIMUM$9=&SSR_CLSRCH_WRK_SSR_UNITS_MAX_OPR$9=LE&SSR_CLSRCH_WRK_UNITS_MAXIMUM$9=&SSR_CLSRCH_WRK_SSR_COMPONENT$10=&SSR_CLSRCH_WRK_SESSION_CODE$11=&SSR_CLSRCH_WRK_INSTRUCTION_MODE$12=&SSR_CLSRCH_WRK_CAMPUS$13=' \\"
    return queryString

#extract class list(s)
def createSearchCommand(term, state, dept, splitSearch, ICSID, cutoff = 500):
    stateNum = state + 1

    if not splitSearch:
        command = open("COMP_search_curl.sh", "r").read().splitlines()
        command[-1] = makeDeptQuery(term, stateNum, ICSID, dept, 0)
        dept_search_file = "working_files/"+dept+"_search_curl.sh"
        new_command_file = open(dept_search_file, "w")
        for line in command:
            new_command_file.write(line+"\n")
        new_command_file.close()
    else:
        command = open("COMP_search_curl.sh", "r").read().splitlines()
        command[-1] = makeDeptQuery(term, stateNum, ICSID, dept, 2, cutoff)
        dept_search_file = "working_files/second_"+dept+"_search_curl.sh"
        new_command_file = open(dept_search_file, "w")
        for line in command:
            new_command_file.write(line+"\n")
        new_command_file.close()

        command = open("COMP_search_curl.sh", "r").read().splitlines()
        command[-1] = makeDeptQuery(term, stateNum, ICSID, dept, 1, cutoff)
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
    count = 0
    numClasses = 0
    classListData = ""
    while (classListData == "" or numClasses == 0) and count < 3:
        classListData = subprocess.run(["bash", dept_search_file], capture_output=True).stdout.decode("utf-8")
        if classListData == "":
            time.sleep(1)
            print("couldn't get classListData, trying again\n")
            count += 1
            continue
        #extract number of classes
        for line in classListData.splitlines():
            if "class section(s) found" in line:
                numClasses = int(re.sub("[^0-9]", "", line))
                break
        print("number of classes: " + str(numClasses))
        if numClasses == 0:
            time.sleep(1)
            print("no classes, trying again\n")
            count += 1
            
            
    #print("result of command: \n" + classListData)
    #classListData = open("class_list_res.html", "r").read()
    #save classListData to a temp file in working_files directory
    logResponse("working_files/dept_response.txt", classListData)

    #abort if fail
    if numClasses == 0:
        print("wasn't able to find any classes")
        return -1

    return numClasses

def addClassEntry(state, dept_search_file, ICSID, i):
    #form a class_search_curl.sh file by copying info from the dept search headers/cookies and modifying data
    class_search = open(dept_search_file, "r").read().splitlines()
    StateNum = state + 2
    class_search[-1] = "  --data-raw 'ICAJAX=1&ICNAVTYPEDROPDOWN=1&ICType=Panel&ICElementNum=0&ICStateNum="+str(StateNum)+"&ICAction=MTG_CLASS_NBR%24"+str(i)+"&ICModelCancel=0&ICXPos=0&ICYPos=0&ResponsetoDiffFrame=-1&TargetFrameName=None&FacetPath=None&ICFocus=&ICSaveWarningFilter=0&ICChanged=-1&ICSkipPending=0&ICAutoSave=0&ICResubmit=0&ICSID="+ICSID+"&ICActionPrompt=false&ICBcDomData=&ICPanelName=&ICFind=&ICAddCount=&ICAppClsData=' \\"

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
        #save classRawData to a temp file in working_files directory
        logResponse("working_files/class_response.txt", classRawData)
        if classRawData == "":
            time.sleep(1)
            print("couldn't get classRawData, trying again\n")
            count += 1
        else:
            classNum = getContentById("SSR_CLS_DTL_WRK_CLASS_NBR", classRawData)
            if classNum == "":
                time.sleep(1)
                print("couldn't get classNum, trying again\n")
                classRawData = ""
                count += 1

    #parse class data, output html
    className = getContentById("DERIVED_CLSRCH_DESCR200", classRawData)
    classTime = getContentById("MTG_SCHED$0", classRawData)
    instructor = getContentById("MTG_INSTR$0", classRawData)
    room = getContentById("MTG_LOC$0", classRawData)
    unresEnrollmentString = correctEnrollment(getContentById("NC_RC_OPEX_WRK_DESCR1$0", classRawData))
    resEnrollmentString = correctEnrollment(getContentById("NC_RC_OPEX_WRK_DESCR1$1", classRawData))
    waitlistString = correctEnrollment(getContentById("NC_RC_OPEX_WRK_DESCR1$311$$0", classRawData))
    totalSeatsString = getContentById("NC_RC_OPEX_WRK_DESCR1$2", classRawData)
    description = getContentById("DERIVED_CLSRCH_DESCRLONG", classRawData)
    units = getContentById("SSR_CLS_DTL_WRK_UNITS_RANGE", classRawData)
    
    #extra work if this is a COMP class with a topic
    if "COMP" in className and ("89 -" in className or "590 -" in className or "790 -" in className):
        notes = getContentById("DERIVED_CLSRCH_SSR_CLASSNOTE_LONG", classRawData)
        #get the desired title
        specialTitleStart = notes.find("TITLE:") + 7
        specialTitleEnd = notes.find('\n')#getContentById makes sure it always ends with a \n
        #print(notes+"\n"+str(specialTitleStart)+" "+str(specialTitleEnd))
        if specialTitleStart != 6:#if we didn't find TITLE:
        	genericTitleStart = className.find("Topics in Computer Science")
        	className = className[:genericTitleStart] +"Special Topics: "+ notes[specialTitleStart:specialTitleEnd]
        

    #get the total enrollment
    unresNums = unresEnrollmentString.split('/')
    resNums = resEnrollmentString.split('/')
    filledSeats = 0
    if unresEnrollmentString == "Seats filled" and resEnrollmentString == "Seats filled":
        filledSeats = int(totalSeatsString)
    elif unresEnrollmentString != "Seats filled" and resEnrollmentString == "Seats filled":
        filledSeats = int(totalSeatsString) - (int(unresNums[1]) - int(unresNums[0]))
    elif unresEnrollmentString == "Seats filled" and resEnrollmentString != "Seats filled":
        filledSeats = int(totalSeatsString) - (int(resNums[1]) - int(resNums[0]))
    else:
        filledSeats = int(unresNums[0]) + int(resNums[0])

    totalEnrollmentString = str(filledSeats) + "/" + totalSeatsString
	
	
	#nums = enrollmentString.split('/')
    #if len(nums) < 2:
    #    return enrollmentString
    #return str(int(nums[1])-int(nums[0]))+"/"+nums[1]

    #add html
    totalEnrollmentTD = getColoredTD(totalEnrollmentString)
    waitlistTD = getColoredTD(waitlistString)

    tableLines = "<tr><td>"+classNum+"</td><td>"+className+"</td><td>"+classTime+"</td><td>"+instructor+"</td><td>"+room+"</td><td>"+unresEnrollmentString+"</td><td>"+resEnrollmentString+"</td>"+totalEnrollmentTD+totalEnrollmentString+"</td>"+waitlistTD+waitlistString+"</td></tr>\n<tr class='expandable'><td colspan=7><strong>Description: </strong>"+description+" "+units+"."

    tableLines = tableLines + "</td></tr>\n"

    return tableLines


#term_list = ["spring 2024"]
#term_folder_list = ["spring2024"]
#term_query_string_list = ["2242"]
#term_list = ["summer I 2023", "summer II 2023"]
#term_folder_list = ["summerI2023", "summerII2023"]
#term_query_string_list = ["2233", "2234"]
#term_list = ["fall 2024", "summer I 2024", "summer II 2024"]
#term_folder_list = ["fall2024", "summerI2024", "summerII2024"]
#term_query_string_list = ["2249","2243","2244"]
term_list = ["summer I 2025", "summer II 2025", "fall 2025"]
term_folder_list = ["summerI2025","summerII2025","fall2025"]
term_query_string_list = ["2253","2254","2259"]
numTerms = len(term_list)
termCounter = 0

dept_search_file = "COMP_search_curl.sh"

#extract ICSID from the curl used for the search
dept_search = open(dept_search_file, "r").read().splitlines()
dept_search_data = dept_search[-1]
start_ICSID = dept_search_data.find("ICSID=")
end_ICSID = dept_search_data.find("&", start_ICSID)
ICSID = dept_search_data[start_ICSID+6: end_ICSID]
print("retrieved ICSID "+ICSID+"\n")
#extract state number from the curl used for the search
start_state = dept_search_data.find("ICStateNum=")
end_state = dept_search_data.find("&", start_state)
stateNum = int(dept_search_data[start_state+11:end_state])
print("retrieved ICStateNum "+str(stateNum)+"\n")

while termCounter < numTerms:

    term = term_list[termCounter]
    term_folder = term_folder_list[termCounter]
    term_query_string = term_query_string_list[termCounter]

    #Depts causing problems, to be added back in later: GEOL, MASC, HIST, ROML
    #Can include any dept where there are <130 courses listed with a number under 999
    #COMP needs to be first or there will be issues
    dept_list = ["COMP", "AAAD", "AMST", "ANTH", "APPL", "ASTR", "BCB", "BIOC", "BIOL", "BIOS", "BMME", "BUSI", "CHEM", "CLAR", "CMPL", "COMM", "DATA", "DRAM", "ECON", "EDUC", "EMES", "ENEC", "ENGL", "ENVR", "EPID", "EXSS", "GEOG", "HBEH", "INLS", "LING", "MATH", "MEJO", "NSCI", "PHIL", "PHYS", "PLAN", "PLCY", "POLI", "PSYC", "SOCI", "STOR", "WGST"]
    #any department where there are <130 courses under 500 and another <130 listed over 500
    #needs to go in both dept_list and large_dept_list
    large_dept_list = ["BIOL","CHEM","ENGL", "HIST", "MATH"]
    large_dept_cutoffs = [500, 250, 150, 250, 500]

    if "summer" in term:
        dept_list = ["COMP","AMST", "BIOL", "COMM", "MATH", "STOR"]
        large_dept_list = []

    skipToDept = "COMP" #always set to COMP unless trying to skip ahead

    print("Starting term "+term)
    
    skipDeptCounter = 0

    for dept in dept_list:

        try:
            if dept_list.index(dept) < dept_list.index(skipToDept):
                continue
        except ValueError:
            print("can't skip to the selected department. Will skip assuming it's not in this term.")
            continue

        bigDept = False
        bigCutoff = 500
        if dept in large_dept_list:
            bigDept = True
            bigCutoff = large_dept_cutoffs[large_dept_list.index(dept)]

        print("starting to get data for "+dept)

        dept_search_file = createSearchCommand(term_query_string, stateNum, dept, bigDept, ICSID, bigCutoff)

        numClasses = startClassList(dept_search_file)
        if numClasses == -1 and skipDeptCounter < 4:
            skipDeptCounter += 1
            print("skipping to next department\n")
            continue
        elif numClasses == -1:
            print("something is wrong, giving up\n")
            sys.exit(1)

        #open/read the HTML template into a string.
        html = open("page_template.html", "r").read()

        #text at top of page

        html = html + "<h1>"+dept+" Courses</h1>\n\n"

        html = html + "<p>Here is information about "+dept+" class enrollment for <strong>"+term+"</strong>. Classes with no meeting time listed are not shown. Feel free to <a href='https://cs.unc.edu/~saba'>contact me</a> with any questions/comments/issues. I am happy to add any departments that are missing from these listings, just reach out to ask!</p>\n\n"

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
        html = html + "<table>\n<tr>\n<th>Class Number</th>\n<th>Class</th>\n<th>Meeting Time</th>\n<th>Instructor</th>\n<th>Room</th>\n<th>Unreserved Enrollment</th>\n<th>Reserved Enrollment</th>\n<th>Total Enrollment</th>\n<th>Wait List</th>\n</tr>\n"

        #for each class
        for i in range(numClasses):
            time.sleep(1) #avoid too many queries in a rush
            html = html + addClassEntry(stateNum, dept_search_file, ICSID, i)

        #if this is a big dept, we need to repeat some of this work for the second file
        if bigDept:
            #messy
            dept_search_file = "working_files/second_"+dept+"_search_curl.sh"
            numClasses = startClassList(dept_search_file)
            if numClasses == -1 and skipDeptCounter < 4:
                skipDeptCounter += 1
                print("skipping to next department\n")
                continue
            elif numClasses == -1:
                print("something is wrong, giving up\n")
                sys.exit(1)
            #for each class
            for i in range(numClasses):
                time.sleep(1) #avoid too many queries in a rush
                html = html + addClassEntry(stateNum, dept_search_file, ICSID, i)

            #if i % 10 == 0:
            #    print("processed class number " + str(i))

        #add HTML end stuff and write to file
        html = html + "\n</table>\n</body>\n</html>"
        outFileName = "index.html"
        if dept != "COMP":
            outFileName = dept+"_classes.html"
        outFile = open("working_files/"+term_folder+"/"+outFileName, "w")
        outFile.write(html)
        outFile.close()

		#commenting out this copy operation because AFS isn't working right. Will have to manually copy over for now.
        #subprocess.run(["cp", "working_files/"+term_folder+"/"+outFileName, "/afs/cs.unc.edu/home/saba/public_html/UNC_classes/"+term_folder+"/"+outFileName])
        print("done with "+dept+"!")

    termCounter += 1
    print("done with term "+term+"!\n")

print("done!")
