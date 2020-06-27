import sqlite3
import os
import hashlib
import sys
from datetime import datetime
import shutil
import re
import getpass
import math
import socket
from requests import get
import re


"""
Table Name | Fields
----------------------------------------
usr	   | uname, passwd
cudoers	   | un
logs	   | log
login	   | uname, time
inode      | in, fn, ow, gr, perm
grp        | uname, grps
"""


try:
    os.chdir("C:/Users/sanjsark/SarkSys")
    first_try = False
except:
    os.mkdir("C:/Users/sanjsark/SarkSys")
    os.chdir("C:/Users/sanjsark/SarkSys")
    first_try = True

conn = sqlite3.connect("data.db")

cur = conn.cursor()

cudo_ = False
cd = False
cv = ''
is_auth = False

script_run = False
rip = 0
commands = []
alias = {}
g_alias = {}
run_now = False
else_stat = False
while_loop = 0
is_sudo = False
cur_user = ''
is_su = False

root = 'C:/Users/sanjsark/SarkSys/0-ss'
home = ''

live = 1
up = ''

variables = {}

editor_help = {':al': 'Adds a new line after the specified line number\nUsage- :al 3 New added line\n',
               ':aw': 'Adds new word/words after the specfied word number in specified line number\nUsage- :aw 3:2-4 new\n',
               ':dd': 'Deletes the specified line form buffer\nUsage- :dd 3\n',
               ':dw': 'Deletes word/words from from the specified line number\nnUsage- :dw 3:2-4\n',
               ':h': 'Displays help\nUsage- :hl / :hl <command>\n',
               ':ln': 'Displays length of file / length of a line by specifying the line number\nUsage- :ln / :ln 3\n',
               ':pr': 'Print the data in the buffer\nUsage- :pr\n',
               ':q': 'Quit the editor without saving the data\nUsage- :q\n',
               ':q!': 'Quit the text editor wihtout asking for confirmation\nUsage- :q!\n',
               ':rr': 'Replaces a line in place of specified line number\nUsage- :rr 2 This is a new line\n',
               ':rw': 'Replaces word/words in place of specified word/words of a line\nUsage- :rw 3:2-4 new words to replace\n',
               ':sr': 'Searches for the word in the whole file or line specified\nUsage- :sr hi / :sr hi 4\n',
               ':x': 'Save and exit the editor\nUsage- :x\n'}

def enc(s):
    return hashlib.md5(s.encode()).hexdigest()

def userExists(user):
    cur.execute("SELECT * FROM usr WHERE uname='{}'".format(user))
    if cur.fetchone():
        return True
    return False

def addLog(un, tm, cmd,  l):
    s = str(un) + " : " + str(tm) + " : " + str(cmd) + " : " + str(l)
    cur.execute("INSERT INTO logs VALUES ('{}')".format(s))
    conn.commit()

def dt():
    return str(datetime.now())[:19]

def login(usr):
    cur.execute("SELECT * FROM login WHERE uname='{}'".format(usr))
    if cur.fetchone():
        cur.execute("UPDATE login SET time='{}' WHERE uname='{}'".format(dt(), usr))
    else:
        cur.execute("INSERT INTO login VALUES ('{}', '{}')".format(usr, dt()))
    conn.commit()

def llogin(usr):
    cur.execute("SELECT * FROM login WHERE uname='{}'".format(usr))
    if cur.fetchone():
        cur.execute("SELECT time FROM login WHERE uname='{}'".format(usr))
        print("Last Login:", cur.fetchone()[0])

def cleanUp(usr):
    cur.execute("SELECT * FROM cudoers WHERE un='{}'".format(usr))
    if cur.fetchone():
        cur.execute("DELETE FROM cudoers WHERE un='{}'".format(usr))
        conn.commit()

def pd(d, user):
    if user == 'core':
        if d == '/1-core':
            return '~'
        else:
            l = []
            for i in d.split('/'):
                try:
                    l.append(i.split('-')[1])
                except:
                    pass
            return '/' + '/'.join(l)
    else:
        if re.search('/2-home/.*{}$'.format(user), d):
            return '~'
        l = []
        for i in d.split('/'):
            try:
                l.append(i.split('-')[1])
            except:
                pass
        return '/' + '/'.join(l)

def givePerm(usr, i):
    ind = 0
    cur.execute("SELECT * FROM dmask")
    d = int(cur.fetchone()[0])
    cur.execute("SELECT * FROM inode ORDER BY ind DESC LIMIT 1")
    ind = cur.fetchone()[0] + 1
    cur.execute("INSERT INTO inode VALUES ({}, '{}', '{}', '{}', '{}')".format(ind, i, usr, usr, d))
    conn.commit()
    return ind

def remFile(i):
    cur.execute("DELETE FROM inode WHERE ind={}".format(int(i)))
    conn.commit()

def dtb(n):
    if n == '0':
        return '000'
    b = bin(n).replace("0b", "")
    if len(b) < 3:
        c = 3 - len(b)
        b = '0' * c + b
    return b

def prm(f):
    o = []
    if f[0] == '1':
        o.append('r')
    else:
        o.append('-')
    if f[1] == '1':
        o.append('w')
    else:
        o.append('-')
    if f[2] == '1':
        o.append('x')
    else:
        o.append('-')
    return ''.join(o)

def getP(p):
    u = dtb(int(p[0]))
    g = dtb(int(p[1]))
    o = dtb(int(p[2]))
    u = prm(u)
    g = prm(g)
    o = prm(o)
    return u+g+o

def getPerms(i):
    l= []
    cur.execute('SELECT * FROM inode WHERE ind={}'.format(i.split('-')[0]))
    v = cur.fetchone()
    vl = str(v[4])
    if len(vl) < 3:
        vl = (3 - len(vl)) * '0' + vl
    pm = getP(vl)
    l.append(pm)
    l.append(v[2])
    l.append(v[3])
    return l

def isLegalPerm(s):
    try:
        if int(s[0]) > 7 or int(s[1]) > 7 or int(s[2]) > 7:
            return Fasle
        return True
    except:
        return False

def findOwner(f):
    cur.execute("SELECT ow FROM inode WHERE ind={}".format(int(f.split('-')[0])))
    return cur.fetchone()[0]

def isGroup(j):
    cur.execute("SELECT gr FROM inode WHERE ind={}".format(j.split('-')[0]))
    g = cur.fetchone()[0]
    cur.execute("SELECT grps FROM grp WHERE uname='{}'".format(user))
    l = (cur.fetchone()[0]).split('-')
    return g in l

def fixUser():
    with open('C:/Users/sanjsark/SarkSys/0-ss/4-boot/5-login', 'r') as f:
        return f.readline().strip('\n')

def coreLogin():
    print("************* Alert *************")
    print("Error: An error occured while booting the system: login file was not found")
    print("Please enter 'c' to continue as a core user by entering the password or 'e' to exit.")
    if input('-> ').lower().startswith('c'):
        p = ''
        while p == '':
            print("UserName: core")
            p = input("PassWord -> ")
        return ['core', p]
    else:
        sys.exit(0)

def getHostname():
    if not os.path.isdir('C:/Users/sanjsark/SarkSys/0-ss/5-etc'):
        os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/5-etc')
        cur.execute("INSERT INTO inode VALUES(5, 'etc', 'core', 'core', '755')")
    if not os.path.isdir('C:/Users/sanjsark/SarkSys/0-ss/5-etc/9-host'):
        os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/5-etc/9-host')
        cur.execute("INSERT INTO inode VALUES(9, 'host', 'core', 'core', '777')")
    if not os.path.isfile('C:/Users/sanjsark/SarkSys/0-ss/5-etc/9-host/7-hostname'):
        with open('C:/Users/sanjsark/SarkSys/0-ss/5-etc/7-hostname', 'w') as f:
            f.write("SarkSys")
        cur.execute("INSERT INTO inode VALUES(7, 'hostname', 'core', 'core', '766')")
    with open('C:/Users/sanjsark/SarkSys/0-ss/5-etc/9-host/7-hostname', 'r') as f:
        g = f.read()
    conn.commit()
    return g.strip('\n')


def isInt(c):
    try:
        int(c)
        return True
    except:
        return False

def isFloat(c):
    try:
        float(c)
        return True
    except:
        return False

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0"
   if size_bytes < 1024:
        return str(size_bytes)
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def get_file_data(f):
    d  = str((os.stat(str(f)))).split(' ')
    return [datetime.fromtimestamp(int(d[-2][9:-1])).strftime('%B %d, %Y %I:%M'), convert_size(int(d[6][8:-1]))]
    

# Command codes --------------------------------------------------------------------------------------------------------------------------

def clear():
    print("\n" * 40)
    
def su(c, user):
    global is_auth
    global home
    global variables
    global alias
    global g_alias
    global is_su
    #breakpoint()
    if user == 'core':
        if len(c) == 1:
            is_su = True
            return 'core'
        else:
            if userExists(c[1]):
                is_auth = False
                clear()
                llogin(c[1])
                login(c[1])
                for i in os.listdir('C:/Users/sanjsark/SarkSys/0-ss/2-home'):
                    if i.endswith(c[1]):
                        ind = i.split('-')[0]
                #os.chdir('C:/Users/sanjsark/SarkSys/0-ss/2-home/{}-{}'.format(ind, c[1]))
                home = 'C:/Users/sanjsark/SarkSys/0-ss/2-home/{}-{}'.format(ind, c[1])
                variables = {}
                alias = {}
                g_alias = {}
                is_su = True
                return c[1]
            else:
                print("Error: No suh user exists")
                addLog(user, dt(), "su","Error: No suh user exists")
                is_su = True
                return 'core'
    else:
        if len(c) == 1:
            if live:
                p = enc(str(getpass.getpass("[su] PassWord for core -> ")))
            else:
                p = enc(str(input("[su] PassWord for core -> ")))
            cur.execute("SELECT * FROM usr WHERE uname='core' and passwd='{}'".format(p))
            if cur.fetchall():
                clear()
                llogin('core')
                login('core')
                #os.chdir('C:/Users/sanjsark/SarkSys/0-ss/1-core')
                home = 'C:/Users/sanjsark/SarkSys/0-ss/1-core'
                variables = {}
                alias = {}
                g_alias = {}
                is_su = True
                return 'core'
            else:
                print("Error: Incorrect credentials")
                addLog(user, dt(), "su", "Error: Incorrect credentials")
                is_su = True
                return user
        else:
            if userExists(c[1]):
                if live:
                    p = enc(str(getpass.getpass("[su] PassWord for {} -> ".format(c[1]))))
                else:
                    p = enc(str(input("[su] PassWord for {} -> ".format(c[1]))))
                cur.execute("SELECT * FROM usr WHERE uname='{}' and passwd='{}'".format(c[1], p))
                if cur.fetchall():
                    is_auth = False
                    clear()
                    llogin(c[1])
                    login(c[1])
                    if c[1] == 'core':
                        #os.chdir('C:/Users/sanjsark/SarkSys/0-ss/1-core')
                        home = 'C:/Users/sanjsark/SarkSys/0-ss/1-core'
                        variables = {}
                        alias = {}
                        g_alias = {}
                        is_su = True
                        return 'core'
                    for i in os.listdir('C:/Users/sanjsark/SarkSys/0-ss/2-home'):
                        if i.endswith(c[1]):
                            ind = i.split('-')[0]
                    #os.chdir('C:/Users/sanjsark/SarkSys/0-ss/2-home/{}-{}'.format(ind, c[1]))
                    home = 'C:/Users/sanjsark/SarkSys/0-ss/2-home/{}-{}'.format(ind, c[1])
                    variables = {}
                    is_su = True
                    return c[1]
                else:
                    print("Error: Incorrect credentials")
                    addLog(user, dt(), 'su', "Error: Incorrect credentials")
                    is_su = True
                    return user
            else:
                print("Error: No such user exists")
                addLog(user, dt(), 'su', "Error: No such user exists")
                is_su = True
                return user

def useradd(usr):
    global cudo_
    if usr.startswith('$'):
        if usr[1:] in variables:
            usr = variables[usr[1:]]
        else:
            print("E: {}: no such variable".format(usr))
    if user == 'core' or cudo_:
        cur.execute("SELECT * FROM usr WHERE uname='{}'".format(usr))
        if cur.fetchone():
            print("Error: User already exist")
            addLog(user, dt(), 'userad', "Error: User already exist")
        else:
            if live:
                pw = enc(str(getpass.getpass("[userradd] New PassWord for {} -> ".format(usr))))
                cw = enc(str(getpass.getpass("[userradd] Confirm PassWord for {} -> ".format(usr))))
            else:
                pw = enc(str(input("[userradd] New PassWord for {} -> ".format(usr))))
                cw = enc(str(input("[userradd] Confirm PassWord for {} -> ".format(usr))))
            if pw != cw:
                print("E: passwords dont match")
                return
            cur.execute("INSERT INTO usr VALUES ('{}', '{}')".format(usr, pw))
            print("Info: User added successfully")
            addLog(user, dt(), 'useradd', "Info: User added successfully")
            cur.execute("INSERT INTO grp VALUES ('{}', '{}')".format(usr, usr+'-'))
            conn.commit()
            ind = givePerm(usr, usr)
            cur.execute("UPDATE inode SET perm='{}' WHERE ind={}".format('755', int(ind)))
            os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/2-home/{}-{}'.format(str(ind), usr))
        cudo_ = False
    else:
        print("E: Permission denied")
        addLog(user, dt(), 'useradd', "E: Permission denied")

def userdel(usr):
    global cudo_
    if usr.startswith('$'):
        if usr[1:] in variables:
            usr = variables[usr[1:]]
        else:
            print("E: {}: no such variable".format(usr))
    if usr == 'core':
        print("Error: This action is prohibited")
        addLog(user, dt(), 'userdel', "Error: This action is prohibited")
        return
    if user == 'core' or cudo_:
        cur.execute("SELECT * FROM usr WHERE uname='{}'".format(usr))
        if cur.fetchone():
            cur.execute("DELETE FROM usr WHERE uname='{}'".format(usr))
            cleanUp(usr)
            conn.commit()
            for i in os.listdir('C:/Users/sanjsark/SarkSys/0-ss/2-home'):
                if i.endswith(usr):
                    ind = i.split('-')[0]
            shutil.rmtree('C:/Users/sanjsark/SarkSys/0-ss/2-home/{}-{}'.format(ind, usr), ignore_errors = True)
            print("Info: User has been deleted successfully")
            addLog(user, dt(), 'userdel', "Info: User has been deleted successfully")
        else:
            print("Error: User doesn't exist")
            addLog(user, dt(), 'userdel', "Error: User doesn't exist")
        cudo_ = False
    else:
        print("E: Permission denied")
        addLog(user, dt(), 'userdel', "E: Permission denied")

def logs():
    global cudo_
    if  user == 'core' or cudo_:
        cur.execute("SELECT * FROM logs LIMIT 30")
        for i in cur.fetchall():
            for j in i:
                print(j)
        cudo_ = False
    else:
        print("E: Permission denied")
        addLog(user, dt(), 'logs', "E: Permission denied")

def cuadd(c):
    global cudo_
    if user == 'core' or cudo_:
        for i in c[1:]:
            if i.startswith('$'):
                if i[1:] in variables:
                     i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
            cur.execute("SELECT * FROM usr WHERE uname='{}'".format(i))
            if cur.fetchone():
                cur.execute("INSERT INTO cudoers VALUES ('{}')".format(i))
                conn.commit()
                print("Info: User", i, "added to cudoers successfully")
                addLog(user, dt(), 'cuadd', "Info: User " + str(i) + " added to cudoers successfully")
            else:
                print("Error: User", i, " doesn't exist")
                addLog(user, dt(), 'cuadd', "Error: User" + str(i) + " doesn't exist")
        cudo_ = False
    else:
        print("Error: Permission denied.")
        addLog(user, dt(), 'cuadd', "Error: Permission denied.")

