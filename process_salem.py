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

def mdFrontMatter(title,tags):
    fm = "---\n"
    fm_close = "\n---\n\n"
    fm_vars = {}
    fm_vars["title"] = title
    fm_vars["tags"] = " ".join(tags)
    for key in fm_vars.keys():
        fm+=key+": "+fm_vars[key]+"\n"
    fm+="---\n\n"
    return(fm)

def main():
    fname = "swp.xml"

    parser = etree.HTMLParser()
    xml = etree.parse(fname,parser)
    root = xml.getroot()
    cases = root.xpath("//div1[@type='case']")
    for case in cases:
        case_id = case.get("id")
        title = case.xpath(".//name[@type='person']")[0].text    #assume that first person named is the case title
        tags = {x.get("key") for x in case.xpath(".//name[@type='person']")}    #use tag system to index people
        docs = case.xpath(".//div2")
        doc_ids = []
        for doc in docs:
            doc_id = doc.get("id")
            doc_p4 = open("./docs_p4/"+doc_id+".xml", 'w')
            doc_p4.write(etree.tostring(doc, encoding='unicode',method='xml'))
            doc_p4.close()
            os.system("./TEI-XSL/bin/p4totei ./docs_p4/"+doc_id+".xml ./docs_tei/"+doc_id+".xml")
            os.system("./TEI-XSL/bin/teitomarkdown ./docs_tei/"+doc_id+".xml ./docs_md/"+doc_id+".md")
            doc_ids.append(doc_id)

        with open("./cases_md/"+case_id+".md", 'w') as case_md:
            case_md.write(mdFrontMatter(title,tags))
            for doc_id in doc_ids:
                doc_md = open("./docs_md/"+doc_id+".md", 'r')
                case_md.write("\n\n# Document: "+doc_id+"\n\n")
                case_md.write(doc_md.read())
                doc_md.close()

main()
