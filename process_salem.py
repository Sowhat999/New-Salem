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
import json

def mdFrontMatter(slug,cat,title,date,tags):
    #fm = "---\n"
    fm = ""
    #fm_close = "\n---\n\n"
    fm_vars = {}
    #fm_vars["layout"] = "post"
    fm_vars["title"] = " ".join(title.split())
    fm_vars["date"] = date
    fm_vars["slug"] = slug
    fm_vars["category"] = cat
    fm_vars["tags"] = ", ".join(tags)
    for key in fm_vars.keys():
        fm+=key+": "+fm_vars[key]+"\n"
    #fm+="---\n\n"
    fm+="\n\n"
    return(fm)

def mdPerson(key, name):
    return("["+name+"](/tag/"+key+".html)")

# Join all text within lxml element, ignoring nested child elements
def xmlTextJoin(element):
    return "".join([x for x in element.itertext()])

# Make directories if they don't exists
def makedirs(file, dirs):
    if not os.path.exists("./"+file):
        os.makedirs("./"+file)
    for d in dirs:
        if not os.path.exists("./"+file+"/"+d):
            os.makedirs("./"+file+"/"+d+"/")

# Only for certain archives, the figures names don't match up with the filenames for some reason
def figureRename(figure):
    if figure[-1] == 'r':
        return figure[0:-1]+'A'
    elif figure[-1] == 'v':
        return figure[0:-1]+'B'
    else:
        return figure

def figureMD(figure):
    thumb = "assets/images/thumb/"+figure+".jpg"
    large = "assets/images/large/"+figure+".jpg"
    print(figure)
    print(figure.startswith("S"))
    if figure.startswith("H"):
        thumb = "archives/MassHist/gifs/"+figureRename(figure)+".gif"
        large = "archives/MassHist/large/"+figureRename(figure)+".jpg"
    elif figure.startswith("B"):
        thumb = "archives/BPL/gifs/"+figureRename(figure)+".gif"
        large = "archives/BPL/LARGE/"+figureRename(figure)+".jpg"
    elif figure.startswith("S"):
        thumb = "archives/Suffolk/small/"+figureRename(figure)+".jpg"
        large = "archives/Suffolk/large/"+figureRename(figure)+".jpg"
    elif figure.startswith("MA"):
        thumb = "archives/MA135/small/"+figure+".jpg"
        large = "archives/MA135/large/"+figure+".jpg"
    elif figure.startswith("eia"):
        thumb = "archives/essex/eia/gifs/"+figure+".gif"
        large = "archives/essex/eia/large/"+figure+".jpg"
    elif figure.startswith("ecca"):
        thumb = "archives/ecca/thumb/"+figure+".jpg"
        large = "archives/ecca/large/"+figure+".jpg"
    elif figure.startswith("mehs"):
        thumb = "archives/MEHS/small/"+figureRename(figure)+".jpg"
        large = "archives/MEHS/large/"+figureRename(figure)+".jpg"
    elif figure.startswith("NYPL"):
        thumb = "archives/NYPL/SMALL/"+figureRename(figure)+".jpg"
        large = "archives/NYPL/LARGE/"+figureRename(figure)+".jpg"
    elif figure.startswith("SCJ"):
        thumb = "archives/SCJ/small/"+figureRename(figure)+".jpg"
        large = "archives/SCJ/large/"+figureRename(figure)+".jpg"
    return'<a href="'+large+'" class="jqueryLightbox">![Figure '+figure+']('+thumb+')</a>\n'

