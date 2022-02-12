function redirect(dir) {
	location.href = "../"+dir+"/";
}

document.write("<form>\n");
document.write("<label for='terms'>Choose a term: </label>\n");
document.write("<select name='terms' onchange='redirect(this.value)'>\n");
document.write("<option value='spring2022'>Spring 2022</option>\n");
//document.write("<option value='summerI2022'>Summer I 2022</option>\n");
//document.write("<option value='summerII2022'>Summer II 2022</option>\n");
//document.write("<option value='fall2022'>Fall 2022</option>\n");
document.write("</select></form>\n");

