function redirect(dir) {
        location.href = "../"+dir+"/";
}

document.write("<form>\n");
document.write("<label for='terms'>Choose a term: </label>\n");
document.write("<select name='terms' onchange='redirect(this.value)'>\n");
document.write("<option value=''>Choose Term</option>\n");
document.write("<option value='fall2025'>Fall 2025</option>\n");
document.write("<option value='summerII2025'>Summer II 2025</option>\n");
document.write("<option value='summerI2025'>Summer I 2025</option>\n");
document.write("<option value='spring2025'>Spring 2025</option>\n");
document.write("<option value='fall2024'>Fall 2024</option>\n");
document.write("<option value='summerII2024'>Summer II 2024</option>\n");
document.write("<option value='summerI2024'>Summer I 2024</option>\n");
document.write("<option value='spring2024'>Spring 2024</option>\n");
document.write("<option value='fall2023'>Fall 2023</option>\n");
document.write("<option value='summerII2023'>Summer II 2023</option>\n");
document.write("<option value='summerI2023'>Summer I 2023</option>\n");
document.write("<option value='spring2023'>Spring 2023</option>\n");
document.write("<option value='fall2022'>Fall 2022</option>\n");
document.write("<option value='spring2022'>Spring 2022</option>\n");
document.write("</select></form>\n");