def processSWP(file="swp", post_tag="div1"):
    f = open(file+".xml","r")
    tei = f.read()
    f.close()
    makedirs(file, ["tags","docs_p4","docs_tei","pelican_md","docs_md"])
    tei = tei.replace("http://text.lib.virginia.edu/charent/","./")
    # Replace remote entity references with local
    tei = tei.replace('encoding="UTF-8"','')
    # lxml doesn't like parsing unicode strings if there is an encoding specified
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
    with open("./"+file+"/tags/tags.json", 'w') as tag_list:
        json.dump(alltags, tag_list, sort_keys=True)
    cases = root.xpath("//"+post_tag)
    print("Unknown key persons:\n================")
    for case in cases:
        case_id = case.get("id")
        #print("Processing case: "+case_id)
        dates = case.xpath(".//date")
        date = dates[0].get("value") if len(dates)>0 else "1960-01-01" # use first date found (!) - TODO: No dates in n89!
        title = case_id[0]+case_id[1:].zfill(3)+": "+xmlTextJoin(case.xpath(".//head")[0])    #assume that title is the contents of the head
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
            for figure in doc.xpath(".//figure"):
                if doc_id not in figures: figures[doc_id] = []
                if figure.get("n"): figures[doc_id].append(figure.get("n"))
            for person in doc.xpath(".//name[@type='person']"):
                personkey = person.get("key")
                name = " ".join(xmlTextJoin(person).split())
                persons[personkey+name] = [personkey,name]
                tail = person.tail
                person.clear()
                person.text = str(hash(personkey+name)) # drop strikethrough, orig tags
                person.tail = tail
            doc_p4 = open("./"+file+"/docs_p4/"+doc_id+".xml", 'w')
            doc_p4.write(etree.tostring(doc, encoding='unicode',method='xml'))
            doc_p4.close()
            os.system("./Stylesheets/bin/p4totei ./"+file+"/docs_p4/"+doc_id+".xml ./"+file+"/docs_tei/"+doc_id+".xml")
            os.system("./Stylesheets/bin/teitomarkdown ./"+file+"/docs_tei/"+doc_id+".xml ./"+file+"/docs_md/"+doc_id+".md")
            doc_ids.append(doc_id)
        with open("./"+file+"/pelican_md/"+case_id+".md", 'w') as pelican_md:
            pelican_md.write(mdFrontMatter(case_id,file,title,date,tags))
            for doc_id in doc_ids:
                doc_md = open("./"+file+"/docs_md/"+doc_id+".md", 'r')
                pelican_md.write("\n\n# Document: "+doc_id+"\n\n")
                for figure in figures.get(doc_id) or []:
                    pelican_md.write(figureMD(figure))
                doc_content = doc_md.read()
                for key in persons:
                    doc_content = doc_content.replace(str(hash(key)), mdPerson(persons[key][0],persons[key][1]))
                pelican_md.write(doc_content)
                doc_md.close()

def processSalVRec(file="SalVRec", post_tag="div3"):
    makedirs(file, ["tags","docs_p4","docs_tei","docs_md","pelican_md"])
    # lxml doesn't like parsing unicode strings if there is an encoding specified
    parser = etree.XMLParser()
    xml = etree.parse(file+".xml",parser)
    root = xml.getroot()
    docs = root.xpath("//"+post_tag)
    for doc in docs:
        doc_id = doc.get("id")
        date = doc.get("n")
        title = xmlTextJoin(doc.xpath(".//head")[0])    #assume that title is the contents of the head
        figures = {}
        for figure in doc.xpath(".//figure"):
            if doc_id not in figures: figures[doc_id] = []
            if figure.get("n"): figures[doc_id].append(figure.get("n"))

        doc_p4 = open("./"+file+"/docs_p4/"+doc_id+".xml", 'w')
        doc_p4.write(etree.tostring(doc, encoding='unicode',method='xml'))
        doc_p4.close()
        os.system("./Stylesheets/bin/p4totei ./"+file+"/docs_p4/"+doc_id+".xml ./"+file+"/docs_tei/"+doc_id+".xml")
        os.system("./Stylesheets/bin/teitomarkdown ./"+file+"/docs_tei/"+doc_id+".xml ./"+file+"/docs_md/"+doc_id+".md")

        with open("./"+file+"/pelican_md/"+doc_id+".md", 'w') as pelican_md:
            pelican_md.write(mdFrontMatter(doc_id,file,title,date,[]))
            doc_md = open("./"+file+"/docs_md/"+doc_id+".md", 'r')
            pelican_md.write("\n\n# Document: "+doc_id+"\n\n")
            for figure in figures.get(doc_id) or []:
                pelican_md.write(figureMD(figure))
            doc_content = doc_md.read()
            pelican_md.write(doc_content)
            doc_md.close()

processSWP()
processSalVRec()
