# LetsChat
A program for personal weChat


登录后自动回复功能开启，如果朋友发来的消息超过两分钟没被回复，图灵机器人会替你陪朋友聊天。

反撤回功能：朋友撤回的消息会被直接发送回对方那里
使用要求：

安装Python2.7.10+
安装pip
用pip安装依赖的模块：itchat、pyqrcode、requests等。
默认使用命令行的窗口绘制登录二维码，windows用户使用时，请先删除get_QR()函数的代码，
