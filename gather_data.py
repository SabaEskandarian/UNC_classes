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
#4) search for COMP classes in Spring 2022 with course number <=950, uncheck box about only searching for open classes
#5) right click on the resulting POST request and select copy as curl. 
#6) paste contents into COMP_search_curl.sh in SAME DIRECTORY as script

#currently output text assumes searches for spring 2022 classes numbered under 950
#fails if there are too many results


def getContentById(targetId, data):
    relevantData = ""
    for line in data.splitlines():
        if targetId in line:
            relevantData = relevantData + line + "\n"
    if not relevantData:
        print("couldn't find match for id "+targetId+"!\n")
    soup = BeautifulSoup(relevantData, 'html.parser')
    return str(soup.find(id=targetId).string).replace(u'\xa0', u'&nbsp;')

term = "spring 2022"
dept_search_file = "COMP_search_curl.sh"

#Can include any dept where there are <130 courses listed with a number under 950
#COMP needs to be first or there will be issues
dept_list = ["COMP", "STOR", "AAAD", "WGST", "DRAM", "AMST"]

for dept in dept_list:

    print("starting to get data for "+dept)

    if dept != "COMP":
        new_command = subprocess.run(["sed", "s/COMP/"+dept+"/g", "COMP_search_curl.sh"], capture_output=True).stdout.decode("utf-8")
        dept_search_file = "working_files/"+dept+"_search_curl.sh"
        new_command_file = open(dept_search_file, "w")
        new_command_file.write(new_command)
        new_command_file.close()

    #use curl to get class list
    classListData = subprocess.run(["bash", dept_search_file], capture_output=True).stdout.decode("utf-8")
    #print("result of command: \n" + classListData)
    #classListData = open("class_list_res.html", "r").read()

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

    #extract ICSID from the curl used for the dept search
    dept_search = open(dept_search_file, "r").read().splitlines()
    dept_search_data = dept_search[-2]
    start_ICSID = dept_search_data.find("ICSID=")
    end_ICSID = dept_search_data.find("&", start_ICSID)
    ICSID = dept_search_data[start_ICSID+6: end_ICSID]
    print("retrieved ICSID "+ICSID+"\n")

    #open/read the HTML template into a string.
    html = open("page_template.html", "r").read()

    #text at top of page

    html = html + "<h1>"+dept+" Courses</h1>\n\n"

    html = html + "<p>Here is information about "+dept+" class enrollment for "+term+". Course numbers over 950 are not shown. Feel free to <a href='https://cs.unc.edu/~saba'>contact me</a> with any questions/comments/issues.</p>\n\n"

    html = html + "<p><strong>Click <a id='show'>here</a> to show class descriptions</strong>. Click <a id='hide'>here</a> to hide them.</p>\n\n"

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

        #form a class_search_curl.sh file by copying info from the dept search headers/cookies and modifying data
        class_search = dept_search
        class_search[-2] = "  --data-raw 'ICAJAX=1&ICNAVTYPEDROPDOWN=1&ICType=Panel&ICElementNum=0&ICStateNum=5&ICAction=MTG_CLASS_NBR%24"+str(i)+"&ICModelCancel=0&ICXPos=0&ICYPos=0&ResponsetoDiffFrame=-1&TargetFrameName=None&FacetPath=None&ICFocus=&ICSaveWarningFilter=0&ICChanged=-1&ICSkipPending=0&ICAutoSave=0&ICResubmit=0&ICSID="+ICSID+"&ICActionPrompt=false&ICBcDomData=&ICPanelName=&ICFind=&ICAddCount=&ICAppClsData=' \\"

        #write the class search to a file
        class_file_name = "working_files/class_search_curl.sh"
        class_file = open(class_file_name, "w")
        for line in class_search:
            class_file.write(line+"\n")
        class_file.close()

        #run query
        classRawData = subprocess.run(["bash", class_file_name], capture_output=True).stdout.decode("utf-8")

        #print(classRawData)

        #parse class data, output html
        classNum = getContentById("SSR_CLS_DTL_WRK_CLASS_NBR", classRawData)
        className = getContentById("DERIVED_CLSRCH_DESCR200", classRawData)
        classTime = getContentById("MTG_SCHED$0", classRawData)
        instructor = getContentById("MTG_INSTR$0", classRawData)
        room = getContentById("MTG_LOC$0", classRawData)
        enrollment = getContentById("SSR_CLS_DTL_WRK_ENRL_TOT", classRawData)
        enrollmentMax = getContentById("SSR_CLS_DTL_WRK_ENRL_CAP", classRawData)
        waitlist = getContentById("SSR_CLS_DTL_WRK_WAIT_TOT", classRawData)
        waitlistMax = getContentById("SSR_CLS_DTL_WRK_WAIT_CAP", classRawData)
        description = getContentById("DERIVED_CLSRCH_DESCRLONG", classRawData)

        #if meeting time is TBA, instructor is Staff, and nobody's enrolled, this is probably not a real class
        #NOTE: this is a heuristic, but I think it's a good choice for making the results less cluttered
        if classTime == "TBA" and instructor == "Staff" and int(enrollment) == 0:
            continue

        #add html

        enrollmentTD = "<td>"
        #if class is full, make the enrollment red
        if int(enrollment) >= int(enrollmentMax):
            enrollmentTD = "<td style='color:red'>"

        tableLine = "<tr><td>"+classNum+"</td><td>"+className+"</td><td>"+classTime+"</td><td>"+instructor+"</td><td>"+room+"</td>"+enrollmentTD+enrollment+"/"+enrollmentMax+"</td><td>"+waitlist+"/"+waitlistMax+"</td></tr>\n"

        descriptionLine = "<tr class='expandable'><td colspan=7><strong>Description: </strong>"+description+"</td></tr>\n"

        html = html + tableLine + descriptionLine

        #if i % 10 == 0:
        #    print("processed class number " + str(i))

        #comment out when done testing
        #break early for testing
        #if i == 3:
        #    break

    #add HTML end stuff and write to file
    html = html + "\n</table>\n</body>\n</html>"
    outFileName = "index.html"
    if dept != "COMP":
        outFileName = dept+"_classes.html"
    outFile = open("working_files/"+outFileName, "w")
    outFile.write(html)
    outFile.close()

    subprocess.run(["cp", "working_files/"+outFileName, "/afs/cs.unc.edu/home/saba/public_html/COMP_classes/"+outFileName])
    print("done with "+dept+"!")
print("done!")
