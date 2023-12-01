import time
import config
import asyncio
from typing import List
from helper import Group
from pyrogram import Client


client = Client(config.PHONE_NUMBER, config.API_ID, config.API_HASH, phone_number=config.PHONE_NUMBER)



def getGroupList():
    groupList = []
    for group in config.GROUP_LIST:
        username, timeout = group['username'], group['timeout']
        groupList.append(Group(username, timeout))
    return groupList

async def sendMessage(group: Group, client: Client):
    time.sleep(1)
    print("Sending message to @{}...".format(group.username))
    try: await client.send_message(group.username, config.MESSAGE_TEXT)
    except Exception as e: print(e)
    else: group.set_timeout
    return
    

async def checkMessageTimeout(groupList: List[Group], client: Client):
    while True:
        time.sleep(5)
        for group in groupList:
            if group.is_timeout:
                await sendMessage(group, client)


async def main():
    await client.start()
    groupList = getGroupList()
    await checkMessageTimeout(groupList, client)
    
                

if __name__ == "__main__":
    asyncio.run(main())
    
    
    
    
        


            
            
            
            
    
    



    
