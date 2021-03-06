import os
import argparse
import io
import codecs
import json
import re
# import requests
from os import listdir
from os.path import isdir, exists, join
from re import split

sdks = {}
clientClass = {}

def generateDocsMap(apiDefinitionsPath, apiDefinitionsRelativeFilePath):

    filesInDir = [f for f in listdir(apiDefinitionsPath) if isdir(join(apiDefinitionsPath, f))]
    for file in filesInDir :
        serviceJsonFileName = join(apiDefinitionsPath, join(file, apiDefinitionsRelativeFilePath))

        if(exists(serviceJsonFileName)) :
            with codecs.open(serviceJsonFileName, 'rb', 'utf-8') as api_definition:
                api_content = json.loads(api_definition.read())
                if "uid" in api_content["metadata"].keys():
                    sdks[api_content["metadata"]["uid"]] = file
                clientClass[api_content["metadata"]["uid"]] = getClientClassNameFromMetadata(api_content["metadata"])

#                 # Below  code can be used for debugging  failing clients
#                 str  = "https://sdk.amazonaws.com/java/api/latest/software/amazon/awssdk/services/"+ file +"/"+getClientClassNameFromMetadata(api_content["metadata"])+".html"+"#validateTemplate--"
#                 ret = requests.head(str)
#                 if( ret.status_code != 200 ):
#                     print(str)

    return sdks

def splitOnWordBoundaries(toSplit) :
    result = toSplit
    result = re.sub(r'[^A-Za-z0-9]+', " ", result)
    result = re.sub(r'([^a-z]{2,})v([0-9]+)', r'\g<1> v\g<2>' , result)
    result = re.sub(r'([^A-Z]{2,})V([0-9]+)', r'\g<1> V\g<2>', result)
    result = re.sub(r'(?<=[a-z])(?=[A-Z]([a-zA-Z]|[0-9]))', r' ', result)
    result = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\g<1> \g<2>', result)
    result = re.sub(r'([0-9])([a-zA-Z])', r'\g<1> \g<2>', result)
    result = re.sub(r' +', ' ', result)
    return result.split(" ");


def capitalize(str):
    if(str is None or len(str) == 0):
        return str
    strFirstCaps = str[0].title() + str[1:]
    return strFirstCaps


def lowerCase(str):
    if(str is None or len(str) == 0):
        return str
    return str.lower()

def pascalCase(str):
    splits = splitOnWordBoundaries(str)
    modifiedStr = ""
    for i in range(0, len(splits)) :
        modifiedStr += capitalize(lowerCase(splits[i]))
    return modifiedStr

def getClientClassNameFromMetadata(metadataNode):
    toSanitize = ""
    if "serviceId" in metadataNode.keys():
        toSanitize = metadataNode["serviceId"]
    clientName = pascalCase(toSanitize)
    clientName =  removeLeading(clientName , "Amazon")
    clientName =  removeLeading(clientName, "Aws")
    clientName = removeTrailing(clientName, "Service" )
    return   clientName + "Client"


def removeLeading(str, toRemove) :
    if(str is None) :
        return str
    if(str.startswith(toRemove)):
        return str.replace(toRemove, "")
    return str

def removeTrailing(str, toRemove) :
    if(str is None) :
        return str
    if(str.endswith(toRemove)):
        return str.replace(toRemove, "")
    return str

def insertDocsMapToRedirect(apiDefinitionsBasePath, apiDefinitionsRelativeFilePath, templateFilePath, outputFilePath):
    generateDocsMap(apiDefinitionsBasePath, apiDefinitionsRelativeFilePath)
    output = ""
    with codecs.open(templateFilePath, 'rb', 'utf-8') as redirect_template:
        current_template = redirect_template.read();
        output = current_template.replace("${UID_SERVICE_MAPPING}", json.dumps(sdks, ensure_ascii=False))
        output = output.replace("${UID_CLIENT_CLASS_MAPPING}", json.dumps(clientClass, ensure_ascii=False))
    with open(outputFilePath, 'w') as redirect_output:
        redirect_output.write(output)

def Main():
    parser = argparse.ArgumentParser(description="Generates a Cross-link redirect file.")
    parser.add_argument("--apiDefinitionsBasePath", action="store")
    parser.add_argument("--apiDefinitionsRelativeFilePath", action="store")
    parser.add_argument("--templateFilePath", action="store")
    parser.add_argument("--outputFilePath", action="store")
    
    args = vars( parser.parse_args() )
    argMap = {}
    argMap[ "apiDefinitionsBasePath" ] = args[ "apiDefinitionsBasePath" ] or "./../services/"
    argMap[ "apiDefinitionsRelativeFilePath" ] = args[ "apiDefinitionsRelativeFilePath" ] or "/src/main/resources/codegen-resources/service-2.json"
    argMap[ "templateFilePath" ] = args[ "templateFilePath" ] or "./scripts/crosslink_redirect.html"
    argMap[ "outputFilePath" ] = args[ "outputFilePath" ] or "./crosslink_redirect.html"
    
    insertDocsMapToRedirect(argMap["apiDefinitionsBasePath"], argMap["apiDefinitionsRelativeFilePath"], argMap["templateFilePath"], argMap["outputFilePath"])
    print("Generated Cross link at " + argMap["outputFilePath"])
    
Main()    
            