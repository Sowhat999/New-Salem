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
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup, Tag

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
    if not os.path.exists("./output/"+file):
        os.makedirs("./output/"+file)
    for d in dirs:
        if not os.path.exists("./output/"+file+"/"+d):
            os.makedirs("./output/"+file+"/"+d+"/")

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
    elif figure.startswith("Uphv"):
        thumb = "archives/upham/gifs/"+figureRename(figure)+".gif"
        large = "archives/upham/large/"+figureRename(figure)+".jpg"
    return '\n\n<span markdown class="figure">[![Figure '+figure+']('+thumb+')]('+large+')</span>\n\n'

def processSWP(file="swp", post_tag="div1"):
    f = open("./cocoon-xml/"+file+".xml","r")
    tei = f.read()
    f.close()
    makedirs(file, ["tags","_docs_p4","_docs_tei","pelican_md","_docs_md"])
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
    print("Non-LCSH persons:\n================")
    for person in root.xpath("//name[@type='person']"):
        personkey = person.get("key")
        if personkey not in alltags:
            alltags[personkey] = ' '.join(xmlTextJoin(person).split())
            print(personkey+": "+alltags[personkey])
    with open("./output/"+file+"/tags/tags.json", 'w') as tag_list:
        json.dump(alltags, tag_list, sort_keys=True)
    cases = root.xpath("//"+post_tag)
    print("Unknown key persons:\n================")

    for case in cases:
        case_id = case.get("id")
        #print("Processing case: "+case_id)
        dates = case.xpath(".//date")
        date = dates[0].get("value") if len(dates)>0 else "1960-01-01" # use first date found (!) - TODO: No dates in n89!
        case_id_list = re.findall(r"[^\W\d_]+|\d+", case_id)
        for i in range(len(case_id_list)):
            try:
                int(case_id_list[i])
                case_id_list[i] = case_id_list[i].zfill(3)
            except ValueError:
                continue
        # assume that title is the contents of the head
        title = "SWP No. "+"".join(case_id_list)[1:]+": "+xmlTextJoin(case.xpath(".//head")[0])
        tags = {x.get("key") for x in case.xpath(".//name[@type='person']")}    #use tag system to index people
        docs = case.xpath(".//div2")
        if len(docs)==0:
            continue
        doc_ids = []
        figures = {}
        persons = {}
        for doc in docs:
            doc_id = doc.get("id")
            for person in doc.xpath(".//name[@type='person']"):
                if person.get("key") == "unknown":
                    print(' '.join(xmlTextJoin(person).split()) + " ("+doc_id+")")
            continue
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
            doc_p4 = open("./output/"+file+"/_docs_p4/"+doc_id+".xml", 'w')
            doc_p4.write(etree.tostring(doc, encoding='unicode',method='xml'))
            doc_p4.close()
            os.system("./Stylesheets/bin/p4totei ./output/"+file+"/_docs_p4/"+doc_id+".xml ./output/"+file+"/_docs_tei/"+doc_id+".xml")
            os.system("./Stylesheets/bin/teitomarkdown ./output/"+file+"/_docs_tei/"+doc_id+".xml ./output/"+file+"/_docs_md/"+doc_id+".md")
            doc_ids.append(doc_id)
        with open("./output/"+file+"/pelican_md/"+case_id+".md", 'w') as pelican_md:
            pelican_md.write(mdFrontMatter(case_id,file,title,date,tags))
            for doc_id in doc_ids:
                doc_md = open("./output/"+file+"/_docs_md/"+doc_id+".md", 'r')
                pelican_md.write('\n\n<div markdown class="doc" id="'+doc_id+'">\n\n<div class="doc_id">SWP No. '+doc_id[1:]+'</div>\n\n')
                for figure in figures.get(doc_id) or []:
                    pelican_md.write(figureMD(figure))
                doc_content = doc_md.read()
                for key in persons:
                    doc_content = doc_content.replace(str(hash(key)), mdPerson(persons[key][0],persons[key][1]))
                pelican_md.write(doc_content)
                pelican_md.write('\n\n</div>\n\n')
                doc_md.close()

