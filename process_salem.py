#!/usr/bin/python3
"""
Super-hack TEIP4->Jekyll Markdown conversion for SWP

Requires TEI Stylesheets (https://github.com/TEIC/Stylesheets)

Example:
    Script takes no arguments and depends on static resource locations.
        $ python3 process_salem.py
"""
from lxml import etree
import uuid
import os

def mdFrontMatter(case_id, title,date,tags):
    fm = "---\n"
    fm_close = "\n---\n\n"
    fm_vars = {}
    fm_vars["layout"] = "post"
    fm_vars["title"] = case_id + " " + title
    fm_vars["date"] = date
    fm_vars["permalink"] = case_id
    fm_vars["category"] = "swp"
    fm_vars["tags"] = " ".join(tags)
    for key in fm_vars.keys():
        fm+=key+": "+fm_vars[key]+"\n"
    fm+="---\n\n"
    return(fm)

def mdPerson(key, name):
    return("["+name+"](/tag/"+key+".html)")

def main():
    fname = "swp.xml"

    parser = etree.HTMLParser()
    xml = etree.parse(fname,parser)
    root = xml.getroot()
    cases = root.xpath("//div1[@type='case']")
    for case in cases:
        case_id = case.get("id")
        print("Processing case: "+case_id)
        dates = case.xpath(".//date")
        date = dates[0].get("value") if len(dates)>0 else "1960-01-01" # use first date found (!) - TODO: No dates in n89!
        title = case.xpath(".//name[@type='person']")[0].text    #assume that first person named is the case title
        tags = {x.get("key") for x in case.xpath(".//name[@type='person']")}    #use tag system to index people
        docs = case.xpath(".//div2")
        doc_ids = []
        figures = {}
        persons = {}
        for doc in docs:
            doc_id = doc.get("id")
            print("   Processing doc: "+doc_id)
            for figure in doc.xpath(".//figure"):
                if doc_id not in figures: figures[doc_id] = []
                if figure.get("n"): figures[doc_id].append(figure.get("n"))
            for person in doc.xpath(".//name[@type='person']"):
                personkey = person.get("key")
                name = "".join([x for x in person.itertext()]) #grab all child element text, in case of nested tags
                persons[personkey+name] = [personkey,name]
                tail = person.tail
                person.clear()
                person.text = str(hash(personkey+name)) # drop strikethrough, orig tags
                person.tail = tail
            doc_p4 = open("./docs_p4/"+doc_id+".xml", 'w')
            doc_p4.write(etree.tostring(doc, encoding='unicode',method='xml'))
            doc_p4.close()
            os.system("./TEI-XSL/bin/p4totei ./docs_p4/"+doc_id+".xml ./docs_tei/"+doc_id+".xml")
            os.system("./TEI-XSL/bin/teitomarkdown ./docs_tei/"+doc_id+".xml ./docs_md/"+doc_id+".md")
            doc_ids.append(doc_id)

        with open("./cases_md/"+date+"-"+case_id+".md", 'w') as case_md:
            case_md.write(mdFrontMatter(case_id,title,date,tags))
            for doc_id in doc_ids:
                doc_md = open("./docs_md/"+doc_id+".md", 'r')
                case_md.write("\n\n# Document: "+doc_id+"\n\n")
                for figure in figures.get(doc_id) or []:
                    case_md.write("![Figure "+figure+"](/assets/thumb/"+figure+".jpg)\n")
                doc_content = doc_md.read()
                for key in persons:
                    doc_content = doc_content.replace(str(hash(key)), mdPerson(persons[key][0],persons[key][1]))
                case_md.write(doc_content)
                doc_md.close()

main()