def curem(c):
    global cudo_
    if user == 'core' or cudo_:
        for i in c[1:]:
            if i.startswith('$'):
                if i[1:] in variables:
                     i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
            cur.execute("SELECT * FROM usr WHERE uname='{}'".format(i))
            if cur.fetchone():
                cur.execute("DELETE FROM cudoers WHERE un='{}'".format(i))
                conn.commit()
                print("Info: User", i, "deleted from cudoers successfully")
                addLog(user, dt(), 'curem', "Info: User " + str(i) + " deleted from cudoers successfully")
            else:
                print("Error: User", i, " doesn't exist")
                addLog(user, dt(), 'curem', "Error: User" + str(i) + " doesn't exist")
        cudo_ = False
    else:
        print("Error: Permission denied.")
        addLog(user, dt(), 'curem', "Error: Permission denied.")

def culist():
    global cudo_
    if user == 'core' or cudo_:
        cur.execute("SELECT * FROM cudoers")
        for i in cur.fetchall():
            for j in i:
                print(j)
        cudo_ = False
    else:
        print("Error: Permission denied.")
        addLog(user, dt(), 'culist', "Error: Permission denied.")

def passwd(c):
    global cudo_
    if user == 'core':
        if len(c) == 1:
            if live:
                np = getpass.getpass("[passwd] New PassWord -> ")
                cp = getpass.getpass("[passwd] Confirm New PassWord -> ")
            else:
                np = input("[passwd] New PassWord -> ")
                cp = input("[passwd] Confirm New PassWord -> ")
            if np == cp:
                pw = enc(str(np))
                cur.execute("UPDATE usr SET passwd='{}' WHERE uname='{}'".format(pw, user))
                print("Info: PassWord updated successfully for {}".format(user))
                addLog(user, dt(), 'passwd', "Info: PassWord updated successfully for {}".format(user))
            else:
                print("Error: PassWords don't match")
                addLog(user, dt(), 'passwd', "Error: PassWords dont match")
        else:
            if user == 'core' or c[1] != 'core':
                if live:
                    np = getpass.getpass("[passwd] New PassWord -> ")
                    cp = getpass.getpass("[passwd] Confirm New PassWord -> ")
                else:
                    np = input("[passwd] New PassWord -> ")
                    cp = input("[passwd] Confirm New PassWord -> ")
                if np == cp:
                    pw = enc(str(np))
                    cur.execute("UPDATE usr SET passwd='{}' WHERE uname='{}'".format(pw, c[1]))
                    print("Info: PassWord updated successfully for {}".format(c[1]))
                    addLog(user, dt(), 'passwd', "Info: PassWord updated successfully for {}".format(c[1]))
                else:
                    print("Error: PassWords don't match")
                    addLog(user, dt(), 'passwd', "Error: PassWords dont match")
            else:
                print("Error: Permission denied.")
                addLog(user, dt(), 'passwd', "Error: Permission denied.")
        cudo_ = False
    else:
        if len(c) == 1:
            pw = enc(str(getpass.getpass("[passwd] PassWord for {} -> ".format(user))))
            cur.execute("SELECT * FROM usr WHERE uname='{}' AND passwd='{}'".format(user, pw))
            if not cur.fetchone():
                print("Error: incorrect password")
                return
            np = getpass.getpass("[passwd] New PassWord -> ")
            cp = getpass.getpass("[passwd] Confirm New PassWord -> ")
            if np == cp:
                pw = enc(str(np))
                cur.execute("UPDATE usr SET passwd='{}' WHERE uname='{}'".format(pw, user))
                print("Info: PassWord updated successfully for {}".format(user))
                addLog(user, dt(), 'passwd', "Info: PassWord updated successfully for {}".format(user))
            else:
                print("Error: PassWords don't match")
                addLog(user, dt(), 'passwd', "Error: PassWords dont match")
        else:
            if c[1] == user:
                np = getpass.getpass("[passwd] New PassWord -> ")
                cp = getpass.getpass("[passwd] Confirm New PassWord -> ")
                if np == cp:
                    pw = enc(str(np))
                    cur.execute("UPDATE usr SET passwd='{}' WHERE uname='{}'".format(pw, user))
                    print("Info: PassWord updated successfully for {}".format(user))
                    addLog(user, dt(), 'passwd', "Info: PassWord updated successfully for {}".format(user))
                else:
                    print("Error: PassWords don't match")
                    addLog(user, dt(), 'passwd', "Error: PassWords dont match")
            else:
                print("Error: Permission denied.")
                addLog(user, dt(), 'passwd', "Error: Permission denied.")

def pwd():
    cwd = os.getcwd()
    l = os.getcwd().split('\\')[5:]
    ll = []
    for i in l:
        ll.append(i.split('-')[1])
    print('/' + '/'.join(ll))

def ls(c):
    if len(c) == 1:
        d = (os.getcwd().split('\\')[-1])
        p = getPerms(d)[0]
        if user == 'core' or user == findOwner(d):
            if p[0] == 'r':
                for i in os.listdir():
                    if os.path.isfile(i):
                        if not str(i).split('-')[1].startswith('.'):
                            print('- ' + ' ' + str(i).split('-')[1])
                    elif os.path.isdir(i):
                        if not str(i).split('-')[1].startswith('.'):
                            print('d ' + ' ' + str(i).split('-')[1])
            else:
                print("E: Permission denied")
        elif isGroup(d):
            if p[3] == 'r':
                for i in os.listdir():
                    if os.path.isfile(i):
                        if not str(i).split('-')[1].startswith('.'):
                            print('- ' + ' ' + str(i).split('-')[1])
                    elif os.path.isdir(i):
                        if not str(i).split('-')[1].startswith('.'):
                            print('d ' + ' ' + str(i).split('-')[1])
            else:
                print("E: Permission denied")
        else:
            if p[6] == 'r':
                for i in os.listdir():
                    if os.path.isfile(i):
                        if not str(i).split('-')[1].startswith('.'):
                            print('- ' + ' ' + str(i).split('-')[1])
                    elif os.path.isdir(i):
                        if not str(i).split('-')[1].startswith('.'):
                            print('d ' + ' ' + str(i).split('-')[1])
            else:
                print("E: Permission denied")
    else:
        if c[1].startswith('/'):
            r = 'C:/Users/sanjsark/SarkSys/0-ss'
            go = True
            for i in c[1].split('/')[1:]:
                if not go:
                    break
                for j in os.listdir(r):
                    if j.endswith(i) and os.path.isdir(r+'/'+j):
                        p = getPerms(j)[0]
                        if user == 'core' or user == findOwner(j):
                            if p[0] == 'r':
                                r = r + '/' + j
                            else:
                                print("E: Permission denied.")
                                go = False
                        elif isGroup(j):
                            if p[3] == 'r':
                                r = r + '/' + j
                            else:
                                print("E: Permission denied.")
                                go = False
                        else:
                            if p[6] == 'r':
                                r = r + '/' + j
                            else:
                                print("E: Permission denied.")
                                go = False
            if go:
                p = getPerms(j)[0]
                if user == 'core' or user == findOwner(j):
                    if p[0] == 'r':
                        for i in os.listdir(r):
                            if os.path.isfile(i):
                                if not str(i).split('-')[1].startswith('.'):
                                    print('- ' + ' ' + str(i).split('-')[1])
                            elif os.path.isdir(i):
                                if not str(i).split('-')[1].startswith('.'):
                                    print('d ' + ' ' + str(i).split('-')[1])
                    else:
                        print("E: Permission denied.")
                elif isGroup(j):
                    if p[3] == 'r':
                         for i in os.listdir(r):
                            if os.path.isfile(i):
                                if not str(i).split('-')[1].startswith('.'):
                                    print('- ' + ' ' + str(i).split('-')[1])
                            elif os.path.isdir(i):
                                if not str(i).split('-')[1].startswith('.'):
                                    print('d ' + ' ' + str(i).split('-')[1])
                    else:
                        print("E: Permission denied.")
                else:
                    if p[6] == 'r':
                        for i in os.listdir(r):
                            if os.path.isfile(i):
                                if not str(i).split('-')[1].startswith('.'):
                                    print('- ' + ' ' + str(i).split('-')[1])
                            elif os.path.isdir(i):
                                if not str(i).split('-')[1].startswith('.'):
                                    print('d ' + ' ' + str(i).split('-')[1])
                    else:
                        print("E: Permission denied.")
        else:
            if '/' not in c[1]:
                for i in os.listdir():
                    if i.endswith(c[1]) and os.path.isdir(i):
                        p = getPerms(i)[0]
                        if user == 'core' or user == findOwner(i):
                            if p[0] == 'r':
                                for j in os.listdir(i):
                                    if os.path.isfile(i):
                                        if not str(i).split('-')[1].startswith('.'):
                                            print('- ' + ' ' + str(i).split('-')[1])
                                    elif os.path.isdir(i):
                                        if not str(i).split('-')[1].startswith('.'):
                                            print('d ' + ' ' + str(i).split('-')[1])
                                break
                            else:
                                print("E: Permission denied.")
                                break
                        elif isGroup(i):
                            if p[3] == 'r':
                                for j in os.listdir(i):
                                    if os.path.isfile(i):
                                        if not str(i).split('-')[1].startswith('.'):
                                            print('- ' + ' ' + str(i).split('-')[1])
                                    elif os.path.isdir(i):
                                        if not str(i).split('-')[1].startswith('.'):
                                            print('d ' + ' ' + str(i).split('-')[1])
                                break
                            else:
                                print("E: Permission denied.")
                                break
                        else:
                            if p[6] == 'r':
                                for j in os.listdir(i):
                                    if os.path.isfile(i):
                                        if not str(i).split('-')[1].startswith('.'):
                                            print('- ' + ' ' + str(i).split('-')[1])
                                    elif os.path.isdir(i):
                                        if not str(i).split('-')[1].startswith('.'):
                                            print('d ' + ' ' + str(i).split('-')[1])
                                break
                            else:
                                print("E: Permission denied.")
                                break


def ccd(c, cur_d):
    if len(c) == 1:
        os.chdir(home)
    else:
        if c[1].startswith('$'):
                if c[1][1:] in variables:
                    c[1] = variables[c[1][1:]]
                else:
                    print("E: {}: no such variable".format(c[1]))
        if c[1].startswith('..'):
            if '/' in c[1]:
                for i in c[1].split('/'):
                    if i == '..':
                        if os.getcwd() == 'C:\\Users\\sanjsark\\SarkSys\\0-ss':
                            return
                        os.chdir('..')
                    else:
                        for j in os.listdir():
                            if j.endswith(i) and os.path.isdir(j):
                                p = getPerms(j)[0]
                                if user == 'core' or user == findOwner(j):
                                    if p[2] == 'x':
                                        os.chdir(j)
                                    else:
                                        print("E: Permission denied")
                                        os.chdir(cur_d)
                                elif isGroup(j):
                                    if p[5] == 'x':
                                        os.chdir(j)
                                    else:
                                        print("E: Permission denied")
                                        os.chdir(cur_d)
                                else:
                                    if p[8] == 'x':
                                        os.chdir(j)
                                    else:
                                        print("E: Permission denied")
                                        os.chdir(cur_d)
            else:
                if os.getcwd() == 'C:\\Users\\sanjsark\\SarkSys\\0-ss':
                    return
                os.chdir('..')
                            
        elif c[1].startswith('/'):
            if c[1] == '/':
                os.chdir('C:/Users/sanjsark/SarkSys/0-ss')
            else:
                os.chdir('C:/Users/sanjsark/SarkSys/0-ss')
                for i in c[1].split('/')[1:]:
                    found = False
                    for j in os.listdir():
                        if j.endswith(i) and os.path.isdir(j):
                            p = getPerms(j)[0]
                            if user == 'core' or user == findOwner(j):
                                if p[2] == 'x':
                                    os.chdir(j)
                                    found = True
                                    continue
                                else:
                                    print("E: Permission denied")
                                    found = True
                                    os.chdir(cur_d)
                                    continue
                            elif isGroup(j):
                                if p[5] == 'x':
                                    os.chdir(j)
                                    found = True
                                    continue
                                else:
                                    print("E: Permission denied")
                                    found = True
                                    os.chdir(cur_d)
                                    continue
                            else:
                                if p[8] == 'x':
                                    os.chdir(j)
                                    found = True
                                    continue
                                else:
                                    print("E: Permission denied")
                                    found = True
                                    os.chdir(cur_d)
                                    continue
                    if not found:
                        print("E: " + i + " - not found")
                        os.chdir(cur_d)
                        break
        else:
            found = False
            for i in os.listdir():
                if i.endswith(c[1]) and os.path.isdir(i):
                    p = getPerms(i)[0]
                    if user == 'core' or user == findOwner(i):
                        found = True
                        if p[2] == 'x':
                            os.chdir(i)
                        else:
                            print("E: Permission denied")
                    elif isGroup(i):
                        found = True
                        if p[5] == 'x':
                            os.chdir(i)
                        else:
                            print("E: Permission denied")
                    else:
                        found = True
                        if p[8] == 'x':
                            os.chdir(i)
                        else:
                            print("E: Permission denied")
            if not found:
                print("E: no such directory")

def mkdir(c):
    if c[1].startswith('/'):
        print("E: cannot work with absolute path")
    else:
        if '-' in c[1]:
            print("E: " + c[1] + ": filename cannot contain '-'.")
            return
        for i in os.listdir():
            if i.endswith(c[1]):
                print("E: cant create directory: file already exist")
                return
        if c[1].startswith('$'):
                if c[1][1:] in variables:
                    c[1] = variables[c[1][1:]]
                else:
                    print("E: {}: no such variable".format(c[1]))
        d = (os.getcwd().split('\\')[-1])
        p = getPerms(d)[0]
        if user == 'core' or user == findOwner(d):
            if p[1] == 'w':
                i = givePerm(user, c[1])
                os.mkdir(str(i)+'-'+c[1])
            else:
                print("E: Permission denied")
        elif isGroup:
            if p[4] == 'w':
                i = givePerm(user, c[1])
                os.mkdir(str(i)+'-'+c[1])
            else:
                print("E: Permission denied")
        else:
            if p[7] == 'w':
                i = givePerm(user, c[1])
                os.mkdir(str(i)+'-'+c[1])
            else:
                print("E: Permission denied")

def rmdir(c):
    if c[1].startswith('/'):
        print("E: cannot work with absolute path")
    else:
        found = False
        if c[1].startswith('$'):
                if c[1][1:] in variables:
                     c[1] = variables[c[1][1:]]
                else:
                    print("E: {}: no such variable".format(c[1]))
        for i in os.listdir():
            if user == 'core' or (i.endswith(c[1]) and user == findOwner(i)):
                try:
                    os.rmdir(i)
                    remFile(i.split('-')[0])
                    found = True
                except:
                    found = True
                    print("E: folder is not empty")
        if not found:
            print("E: no such directory exist")
                
def touch(c):
    for i in c[1:]:
        found = False
        if '-' in i:
            print("E: " + i + ": filename cannot contain '-'.")
            continue
        if i.startswith('/'):
            print("E: cannot create file using absolute path")
            continue
        for j in os.listdir():
                if j.endswith(i):
                    print("E: cant create file: file already exists.")
                    found = True
                    break
        if not found:
            if i.startswith('$'):
                if i[1:] in variables:
                    i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
            d = os.getcwd().split('\\')[-1]
            p = getPerms(d)[0]
            if user == 'core' or user == findOwner(d):
                if p[1] == 'w':
                    ind = givePerm(user, i)
                    with open(str(ind) + '-' + i, 'w') as f:
                        continue
                else:
                    print("E: Permission denied")
            elif isGroup(d):
                if p[4] == 'w':
                    ind = givePerm(user, i)
                    with open(str(ind) + '-' + i, 'w') as f:
                        continue
                else:
                    print("E: Permission denied")
            else:
                if p[7] == 'w':
                    ind = givePerm(user, i)
                    with open(str(ind) + '-' + i, 'w') as f:
                        continue
                else:
                    print("E: Permission denied")