def processSalVRec(file="SalVRec", post_tag="div3"):
    makedirs(file, ["tags","_docs_p4","_docs_tei","_docs_md","pelican_md"])
    # lxml doesn't like parsing unicode strings if there is an encoding specified
    parser = etree.XMLParser()
    xml = etree.parse("./cocoon-xml/"+file+".xml",parser)
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

        doc_p4 = open("./output/"+file+"/_docs_p4/"+doc_id+".xml", 'w')
        doc_p4.write(etree.tostring(doc, encoding='unicode',method='xml'))
        doc_p4.close()
        os.system("./Stylesheets/bin/p4totei ./output/"+file+"/_docs_p4/"+doc_id+".xml ./output/"+file+"/_docs_tei/"+doc_id+".xml")
        os.system("./Stylesheets/bin/teitomarkdown ./output/"+file+"/_docs_tei/"+doc_id+".xml ./output/"+file+"/_docs_md/"+doc_id+".md")

        with open("./output/"+file+"/pelican_md/"+doc_id+".md", 'w') as pelican_md:
            pelican_md.write(mdFrontMatter(doc_id,file,title,date,[]))
            doc_md = open("./output/"+file+"/_docs_md/"+doc_id+".md", 'r')
            pelican_md.write('<div markdown class="doc" id="'+doc_id+'">\n\n')
            for figure in figures.get(doc_id) or []:
                pelican_md.write(figureMD(figure))
            doc_content = doc_md.read()
            pelican_md.write(doc_content)
            pelican_md.write('</div>')
            doc_md.close()


# Uses web scraping. Won't work after old-salem is deprecated.
def processBiosWeb(file="bio-index", post_tag="persname"):
    makedirs(file, [])
    parser = etree.XMLParser()
    #xmls = {"mbio":etree.parse("./cocoon-xml/minibios.xml",parser).getroot(),"bio":etree.parse("./cocoon-xml/bios.xml",parser).getroot(),"pics":etree.parse("./cocoon-xml/pics.xml",parser).getroot(),"crt":etree.parse("./cocoon-xml/courtexams.xml",parser).getroot()}
    root = etree.parse("./cocoon-xml/"+file+".xml",parser).getroot()
    persons = root.xpath("//"+post_tag)
    bios = []
    with open("./output/"+file+"/index.html", 'w') as output:
        for person in persons:
            if not person.get("mbio"):
                continue
            key = person.get("key")
            bios.append(key)
            residence = person.get("residence")
            cats = person.get("cats")
            name = person.text
            soup = BeautifulSoup("",'html.parser')
            person_div = soup.new_tag("div")
            person_div["id"] = key
            person_div["class"] = "person"
            person_div["data-name"] = name
            person_div["data-cats"] = cats
            person_div["data-residence"] = residence
            swp_link_div = soup.new_tag("div")
            swp_link_div["class"] = "link"
            swp_link = soup.new_tag("a", href="../tag/"+key+".html")
            swp_link.string = "Find in the Court Records"
            swp_link_div.append(swp_link)
            page = urlopen("http://salem.lib.virginia.edu/people?group.num=all&mbio.num="+person.get("mbio"))
            html = BeautifulSoup(page, 'html.parser')
            td = html.find('td', attrs={'style': 'width:80%;vertical-align:top;padding:12px;'})
            for img in td.find_all('img'):
                img["src"] = "../"+img["src"]
            for img_link in td.find_all("a",{"class":"personsLightbox"}):
                img_link['href'] = "../"+img_link['href']
            for a_top in td.find_all("a",{"name":"top"}):
                a_top.extract()
            for a_toplink in td.find_all("a",{"href":"#top"}):
                a_toplink.extract()
            for content in reversed(td.contents):
                person_div.insert(0, content.extract())
            person_div.append(swp_link_div)
            output.write(str(person_div))
    with open("./output/"+file+"/bios.json", 'w') as output:
        json.dump(bios,output)


