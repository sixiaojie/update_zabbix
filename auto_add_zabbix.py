#!/usr/bin/env python
#coding:utf8
import urllib2
import json,sys,os
import param
import MySQLdb
import datetime

class ZabbixApi(object):
    def __init__(self,username="xxx",password="xxxxx",server="http://127.0.0.1/api_jsonrpc.php",host_list='xx',db_host="",db_username="",db_password=""):
        self.username = username
        self.password = password
        self.server = server
        self.list = host_list
        self.db_host = db_host
        self.db_username = db_username
        self.db_passwprd = db_password
        self.log = self.log()
        self.header = {"Content-Type": "application/json"}
        self.token = self.login_token()

    def _reponse(self,data):
        request = urllib2.Request(self.server,data)
        for key in self.header:
            request.add_header(key, self.header[key])
        try:
            result = urllib2.urlopen(request)
        except urllib2.URLError as e:
            print "Failed, Please Check :", e.code
            sys.exit(10)
        return result

    def log(self):
        f = open("./action.log","w+")
        return f

    def logger(self,msg):
        nowTime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log.write("%s: %s\n" %(nowTime,msg))

    def login_token(self):
        data = json.dumps(param.param['user']['login']) %(self.username,self.password)
        result =self._reponse(data)
        response = json.loads(result.read())
        result.close()
        return response['result']

    ### 这里有待优化，例如 json.dumps(param.param['user']['login']) %(self.username,self.password)这样的形式
    def create_host(self,hostname,ip,groupid=2,templateid=10001):
        param.param['host']['create']['params']['host']=hostname
        param.param['host']['create']['params']['interfaces'][0]['ip']=ip
        param.param['host']['create']['params']['groups'][0]['groupid']=groupid
        param.param['host']['create']['params']['templates'][0]['templateid'] = templateid
        param.param['host']['create']['auth']=self.token
        data = json.dumps(param.param["host"]["create"])
        result = self._reponse(data)

    def db(self):
        exist_ip=[]
        db = MySQLdb.connect(host=self.db_host,user=self.db_username,passwd=self.db_passwprd)
        cursor = db.cursor()
        cursor.execute("select ip from zabbix.interface")
        data = cursor.fetchall()
        for ip in data:
            exist_ip.append(ip[0])
        return exist_ip

    def real_ip(self):
        if os.path.isfile(self.list) is False:
            print "%s 不存在" %self.list
            sys.exit(10)
        real_ip_list={}
        with open(self.list) as ip_list:
            for line in ip_list:
                real_ip_list[line.split(" ")[0]] = line.split(" ")[-2]
        return real_ip_list

    def diff_ip(self):
        if os.path.isfile(self.list) is False:
            print "%s 不存在" %self.list
            sys.exit(10)
        zabbix_ip_list=self.db()
        real_ip_list = self.real_ip()
        for item in real_ip_list:
            if item in zabbix_ip_list:
                continue
            else:
                self.logger("增加新的机器到zabbix，机器为：%s:%s" %(real_ip_list[item],item))
                self.create_host(real_ip_list[item],item)


    def remove_unavaiable_host(self):
        remove_ip_list = []
        zabbix_ip=self.db()
        read_ip_list = self.real_ip()
        for ip in zabbix_ip:
            if ip not in read_ip_list:
                remove_ip_list.append(ip)
        if len(remove_ip_list) <10:
            for item in remove_ip_list:
                hostid = self.get_interface(item)
                if hostid == None:
                    continue
                self.logger("从zabbix中去除%s" %item)
                self.delete_host(hostid)


    def get_interface(self,ip):
        param.param['hostinterface']['get']['auth']=self.token
        data = param.param['hostinterface']['get']
        result = self._reponse(json.dumps(data))
        data = json.loads(result.read())['result']
        for item in data:
            if ip == item["ip"]:
                return item["hostid"]

    def delete_host(self,hostid):
        param.param["host"]["delete"]["params"]=[hostid]
        param.param['host']['delete']['auth']=self.token
        data = json.dumps(param.param["host"]["delete"])
        result = self._reponse(data)


if __name__ == "__main__":
    zabbix = ZabbixApi(server="https://xxxxx/api_jsonrpc.php",db_username="xxx",db_password="xxx",db_host="xxx")
    zabbix.diff_ip()
    zabbix.remove_unavaiable_host()