def rm(c):
    if c[1] == '*':
            for j in os.listdir():
                    if os.path.isfile(j):
                        o = findOwner(j)
                        if user == 'core':
                            os.remove(j)
                            remFile(j.split('-')[0])
                            continue
                        if user != o:
                            print("Error: " + j.split('-')[1] + "- you are not authorized")
                            addLog(user, dt(), 'rm', "Error: " + j.split('-')[1] + "- you are not authorized")
                            continue
                        os.remove(j)
                        remFile(j.split('-')[0])
    else:
        for i in c[1:]:
            found = False
            if i.startswith('$'):
                if i[1:] in variables:
                    i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
            if i.startswith('/'):
                print("E: it does not support absolute path")
            for j in os.listdir():
                if j.endswith(i):
                    if os.path.isfile(j):
                        o = findOwner(j)
                        if user == 'core':
                            os.remove(j)
                            remFile(j.split('-')[0])
                            found = True
                            continue
                        if user != o:
                            print("Error: " + i + "- you are not authorized")
                            addLog(user, dt(), 'rm', "Error: " + i + "- you are not authorized")
                            found = True
                            continue
                        os.remove(j)
                        remFile(j.split('-')[0])
                        found = True
            if not found:
                print('Error:' + i + ' No such file')
                addLog(user, dt(), 'rm', 'Error:' + i + ' No such file')
def ll(c):
    if len(c) == 1:
        d = (os.getcwd().split('\\')[-1])
        p = getPerms(d)[0]
        if user == 'core' or user == findOwner(d):
            if p[0] == 'r':
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isdir(i):
                        get = getPerms(i)
                        if not i.split('-')[1].startswith('.'):
                            print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isfile(i):
                        get = getPerms(i)
                        if not i.split('-')[1].startswith('.'):
                            print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
            else:
                print("E: Permission denied")
        elif isGroup(d):
            if p[3] == 'r':
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isdir(i):
                        get = getPerms(i)
                        if not i.split('-')[1].startswith('.'):
                            print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isfile(i):
                        get = getPerms(i)
                        if not i.split('-')[1].startswith('.'):
                            print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
            else:
                print("E: Permission denied")
        else:
            if p[6] == 'r':
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isdir(i):
                        get = getPerms(i)
                        if not i.split('-')[1].startswith('.'):
                            print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isfile(i):
                        get = getPerms(i)
                        if not i.split('-')[1].startswith('.'):
                            print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
            else:
                print("E: Permission denied")
    else:
        if c[1].startswith('/'):
            r = 'C:/Users/sanjsark/SarkSys/0-ss'
            go = True
            for i in c[1].split('/')[1:]:
                if not go:
                    break
                for j in os.listdir(r):
                    if j.endswith(i) and os.path.isdir(r+'/'+j):
                        p = getPerms(j)[0]
                        if user == 'core' or user == findOwner(j):
                            if p[0] == 'r':
                                r = r + '/' + j
                            else:
                                print("E: Permission denied.")
                                go = False
                        elif isGroup(j):
                            if p[3] == 'r':
                                r = r + '/' + j
                            else:
                                print("E: Permission denied.")
                                go = False
                        else:
                            if p[6] == 'r':
                                r = r + '/' + j
                            else:
                                print("E: Permission denied.")
                                go = False
            if go:
                p = getPerms(j)[0]
                if user == 'core' or user == findOwner(j):
                    if p[0] == 'r':
                        for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isdir(i):
                                get = getPerms(i)
                                if not i.split('-')[1].startswith('.'):
                                    print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                        for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isfile(i):
                                get = getPerms(i)
                                if not i.split('-')[1].startswith('.'):
                                    print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                    else:
                        print("E: Permission denied.")
                elif isGroup(j):
                    if p[3] == 'r':
                         for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isdir(i):
                                get = getPerms(i)
                                if not i.split('-')[1].startswith('.'):
                                    print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                         for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isfile(i):
                                get = getPerms(i)
                                if not i.split('-')[1].startswith('.'):
                                    print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                    else:
                        print("E: Permission denied.")
                else:
                    if p[6] == 'r':
                        for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isdir(i):
                                get = getPerms(i)
                                if not i.split('-')[1].startswith('.'):
                                    print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                        for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isfile(i):
                                get = getPerms(i)
                                if not i.split('-')[1].startswith('.'):
                                    print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                    else:
                        print("E: Permission denied.")
        else:
            if '/' not in c[1]:
                for k in os.listdir():
                    if k.endswith(c[1]) and os.path.isdir(k):
                        p = getPerms(k)[0]
                        if user == 'core' or user == findOwner(k):
                            if p[0] == 'r':
                                for i in os.listdir():
                                    data = get_file_data(i)
                                    if os.path.isdir(i):
                                        get = getPerms(i)
                                        if not i.split('-')[1].startswith('.'):
                                            print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                for i in os.listdir():
                                    data = get_file_data(i)
                                    if os.path.isfile(i):
                                        get = getPerms(i)
                                        if not i.split('-')[1].startswith('.'):
                                            print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                break
                            else:
                                print("E: Permission denied.")
                                break
                        elif isGroup(k):
                            if p[3] == 'r':
                                for i in os.listdir():
                                    data = get_file_data(i)
                                    if os.path.isdir(i):
                                        get = getPerms(i)
                                        if not i.split('-')[1].startswith('.'):
                                            print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                for i in os.listdir():
                                    data = get_file_data(i)
                                    if os.path.isfile(i):
                                        get = getPerms(i)
                                        if not i.split('-')[1].startswith('.'):
                                            print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                break
                            else:
                                print("E: Permission denied.")
                                break
                        else:
                            if p[6] == 'r':
                                for i in os.listdir():
                                    data = get_file_data(i)
                                    if os.path.isdir(i):
                                        get = getPerms(i)
                                        if not i.split('-')[1].startswith('.'):
                                            print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                for i in os.listdir():
                                    data = get_file_data(i)
                                    if os.path.isfile(i):
                                        get = getPerms(i)
                                        if not i.split('-')[1].startswith('.'):
                                            print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                break
                            else:
                                print("E: Permission denied.")
                                break

