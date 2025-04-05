import sqlite3
import os.path
from os import listdir
from bs4 import BeautifulSoup
import csv

#build a table of term, department, instructor, course (first two tokens of class), total enrollment
con = sqlite3.connect("data.db")
cur = con.cursor()

#create the database if it doesn't already exist
res = cur.execute("SELECT name FROM sqlite_master")
if res.fetchone() is None:
    cur.execute("CREATE TABLE course_data(term, dept, instructor, course, enrollment)")

    #open all folders in working_files dir, read each html file in each folder.
    #only open the ones that are fall or spring
    folders = [name for name in listdir("working_files/")
            if not os.path.isfile("working_files/"+name)
            and ( "fall" in name or "spring" in name )]

    for folder in folders:
        term_name = folder
        files = [name for name in listdir("working_files/"+folder)]
        for file in files:
            #parse files to fill table
            dept = ""
            file_parts = file.split("_")
            if not file_parts[0]:
                continue
            else:
                dept = file_parts[0]
            with open("working_files/"+folder+"/"+file) as f: content = f.read()
            soup = BeautifulSoup(content, "html.parser")
            rows = soup.find_all('tr')
            for row in rows:
                #skip headers row
                if row.find("th"):
                    continue
                #skip the course descriptions, which have a class "expandable"
                if row.has_attr("class"):
                    continue
                cells = row.find_all('td')
                instructor = cells[3].get_text()
                course_parts = cells[1].get_text().split(" ")
                course_name  = course_parts[0]+course_parts[1]
                enrollment = cells[7].get_text().split("/")[0]
                cur.execute("INSERT INTO course_data VALUES(?, ?, ?, ?, ?)", (term_name, dept, instructor, course_name, enrollment))
            con.commit()

#now the DB exists and is populated. Delete the file if it neeeds to be recomputed.
res = cur.execute("SELECT instructor, dept, term, SUM(enrollment) as total_enrollment, COUNT(DISTINCT course) as preps FROM course_data group by dept, instructor, term ORDER BY dept, term, instructor")
#print(res.fetchall())

with open("data.csv", 'w', newline='') as out_file:
    writer = csv.writer(out_file)
    writer.writerow(["instructor", "dept", "term", "total enrollment", "distinct preps"])
    writer.writerows(res.fetchall())

con.close()