# Bad. Produces output, but badly mauls figures with built-in TEI XSLs. Use alternate webscraping function if available.
def processBiosLocal(file="bio-index", post_tag="persname"):
    makedirs(file, ["tags","_tei","_html"])
    # lxml doesn't like parsing unicode strings if there is an encoding specified
    parser = etree.XMLParser()
    xmls = {"mbio":etree.parse("./cocoon-xml/minibios.xml",parser).getroot(),"bio":etree.parse("./cocoon-xml/bios.xml",parser).getroot(),"pics":etree.parse("./cocoon-xml/pics.xml",parser).getroot(),"crt":etree.parse("./cocoon-xml/courtexams.xml",parser).getroot()}
    root = etree.parse("./cocoon-xml/"+file+".xml",parser).getroot()
    persons = root.xpath("//"+post_tag)
    for person in persons:
        if not person.get("mbio"):
            continue
        key = person.get("key")
        residence = person.get("residence")
        cats = person.get("cats")
        content = "<div1 id='"+key+"' class='person' data-cats='"+cats+"' data-residence='"+residence+"'>"
        content += etree.tostring(xmls["mbio"].xpath("//div2[@id = '"+person.get("mbio")+"']")[0],encoding="unicode")+"\n\n" if person.get("mbio") is not None else ""
        content += etree.tostring(xmls["bio"].xpath("//div2[@id = '"+person.get("bio")+"']")[0],encoding="unicode")+"\n\n" if person.get("bio") is not None else ""
        content += etree.tostring(xmls["pics"].xpath("//div2[@id = '"+person.get("pics")+"']")[0],encoding="unicode")+"\n\n" if person.get("pics") is not None else ""
        content += etree.tostring(xmls["crt"].xpath("//div2[@id = '"+person.get("crt")+"']")[0],encoding="unicode")+"\n\n" if person.get("crt") is not None else ""
        content+="</div1>"
        p_tei = open("./output/"+file+"/_p4/"+key+".xml", 'w')
        p_tei.write(content)
        p_tei.close()
        os.system("./Stylesheets/bin/p4totei ./output/"+file+"/_p4/"+key+".xml ./output/"+file+"/_tei/"+key+".xml")
        os.system("./Stylesheets/bin/teitohtml ./output/"+file+"/_tei/"+key+".xml ./output/"+file+"/_html/"+key+".html")


def processUpham(file="Uph1Wit", post_tag="div1"):
    makedirs(file, ["tags", "_docs_p4", "_docs_tei", "_docs_md", "pelican_md"])
    # lxml doesn't like parsing unicode strings if there is an encoding specified
    parser = etree.XMLParser()
    xml = etree.parse("./cocoon-xml/"+file+".xml", parser)
    root = xml.getroot()
    docs = root.xpath("//"+post_tag)
    for doc in docs:
        doc_id = doc.get("id")
        date = "01/01/1860"
        # assume that title is the contents of the head
        title = xmlTextJoin(doc.xpath(".//head")[0])
        figures = {}
        for figure in doc.xpath(".//figure"):
            if doc_id not in figures:
                figures[doc_id] = []
            if figure.get("id"):
                figures[doc_id].append(figure.get("id"))
            figure.text = str(hash(figure.get("id")))
        doc_p4 = open("./output/"+file+"/_docs_p4/"+doc_id+".xml", 'w')
        doc_p4.write(etree.tostring(doc, encoding='unicode', method='xml'))
        doc_p4.close()
        os.system("./Stylesheets/bin/p4totei ./output/"+file+"/_docs_p4/" +
                  doc_id+".xml ./output/"+file+"/_docs_tei/"+doc_id+".xml")
        os.system("./Stylesheets/bin/teitomarkdown ./output/"+file +
                  "/_docs_tei/"+doc_id+".xml ./output/"+file+"/_docs_md/"+doc_id+".md")

        with open("./output/"+file+"/pelican_md/"+doc_id+".md", 'w') as pelican_md:
            pelican_md.write(mdFrontMatter(doc_id, file, title, date, []))
            doc_md = open("./output/"+file+"/_docs_md/"+doc_id+".md", 'r')
            pelican_md.write('<div markdown class="doc" id="'+doc_id+'">\n\n')
            doc_content = doc_md.read()
            for figure in figures.get(doc_id) or []:
                doc_content = doc_content.replace(str(hash(figure)), figureMD(figure))
            pelican_md.write(doc_content)
            pelican_md.write('</div>')
            doc_md.close()


#processBiosWeb()
processSWP()
#processSalVRec()
#processUpham()
