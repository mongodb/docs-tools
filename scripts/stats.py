#!/usr/bin/python

import os
import re
import copy
# obtain a list of the latest git log

script_dir=os.path.dirname(os.path.realpath(__file__))

output=os.popen("git --no-pager log --format='format:%an %ae %ai'  --numstat --since='2014-09-04' locale/zh ").read()
#print output

articles = {}
cur={}
for line in output.splitlines():
    words = line.split()
    if (len(words)>3):
        cur["author"] = words[0]
        cur["email"] = words[1]
        cur["date"] =  words[2]
        cur["time"] = words[3]
        if not "@" in words[1] and "@" in words[2]:
            cur["email"] = words[2]
            cur["date"] = words[3]
            cur["time"] = words[4]
        #print cur["name"]
    elif ( line == ""): 
        cur = {}
        continue
    elif (len(words) == 3):
        aname = words[2]
        aname = aname.replace("locale/zh/LC_MESSAGES/", "")
        aobj =  articles[aname] if aname in articles else {}
        revs = aobj['revisions'] if 'revisions' in aobj else []
        if(not cur):
            print "Error parsing %s" %(words)
            continue
        rev = copy.copy(cur)
        rev["added"] = words[0]
        rev["deleted"] = words[1]

        revs.insert(0, rev)
        aobj["revisions"] = revs
        aobj["name"] = aname
        if(len(revs) == 1):
            aobj["last_updated"] = rev["date"]+" "+rev["time"]
        articles[aname] = aobj

    else:
        print "ERROR ######## " + line 


file = open( script_dir+"/index.html.template")
contents = file.read()

### obtain all pages ####
matches = re.finditer('reference.*?href="(.*).html"', contents)  
all_pages=[]
for m in matches:
    pname = m.group(1)
    if(pname.find("reference/") == 0):
        continue
    all_pages.append(pname)
    #print m.group(1) +" #####"

print "Total pages %d" %(len(all_pages))



# Leader board
translated = 0
leaders = {}
for aname in sorted(articles, key=articles.get):
    last_author = ""
    article = articles[aname]
    revs = article["revisions"]

    if(len(revs)>0):
        last_author = revs[0]['author']
    #print "%s %s" %(aname, last_author)

    # todo: calculate main author
    main_author = last_author 
    leaders[main_author] = 1 if main_author not in leaders else leaders[main_author]+1

    article["main_author"] = main_author
    article["last_author"] = last_author

    if(aname.replace(".po", "") in all_pages):
        translated +=1
    #print line
    #print "%d %s" %(count, line)
    #for word in line.split():

percent_completed = float(translated)/(len(all_pages)) 

pixels = 600 * percent_completed 

print "#### Leader Board (%s translated out of %s pages) #####" %(translated, len(all_pages))
str='<div style="width:600px;height:50px;background-color:#DDD;border:2px solid green"><div style="background-color:green;width:%dpx;height:46px;color:white;font-weight:bold;font-size:16px;padding:10px">%d%% (%s out of %d) completed</div> </div>' %(pixels, percent_completed*100, translated, len(all_pages) )
str+="<table><tr><th width=200>Translator</th><th>Count</th></tr>"
for author in sorted(leaders, key=lambda key: leaders[key] , reverse=True):
    print "%s\t%d" %(author, leaders[author])
    str+="<tr><td>%s</td><td>%d</td></tr>" %(author, leaders[author])
str+="</table>"
contents = contents.replace("<!--TranslationProgress-->", str)

print "##########  Most Recent Translations ##############"

str="<table><tr><th width='300'>Page</th><th width='200'>Translator</th><th>Date</th></tr>"
count = 20
for aname in sorted(articles, key=lambda key: articles[key]['last_updated'], reverse=True):    
    if(count == 0):
        break
    print  "%s - %s at %s" %(aname.replace(".po",""), articles[aname]["main_author"], articles[aname]['last_updated'])
    str+="<tr><td><a href='%s'>%s</a></td><td> %s</td> <td> %s</td></tr>" %(aname.replace(".po",".html"),aname.replace(".po",""), articles[aname]["main_author"], articles[aname]['last_updated'])
        
    count-=1
    link=aname.replace(".po", ".html")
str+="</table>"
contents = contents.replace("<!--MostRecentTen-->", str)

printed=""
str="<table> "
print "##########  Translations by Translators ##############"
for aname in sorted(articles, key=lambda key: articles[key]['main_author']):    
    article = articles[aname]
    if(printed != article['main_author']):
        print "\n---- "+article['main_author']+" -----"
        str+="<tr><td colspan=2><h3>"+article['main_author']+"</h3></td></tr>"
        printed = article['main_author']

    #print  "%s  at %s" %(aname.replace(".po","") , articles[aname]['last_updated'])
    str+="<tr><td><a href='%s'>%s</a></td><td> %s</td></tr>" %(aname.replace(".po",".html") ,aname.replace(".po",""), articles[aname]['last_updated'])
    link=aname.replace(".po", ".html")
str+="</table>"
contents = contents.replace("<!--TranslationList-->", str)

error_file  = open( "po-errors")
errors = error_file.read()
#if(not errors):errors = "N/A"
contents = contents.replace("<!--ErrorList-->", errors)    

file=open(script_dir+"/index-generated.html", "w")
file.write(contents)

file=open("./build/master/html-zh/index.html", "w")
file.write(contents)

    # http://localhost:8000/core/sharded-cluster-high-availability.html
# data structure:
sx="""
article -> {       
    revisions: [{
        author: tj,
        author_email: xxx
        date: xxx
        added: 4
        removed: 5
    } ],
    main_author: TJ     
}
"""
#xbsura xbsura@qq.com 2014-09-09 16:37:47 +0800
#2   2   locale/zh/LC_MESSAGES/core/sharding.po
#6   0   locale/zh/LC_MESSAGES/sharding.po

#J evertang@gmail.com 2014-09-08 19:08:45 +0800
#94  12  locale/zh/LC_MESSAGES/core/data-model-operations.po
#1   1   locale/zh/LC_MESSAGES/core/data-models.po
