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
import io
from ruamel.yaml import YAML

def mdFrontMatter(case_id, title,date,tags):
    fm = "---\n"
    fm_close = "\n---\n\n"
    fm_vars = {}
    fm_vars["layout"] = "post"
    fm_vars["title"] = case_id + " " + " ".join(title.split())
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

# Join all text within lxml element, ignoring nested child elements
def xmlTextJoin(element):
    return "".join([x for x in element.itertext()])

def main():
    f = open("swp.xml","r")
    tei = f.read()
    f.close()
    tei = tei.replace("http://text.lib.virginia.edu/charent/","./")
    tei = tei.replace('encoding="UTF-8"','')
    parser = etree.XMLParser()
    xml = etree.parse(io.StringIO(tei),parser)
    root = xml.getroot()
    alltags = {}
    # Use LCSH keywords list as definitive name, if the entry exists
    for keywords in root.xpath("//keywords[@scheme='LCSH']"):
        for keyword in keywords.xpath(".//term"):
            personkey = keyword.get("id")
            if personkey and personkey not in alltags:
                alltags[personkey] = ' '.join(xmlTextJoin(keyword).split())

    #Otherwise, use first instance of name
    unknowns = []
    print("Non-LCSH persons:\n================")
    for person in root.xpath("//name[@type='person']"):
        personkey = person.get("key")
        if personkey not in alltags:
            alltags[personkey] = ' '.join(xmlTextJoin(person).split())
            print(personkey+": "+alltags[personkey])
    with open("./tag_yaml/tags.yml", 'w') as tag_yaml:
        yaml=YAML()
        yaml.default_flow_style = False
        yaml.dump(alltags, tag_yaml)
    cases = root.xpath("//div1")
    print("Unknown key persons:\n================")
    for case in cases:
        case_id = case.get("id")
        #print("Processing case: "+case_id)
        dates = case.xpath(".//date")
        date = dates[0].get("value") if len(dates)>0 else "1960-01-01" # use first date found (!) - TODO: No dates in n89!
        title = xmlTextJoin(case.xpath(".//head")[0])    #assume that title is the contents of the head
        tags = {x.get("key") for x in case.xpath(".//name[@type='person']")}    #use tag system to index people
        docs = case.xpath(".//div2")
        doc_ids = []
        figures = {}
        persons = {}
        for doc in docs:
            doc_id = doc.get("id")
            for person in doc.xpath(".//name[@type='person']"):
                if person.get("key") == "unknown":
                    print(' '.join(xmlTextJoin(person).split()) + " ("+doc_id+")")
            #print("   Processing doc: "+doc_id)
            for figure in doc.xpath(".//figure"):
                if doc_id not in figures: figures[doc_id] = []
                if figure.get("n"): figures[doc_id].append(figure.get("n"))
            for person in doc.xpath(".//name[@type='person']"):
                personkey = person.get("key")
                name = xmlTextJoin(person)
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
