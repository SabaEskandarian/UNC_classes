import sys
import subprocess
import re
import time
import datetime
from bs4 import BeautifulSoup

#searches for spring 2022 classes numbered under 950
#fails if there are too many results
#may want to switch the class count to be classes <= 500 + classes >=500
#if I want to use this for other departments. For now just focusing on COMP

dept = "COMP"
dept_search_file = "COMP_search_curl.sh"

def getContentById(targetId, data):
    relevantData = ""
    for line in data.splitlines():
        if targetId in line:
            relevantData = relevantData + line + "\n"
    if not relevantData:
        print("couldn't find match for id "+targetId+"!\n")
    soup = BeautifulSoup(relevantData, 'html.parser')
    return str(soup.find(id=targetId).string).replace(u'\xa0', u'&nbsp;')

#rewrite query for the department we want if needed
if len(sys.argv) > 1:
    dept = sys.argv[1]
    new_command = subprocess.run(["sed", "s/COMP/"+dept+"/g", "COMP_search_curl.sh"], capture_output=True).stdout.decode("utf-8")
    dept_search_file = dept+"_search_curl.sh"
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

#get timestamp for start of search
timestamp = datetime.datetime.now()

#open/read the HTML template into a string.
html = open("page_template.html", "r").read()

#for each class
for i in range(numClasses):
    time.sleep(1) #avoid too many queries in a rush

    #get the query template for searching the class (modify template in file)
    new_command = subprocess.run(["sed", "s/MTG_CLASS_NBR%240/MTG_CLASS_NBR%24"+str(i)+"/g", "class_search_curl.sh"], capture_output=True).stdout.decode("utf-8")
    class_search_file = "working_files/temp_class_search_curl.sh"
    new_command_file = open(class_search_file, "w")
    new_command_file.write(new_command)
    new_command_file.close()

    #run query
    classRawData = subprocess.run(["bash", class_search_file], capture_output=True).stdout.decode("utf-8")

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

    #add html
    tableLine = "<tr><td>"+classNum+"</td><td>"+className+"</td><td>"+classTime+"</td><td>"+instructor+"</td><td>"+room+"</td><td>"+enrollment+"/"+enrollmentMax+"</td><td>"+waitlist+"/"+waitlistMax+"</td></tr>\n"

    descriptionLine = "<tr class='expandable'><td colspan=7><strong>Description: </strong>"+description+"</td></tr>\n"

    html = html + tableLine + descriptionLine

    print("processed class number " + str(i))

#add HTML end stuff and write to file
html = html + "\n</table>\nData last updated: "+str(timestamp)+"\n</body>\n</html>"
outFile = open("working_files/comp_classes.html", "w")
outFile.write(html)
outFile.close()

#copy file to server
subprocess.run(["scp", "working_files/comp_classes.html", "login.cs.unc.edu:~/www/COMP_classes/index.html"])
print("done!")
