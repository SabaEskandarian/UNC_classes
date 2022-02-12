function redirect(dir) {
	location.href = "../"+dir+"/";
}

document.write("<select onchange='redirect(this.value)'>\n");
document.write("<option value='spring2022'>Spring 2022</option>\n");
document.write("<option value='summerI2022'>Summer I 2022</option>\n");
document.write("<option value='summerII2022'>Summer II 2022</option>\n");
document.write("</select>");

