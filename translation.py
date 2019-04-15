from pathlib import os
import sys, uuid, json, asyncio
import logging
import requests

headers = {
    'Ocp-Apim-Subscription-Key': [insert-your-subscription-key],
    'Content-type': 'application/json',
    'X-ClientTraceId': str(uuid.uuid4())
}

async def main():
    base_url = 'https://api.cognitive.microsofttranslator.com'
    path = '/translate?api-version=3.0'
    params = '&to='
    if len(sys.argv) > 2:
        params = params + sys.argv[2]
    else:
        params = params + 'fr'

    constructed_url = base_url + path + params
    if os.path.isdir(sys.argv[1]):
        await translateDirectory(sys.argv[1], constructed_url)
    elif os.path.isfile(sys.argv[1]):
        await translateFile(open(sys.argv[1]), constructed_url)
    else:
        await translateString(sys.argv[1], constructed_url)



async def translateDirectory(dirPath, constructed_url):
    fileList = os.listdir(dirPath)
    try:
        for file in fileList:
            if("_en." in file):
                with open(dirPath+'/'+file) as hybrisFile:
                    translatedFile_fr = await translateFile(hybrisFile, constructed_url, dirPath+'/')
    except Exception as e:
        logging.warning('Error in Translating Directory: {}'.format(e))


async def translateFile(hybrisFile, constructed_url, dirPath=""):
    output_fr = ""
    print("***FileName: %s***" % hybrisFile.name)
    index = hybrisFile.name.rfind('_en.')
    try:
        stringsToTranslate = []
        keysToTranslate = []
        translatedStrings_fr = []
        for cnt, line in enumerate(hybrisFile):
            if (not line.startswith("#")) and "=" in line:
                obj = line.split("=")
                if obj[1]:
                    keysToTranslate.append(obj[0])
                    stringsToTranslate.append({ 'text': obj[1] })
            else:
                keysToTranslate.append(line)
                stringsToTranslate.append({ 'text': "" })

        if len(stringsToTranslate) > 99:
            fromIndex = 0
            while fromIndex < (len(stringsToTranslate)):
                toIndex = fromIndex + 99 if (fromIndex + 99) < len(stringsToTranslate) else len(stringsToTranslate)
                translatedStrings_fr += list(map(lambda x: x["translations"][0]["text"], await translateString(stringsToTranslate[fromIndex:toIndex], constructed_url)))
                fromIndex += 99
        else:
            translationResponse = await translateString(stringsToTranslate, constructed_url)
            translatedStrings_fr = list(map(lambda x: x["translations"][0]["text"], translationResponse))

        outfile = open(hybrisFile.name[:index] + '_fr.' + hybrisFile.name[index+4:], "w+")
        output_fr = map(lambda x, y: x + '=' + y if len(y) > 0 else x+y, list(keysToTranslate), translatedStrings_fr)
        outfile.write(''.join([str(x) for x in list(output_fr)]))
        outfile.close()
        print("**File Translation complete**\n")
    except Exception as e:
        logging.warning('Error in Translating File: {}'.format(e))

async def translateString(body, constructed_url):
    try:
        request = requests.post(constructed_url, headers=headers, json=([{'text': body}] if isinstance(body, str) else list(body)))
        response = request.json()
        if (not isinstance(response, list)) and response["error"]:
            raise Exception(response)
        if isinstance(body, str):
            print("###Response###\n{}".format(response[0]["translations"][0]["text"]))
        return response
    except Exception as e:
        logging.warning('Error in Translating Strings: {}'.format(e))

if __name__ == '__main__':
     loop = asyncio.get_event_loop()
     loop.run_until_complete(main())
