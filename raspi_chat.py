#!/usr/bin/env python
# -*- coding: utf-8 -*-
import itchat
from itchat.content import *
from pyqrcode import QRCode
import hashlib
import urllib
import urllib2
import time
import os
import io
import re
import json
import threading


class LetItChat(itchat.Core):
    def __init__(self):
        itchat.Core.__init__(self)
        self.msg_queue = []

    def get_msg_from_queue(self, msgId):
        for msg in self.msg_queue:
            if msg['MsgId'] == msgId:
                return msg

    def me(self):
        return self.storageClass.userName

    def get_QR(self, uuid=None, enableCmdQR=False, picDir=None, qrCallback=None):
        """
            Rewrite the get_QR() function to make it work on Raspberry pi
        """
        uuid = uuid or self.uuid
        qrStorage = io.BytesIO()
        qrCode = QRCode('https://login.weixin.qq.com/l/' + uuid)
        qrCode.png(qrStorage, scale=4)
        if hasattr(qrCallback, '__call__'):
            qrCallback(uuid=uuid, status='0', qrcode=qrStorage.getvalue())
        else:
            if enableCmdQR:
                os.system('reset')
                os.system('qrencode -t UTF8 "%s"' % qrCode.data)
        return qrStorage

    def auto_save(self, msg):
        self.msg_queue.append(msg)
        if msg['Type'] in ['Picture', 'Recording', 'Video', 'Attachment']:
            msg['Text'](msg['FileName'])
            if '@@' in msg['FromUserName']:
                friend = self.search_chatrooms(userName=msg['FromUserName'])
            else:
                friend = self.search_friends(userName=msg['FromUserName'])
            print "%s> Saved %s from %s" % (time.strftime("%H:%M:%S", time.localtime()),
                                            msg['FileName'], friend['NickName'])
        else:
            pass

    def clear_msg(self, msgid):
        for msg in self.msg_queue:
            if msg['MsgId'] == msgid:
                self.msg_queue.remove(msg)
                if msg['Type'] in ['Picture', 'Recording', 'Attachment', 'Video']:
                    try:
                        os.remove(msg['FileName'])
                    except OSError:
                        print "%s Can't find %s, maybe it has been deleted." % \
                              (time.strftime("%H:%M:%S", time.localtime()), msg['FileName'])
                        pass


def zh2py(content):
    show_api_appid = "44703"
    show_api_secret = "b1e4c9dfa292465a96041b3b8888de15"
    show_api_timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
    md5str = "content" + content + \
             "showapi_appid" + show_api_appid + \
             "showapi_timestamp" + show_api_timestamp + show_api_secret
    md5obj = hashlib.md5()
    md5obj.update(md5str)
    show_api_sign = md5obj.hexdigest().upper()
    url = "http://route.showapi.com/99-38"
    send_data = urllib.urlencode([
        ('showapi_appid', show_api_appid)
        , ('showapi_sign', show_api_sign)
        , ('content', content)
        , ('showapi_timestamp', show_api_timestamp)
    ])
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req, data=send_data.encode('utf-8'), timeout=10)
        result = response.read().decode('utf-8')
        result_json = json.loads(result)
        return result_json.get('showapi_res_body').get('data')
    except Exception as e:
        return e.message


def assemble(res):
    letters = res.split(' ')
    statement = ''
    for l in letters:
        L = l.upper()
        newl = L[0] + l[1:]
        statement += newl
    return statement


def timer(robot):
    """
        This is a timer to check whether the old message is timeout or not.
        It will clean the messages over 2 minutes.

    """
    while 1:
        time.sleep(0.1)
        for msg in robot.msg_queue:
            if time.time() - msg['CreateTime'] > 120:
                robot.clear_msg(msg['MsgId'])

