"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat.chat_utils import *
import json
import gol
import  os

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE #client的状态
        self.peer = '' #等待Peer的连接
        self.me = '' #自身的名字
        self.out_msg = ''  #根据自身情况的out_msg
        self.s = s  #client的socket对象

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action":"connect", "target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''

    def proc(self, my_msg, peer_msg):
        self.out_msg = ''

#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    return time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    # self.out_msg += 'Here are all the users in the system:\n'
                    # self.out_msg += logged_in
                    gol.set_value('logged_in', logged_in)


                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer) == True:
                        self.state = S_CHATTING
                        self.out_msg += 'Connect to ' + peer + '. Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n'

                elif my_msg[0] == '?':
                    term = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"search", "target":term}))
                    search_rslt = json.loads(myrecv(self.s))["results"].strip()
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                #Funny things to try
                elif my_msg == 'ping blah blah':
                    mysend(self.s,json.dumps({"action":"alone","from":self.me}))
                    received = json.loads(myrecv(self.s))["message"]
                    self.out_msg += "[Server Response]"+received+"\n\n"


                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                try:
                    #转化成字典的数据格式
                    peer_msg = json.loads(peer_msg)
                except Exception as err :
                    self.out_msg += " json.loads failed " + str(err)
                    return self.out_msg
            
                if peer_msg["action"] == "connect":

                    # ----------your code here------#
                    from_name  = peer_msg["from"]

                    self.state = S_CHATTING
                    self.peer = from_name
                    self.out_msg += "Request from %s\n"%(from_name)
                    self.out_msg += "you are connected with %s \n\n"%(from_name)
                    self.out_msg += '-----------------------------------\n'


                    # ----------end of your code----#
                    
#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0 and "&" in my_msg:     # my stuff going out
                if "file" not in my_msg :
                    my_msg = my_msg.split("&")[1]
                mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "message":my_msg}))
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''

            if len(peer_msg) > 0:    # peer's stuff, coming in
  

                # ----------your code here------#
                peer_msg = json.loads(peer_msg)
                """3 scenarios: 
                peer try to connect with me. 
                peer exchange msg with me. 
                peer disconnect and I am the only one left """
                if peer_msg["action"] == "connect":
                    from_name = peer_msg["from"]
                    self.out_msg = "(%s joined)"%(from_name)+'\n\n'

                elif peer_msg["action"] == "exchange":
                    msg = peer_msg["message"]
                    if "file" in msg:
                        my_msg = msg.split("&")

                        filename = my_msg[1]
                        print(os.getcwd() + "/file" + filename)
                        with open(os.getcwd() + "/file/" + filename, 'w') as file_object:
                            file_object.write(my_msg[2])
                        file_object.close()
                        msg = filename + "     Download complete"
                    self.out_msg = peer_msg["from"]+ msg +'\n\n'
                    gol.set_value("message", peer_msg["from"] + msg +'')


                elif peer_msg["action"] == "disconnect":
                    state = peer_msg["msg"]

                    if state != "everyone left, you are alone":
                        from_name = peer_msg["from"]
                        self.out_msg += "({} left the chat group)\n\n".format(from_name)
                    else:
                        self.peer = ''
                        self.out_msg += "everyone left, you are alone\n\n"
                        self.state = S_LOGGEDIN

                # ----------end of your code----#
                
            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
#==============================================================================
# invalid state
#==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
