#!/usr/bin/python3
"""
Super-hack TEIP4->Jekyll Markdown conversion for SWP

Requires TEI Stylesheets (https://github.com/TEIC/Stylesheets)

Example:
    Script takes no arguments and depends on static resource locations.
        $ python3 process_salem.py
"""
from lxml import etree
import os

fname = "swp.xml"

parser = etree.HTMLParser()
xml = etree.parse(fname,parser)
root = xml.getroot()
cases = root.xpath("//div1[@type='case']")
for case in cases:
    id = case.get("id")
    tags = {x.get("key") for x in case.xpath(".//name[@type='person']")}
    f = open("./cases_p4/"+id+".xml", 'w')
    f.write(etree.tostring(case, encoding='unicode',method='xml'))
    f.close()
    os.system("./TEI-XSL/bin/p4totei ./cases_p4/"+id+".xml ./cases_tei/"+id+".xml")
    os.system("./TEI-XSL/bin/teitomarkdown ./cases_tei/"+id+".xml ./cases_md/"+id+".md")
    with open("./cases_md/"+id+".md", 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write("---\ntags: ")
        for tag in tags:
            f.write(tag+" ")
        f.write("\n---\n\n"+content)