if __name__ == '__main__':
    chatRobot = LetItChat()
    timer_thread = threading.Thread(target=timer, args=(chatRobot,))
    timer_thread.setDaemon(True)
    timer_thread.start()

    @chatRobot.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS],
                            isFriendChat=True)
    def display(msg):
        chatRobot.auto_save(msg)
        if msg['Type'] == 'Text':
            content = msg['Text']
        elif msg['Type'] == 'Picture':
            content = "Picture: " + msg['FileName']
        elif msg['Type'] == 'Card':
            content = msg['RecommendInfo']['NickName'] + "profile"
        elif msg['Type'] == 'Map':
            x, y, location = re.search("<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*",
                                       msg['OriContent']).group(1, 2, 3)
            if location is None:
                content = "Longitude: " + str(x) + " Latitude: " + str(y)
            else:
                content = "Location: " + location
        elif msg['Type'] == 'Sharing':
            content = "Sharing"
        elif msg['Type'] == 'Recording':
            content = "Recording"
        elif msg['Type'] == 'Attachment':
            content = "Attachment: " + msg['FileName']
        elif msg['Type'] == 'Video':
            content = "Video: " + msg['FileName']
        else:
            content = "Message"
        from_user = chatRobot.search_friends(userName=msg['FromUserName'])
        from_nickname = assemble(zh2py(from_user['NickName']))
        to_user = chatRobot.search_friends(userName=msg['ToUserName'])
        if not to_user:
            to_nickname = assemble(zh2py(msg['ToUserName']))
        else:
            to_nickname = assemble(zh2py(to_user['NickName']))
        print "%s %s -> %s: %s." % (time.strftime("%H:%M:%S", time.localtime()),
                                    from_nickname, to_nickname, zh2py(content))


    @chatRobot.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS],
                            isGroupChat=True)
    def display(msg):
        chatRobot.auto_save(msg)
        if msg['Type'] == 'Text':
            content = msg['Text']
        elif msg['Type'] == 'Picture':
            content = "Picture: " + msg['FileName']
        elif msg['Type'] == 'Card':
            content = msg['RecommendInfo']['NickName'] + "profile"
        elif msg['Type'] == 'Map':
            x, y, location = re.search("<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*",
                                       msg['OriContent']).group(1, 2, 3)
            if location is None:
                content = "Longitude: " + str(x) + " Latitude: " + str(y)
            else:
                content = "Location: " + location
        elif msg['Type'] == 'Sharing':
            content = "Sharing"
        elif msg['Type'] == 'Recording':
            content = "Recording"
        elif msg['Type'] == 'Attachment':
            content = "Attachment: " + msg['FileName']
        elif msg['Type'] == 'Video':
            content = "Video: " + msg['FileName']
        else:
            content = "Message"
        if '@@' in msg['FromUserName']:
            chat_room = chatRobot.search_chatrooms(userName=msg['FromUserName'])
            chat_room_nickname = assemble(zh2py(chat_room['NickName']))
            from_nickname = assemble(zh2py(msg['ActualNickName']))
            to_user = chatRobot.search_friends(userName=msg['ToUserName'])
            if not to_user:
                to_nickname = assemble(zh2py(msg['ToUserName']))
            else:
                to_nickname = assemble(zh2py(to_user['NickName']))
            print "%s (%s)%s -> %s: %s." % (time.strftime("%H:%M:%S", time.localtime()),
                                            chat_room_nickname, from_nickname, to_nickname, content)
        else:
            chat_room = chatRobot.search_chatrooms(userName=msg['ToUserName'])
            chat_room_nickname = assemble(zh2py(chat_room['NickName']))
            from_nickname = assemble(zh2py(chatRobot.search_friends(userName=msg['FromUserName'])['NickName']))
            print "%s %s -> (%s): %s." % (time.strftime("%H:%M:%S", time.localtime()),
                                          from_nickname, chat_room_nickname, zh2py(content))

    @chatRobot.msg_register([NOTE], isFriendChat=True)
    def forFriendChat(msg):
        """
        if your friend recalled a message
        these codes will be execute
        """
        if re.search(u"<replacemsg><!\[CDATA\[.*撤回了一条消息]]></replacemsg>", msg['Content']) is not None:
            old_msg_id = re.search(u"<msgid>(.*?)</msgid>", msg['Content']).group(1)
            old_msg = chatRobot.get_msg_from_queue(old_msg_id)
            try:
                if old_msg['Type'] == 'Text':
                    reply_content = u': ' + old_msg['Text']
                elif old_msg['Type'] == 'Picture':
                    if old_msg['FileName'][-4:] == '.gif':
                        reply_content = u'上面的表情'
                        """WeChat's official face can't be downloaded"""
                    else:
                        reply_content = u'上面的图片'
                    if old_msg['FromUserName'] != chatRobot.me():
                        chatRobot.send_image(fileDir=old_msg['FileName'], toUserName=old_msg['FromUserName'])
                elif old_msg['Type'] == 'Card':
                    reply_content = u'一张名片\n微信号: \n' + old_msg['RecommendInfo']['Alias']
                elif old_msg['Type'] == 'Map':
                    x, y, location = re.search("<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*",
                                               old_msg['OriContent']).group(1, 2, 3)
                    if location is None:
                        reply_content = u'经度:' + str(x) + u'纬度: ' + str(y)
                    else:
                        reply_content = u'位置: ' + location
                elif old_msg['Type'] == 'Sharing':
                    reply_content = u'一条链接：\n'
                    reply_content += old_msg['Text'] + u'\n'
                    reply_content += old_msg['Url']
                elif old_msg['Type'] == 'Recording':
                    reply_content = u'上面的录音'
                    if old_msg['FromUserName'] != chatRobot.me():
                        chatRobot.send_file(fileDir=old_msg['FileName'], toUserName=old_msg['FromUserName'])
                elif old_msg['Type'] == 'Attachment':
                    reply_content = "Attachment: " + old_msg['FileName']
                elif old_msg['Type'] == 'Video':
                    reply_content = u'上面的视频'
                    if old_msg['FromUserName'] != chatRobot.me():
                        chatRobot.send_video(fileDir=old_msg['FileName'], toUserName=old_msg['FromUserName'])
                else:
                    reply_content = "Message"
                if old_msg['FromUserName'] != chatRobot.me():
                    chatRobot.send(u'你撤回了' + reply_content, old_msg['FromUserName'])
            except TypeError:
                print "Got a TypeError, but nothing serious."
                pass

    # @chatRobot.msg_register([NOTE], isGroupChat=True)
    # def forGroupChat(msg):
    #     """
    #         if your friend recalled a message during group chat these codes will be execute.
    #     """
    #     if re.search(u"<replacemsg><!\[CDATA\[.*撤回了一条消息]]></replacemsg>", msg['Content']) is not None:
    #         old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)
    #         old_msg = chatRobot.get_msg_from_queue(old_msg_id)
    #         old_msg_from = old_msg['ActualNickName']
    #         try:
    #             if old_msg['Type'] == 'Text':
    #                 reply_content = u': ' + old_msg['Text']
    #             elif old_msg['Type'] == 'Picture':
    #                 if old_msg['FileName'][-4:] == '.gif':
    #                     reply_content = u'上面的表情'
    #                     """WeChat's official face can't be downloaded"""
    #                 else:
    #                     reply_content = u'上面的图片'
    #                 if old_msg['FromUserName'] != chatRobot.me():
    #                     chatRobot.send_image(fileDir=old_msg['FileName'], toUserName=old_msg['FromUserName'])
    #             elif old_msg['Type'] == 'Card':
    #                 reply_content = old_msg['RecommendInfo']['NickName'] + "profile"
    #             elif old_msg['Type'] == 'Map':
    #                 x, y, location = re.search("<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*",
    #                                            old_msg['OriContent']).group(1, 2, 3)
    #                 if location is None:
    #                     reply_content = u'经度:' + str(x) + u'纬度: ' + str(y)
    #                 else:
    #                     reply_content = u'位置: ' + location
    #             elif old_msg['Type'] == 'Sharing':
    #                 reply_content = u'一条链接：\n'
    #                 reply_content += old_msg['Text'] + u'\n'
    #                 reply_content += old_msg['Url']
    #             elif old_msg['Type'] == 'Recording':
    #                 reply_content = u'上面的录音'
    #                 if old_msg['FromUserName'] != chatRobot.me():
    #                     chatRobot.send_file(fileDir=old_msg['FileName'], toUserName=old_msg['FromUserName'])
    #             elif old_msg['Type'] == 'Attachment':
    #                 reply_content = "Attachment: " + old_msg['FileName']
    #             elif old_msg['Type'] == 'Video':
    #                 reply_content = u'上面的视频'
    #                 if old_msg['FromUserName'] != chatRobot.me():
    #                     chatRobot.send_video(fileDir=old_msg['FileName'], toUserName=old_msg['FromUserName'])
    #             else:
    #                 reply_content = "Message"
    #             if old_msg['FromUserName'] != chatRobot.me():
    #                 chatRobot.send(old_msg_from + u'撤回了' + reply_content, old_msg['FromUserName'])
    #         except TypeError:
    #             print "Got a TypeError, but nothing serious."
    #             pass

    chatRobot.auto_login(hotReload=True, enableCmdQR=True)
    chatRobot.run(debug=False)