def la(c):
    if len(c) == 1:
        d = (os.getcwd().split('\\')[-1])
        p = getPerms(d)[0]
        if user == 'core' or user == findOwner(d):
            if p[0] == 'r':
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isdir(i):
                        get = getPerms(i)
                        print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isfile(i):
                        get = getPerms(i)
                        print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
            else:
                print("E: Permission denied")
        elif isGroup(d):
            if p[3] == 'r':
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isdir(i):
                        get = getPerms(i)
                        print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isfile(i):
                        get = getPerms(i)
                        print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
            else:
                print("E: Permission denied")
        else:
            if p[6] == 'r':
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isdir(i):
                        get = getPerms(i)
                        print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                for i in os.listdir():
                    data = get_file_data(i)
                    if os.path.isfile(i):
                        get = getPerms(i)
                        print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
            else:
                print("E: Permission denied")
    else:
        if c[1].startswith('/'):
            r = 'C:/Users/sanjsark/SarkSys/0-ss'
            go = True
            for i in c[1].split('/')[1:]:
                if not go:
                    break
                for j in os.listdir(r):
                    if j.endswith(i) and os.path.isdir(r+'/'+j):
                        p = getPerms(j)[0]
                        if user == 'core' or user == findOwner(j):
                            if p[0] == 'r':
                                r = r + '/' + j
                            else:
                                print("E: Permission denied.")
                                go = False
                        elif isGroup(j):
                            if p[3] == 'r':
                                r = r + '/' + j
                            else:
                                print("E: Permission denied.")
                                go = False
                        else:
                            if p[6] == 'r':
                                r = r + '/' + j
                            else:
                                print("E: Permission denied.")
                                go = False
            if go:
                p = getPerms(j)[0]
                if user == 'core' or user == findOwner(j):
                    if p[0] == 'r':
                        for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isdir(i):
                                get = getPerms(i)
                                print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                        for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isfile(i):
                                get = getPerms(i)
                                print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                    else:
                        print("E: Permission denied.")
                elif isGroup(j):
                    if p[3] == 'r':
                         for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isdir(i):
                                get = getPerms(i)
                                print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                         for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isfile(i):
                                get = getPerms(i)
                                print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                    else:
                        print("E: Permission denied.")
                else:
                    if p[6] == 'r':
                        for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isdir(i):
                                get = getPerms(i)
                                print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                        for i in os.listdir():
                            data = get_file_data(i)
                            if os.path.isfile(i):
                                get = getPerms(i)
                                print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                    else:
                        print("E: Permission denied.")
        else:
            if '/' not in c[1]:
                for k in os.listdir():
                    if k.endswith(c[1]) and os.path.isdir(k):
                        p = getPerms(k)[0]
                        if user == 'core' or user == findOwner(k):
                            if p[0] == 'r':
                                for i in os.listdir(k):
                                    data = get_file_data(i)
                                    if os.path.isdir(k+'/'+i):
                                        get = getPerms(i)
                                        print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                for i in os.listdir(k):
                                    data = get_file_data(i)
                                    if os.path.isfile(k+'/'+i):
                                        get = getPerms(i)
                                        print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                break
                            else:
                                print("E: Permission denied.")
                                break
                        elif isGroup(k):
                            if p[3] == 'r':
                                for i in os.listdir(k):
                                    data = get_file_data(i)
                                    if os.path.isdir(k+'/'+i):
                                        get = getPerms(i)
                                        print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                for i in os.listdir(k):
                                    data = get_file_data(i)
                                    if os.path.isfile(k+'/'+i):
                                        get = getPerms(i)
                                        print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                break
                            else:
                                print("E: Permission denied.")
                                break
                        else:
                            if p[6] == 'r':
                                for i in os.listdir(k):
                                    data = get_file_data(i)
                                    if os.path.isdir(k+'/'+i):
                                        get = getPerms(i)
                                        print('d ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                for i in os.listdir(k):
                                    data = get_file_data(i)
                                    if os.path.isfile(i):
                                        get = getPerms(k+'/'+i)
                                        print('- ' + get[0] + '\t' + get[1] + '\t' + get[2] + '\t' + data[0] + '\t' + data[1] + '\t' + i.split('-')[1])
                                break
                            else:
                                print("E: Permission denied.")
                                break

def chmod(c):
    if not isLegalPerm(c[1]):
        print("Error: " + c[1] + " - illeagal permission")
        addLog(user, dt(), 'chmod', "Error: " + c[1] + " - illeagal permission")
    if c[2] == '*':
        for i in os.listdir():
            cur.execute("SELECT ow FROM inode WHERE ind={}".format(int(i.split('-')[0])))
            vl = cur.fetchone()[0]
            if user == 'core':
                cur.execute("UPDATE inode SET perm='{}' WHERE ind={}".format(c[1], int(i.split('-')[0])))
                conn.commit()
                continue
            if user != vl:
                print("Error: " + i.split('-')[1] + "- you are not authorized")
                addLog(user, dt(), 'chmod', "Error: " + i.split('-')[1] + "- you are not authorized")
                continue
            cur.execute("UPDATE inode SET perm='{}' WHERE ind={}".format(c[1], int(i.split('-')[0])))
            conn.commit()
    else:
        for i in c[2:]:
            if i.startswith('$'):
                if i[1:] in variables:
                    i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
            for j in os.listdir():
                if j.endswith(i):
                    cur.execute("SELECT ow FROM inode WHERE ind={}".format(int(j.split('-')[0])))
                    vl = cur.fetchone()[0]
                    if user == 'core':
                        cur.execute("UPDATE inode SET perm='{}' WHERE ind={}".format(c[1], int(j.split('-')[0])))
                        conn.commit()
                        continue
                    if user != vl:
                        print("Error: " + i + "- you are not authorized")
                        addLog(user, dt(), 'chmod', "Error: " + i + "- you are not authorized") 
                        continue
                    cur.execute("UPDATE inode SET perm='{}' WHERE ind={}".format(c[1], int(j.split('-')[0])))
                    conn.commit()

def dmask(c):
    global cudo_
    if len(c) == 1:
        cur.execute("SELECT dmask FROM dmask")
        c = str(cur.fetchone()[0])
        if len(c) < 3:
            c = (3 - len(c)) * '0' + c
        print(c)
    else:
        if user == 'core' or cudo_:
            if isLegalPerm(c[1]):
                cur.execute("SELECT dmask FROM dmask")
                cur.execute("UPDATE dmask SET dmask={} WHERE dmask={}".format(int(c[1]), int(cur.fetchone()[0])))
                conn.commit()
            else:
                print("E: illegal permission")
            cudo_ = False
        else:
            print("E: Permission denied")
            addLog(user, dt(), 'useradd', "E: Permission denied")
    
def me():
    print("Username:", user)
    cur.execute("SELECT grps FROM grp WHERE uname='{}'".format(user))
    v = cur.fetchone()[0]
    print("Groups:", v.replace('-', ': '))

def groupadd(c):
    global cudo_
    if user == 'core' or cudo_:
        for i in c[1:-1]:
            if i.startswith('$'):
                if i[1:] in variables:
                    i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
            cur.execute("SELECT * FROM usr WHERE uname='{}'".format(i))
            if not cur.fetchone():
                print("E: " + i +" no such user")
                continue
            cur.execute("SELECT grps FROM grp WHERE uname='{}'".format(i))
            cur.execute("UPDATE grp SET grps='{}' WHERE uname='{}'".format(cur.fetchone()[0] + c[-1] +'-', i))
            conn.commit()
    else:
        print("E: Permission denied")
        addLog(user, dt(), 'useradd', "E: Permission denied")
    cudo_ = False

def chown(c):
    cur.execute("SELECT * FROM usr WHERE uname='{}'".format(user))
    if not cur.fetchone():
        print("E: no such user")
        return
    for i in c[2:]:
        if i.startswith('$'):
                if i[1:] in variables:
                    i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
        for j in os.listdir():
            if j.endswith(i):
                o = findOwner(j)
                if o == user or user == 'core':
                    cur.execute("UPDATE inode SET ow='{}' WHERE ind={}".format(c[1], int(j.split('-')[0])))
                    conn.commit()
                else:
                    print("E: " + i + " you are authorized")

def chgroup(c):
    cur.execute("SELECT * FROM usr WHERE uname='{}'".format(user))
    if not cur.fetchone():
        print("E: no such user")
        return
    for i in c[2:]:
        if i.startswith('$'):
                if i[1:] in variables:
                    i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
        for j in os.listdir():
            if j.endswith(i):
                o = findOwner(j)
                if o == user or user == 'core':
                    cur.execute("UPDATE inode SET gr='{}' WHERE ind={}".format(c[1], int(j.split('-')[0])))
                    conn.commit()
                else:
                    print("E: " + i + " you are authorized")

def cat (c):
    for i in c[1:]:
        found = False
        if i.startswith('$'):
                if i[1:] in variables:
                    i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
        for j in os.listdir():
            if j.endswith(i):
                found = True
                p = getPerms(j)[0]
                if user == findOwner(j) or user == 'core':
                    if p[0] == 'r':
                        with open(j, 'r') as f:
                            for i in f.readlines():
                                if i.endswith('\n'):
                                    print(i, end='')
                                else:
                                    print(i)
                    else:
                        print("E: " + i + " - Permission denied")
                elif isGroup(j):
                    if p[3] == 'r':
                        with open(j, 'r') as f:
                            for i in f.readlines():
                                if i.endswith('\n'):
                                    print(i, end='')
                                else:
                                    print(i)
                    else:
                        print("E: " + i + " - Permission denied")
                else:
                    if p[6] == 'r':
                        with open(j, 'r') as f:
                            for i in f.readlines():
                                if i.endswith('\n'):
                                    print(i, end='')
                                else:
                                    print(i)
                    else:
                        print("E: " + i + " - Permission denied")
        if not found:
            print("E: " + i + " - no such file")

def grouprem(c):
    global cudo_
    #breakpoint()
    if user == 'core' or cudo_:
        for i in c[1:-1]:
            if i.startswith('$'):
                if i[1:] in variables:
                    i = variables[i[1:]]
                else:
                    print("E: {}: no such variable".format(i))
                    continue
            cur.execute("SELECT * FROM usr WHERE uname='{}'".format(i))
            if not cur.fetchone():
                print("E: " + i +" no such user")
                continue
            cur.execute("SELECT grps FROM grp WHERE uname='{}'".format(i))
            g = cur.fetchone()[0]
            g = g.replace(c[2]+'-', '')
            cur.execute("UPDATE grp SET grps='{}' WHERE uname='{}'".format(g, i))
            conn.commit()
    else:
        print("E: Permission denied")
        addLog(user, dt(), 'useradd', "E: Permission denied")
    cudo_ = False

def inlog(c):
    global cudo_
    if '-d' in c:
            if not os.path.isdir('C:/Users/sanjsark/SarkSys/0-ss/4-boot'):
                os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/4-boot')
                cur.execute("INSERT INTO inode VALUES(4, 'boot', 'core', 'core', '755')")
            with open('C:/Users/sanjsark/SarkSys/0-ss/4-boot/5-login', 'w') as f:
                pass
    else:
        if user == 'core' or cudo_:
            if not os.path.isdir('C:/Users/sanjsark/SarkSys/0-ss/4-boot'):
                os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/4-boot')
                cur.execute("INSERT INTO inode VALUES(4, 'boot', 'core', 'core', '755')")
            cur.execute("SELECT * FROM usr WHERE uname='{}'".format(c[1]))
            if not cur.fetchone():
                print("E: " + c[1] + " - no such user")
                return
            with open('C:/Users/sanjsark/SarkSys/0-ss/4-boot/5-login', 'r') as f:
                r = f.readline()
            if r:
                print("User: " + r + ", already exist in initial login, do you want to overwrite it? (Y/n): ")
                if not input('-> ').lower().startswith('y'):
                    print('Info: action aborted')
                    return
            with open('C:/Users/sanjsark/SarkSys/0-ss/4-boot/5-login', 'w') as f:
                f.write(c[1])
            cudo_ = False
        else:
            print("E: you are not authorized")

def echo(c):
    #breakpoint()
    global variables
    if '>' in c or '>>' in c:
        if '>' in c and '>>' in c:
            print("E: incorrect use of '>'/'>>'")
        else:
            if '>' in c:
                if c.count('>') > 1:
                    print("E: not more than 1 '>' allowed")
                    return
                if len(c[c.index('>')+1:]) > 1:
                    print("E: only one filename allowd")
                    return
                if '-' in c[-1]:
                    print("E: " + i + ": filename cannot contain '-'.")
                    return
                if c[-1].startswith('/'):
                    print("E: cannot create file using absolute path")
                    return
                d = os.getcwd().split('\\')[-1]
                p = getPerms(d)[0]
                inde = ''
                for k in os.listdir():
                    if os.path.isfile(k) and k.endswith(c[-1]):
                        inde = k.split('-')[0]
                        break
                if user == 'core' or user == findOwner(d):
                    if p[1] == 'w':
                        if inde:
                            ind = int(inde)
                            q = getPerms(k)[0]
                            if user == 'core' or user == findOwner(k):
                                if not q[1] == 'w':
                                    print("E: Permission denied")
                                    return
                            elif isGroup(k):
                                if not q[4] == 'w':
                                    print("E: Permission denied")
                                    return
                            else:
                                if not q[7] == 'w':
                                    print("E: Permission denied")
                                    return
                        else:
                            ind = givePerm(user, c[-1])
                        with open(str(ind) + '-' + c[-1], 'w') as f:
                            l = []
                            for i in c[1:c.index('>')]:
                                if i.startswith('$'):
                                        l.append(variables[i[1:]])
                                elif i.startswith('\\'):
                                    l.append(i[1:])
                                else:
                                    l.append(i)
                            f.write(' '.join(l))
                            f.write('\n')
                    else:
                        print("E: Permission denied")
                elif isGroup(d):
                    if p[4] == 'w':
                        if inde:
                            ind = int(inde)
                            q = getPerms(k)[0]
                            if user == 'core' or user == findOwner(k):
                                if not q[1] == 'w':
                                    print("E: Permission denied")
                                    return
                            elif isGroup(k):
                                if not q[4] == 'w':
                                    print("E: Permission denied")
                                    return
                            else:
                                if not q[7] == 'w':
                                    print("E: Permission denied")
                                    return
                        else:
                            ind = givePerm(user, c[-1])
                        with open(str(ind) + '-' + c[-1], 'w') as f:
                            l = []
                            for i in c[1:c.index('>')]:
                                if i.startswith('$'):
                                        l.append(variables[i[1:]])
                                elif i.startswith('\\'):
                                    l.append(i[1:])
                                else:
                                    l.append(i)
                            f.write(' '.join(l))
                            f.write('\n')
                    else:
                        print("E: Permission denied")
                else:
                    if p[7] == 'w':
                        if inde:
                            ind = int(inde)
                            q = getPerms(k)[0]
                            if user == 'core' or user == findOwner(k):
                                if not q[1] == 'w':
                                    print("E: Permission denied")
                                    return
                            elif isGroup(k):
                                if not q[4] == 'w':
                                    print("E: Permission denied")
                                    return
                            else:
                                if not q[7] == 'w':
                                    print("E: Permission denied")
                                    return
                        else:
                            ind = givePerm(user, c[-1])
                        with open(str(ind) + '-' + c[-1], 'w') as f:
                            l = []
                            for i in c[1:c.index('>')]:
                                if i.startswith('$'):
                                        l.append(variables[i[1:]])
                                elif i.startswith('\\'):
                                    l.append(i[1:])
                                else:
                                    l.append(i)
                            f.write(' '.join(l))
                            f.write('\n')
                    else:
                        print("E: Permission denied")
            else:
                if c.count('>>') > 1:
                    print("E: not more than 1 '>' allowed")
                    return
                if len(c[c.index('>>')+1:]) > 1:
                    print("E: only one filename allowd")
                    return
                if '-' in c[-1]:
                    print("E: " + i + ": filename cannot contain '-'.")
                    return
                if c[-1].startswith('/'):
                    print("E: cannot create file using absolute path")
                    return
                d = os.getcwd().split('\\')[-1]
                p = getPerms(d)[0]
                inde = ''
                for k in os.listdir():
                    if os.path.isfile(k) and k.endswith(c[-1]):
                        inde = k.split('-')[0]
                if user == 'core' or user == findOwner(d):
                    if p[1] == 'w':
                        if inde:
                            ind = int(inde)
                            q = getPerms(k)[0]
                            if user == 'core' or user == findOwner(k):
                                if not q[1] == 'w':
                                    print("E: Permission denied")
                                    return
                            elif isGroup(k):
                                if not q[4] == 'w':
                                    print("E: Permission denied")
                                    return
                            else:
                                if not q[7] == 'w':
                                    print("E: Permission denied")
                                    return
                        else:
                            ind = givePerm(user, c[-1])
                        with open(str(ind) + '-' + c[-1], 'a') as f:
                            l = []
                            for i in c[1:c.index('>>')]:
                                if i.startswith('$'):
                                        l.append(variables[i[1:]])
                                elif i.startswith('\\'):
                                    l.append(i[1:])
                                else:
                                    l.append(i)
                            f.write(' '.join(l))
                            f.write('\n')
                    else:
                        print("E: Permission denied")
                elif isGroup(d):
                    if p[4] == 'w':
                        if inde:
                            ind = int(inde)
                            q = getPerms(k)[0]
                            if user == 'core' or user == findOwner(k):
                                if not q[1] == 'w':
                                    print("E: Permission denied")
                                    return
                            elif isGroup(k):
                                if not q[4] == 'w':
                                    print("E: Permission denied")
                                    return
                            else:
                                if not q[7] == 'w':
                                    print("E: Permission denied")
                                    return
                        else:
                            ind = givePerm(user, c[-1])
                        with open(str(ind) + '-' + c[-1], 'a') as f:
                            l = []
                            for i in c[1:c.index('>>')]:
                                if i.startswith('$'):
                                        l.append(variables[i[1:]])
                                elif i.startswith('\\'):
                                    l.append(i[1:])
                                else:
                                    l.append(i)
                            f.write(' '.join(l))
                            f.write('\n')
                    else:
                        print("E: Permission denied")
                else:
                    if p[7] == 'w':
                        if inde:
                            ind = int(inde)
                            q = getPerms(k)[0]
                            if user == 'core' or user == findOwner(k):
                                if not q[1] == 'w':
                                    print("E: Permission denied")
                                    return
                            elif isGroup(k):
                                if not q[4] == 'w':
                                    print("E: Permission denied")
                                    return
                            else:
                                if not q[7] == 'w':
                                    print("E: Permission denied")
                                    return
                        else:
                            ind = givePerm(user, c[-1])
                        with open(str(ind) + '-' + c[-1], 'a') as f:
                            l = []
                            for i in c[1:c.index('>>')]:
                                if i.startswith('$'):
                                        l.append(variables[i[1:]])
                                elif i.startswith('\\'):
                                    l.append(i[1:])
                                else:
                                    l.append(i)
                            f.write(' '.join(l))
                            f.write('\n')
                    else:
                        print("E: Permission denied")
    else:
        l = []
        for i in c[1:]:
            if i.startswith('$'):
                if i[1:] in variables:
                    l.append(variables[i[1:]])
                else:
                    print("E: " + i[1:] + ": no such variable")
                    return
            elif i.startswith('\\'):
                    l.append(i[1:])
            else:
                l.append(i)
        print(' '.join([str(x) for x in l]))

def check_if_num(c):
    #breakpoint()
    global variables
    x = []
    for i in c[2:]:
        if i in '+ - * / ( )'.split(' '):
            x.append(i)
            continue
        if i.startswith('$'):
            if i[1:] in variables:
                if type(variables[i[1:]]) in [int, float]:
                    x.append(variables[i[1:]])
                else:
                    return False
        else:
            if isInt(i):
                x.append(int(i))
            elif isFloat(i):
                x.append(float(i))
            else:
                return False
    return evaluate(' '.join([str(s) for s in x]))

def var(c):
    #breakpoint()
    global variables
    if isInt(c[0][0]) or isFloat(c[0][0]):
        print("E: variable cannot be/begin with number")
        return
    if len(c) > 3:
        if ('+' in c or '-' in c or '*' in c or '/' in c) and c[2] != '!':
            if type(check_if_num(c)) in [int, float]:
                variables[c[0]] = check_if_num(c)
            else:
                x = []
                for i in c[2:]:
                    if i.startswith('$'):
                        if i[1:] in variables:
                            x.append(variables[i[1:]])
                    else:
                        x.append(i)
                variables[c[0]] = ' '.join(x)
        else:
            if c[2] == '!':
                del c[2]
            variables[c[0]] = ' '.join(c[2:])
    else:
        if isInt(c[2]):
            variables[c[0]] = int(c[2])
        elif isFloat(c[2]):
            variables[c[0]] = float(c[2])
        else:
            variables[c[0]] = str(c[2])

def precedence(op): 
	
	if op == '+' or op == '-': 
		return 1
	if op == '*' or op == '/': 
		return 2
	return 0

def applyOp(a, b, op): 
	
	if op == '+': return a + b 
	if op == '-': return a - b 
	if op == '*': return a * b 
	if op == '/': return a // b 

def evaluate(tokens): 
	
	values = [] 
	
	ops = [] 
	i = 0
	
	while i < len(tokens): 
		
		if tokens[i] == ' ': 
			i += 1
			continue
		
		elif tokens[i] == '(': 
			ops.append(tokens[i]) 
		
		elif tokens[i].isdigit(): 
			val = 0
			
			while (i < len(tokens) and
				tokens[i].isdigit()): 
			
				val = (val * 10) + int(tokens[i]) 
				i += 1
			
			values.append(val) 
		
		elif tokens[i] == ')': 
		
			while len(ops) != 0 and ops[-1] != '(': 
			
				val2 = values.pop() 
				val1 = values.pop() 
				op = ops.pop() 
				
				values.append(applyOp(val1, val2, op)) 
			
			ops.pop() 
		
		else: 
			while (len(ops) != 0 and
				precedence(ops[-1]) >= precedence(tokens[i])): 
						
				val2 = values.pop() 
				val1 = values.pop() 
				op = ops.pop() 
				
				values.append(applyOp(val1, val2, op)) 
			
			ops.append(tokens[i]) 
		
		i += 1
	
	while len(ops) != 0: 
		
		val2 = values.pop() 
		val1 = values.pop() 
		op = ops.pop() 
				
		values.append(applyOp(val1, val2, op)) 
	
	return values[-1] 



def read(c):
    if len(c) > 2:
        print(' '.join(c[2:]))
    inp = input()
    if isInt(inp):
        variables[c[1]] = int(inp)
    elif isFloat(inp):
        variables[c[1]] = float(inp)
    else:
        variables[c[1]] = str(inp)

def cp(c):
    if c[1].startswith('/'):
        print("E: can copy file from current directory to other directory only")
        return
    if c[2] == '.':
        print("E: cant copy to same directory")
        return
    found = False
    for i in os.listdir():
        if i.endswith(c[1]):
            found = True
            break
    if not found:
        print("E: " + c[1] + ": file not found")
        return
    perm = False
    d = os.getcwd().split('\\')[-1]
    p = getPerms(d)[0]
    if user == 'core' or user == findOwner(d):
        if p[0] == 'r' and p[2] == 'x':
            perm = True
    elif isGroup(d):
        if p[3] == 'r' and p[5] == 'x':
            perm = True
    else:
        if p[6] == 'r' and p[8] == 'x':
            perm = True
    if not perm:
        print("E: " + d.split('\\')[-1].split('-')[0] + ": Permission denied")
        return
    #breakpoint()
    perm = False
    for i in os.listdir():
        if i.endswith(c[1]):
            p = getPerms(i)[0]
            if user == 'core' or user == findOwner(i):
                if p[0] == 'r':
                    perm = True
                    break
            elif isGroup(d):
                if p[3] == 'r':
                    perm = True
                    break
            else:
                if p[6] == 'r':
                    perm = True
                    break
    if not perm:
        print("E: " + c[1] + ": Permission denied")
        return
    if c[2].startswith('/'):
        if c[2] == '/':
            perm = False
            p = getPerms('0-ss')[0]
            if user == 'core' or user == findOwner('0-ss'):
                if p[1] == 'w' and p[2] == 'x':
                    perm = True
            elif isGroup('0-ss'):
                if p[4] == 'w' and p[5] == 'x':
                    perm = True
            else:
                if p[7] == 'w' and p[8] == 'x':
                    perm = True
            if not perm:
                print("E: / : Permission denied")
                return
            shutil.copyfile(c[1], 'C:/Users/sanjsark/SarkSys/0-ss')
        else:
            perm = False
            od = 'C:/Users/sanjsark/SarkSys/0-ss'
            for i in c[2].split('/'):
                found = False
                for j in os.listdir(od):
                    if j.endswith(j) and os.path.isdir(j):
                        p = getPerms(j)[0]
                        if user == 'core' or user == findOwner(j):
                            found = True
                            if p[1] == 'w' and p[2] == 'x':
                                od += ('/' + j)
                            else:
                                print("E: " + i + ": Permission denied")
                                return
                        elif isGroup(j):
                            found = True
                            if p[4] == 'w' and p[5] == 'x':
                                od += ('/' + j)
                            else:
                                print("E: " + i + ": Permission denied")
                                return
                        else:
                            found = True
                            if p[7] == 'w' and p[8] == 'x':
                                od += ('/' + j)
                            else:
                                print("E: " + i + ": Permission denied")
                                return
            if found:
                shutil.copyfile(c[1], c[2])
    else:
        od = os.getcwd().replace('\\', '/')
        cd = od
        for i in c[2]:
            for j in os.listdir():
                if j.endswith(i) and os.path.isdir(j):
                    p = getPerms(j)[0]
                    if user == 'core' or user == findOwner(j):
                        if p[1] == 'w' and p[2] == 'x':
                            cd += ('/' + j)
                            os.chdir(cd)
                        else:
                            print("E: " + i + ": Permission denied")
                            return
                    elif isGroup(j):
                        if p[4] == 'w' and p[5] == 'x':
                            cd += ('/' + j)
                            os.chdir(cd)
                        else:
                            print("E: " + i + ": Permission denied")
                            return
                    else:
                        if p[7] == 'w' and p[8] == 'x':
                            cd += ('/' + j)
                            os.chdir(cd)
                        else:
                            print("E: " + i + ": Permission denied")
                            return
        for i in os.listdir(od):
            if i.endswith(c[1]) and os.path.isfile(i):
                break
        ind = givePerm(user, c[1])
        with open(od+'/'+i, 'r') as f1:
            with open(str(ind)+'-'+c[1], 'w') as f2:
                for k in f1.readlines():
                    f2.write(k+'\n')
        os.chdir(od)


def is_authorized_x(f):
    for i in os.listdir():
        if i.endswith(f) and os.path.isfile(i):
            p = getPerms(i)[0]
            if user == 'core' or user == findOwner(i):
                if p[2] == 'x':
                    return True
                else:
                    print("E: " + f + ": Permission denied")
                    return False
            elif isGroup(i):
                if p[5] == 'x':
                    return True
                else:
                    print("E: " + i + ": Permission denied")
                    return False
            else:
                if p[8] == 'x':
                    return True
                else:
                    print("E: " + i + ": Permission denied")
                    return False

def is_authorized_w(f):
    for i in os.listdir():
        if i.endswith(f) and os.path.isfile(i):
            p = getPerms(i)[0]
            if user == 'core' or user == findOwner(i):
                if p[1] == 'w':
                    return True
                else:
                    return False
            elif isGroup(i):
                if p[4] == 'w':
                    return True
                else:
                    return False
            else:
                if p[7] == 'w':
                    return True
                else:
                    return False

def get_file_name(f):
    for i in os.listdir():
        if i.endswith(f) and os.path.isfile(i):
            return i

def save(fn, lines):
    with open(fn, 'w') as f:
        for i in lines:
            if i.endswith('\n'):
                f.write(i)
            else:
                f.write(i+'\n')

def isFile(f):
    for i in os.listdir():
        if i.endswith(f) and os.path.isfile(i):
            return True
    touch(c)
    return True

def print_data(f, l, tf):
            clear()
            ln = 1
            print('\n' + f + '{}'.format('' if tf else '*'))
            for i in l:
                print('{} | {}'.format(ln, i), end='')
                ln += 1
            print()


def editor(c):
    global editor_help
    
    if isFile(c[1]):
        fn = get_file_name(c[1])
        
    if not is_authorized_w(c[1]):
        print("E: " + c[1] + ": you are not authorized")
        return
    
        
    lines = []
    c_lines = []
    auto_save = False
    l = 1
    f = None

    clear()
    
    with open(fn, 'r+') as f:
        for i in f.readlines():
            print('{} | >> {}'.format(l, i), end='')
            lines.append(i)
            c_lines.append(i)
            l += 1

    while True:
        if auto_save:
            c_lines = []
            for i in lines:
                c_lines.append(i)
            save(fn, lines)
        inp = input("{} | >> ".format(len(lines)+1)).split(' ')
        if len(inp) == 0:
            lines.append('\n')
            
        elif inp[0].startswith('\\'):
            inp[0] = inp[0][1:]
            lines.append(' '.join(inp))

        elif inp[0].startswith(':'):
            if inp[0] == ':as':
                if auto_save:
                    auto_save = False
                    print("\tAuto-Save disabled")
                else:
                    auto_save = True
                    print("\tAuto-Save enabled")


            elif inp[0] == ':h':
                if len(inp) == 1:
                    clear()
                    for i in editor_help:
                        print(i+'\n'+editor_help[i])
                elif len(inp) == 2:
                    if ':'+inp[1] in editor_help:
                        print()
                        print(':'+inp[1]+'\n'+editor_help[':'+inp[1]])
                    else:
                        print_data(c[1], lines, lines == c_lines)
                        print('E: ' + inp[1] + ': not found')
                else:
                    print('E: :h : incorrect  use')
                    
            elif inp[0] == ':dd':
                if len(inp) > 1:
                    for i in inp[1:]:
                        if isInt(i):
                            if int(i) <= len(lines):
                                del lines[int(i) - 1]
                    print_data(c[1], lines, lines == c_lines)

            elif inp[0] == ':dw':
                if len(inp) > 1:
                    for i in inp[1:]:
                        e = ''
                        if ':' in i:
                            if '-' in i:
                                ip = i.split(':')[0]
                                rst = i.split(':')[1]
                                ls = rst.split('-')
                                if isInt(ip) and isInt(ls[0]) and isInt(ls[1]):
                                    if int(ip) <= len(lines):
                                        if int(ls[0]) < len(lines[int(ip)-1].split(' ')) and int(ls[1]) < len(lines[int(ip)-1].split(' ')):
                                            if int(ls[0]) < int(ls[1]):
                                                for i in range((int(ls[1])-int(ls[0]))+1):
                                                    lst = lines[int(ip)-1].split(' ')
                                                    del lst[int(ls[0])-1]
                                                    lines[int(ip)-1] = ' '.join(lst)
                                            else:
                                                e = ("E: " + ls[0] + " is smaller than " + ls[1])
                                        else:
                                            e = ("E: length of line " + ip + " is smaller")
                                    else:
                                        e = ("E: line number " + ip + " not found")
                                else:
                                    e = ("E: please enter only integers")
                            else:
                                ip = i.split(':')
                                if isInt(ip[0]) and isInt(ip[1]):
                                    if int(ip[0]) <= len(lines):
                                        if int(ip[1]) < len(lines[int(ip[0])-1].split(' ')):
                                            lst = lines[int(ip[0])-1].split(' ')
                                            del lst[int(ip[1])-1]
                                            lines[int(ip[0])-1] = ' '.join(lst)
                                        else:
                                            e = ("E: length of line " + ip[0] + " is smaller")
                                    else:
                                        e = ("E: line number " + ip[0] + " not found")
                                else:
                                    e = ("E: please enter only integers")
                        else:
                            e = ("E: dw: incorrect usage")
                    print_data(c[1], lines, lines == c_lines)
                    if e:
                        print(e)
                            

            elif inp[0] == ':pr':
                print_data(c[1], lines, lines == c_lines)

            elif inp[0] == ':rr':
                if len(inp) > 2:
                    if isInt(inp[1]):
                        lines [int(inp[1]) - 1] = (str(' '.join(inp[2:]) + '\n'))
                        print_data(c[1], lines, lines == c_lines)

            elif inp[0] == ':rw':
                if len(inp) > 2:
                        e = ''
                        if ':' in inp[1]:
                            if '-' in inp[1]:
                                i = inp[1]
                                ip = i.split(':')[0]
                                rst = i.split(':')[1]
                                ls = rst.split('-')
                                if isInt(ip) and isInt(ls[0]) and isInt(ls[1]):
                                    if int(ip) <= len(lines):
                                        if int(ls[0]) < len(lines[int(ip)-1].split(' ')) and int(ls[1]) < len(lines[int(ip)-1].split(' ')):
                                            if int(ls[0]) < int(ls[1]):
                                                for i in range((int(ls[1])-int(ls[0]))+1):
                                                    lst = lines[int(ip)-1].split(' ')
                                                    del lst[int(ls[0])-1]
                                                    lines[int(ip)-1] = ' '.join(lst)
                                                lines[int(ip)-1] = ' '.join(lst[:(int(ip)-1)] + inp[2:] + lst[(int(ip)-1):])
                                            else:
                                                e = ("E: " + ls[0] + " is smaller than " + ls[1])
                                        else:
                                            e = ("E: length of line " + ip + " is smaller")
                                    else:
                                        e = ("E: line number " + ip + " not found")
                                else:
                                    e = ("E: please enter only integers")
                            else:
                                i = inp[1]
                                ip = i.split(':')
                                if isInt(ip[0]) and isInt(ip[1]):
                                    if int(ip[0]) <= len(lines):
                                        if int(ip[1]) < len(lines[int(ip[0])-1].split(' ')):
                                            lst = lines[int(ip[0])-1].split(' ')
                                            del lst[int(ip[1])-1]
                                            lines[int(ip[0])-1] = ' '.join(lst)
                                            lines[int(ip[0])-1] = ' '.join(lst[:(int(ip[1])-1)] + inp[2:] + lst[(int(ip[1])-1):])
                                        else:
                                            e = ("E: length of line " + ip[0] + " is smaller")
                                    else:
                                        e = ("E: line number " + ip[0] + " not found")
                                else:
                                    e = ("E: please enter only integers")
                        else:
                            e = ("E: rw: incorrect usage")
                        print_data(c[1], lines, lines == c_lines)
                        if e:
                            print(e)

            elif inp[0] == ':al':
                if len(inp) > 2:
                    e = ''
                    if isInt(inp[1]):
                        if int(inp[1]) <= len(lines):
                            lines.insert((int(inp[1])), (' '.join(inp[2:])+'\n'))
                        else:
                            e = ("E: line number " + ip[0] + " not found")
                    else:
                        e = ("E: please enter only integers")
                    print_data(c[1], lines, lines == c_lines)
                    if e:
                        print(e)

            elif inp[0] == ':aw':
                if len(inp) > 2:
                    e = ''
                    if ':' in inp[1]:
                        ip = inp[1].split(':')
                        if isInt(ip[0]) and isInt(ip[1]):
                            if int(ip[0]) <= len(lines):
                                if int(ip[1]) <= len(lines[int(ip[0])-1].split(' ')):
                                    l = lines[int(ip[0])-1].split(' ')
                                    l.insert(int(ip[1])-1, ' '.join(inp[2:]))
                                    lines[int(ip[0])-1] = ' '.join(l)
                                else:
                                    e = ("E: length of line " + ip[0] + " is smaller")
                            else:
                                e = ("E: line number " + ip[0] + " not found")
                        else:
                            e = ("E: please enter only integers")
                    else:
                        e = ("E: aw: incorrect usage")
                    print_data(c[1], lines, lines == c_lines)
                    if e:
                        print(e)

            elif inp[0] == ':ln':
                e = ''
                d = ''
                if len(inp) == 1:
                    d = "Legth of file :" + str(len(lines))
                elif len(inp) == 2:
                    if isInt(inp[1]):
                        i = int(inp[1])
                        if i <= len(lines):
                            d = "Length of line {} : {}".format(inp[1], len(lines[i-1].split(' ')))
                        else:
                            e = ("E: line number " + ip[0] + " not found")
                    else:
                        e = ("E: please enter only integers")
                else:
                    e = ("E: ln: incorrect usage")
                print_data(c[1], lines, lines == c_lines)
                if d:
                    print(d)
                if e:
                    print(e)

            elif inp[0] == ':sr':
                if len(inp) > 1:
                    e = ''
                    d = {}
                    if len(inp) == 2:
                        for d1, i in enumerate(lines):
                            for d2, j in enumerate(i.split(' ')):
                                if j == inp[1]:
                                    d[d1+1] = d2+1
                    elif len(inp) == 3:
                            if isInt(inp[2]):
                                i = int(inp[2])
                                if i <= len(lines):
                                    l = lines[i-1]
                                    for d1, i in enumerate(l.split(' ')):
                                        if i == inp[1]:
                                            d[i] = d1+1
                                else:
                                    e = ("E: line number " + ip[0] + " not found")
                            else:
                                e = ("E: please enter only integers")
                    else:
                        e = ("E: aw: incorrect usage")
                    print_data(c[1], lines, lines == c_lines)
                    if d:
                        for i in d:
                            print("'{}' found in line #{} and word #{}".format(inp[1], i, d[i]))
                    if e:
                        print(e)
                                
                                
                            
                    
            elif inp[0] == ':s':
                c_lines = []
                for i in lines:
                    c_lines.append(i)
                save(fn, lines)
                
            elif inp[0] == ':x':
                save(fn, lines)
                clear()
                break
            
            elif inp[0] == ':q':
                if lines != c_lines:
                    if input("**** Do you really want to exit without saving? (Y/n): ").lower().startswith('y'):
                        clear()
                        break
                else:
                    clear()
                    break

            elif inp[0] == ':q!':
                clear()
                break
                
            else:
                print_data(c[1], lines, lines == c_lines)
                print("E: " + inp[0] + ": no such command")
        
        else:
            lines.append(' '.join(inp))

def getip(c):
    try:
        for i in c[1:]:
            print("{}: {}".format(i, socket.gethostbyname(i)))
    except:
        print("E: ip: Can't connect to internet/Can't get host name")


def ip(c):
    if len(c) == 1 or (len(c) == 2 and c[1] == '-s'):
        try:
            print("Hostname: {}".format(socket.gethostname()))
            print("IP Addr: {}".format(socket.gethostbyname(socket.gethostname())))
        except:
            print("E: an error occured")
    elif len(c) == 2 and c[1] == '-p':
        try:
            ip = get('https://api.ipify.org').text
            print('Public IP address is:', ip)
        except Exception as e:
            print("E: an error occured,", e)
    else:
        print("Usage: ip -s/-p")

def get_alias():
    global g_alias
    global home
    for i in os.listdir(home):
        if i.endswith('.ss_alias') and os.path.isfile(i):
            try:
                with open(home+'/'+i, 'r') as f:
                    for i in f.readlines():
                        g_alias[i.split('=')[0].replace(' ','')] = i.split('=')[1].strip('\n').replace(' ','')
            except:
                pass



def isVarb(v):
    global variables
    if v[1:] in variables:
        return variables[v[1:]]
    else:
        return False


def ifstat(c):
    #breakpoint()
    global script_run
    global commands
    global varibales
    global rip
    global else_stat
    if len(c) > 2 and c[-1] == 'then':
        run = False
        if len(c) == 3:
            if c[1].startswith('$'):
                if c[1][1:] in variables and variables[c[1][1:]] not in ['0', '', 'False']:
                    run = True
            elif c[1] not in ['0', '', 'False']:
                run = True
        elif c[2]in ['<', '>', '==', '!=', '<=', '>=']:
            if isInt(c[1]):
                if isInt(c[3]):
                    if c[2] == '<':
                        if int(c[1]) < int(c[3]):
                            run = True
                    if c[2] == '>':
                        if int(c[1]) > int(c[3]):
                            run = True
                    if c[2] == '==':
                        if int(c[1]) == int(c[3]):
                            run = True
                    if c[2] == '!=':
                        if int(c[1]) != int(c[3]):
                            run = True
                    if c[2] == '<=':
                        if int(c[1]) <= int(c[3]):
                            run = True
                    if c[2] == '>=':
                        if int(c[1]) >= int(c[3]):
                            run = True
                elif isFloat(c[3]):
                    if c[2] == '<':
                        if int(c[1]) < float(c[3]):
                            run = True
                    if c[2] == '>':
                        if int(c[1]) > float(c[3]):
                            run = True
                    if c[2] == '==':
                        if int(c[1]) == float(c[3]):
                            run = True
                    if c[2] == '!=':
                        if int(c[1]) != float(c[3]):
                            run = True
                    if c[2] == '<=':
                        if int(c[1]) <= float(c[3]):
                            run = True
                    if c[2] == '>=':
                        if int(c[1]) >= float(c[3]):
                            run = True
                elif isVarb(c[3]):
                    if isInt(isVarb(c[3])):
                        if c[2] == '<':
                            if int(c[1]) < int(isVarb(c[3])):
                                run = True
                        if c[2] == '>':
                            if int(c[1]) > int(isVarb(c[3])):
                                run = True
                        if c[2] == '==':
                            if int(c[1]) == int(isVarb(c[3])):
                                run = True
                        if c[2] == '!=':
                            if int(c[1]) != int(isVarb(c[3])):
                                run = True
                        if c[2] == '<=':
                            if int(c[1]) <= int(isVarb(c[3])):
                                run = True
                        if c[2] == '>=':
                            if int(c[1]) >= int(isVarb(c[3])):
                                run = True
                    elif isFloat(isVarb(c[3])):
                        if c[2] == '<':
                            if int(c[1]) < float(isVarb(c[3])):
                                run = True
                        if c[2] == '>':
                            if int(c[1]) > float(isVarb(c[3])):
                                run = True
                        if c[2] == '==':
                            if int(c[1]) == float(isVarb(c[3])):
                                run = True
                        if c[2] == '!=':
                            if int(c[1]) != float(isVarb(c[3])):
                                run = True
                        if c[2] == '<=':
                            if int(c[1]) <= float(isVarb(c[3])):
                                run = True
                        if c[2] == '>=':
                            if int(c[1]) >= float(isVarb(c[3])):
                                run = True
                    else:
                        print("E: can't compare int with string")
                else:
                    print("E: can't compare int with string")
            elif isFloat(c[1]):
                if isInt(c[3]):
                    if c[2] == '<':
                        if float(c[1]) < int(c[3]):
                            run = True
                    if c[2] == '>':
                        if float(c[1]) > int(c[3]):
                            run = True
                    if c[2] == '==':
                        if float(c[1]) == int(c[3]):
                            run = True
                    if c[2] == '!=':
                        if float(c[1]) != int(c[3]):
                            run = True
                    if c[2] == '<=':
                        if float(c[1]) <= int(c[3]):
                            run = True
                    if c[2] == '>=':
                        if float(c[1]) >= int(c[3]):
                            run = True
                elif isFloat(c[3]):
                    if c[2] == '<':
                        if float(c[1]) < float(c[3]):
                            run = True
                    if c[2] == '>':
                        if float(c[1]) > float(c[3]):
                            run = True
                    if c[2] == '==':
                        if float(c[1]) == float(c[3]):
                            run = True
                    if c[2] == '!=':
                        if float(c[1]) != float(c[3]):
                            run = True
                    if c[2] == '<=':
                        if float(c[1]) <= float(c[3]):
                            run = True
                    if c[2] == '>=':
                        if float(c[1]) >= float(c[3]):
                            run = True
                elif isVarb(c[3]):
                    if isInt(isVarb(c[3])):
                        if c[2] == '<':
                            if float(c[1]) < int(isVarb(c[3])):
                                run = True
                        if c[2] == '>':
                            if float(c[1]) > int(isVarb(c[3])):
                                run = True
                        if c[2] == '==':
                            if float(c[1]) == int(isVarb(c[3])):
                                run = True
                        if c[2] == '!=':
                            if float(c[1]) != int(isVarb(c[3])):
                                run = True
                        if c[2] == '<=':
                            if float(c[1]) <= int(isVarb(c[3])):
                                run = True
                        if c[2] == '>=':
                            if float(c[1]) >= int(isVarb(c[3])):
                                run = True
                    elif isFloat(isVarb(c[3])):
                        if c[2] == '<':
                            if float(c[1]) < float(isVarb(c[3])):
                                run = True
                        if c[2] == '>':
                            if float(c[1]) > float(isVarb(c[3])):
                                run = True
                        if c[2] == '==':
                            if float(c[1]) == float(isVarb(c[3])):
                                run = True
                        if c[2] == '!=':
                            if float(c[1]) != float(isVarb(c[3])):
                                run = True
                        if c[2] == '<=':
                            if float(c[1]) <= float(isVarb(c[3])):
                                run = True
                        if c[2] == '>=':
                            if float(c[1]) >= float(isVarb(c[3])):
                                run = True
                    else:
                        print("E: can't compare float with string")
                else:
                    print("E: can't compare float with string")
            elif isVarb(c[1]):
                if isInt(isVarb(c[1])):
                    if isInt(c[3]):
                        if c[2] == '<':
                            if int(isVarb(c[1])) < int(c[3]):
                                run = True
                        if c[2] == '>':
                            if int(isVarb(c[1])) > int(c[3]):
                                run = True
                        if c[2] == '==':
                            if int(isVarb(c[1])) == int(c[3]): 
                                run = True
                        if c[2] == '!=':
                            if int(isVarb(c[1])) != int(c[3]):
                                run = True
                        if c[2] == '<=':
                            if int(isVarb(c[1])) <= int(c[3]):
                                run = True
                        if c[2] == '>=':
                            if int(isVarb(c[1])) >= int(c[3]):
                                run = True
                    elif isFloat(c[3]):
                        if c[2] == '<':
                            if int(isVarb(c[1])) < float(c[3]):
                                run = True
                        if c[2] == '>':
                            if int(isVarb(c[1])) > float(c[3]):
                                run = True
                        if c[2] == '==':
                            if int(isVarb(c[1])) == float(c[3]):
                                run = True
                        if c[2] == '!=':
                            if int(isVarb(c[1])) != float(c[3]):
                                run = True
                        if c[2] == '<=':
                            if int(isVarb(c[1])) <= float(c[3]):
                                run = True
                        if c[2] == '>=':
                            if int(isVarb(c[1])) >= float(c[3]):
                                run = True
                    elif isVarb(c[3]):
                        if isInt(isVarb(c[3])):
                            if c[2] == '<':
                                if int(isVarb(c[1])) < int(isVarb(c[3])):
                                    run = True
                            if c[2] == '>':
                                if int(isVarb(c[1])) > int(isVarb(c[3])):
                                    run = True
                            if c[2] == '==':
                                if int(isVarb(c[1])) == int(isVarb(c[3])):
                                    run = True
                            if c[2] == '!=':
                                if int(isVarb(c[1])) != int(isVarb(c[3])):
                                    run = True
                            if c[2] == '<=':
                                if int(isVarb(c[1])) <= int(isVarb(c[3])):
                                    run = True
                            if c[2] == '>=':
                                if int(isVarb(c[1])) >= int(isVarb(c[3])):
                                    run = True
                        elif isFloat(isVarb(c[3])):
                            if c[2] == '<':
                                if int(isVarb(c[1])) < float(isVarb(c[3])):
                                    run = True
                            if c[2] == '>':
                                if int(isVarb(c[1])) > float(isVarb(c[3])):
                                    run = True
                            if c[2] == '==':
                                if int(isVarb(c[1])) == float(isVarb(c[3])):
                                    run = True
                            if c[2] == '!=':
                                if int(isVarb(c[1])) != float(isVarb(c[3])):
                                    run = True
                            if c[2] == '<=':
                                if int(isVarb(c[1])) <= float(isVarb(c[3])):
                                    run = True
                            if c[2] == '>=':
                                if int(isVarb(c[1])) >= float(isVarb(c[3])):
                                    run = True
                        else:
                            print("E: can't compare int with string")
                    else:
                        print("E: can't compare int with string")
                elif isFloat(isVarb(c[1])):
                    if isInt(c[3]):
                        if c[2] == '<':
                            if float(c[1]) < int(c[3]):
                                run = True
                        if c[2] == '>':
                            if float(c[1]) > int(c[3]):
                                run = True
                        if c[2] == '==':
                            if float(c[1]) == int(c[3]):
                                run = True
                        if c[2] == '!=':
                            if float(c[1]) != int(c[3]):
                                run = True
                        if c[2] == '<=':
                            if float(c[1]) <= int(c[3]):
                                run = True
                        if c[2] == '>=':
                            if float(c[1]) >= int(c[3]):
                                run = True
                    elif isFloat(c[3]):
                        if c[2] == '<':
                            if float(c[1]) < float(c[3]):
                                run = True
                        if c[2] == '>':
                            if float(c[1]) > float(c[3]):
                                run = True
                        if c[2] == '==':
                            if float(c[1]) == float(c[3]):
                                run = True
                        if c[2] == '!=':
                            if float(c[1]) != float(c[3]):
                                run = True
                        if c[2] == '<=':
                            if float(c[1]) <= float(c[3]):
                                run = True
                        if c[2] == '>=':
                            if float(c[1]) >= float(c[3]):
                                run = True
                    elif isVarb(c[3]):
                        if isInt(isVarb(c[3])):
                            if c[2] == '<':
                                if float(c[1]) < int(c[3]):
                                    run = True
                            if c[2] == '>':
                                if float(c[1]) > int(c[3]):
                                    run = True
                            if c[2] == '==':
                                if float(c[1]) == int(c[3]):
                                    run = True
                            if c[2] == '!=':
                                if float(c[1]) != int(c[3]):
                                    run = True
                            if c[2] == '<=':
                                if float(c[1]) <= int(c[3]):
                                    run = True
                            if c[2] == '>=':
                                if float(c[1]) >= int(c[3]):
                                    run = True
                        elif isFloat(isVarb(c[3])):
                            if c[2] == '<':
                                if float(c[1]) < float(c[3]):
                                    run = True
                            if c[2] == '>':
                                if float(c[1]) > float(c[3]):
                                    run = True
                            if c[2] == '==':
                                if float(c[1]) == float(c[3]):
                                    run = True
                            if c[2] == '!=':
                                if float(c[1]) != float(c[3]):
                                    run = True
                            if c[2] == '<=':
                                if float(c[1]) <= float(c[3]):
                                    run = True
                            if c[2] == '>=':
                                if float(c[1]) >= float(c[3]):
                                    run = True
                        else:
                            print("E: can't compare float with string")
                    else:
                        print("E: can't compare float with string")
                else:
                    x = isVarb(c[1])
                    if isInt(c[3]) or isInt(c[3]):
                        print("E: can't compare string with int/float")
                    elif isVarb(c[3]):
                        if isInt(isVarb(c[3])) or isInt(isVarb(c[3])):
                            print("E: can't compare string with int/float")
                        else:
                            y = isVarb(c[3])
                            if c[2] == '==':
                                if x == y:
                                    run = True
                            if c[2] == '!=':
                                if x != y:
                                    run = True
                            if c[2] == '<':
                                if x < y:
                                    run = True
                            if c[2] == '<=':
                                if x <= y:
                                    run = True
                            if c[2] == '>':
                                if x > y:
                                    run = True
                            if c[2] == '>=':
                                if x >= y:
                                    run = True
                    else:
                        y = isVarb(c[3])
                        if c[2] == '==':
                                if x == y:
                                    run = True
                        if c[2] == '!=':
                                if x != y:
                                    run = True
                        if c[2] == '<':
                                if x < y:
                                    run = True
                        if c[2] == '<=':
                                if x <= y:
                                    run = True
                        if c[2] == '>':
                                if x > y:
                                    run = True
                        if c[2] == '>=':
                                if x >= y:
                                    run = True
            else:
                breakpoint()
                if isInt(c[3]) or isInt(c[3]):
                    print("E: can't compare string with int/float")
                elif isVarb(c[3]):
                    if isInt(isVarb(c[3])) or isInt(isVarb(c[3])):
                        print("E: can't compare string with int/float")
                    else:
                        y = isVarb(c[3])
                        if c[2] == '==':
                                if x == y:
                                    run = True
                        if c[2] == '!=':
                                if x != y:
                                    run = True
                        if c[2] == '<':
                                if x < y:
                                    run = True
                        if c[2] == '<=':
                                if x <= y:
                                    run = True
                        if c[2] == '>':
                                if x > y:
                                    run = True
                        if c[2] == '>=':
                                if x >= y:
                                    run = True
                else:
                    y = isVarb(c[3])
                    if c[2] == '==':
                                if isVarb(c[1]) == y:
                                    run = True
                    if c[2] == '!=':
                                if isVarb(c[1]) != y:
                                    run = True
                    if c[2] == '<':
                                if isVarb(c[1]) < y:
                                    run = True
                    if c[2] == '<=':
                                if isVarb(c[1]) <= y:
                                    run = True
                    if c[2] == '>':
                                if isVarb(c[1]) > y:
                                    run = True
                    if c[2] == '>=':
                                if isVarb(c[1]) >= y:
                                    run = True
        #breakpoint()
        if script_run:
            if run:
                else_stat = False
                return
            else:
                for ij in range(rip, len(commands)):
                    if commands[ij] == 'else':
                        rip += ij
                        else_stat = True
                        return
        ifb = []
        elb = []
        mode = 'if'
        while True:
                x = input('> ')
                if x == 'fi':
                    break
                if x == 'else':
                    mode = 'else'
                    continue
                if mode == 'if':
                    if x:
                        ifb.append(x)
                else:
                    if x:
                        elb.append(x)
        if run:
            script_run = True
            for i in ifb:
                commands.append(i.strip('\n'))
        elif mode == 'else':
            script_run = True
            for i in elb:
                commands.append(i.strip('\n'))
        else:
            return
    else:
        print("E: incorrect syntax")


def whileloop(c):
    global script_run
    global commands
    global varibales
    global rip
    global while_rip
    if len(c) > 2 and c[-1] == 'do':
        run = False
        while_rip = rip - 1
        if len(c) == 3:
            if c[1].startswith('$'):
                if c[1][1:] in variables and variables[c[1][1:]] not in ['0', '', 'False']:
                    run = True
            elif c[1] not in ['0', '', 'False']:
                run = True
        elif c[2]in ['<', '>', '==', '!=', '<=', '>=']:
            if isInt(c[1]):
                if isInt(c[3]):
                    if c[2] == '<':
                        if int(c[1]) < int(c[3]):
                            run = True
                    if c[2] == '>':
                        if int(c[1]) > int(c[3]):
                            run = True
                    if c[2] == '==':
                        if int(c[1]) == int(c[3]):
                            run = True
                    if c[2] == '!=':
                        if int(c[1]) != int(c[3]):
                            run = True
                    if c[2] == '<=':
                        if int(c[1]) <= int(c[3]):
                            run = True
                    if c[2] == '>=':
                        if int(c[1]) >= int(c[3]):
                            run = True
                elif isFloat(c[3]):
                    if c[2] == '<':
                        if int(c[1]) < float(c[3]):
                            run = True
                    if c[2] == '>':
                        if int(c[1]) > float(c[3]):
                            run = True
                    if c[2] == '==':
                        if int(c[1]) == float(c[3]):
                            run = True
                    if c[2] == '!=':
                        if int(c[1]) != float(c[3]):
                            run = True
                    if c[2] == '<=':
                        if int(c[1]) <= float(c[3]):
                            run = True
                    if c[2] == '>=':
                        if int(c[1]) >= float(c[3]):
                            run = True
                elif isVarb(c[3]):
                    if isInt(isVarb(c[3])):
                        if c[2] == '<':
                            if int(c[1]) < int(isVarb(c[3])):
                                run = True
                        if c[2] == '>':
                            if int(c[1]) > int(isVarb(c[3])):
                                run = True
                        if c[2] == '==':
                            if int(c[1]) == int(isVarb(c[3])):
                                run = True
                        if c[2] == '!=':
                            if int(c[1]) != int(isVarb(c[3])):
                                run = True
                        if c[2] == '<=':
                            if int(c[1]) <= int(isVarb(c[3])):
                                run = True
                        if c[2] == '>=':
                            if int(c[1]) >= int(isVarb(c[3])):
                                run = True
                    elif isFloat(isVarb(c[3])):
                        if c[2] == '<':
                            if int(c[1]) < float(isVarb(c[3])):
                                run = True
                        if c[2] == '>':
                            if int(c[1]) > float(isVarb(c[3])):
                                run = True
                        if c[2] == '==':
                            if int(c[1]) == float(isVarb(c[3])):
                                run = True
                        if c[2] == '!=':
                            if int(c[1]) != float(isVarb(c[3])):
                                run = True
                        if c[2] == '<=':
                            if int(c[1]) <= float(isVarb(c[3])):
                                run = True
                        if c[2] == '>=':
                            if int(c[1]) >= float(isVarb(c[3])):
                                run = True
                    else:
                        print("E: can't compare int with string")
                else:
                    print("E: can't compare int with string")
            elif isFloat(c[1]):
                if isInt(c[3]):
                    if c[2] == '<':
                        if float(c[1]) < int(c[3]):
                            run = True
                    if c[2] == '>':
                        if float(c[1]) > int(c[3]):
                            run = True
                    if c[2] == '==':
                        if float(c[1]) == int(c[3]):
                            run = True
                    if c[2] == '!=':
                        if float(c[1]) != int(c[3]):
                            run = True
                    if c[2] == '<=':
                        if float(c[1]) <= int(c[3]):
                            run = True
                    if c[2] == '>=':
                        if float(c[1]) >= int(c[3]):
                            run = True
                elif isFloat(c[3]):
                    if c[2] == '<':
                        if float(c[1]) < float(c[3]):
                            run = True
                    if c[2] == '>':
                        if float(c[1]) > float(c[3]):
                            run = True
                    if c[2] == '==':
                        if float(c[1]) == float(c[3]):
                            run = True
                    if c[2] == '!=':
                        if float(c[1]) != float(c[3]):
                            run = True
                    if c[2] == '<=':
                        if float(c[1]) <= float(c[3]):
                            run = True
                    if c[2] == '>=':
                        if float(c[1]) >= float(c[3]):
                            run = True
                elif isVarb(c[3]):
                    if isInt(isVarb(c[3])):
                        if c[2] == '<':
                            if float(c[1]) < int(isVarb(c[3])):
                                run = True
                        if c[2] == '>':
                            if float(c[1]) > int(isVarb(c[3])):
                                run = True
                        if c[2] == '==':
                            if float(c[1]) == int(isVarb(c[3])):
                                run = True
                        if c[2] == '!=':
                            if float(c[1]) != int(isVarb(c[3])):
                                run = True
                        if c[2] == '<=':
                            if float(c[1]) <= int(isVarb(c[3])):
                                run = True
                        if c[2] == '>=':
                            if float(c[1]) >= int(isVarb(c[3])):
                                run = True
                    elif isFloat(isVarb(c[3])):
                        if c[2] == '<':
                            if float(c[1]) < float(isVarb(c[3])):
                                run = True
                        if c[2] == '>':
                            if float(c[1]) > float(isVarb(c[3])):
                                run = True
                        if c[2] == '==':
                            if float(c[1]) == float(isVarb(c[3])):
                                run = True
                        if c[2] == '!=':
                            if float(c[1]) != float(isVarb(c[3])):
                                run = True
                        if c[2] == '<=':
                            if float(c[1]) <= float(isVarb(c[3])):
                                run = True
                        if c[2] == '>=':
                            if float(c[1]) >= float(isVarb(c[3])):
                                run = True
                    else:
                        print("E: can't compare float with string")
                else:
                    print("E: can't compare float with string")
            elif isVarb(c[1]):
                if isInt(isVarb(c[1])):
                    if isInt(c[3]):
                        if c[2] == '<':
                            if int(isVarb(c[1])) < int(c[3]):
                                run = True
                        if c[2] == '>':
                            if int(isVarb(c[1])) > int(c[3]):
                                run = True
                        if c[2] == '==':
                            if int(isVarb(c[1])) == int(c[3]): 
                                run = True
                        if c[2] == '!=':
                            if int(isVarb(c[1])) != int(c[3]):
                                run = True
                        if c[2] == '<=':
                            if int(isVarb(c[1])) <= int(c[3]):
                                run = True
                        if c[2] == '>=':
                            if int(isVarb(c[1])) >= int(c[3]):
                                run = True
                    elif isFloat(c[3]):
                        if c[2] == '<':
                            if int(isVarb(c[1])) < float(c[3]):
                                run = True
                        if c[2] == '>':
                            if int(isVarb(c[1])) > float(c[3]):
                                run = True
                        if c[2] == '==':
                            if int(isVarb(c[1])) == float(c[3]):
                                run = True
                        if c[2] == '!=':
                            if int(isVarb(c[1])) != float(c[3]):
                                run = True
                        if c[2] == '<=':
                            if int(isVarb(c[1])) <= float(c[3]):
                                run = True
                        if c[2] == '>=':
                            if int(isVarb(c[1])) >= float(c[3]):
                                run = True
                    elif isVarb(c[3]):
                        if isInt(isVarb(c[3])):
                            if c[2] == '<':
                                if int(isVarb(c[1])) < int(isVarb(c[3])):
                                    run = True
                            if c[2] == '>':
                                if int(isVarb(c[1])) > int(isVarb(c[3])):
                                    run = True
                            if c[2] == '==':
                                if int(isVarb(c[1])) == int(isVarb(c[3])):
                                    run = True
                            if c[2] == '!=':
                                if int(isVarb(c[1])) != int(isVarb(c[3])):
                                    run = True
                            if c[2] == '<=':
                                if int(isVarb(c[1])) <= int(isVarb(c[3])):
                                    run = True
                            if c[2] == '>=':
                                if int(isVarb(c[1])) >= int(isVarb(c[3])):
                                    run = True
                        elif isFloat(isVarb(c[3])):
                            if c[2] == '<':
                                if int(isVarb(c[1])) < float(isVarb(c[3])):
                                    run = True
                            if c[2] == '>':
                                if int(isVarb(c[1])) > float(isVarb(c[3])):
                                    run = True
                            if c[2] == '==':
                                if int(isVarb(c[1])) == float(isVarb(c[3])):
                                    run = True
                            if c[2] == '!=':
                                if int(isVarb(c[1])) != float(isVarb(c[3])):
                                    run = True
                            if c[2] == '<=':
                                if int(isVarb(c[1])) <= float(isVarb(c[3])):
                                    run = True
                            if c[2] == '>=':
                                if int(isVarb(c[1])) >= float(isVarb(c[3])):
                                    run = True
                        else:
                            print("E: can't compare int with string")
                    else:
                        print("E: can't compare int with string")
                elif isFloat(isVarb(c[1])):
                    if isInt(c[3]):
                        if c[2] == '<':
                            if float(c[1]) < int(c[3]):
                                run = True
                        if c[2] == '>':
                            if float(c[1]) > int(c[3]):
                                run = True
                        if c[2] == '==':
                            if float(c[1]) == int(c[3]):
                                run = True
                        if c[2] == '!=':
                            if float(c[1]) != int(c[3]):
                                run = True
                        if c[2] == '<=':
                            if float(c[1]) <= int(c[3]):
                                run = True
                        if c[2] == '>=':
                            if float(c[1]) >= int(c[3]):
                                run = True
                    elif isFloat(c[3]):
                        if c[2] == '<':
                            if float(c[1]) < float(c[3]):
                                run = True
                        if c[2] == '>':
                            if float(c[1]) > float(c[3]):
                                run = True
                        if c[2] == '==':
                            if float(c[1]) == float(c[3]):
                                run = True
                        if c[2] == '!=':
                            if float(c[1]) != float(c[3]):
                                run = True
                        if c[2] == '<=':
                            if float(c[1]) <= float(c[3]):
                                run = True
                        if c[2] == '>=':
                            if float(c[1]) >= float(c[3]):
                                run = True
                    elif isVarb(c[3]):
                        if isInt(isVarb(c[3])):
                            if c[2] == '<':
                                if float(c[1]) < int(c[3]):
                                    run = True
                            if c[2] == '>':
                                if float(c[1]) > int(c[3]):
                                    run = True
                            if c[2] == '==':
                                if float(c[1]) == int(c[3]):
                                    run = True
                            if c[2] == '!=':
                                if float(c[1]) != int(c[3]):
                                    run = True
                            if c[2] == '<=':
                                if float(c[1]) <= int(c[3]):
                                    run = True
                            if c[2] == '>=':
                                if float(c[1]) >= int(c[3]):
                                    run = True
                        elif isFloat(isVarb(c[3])):
                            if c[2] == '<':
                                if float(c[1]) < float(c[3]):
                                    run = True
                            if c[2] == '>':
                                if float(c[1]) > float(c[3]):
                                    run = True
                            if c[2] == '==':
                                if float(c[1]) == float(c[3]):
                                    run = True
                            if c[2] == '!=':
                                if float(c[1]) != float(c[3]):
                                    run = True
                            if c[2] == '<=':
                                if float(c[1]) <= float(c[3]):
                                    run = True
                            if c[2] == '>=':
                                if float(c[1]) >= float(c[3]):
                                    run = True
                        else:
                            print("E: can't compare float with string")
                    else:
                        print("E: can't compare float with string")
                else:
                    x = isVarb(c[1])
                    if isInt(c[3]) or isInt(c[3]):
                        print("E: can't compare string with int/float")
                    elif isVarb(c[3]):
                        if isInt(isVarb(c[3])) or isInt(isVarb(c[3])):
                            print("E: can't compare string with int/float")
                        else:
                            y = isVarb(c[3])
                            if c[2] == '==':
                                if x == y:
                                    run = True
                            if c[2] == '!=':
                                if x != y:
                                    run = True
                            if c[2] == '<':
                                if x < y:
                                    run = True
                            if c[2] == '<=':
                                if x <= y:
                                    run = True
                            if c[2] == '>':
                                if x > y:
                                    run = True
                            if c[2] == '>=':
                                if x >= y:
                                    run = True
                    else:
                        y = isVarb(c[3])
                        if c[2] == '==':
                                if x == y:
                                    run = True
                        if c[2] == '!=':
                                if x != y:
                                    run = True
                        if c[2] == '<':
                                if x < y:
                                    run = True
                        if c[2] == '<=':
                                if x <= y:
                                    run = True
                        if c[2] == '>':
                                if x > y:
                                    run = True
                        if c[2] == '>=':
                                if x >= y:
                                    run = True
            else:
                if isInt(c[3]) or isInt(c[3]):
                    print("E: can't compare string with int/float")
                elif isVarb(c[3]):
                    if isInt(isVarb(c[3])) or isInt(isVarb(c[3])):
                        print("E: can't compare string with int/float")
                    else:
                        y = isVarb(c[3])
                        if c[2] == '==':
                                if x == y:
                                    run = True
                        if c[2] == '!=':
                                if x != y:
                                    run = True
                        if c[2] == '<':
                                if x < y:
                                    run = True
                        if c[2] == '<=':
                                if x <= y:
                                    run = True
                        if c[2] == '>':
                                if x > y:
                                    run = True
                        if c[2] == '>=':
                                if x >= y:
                                    run = True
                else:
                    y = isVarb(c[3])
                    if c[2] == '==':
                                if x == y:
                                    run = True
                    if c[2] == '!=':
                                if x != y:
                                    run = True
                    if c[2] == '<':
                                if x < y:
                                    run = True
                    if c[2] == '<=':
                                if x <= y:
                                    run = True
                    if c[2] == '>':
                                if x > y:
                                    run = True
                    if c[2] == '>=':
                                if x >= y:
                                    run = True
        #breakpoint()
        if script_run:
            if run:
                return
            else:
                for ij in range(rip, len(commands)):
                    if commands[ij] == 'done':
                        rip += ij
                        return
        w_l = [' '.join(c)]
        while True:
            x = input('> ')
            if x == 'done':
                break
            if x:
                w_l.append(x)
        if run:
            script_run = True
            for k in w_l:
                commands.append(k)
            commands.append('done')
        else:
            return
    else:
        print("E: incorrect syntax")


def sudo(c):
    global user
    global cur_user
    global is_sudo
    global cd
    global cv
    global is_auth
    authenticated = False
    if user != 'core':
        if not is_auth:
            pw = enc(str(getpass.getpass("[cudo] PassWord for {} -> ".format(user))))
            cur.execute("SELECT * FROM usr WHERE uname='{}' AND passwd='{}'".format(user, pw))
            if cur.fetchone():
                authenticated = True
        else:
            authenticated = True
        if authenticated:
            fn = get_f_name('/etc/sudoers')
            with open(fn, 'r') as f:
                contents = f.read().splitlines()
            can, msg = can_use_sudo(contents, c)
            #breakpoint()
            if can:
                is_sudo = True
                cd = True
                cv = c[1:]
                cur_user = user
                user = msg
                is_auth = True
            else:
                print(msg)
    else:
        is_sudo = True
        cd = True
        cv = c[1:]

def can_use_sudo(con, c):
    user_present = False
    su_users = ''
    su_cmds = ''
    for i in con:
        if i.split(' ')[0] == user:
            user_present = True
            su_users, su_cmds = i.split(' ')[1].split(':')
            break
    if len(c) >= 2:
        if c[1].startswith('-'):
            if c[1] not in ['-u']:
                return (False, "Error: parameter '{}' not recognozed".format(c[1]))
    if len(c) >=2 and c[1] == '-u':
        if len(c) < 3:
            return (False, "Error: Please specify a user")
        cur.execute("SELECT * FROM usr WHERE uname='{}'".format(c[2]))
        if not cur.fetchall():
            return (False,"Error: No such user {} in the system".format(c[2]))
    if user_present:
        if su_users.upper() == 'ALL':
            if su_cmds.upper() == 'ALL':
                if len(c) >= 3 and c[1] == '-u':
                    if len(c) == 3:
                        return (False,"Info: No command specified")
                    return (True, c[2])
                if len(c) == 1:
                    return (False,"Info: No command specified")
                return (True, 'core')
            else:
                if len(c) >= 3 and c[1] == '-u':
                    if len(c) >= 3 and c[3] in su_cmds.split(','):
                        if len(c) >= 3 and c[1] == '-u':
                            return (True, c[2])
                        return (True, 'core')
                    else:
                        return (False, "Error: You are not authorized to use {} as sudo on {}".format(c[3], getHostname()))
                else:
                    if len(c) >= 2 and c[1] in su_cmds.split(','):
                        if len(c) >= 3 and c[1] == '-u':
                            return (True, c[2])
                        return (True, 'core')
                    else:
                        return (False, "Error: You are not authorized to use {} as core on {}".format(c[1], getHostname()))
        else:
            if len(c) >= 3 and c[1] == '-u':
                if c[2] in su_users.split(','):
                    if su_cmds.upper() == 'ALL':
                        if len(c) >= 3 and c[1] == '-u':
                            return (True, c[2])
                        return (True, 'core')
                    else:
                        if c[1] == '-u':
                            if len(c) >= 4 and c[3] in su_cmds.split(','):
                                if len(c) >= 3 and c[1] == '-u':
                                    return (True, c[2])
                                return (True, 'core')
                            elif len(c) == 3:
                                return (False, "Info: No command specified")
                            else:
                                return (False, "Error: You are not authorized to use {} on {}".format(c[3], getHostname()))
                        else:
                            if len(c) >= 3 and c[1] in su_cmds.split(','):
                                if len(c) >= 3 and c[1] == '-u':
                                    return (True, c[2])
                                return (True, 'core')
                            elif len(c) == 3:
                                return (False, "Info: No command specified")
                            else:
                                return (False, "Error: You are not authorized to use {} on {}".format(c[3], getHostname()))
                else:
                    return (False, "Error: You are not authorized to run sudo as {} on {}".format(c[2], getHostname()))
            else:
                if 'core' in su_users.split(','):
                    if su_cmds.upper() == 'ALL':
                        return (True, '')
                    else:
                        if len(c) >= 4 and c[1] == '-u':
                            if c[3] in su_cmds.split(','):
                                if len(c) >= 3 and c[1] == '-u':
                                    return (True, c[1])
                                return (True, 'core')
                            else:
                                return (False, "Error: You are not authorized to run sudo as {} on {}".format(c[3], getHostname()))
                        else:
                            if len(c) >= 3 and c[1] in su_cmds.split(','):
                                if len(c) >= 3 and c[1] == '-u':
                                    return (True, c[1])
                                return (True, 'core')
                            else:
                                return (False, "Error: You are not authorized to run sudo as {} on {}".format(c[3], getHostname()))
                else:
                    return (False, "Erro: You are not authorized to run sudo as core on {}".format(getHostname()))
    else:
        return (False, "Error: You are not authorized to use sudo on {}".format(getHostname()))
    

def get_f_name(f):
    #breakpoint()
    base = 'C:/Users/sanjsark/SarkSys/0-ss'
    fp = f.split('/')[1:]
    for pfn in fp:
        for fpe in os.listdir(base):
            if fpe.split('-')[-1] == pfn:
                if os.path.isfile(base+'/'+fpe):
                    return base+'/'+fpe
                elif os.path.isdir(base+'/'+fpe):
                    base = base+'/'+fpe
    
            


# Login ------------------------------------------------------------------------------------------------------------------------------------------

if first_try:
    os.mkdir('C:/Users/sanjsark/SarkSys/0-ss')
    os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/2-home')
    print("It seems to be your first time using SarkSys, please create a CORE user who has full access of the System.")
    print("Please enter a password for the CORE user. (Note: You won't be able to see the password being entered)")
    if live:
        cp = getpass.getpass("PassWord for core -> ")
    else:
        cp = str(input("PassWord for core -> "))
    print("Please create another user with limited access (It can be your ID as well)")
    un = input("Enter UserName -> ")
    if live:
        pw = getpass.getpass("Enter PassWord -> ")
    else:
        pw = str(input("Enter PassWord -> "))
    cur.execute("CREATE TABLE usr (uname VARCHAR(20), passwd VARCHAR(20));")
    cur.execute("CREATE TABLE cudoers (un VARCHAR(20));")
    cur.execute("CREATE TABLE logs (log VARCHAR(20));")
    cur.execute("CREATE TABLE inode (ind INTEGER(10), fn VARCHAR(20), ow VARCHAR(20), gr VARCHAR(20), perm VARCHAR(5))")
    cur.execute("CREATE TABLE dmask (dmask INTEGER(5))")
    cur.execute("CREATE TABLE login (uname VARCHAR(20), time VARCHAR(20));")
    cur.execute("CREATE TABLE grp (uname TEXT, grps TEXT)")
    cur.execute("INSERT INTO grp VALUES('{}', '{}')".format('core', 'core-'))
    cur.execute("INSERT INTO grp VALUES('{}', '{}')".format(un, un+'-'))
    cur.execute("INSERT INTO dmask VALUES (754)")
    cur.execute("INSERT INTO usr VALUES ('core', '{}')".format(enc(cp)))
    os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/1-core')
    cur.execute("INSERT INTO usr VALUES ('{}', '{}')".format(un, enc(pw)))
    os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/2-home/3-{}'.format(un))
    os.chdir('C:/Users/sanjsark/SarkSys/0-ss/2-home/3-{}'.format(un))
    cur.execute("INSERT INTO cudoers VALUES ('{}')".format(un))
    home = 'C:/Users/sanjsark/SarkSys/0-ss/2-home/3-{}'.format(un)
    cur.execute("INSERT INTO inode VALUES(0, 'ss', 'core', 'core', '754')")
    cur.execute("INSERT INTO inode VALUES(1, 'core', 'core', 'core', '750')")
    cur.execute("INSERT INTO inode VALUES(2, 'home', 'core', 'core', '755')")
    cur.execute("INSERT INTO inode VALUES(3, '{}', '{}', '{}', '755')".format(un, un, un))
    cur.execute("INSERT INTO inode VALUES(4, 'boot', 'core', 'core', '755')")
    os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/4-boot')
    cur.execute("INSERT INTO inode VALUES(5, 'etc', 'core', 'core', '755')")
    os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/5-etc')
    cur.execute("INSERT INTO inode VALUES(9, 'host', 'core', 'core', '777')")
    os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/5-etc/9-host')
    cur.execute("INSERT INTO inode VALUES(6, 'login', 'core', 'core', '754')")
    with open('C:/Users/sanjsark/SarkSys/0-ss/4-boot/5-login', 'w') as f:
        pass
    cur.execute("INSERT INTO inode VALUES(7, 'hostname', 'core', 'core', '766')")
    with open('C:/Users/sanjsark/SarkSys/0-ss/5-etc/9-host/7-hostname', 'w') as f:
        f.write('SarkSys')
    cur.execute("INSERT INTO inode VALUES(10, 'sudoers', 'core', 'sudoers', '640')")
    with open('C:/Users/sanjsark/SarkSys/0-ss/5-etc/10-sudoers', 'w') as f:
        f.write('{} ALL:ALL'.format(un))
    login(un)
    conn.commit()
    access = True
    clear()
else:
    print("**SarkSys**")
    while True:
        try:
            if fixUser():
                us = fixUser()
                print("An initial user is found, please enter your password to continue")
                print("Welcome, {}".format(us))
                un = us
                if live:
                    pw = getpass.getpass("PassWord -> ")
                else:
                    pw = str(input("PassWord -> "))
            else:
                print("Welcome, please authenticate.")
                un = input("UserName -> ")
                if live:
                    pw = getpass.getpass("PassWord -> ")
                else:
                    pw = str(input("PassWord -> "))
        except:
            up = coreLogin()
            un, pw = up[0], up[1]
        cur.execute("SELECT * FROM usr WHERE uname='{}' AND passwd='{}'".format(un, enc(pw)))
        if cur.fetchall():
            access = True
            clear()
            llogin(un)
            login(un)
            if un == 'core':
                os.chdir('C:/Users/sanjsark/SarkSys/0-ss/1-core')
                home = 'C:/Users/sanjsark/SarkSys/0-ss/1-core'
            else:
                for i in os.listdir('C:/Users/sanjsark/SarkSys/0-ss/2-home/'):
                    if os.path.isdir('C:/Users/sanjsark/SarkSys/0-ss/2-home/' + i) and i.endswith(un):
                        os.chdir('C:/Users/sanjsark/SarkSys/0-ss/2-home/{}'.format(i))
                        home = 'C:/Users/sanjsark/SarkSys/0-ss/2-home/{}'.format(i)
            if up:
                if not os.path.isdir('C:/Users/sanjsark/SarkSys/0-ss/4-boot'):
                    os.mkdir('C:/Users/sanjsark/SarkSys/0-ss/4-boot')
                    cur.execute("INSERT INTO inode VALUES(4, 'boot', 'core', 'core', '755')")
                with open('C:/Users/sanjsark/SarkSys/0-ss/4-boot/5-login', 'w') as f:
                    pass
                i = givePerm(un, un)
                cur.execute("UPDATE inode SET perm='{}' WHERE ind={}".format('750', int(i)))
                cur.execute("INSERT INTO inode VALUES(5, 'login', 'core', 'core', '754')")
            break
        else:
            print("Incorrect credentials.\n")

user = un

if access:

    login(user)

    #breakpoint()
    
    while True:
        #breakpoint()
        get_alias() 
        cur_d = '/' + '/'.join(os.getcwd().split('\\')[5:])
        if script_run:
            if commands:
                if rip < len(commands):
                    c = commands[rip].split(' ')
                    rip += 1
                else:
                    commands = []
                    rip = 0
                    script_run = False
                    run_now = True
        elif not cd or run_now:
            c = input("{}@{}[{}]{} ".format(getHostname(), user.upper(), pd(cur_d, user), '#' if user == 'core' else '$')).split()
        else:
            c = cv
            cd = False
            cv = ''
        if run_now:
            c = input("{}@{}[{}]{} ".format(getHostname(), user.upper(), pd(cur_d, user), '#' if user == 'core' else '$')).split()
            run_now = False
        if len(c) == 0:
            continue

        elif c[0] == 'fi':
            continue

        elif c[0] == 'else':
            if else_stat:
                else_stat = False
                continue
            else:
                for ij in range(rip, len(commands)):
                    if commands[ij] == 'fi':
                        rip += ij
                        break

        elif c[0] == 'done':
            rip = while_rip

        elif c[0].startswith('#'):
            continue


        elif c[0] in alias:
            cd = True
            cv = alias[c[0]].split(' ')

        elif c[0] in g_alias:
            cd = True
            cv = g_alias[c[0]].split(' ')
            
        elif c[0] == 'clear':
            clear()
        elif c[0] == 'su':
            if len(c) >  2:
                print("Usage: su [<username>]")
            else:
                user = su(c, user)

        elif c[0] == 'useradd':
            if len(c) != 2:
                print("Usage: useradd <username>")
            else:
                useradd(c[1])

        elif c[0] == 'sudo':
            if len(c) >= 2 and c[1] == '-l':
                pw = enc(str(getpass.getpass("[cudo] PassWord for {} -> ".format(user))))
                cur.execute("SELECT * FROM usr WHERE uname='{}' AND passwd='{}'".format(user, pw))
                if cur.fetchone():
                    lne = ''
                    filename = get_f_name('/etc/sudoers')
                    with open(filename, 'r') as f:
                        cont = f.read().splitlines()
                    for i in cont:
                        if i.split(' ')[0] == user:
                            lne = i
                    if lne:
                        print("User {} can run following commands on {}".format(user, getHostname()))
                        print(lne)
                    else:
                        print("User {} cannot run sudo on {}".format(user, getHostname()))
            else:
                sudo(c)
                continue        

        elif c[0] == 'cudo':
            print("Info: 'codo' has been deprecated, please user 'sudo'")
            continue
            if len(c) ==  1:
                print("Usage: cudo [command]")
            else:
                if is_auth:
                    cd = True
                    cv = c[1:]
                    cudo_ = True
                else:
                    if user != 'core':
                        pw = enc(str(getpass.getpass("[cudo] PassWord for {} -> ".format(user))))
                        cur.execute("SELECT * FROM usr WHERE uname='{}' AND passwd='{}'".format(user, pw))
                        if cur.fetchone():
                            cur.execute("SELECT * FROM cudoers WHERE un='{}'".format(user))
                            if cur.fetchone():
                                is_auth = True
                                cd = True
                                cv = c[1:]
                                cudo_ = True
                            else:
                                print("Error: You are not authorized to use cudo on {}".format(getHostname()))
                                addLog(user, dt(), 'cudo', "Error: You are not authorized to use cudo on {}".format(getHostname()))
                    else:
                        cd = True
                        cv = c[1:]
                        
        elif c[0] == 'userdel':
            if len(c) != 2:
                print("Usage: userdel <username>")
            else:
                userdel(c[1])

        elif c[0] == 'logs':
            if len(c) > 1:
                print("Usage: logs")
            else:
                logs()

        elif c[0] == 'cuadd':
            if len(c) < 2:
                print("Usage: cuadd [username1, [username2,[....]]")
            else:
                cuadd(c)

        elif c[0] == 'curem':
            if len(c) < 2:
                print("Usage: curem [username1, [username2,[....]]")
            else:
                curem(c)

        elif c[0] == 'culist':
            if len(c) > 1:
                print("Usage: culist")
            else:
                culist()

        elif c[0] == 'passwd':
            if len(c) > 2:
                print("Usage: passwd [username]")
            else:
                passwd(c)

        elif c[0] == 'pwd':
            if len(c) > 1:
                print("Usage: pwd")
            else:
                pwd()

        elif c[0] == 'ls':
            if len(c) > 2:
                print("Usage: ls [dir]")
            else:
                ls(c)

        elif c[0] == 'la':
            if len(c) > 2:
                print("Usage: la [dir]")
            else:
                la(c)

        elif c[0] == 'cd':
            if len(c) > 2:
                print("Usage: cd [path]")
            else:
                ccd(c, os.getcwd())

        elif c[0] == 'mkdir':
            if len(c) != 2:
                print("Usage: mkdir <dirname>")
            else:
                mkdir(c)

        elif c[0] == 'rmdir':
            if len(c) !=  2:
                print("Usage: rmdir <dirname>")
            else:
                rmdir(c)

        elif c[0] == 'touch':
            if len(c) < 2:
                print("Usage: touch [filename1,[filename2[,,]]")
            else:
                touch(c)

        elif c[0] == 'rm':
            if len(c) < 2:
                print("Usage: rm [filename1,[filename2[,,]]")
            else:
                rm(c)

        elif c[0] == 'll':
            if len(c) > 2:
                print("Usage: ll [dir]")
            else:
                ll(c)

        elif c[0] == 'chmod':
            if len(c) < 3:
                print("Usage: chmod <perms> [filname1, filename2[,]]")
            else:
                chmod(c)

        elif c[0] == 'whoami':
            print(user)

        elif c[0] == 'dmask':
            if len(c) > 2:
                print("Usage: dmask <value>")
            else:
                dmask(c)

        elif c[0] == 'me':
            if len(c) > 1:
                print("Usage: me")
            else:
                me()

        elif c[0] == 'groupadd':
            if len(c) < 3:
                print("Usage: groupadd [uname1, [uname2,[,]]] [groupname]")
            else:
                groupadd(c)

        elif c[0] == 'chown':
            if len(c) < 3:
                print("Usage:chown [uname] [filename1,[filename2[,]]]")
            else:
                chown(c)

        elif c[0] == 'chgroup':
            if len(c) < 3:
                print("Usage:chgroup [uname] [filename1,[filename2[,]]]")
            else:
                chgroup(c)

        elif c[0] == 'cat':
            if len(c) < 2:
                print("Usage: cat [filename1,[filename2[,]]]")
            else:
                cat(c)

        elif c[0] == 'grouprem':
            if len(c) < 3:
                print("Usage: grouprem [uname1, [uname2,[,]]] [groupname]")
            else:
                grouprem(c)

        elif c[0] == 'inlog':
            if len(c) > 2:
                print("Usage: inlog <username>")
            else:
                inlog(c)

        elif c[0] == 'getip':
            if len(c) < 2:
                print("Usage: ip [hostname1,[hostname2[,]]]")
            else:
                getip(c)

        elif c[0] == 'ip':
            ip(c)

        elif c[0] == 'cp':
            if len(c) > 3  or len(c) < 2:
                print("Usage: cp <source-file> <destination-file>")
            else:
                cp(c)

        elif c[0] == 'alias':
            if len(c) < 2:
                for k,v in alias.items():
                    print('{}: {}'.format(k, v))
                for k,v in g_alias.items():
                    print('{}: {}'.format(k, v))
            else:
                ph = ' '.join(c[1:])
                alias[ph.split('=')[0]] = ph.split('=')[1]

        elif c[0] == 'unalias':
            if len(c) < 2:
                print('Usage: unalias <alias_name>/-a')
            else:
                if c[1] == '-a':
                    alias = {}
                    g_alias = {}
                else:
                    for i in c[1:]:
                        if i in alias:
                            del alias[i]
                        elif i in g_alias:
                            del g_alias
                        else:
                            print('E: alias {} not found'.format(i))


        elif c[0] == 'echo':
            if len(c) > 1:
                echo(c)

        elif c[0] == 'vars':
            for i in variables:
                print(i)

        elif c[0] == 'del':
            if len(c) < 1:
                print("Usage: del [var1, [var2[,]]]")
            else:
                for i in c[1:]:
                    if i in variables:
                        del variable[i]
                    else:
                        print("E: " + i + ": no such variable")

        elif c[0] == 'read':
            if len(c) > 1:
                read(c)

        elif c[0] == 'ss':
            if len(c) != 2:
                print("Usage: ss <filename>")
            else:
                if is_authorized_x(c[1]):
                    script_run = True
                    fn = get_file_name(c[1])
                    with open(fn, 'r') as f:
                        for i in f.readlines():
                            commands.append(i.strip('\n'))

        elif c[0] == 'se':
            if len(c) != 2:
                print("Usage: se <filename>")
            else:
                editor(c)

        elif c[0] == 'if':
            ifstat(c)


        elif c[0] == 'while':
            whileloop(c)
                
            
        elif c[0] == 'exit':
            print("Exiting...")
            conn.commit()
            conn.close()
            sys.exit(0)

        else:
            if '=' in c:
                var(c)
            else:
                print(c[0], ": no such command")
        if is_sudo:
            is_sudo = False
            if is_su:
                is_su = False
                continue
            user = cur_user
