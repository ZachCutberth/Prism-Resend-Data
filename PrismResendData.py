#! python3
# Resend Prism data through day to day replication
# By Zach Cutberth

import PySimpleGUI as sg
import cx_Oracle
import pymysql.cursors
import os
import winreg
from subprocess import Popen, PIPE
import config

version = '1.1'

about_text = f'''
Prism Resend Tool
Version: {version}
Retail Pro International

Supports Prism 1.11.*, 1.12.*, 1.13.*, 1.14.*

Resending Data to MySQL Requires: 
- Microsoft Visual C++ 2013 Redistributable (x64)
'''

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_prism_dbtype():
    try: 
        prism_regkeys = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                "SOFTWARE\\WOW6432Node\\Retail Pro\\Prism\\Primary")
    except:
        prism_not_found = 1
        return prism_not_found

    try:
        [dbtype, reg_type] = winreg.QueryValueEx(prism_regkeys, "DBType")
        if dbtype == 'Oracle':
            winreg.CloseKey(prism_regkeys)
            return dbtype
        else:
            dbtype = 'MySQL'
            winreg.CloseKey(prism_regkeys)
            return dbtype
    except:
            dbtype = 'None'
            return dbtype
    

def get_mysql_path():
    try:
        prism_regkeys = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                "SOFTWARE\\WOW6432Node\\Retail Pro\\Prism\\Primary")
        mysql_path = winreg.QueryValueEx(prism_regkeys, "DBInstallPath")
        winreg.CloseKey(prism_regkeys)
        return mysql_path
    except:
        pass

def resend_oracle(resource_type, filter_type, from_date=None, to_date=None, sid_list=None, docnum_list=None, store_list=None):
    connstr = config.connstr
    dbconnection = cx_Oracle.connect(connstr)
    cursor = dbconnection.cursor()

    if resource_type == 'Document':
        if filter_type == 'date':
            select_statement = 'for rRec in (select * from rps.document t where t.status = 4 and coalesce(t.is_held, 0) = 0 and t.invc_post_date >= from_date and t.invc_post_date < to_date + 1) loop'
        if filter_type == 'date_store':
            select_statement = 'for rRec in (select * from rps.document t where t.status = 4 and coalesce(t.is_held, 0) = 0 and t.invc_post_date >= from_date and t.invc_post_date < to_date + 1 and store_code in (' + store_list + ')) loop'
        if filter_type == 'sid':
            select_statement = 'for rRec in (select * from rps.document t where t.status = 4 and coalesce(t.is_held, 0) = 0 and t.sid in (' + sid_list + ')) loop'
        if filter_type == 'docnum':
            select_statement = 'for rRec in (select * from rps.document t where t.status = 4 and coalesce(t.is_held, 0) = 0 and t.doc_no in (' + docnum_list + ')) loop'

    if resource_type == 'Inventory':
        if filter_type == 'date':
            select_statement = 'for rRec in (select * from rps.invn_sbs_item t where t.publish_status = 0 and t.modified_datetime >= from_date and t.modified_datetime < to_date + 1) loop'
        if filter_type == 'sid':
            select_statement = 'for rRec in (select * from rps.invn_sbs_item t where t.publish_status = 0 and t.sid in (' + sid_list + ')) loop'

    if resource_type == 'Customer':
        if filter_type == 'date':
            select_statement = 'for rRec in (select * from rps.customer t where t.modified_datetime >= from_date and t.modified_datetime < to_date + 1) loop'
        if filter_type == 'sid':
            select_statement = 'for rRec in (select * from rps.customer t where t.sid in (' + sid_list + ')) loop'

    if resource_type == 'Vendor':
        if filter_type == 'date':
            select_statement = 'for rRec in (select * from rps.vendor t where t.modified_datetime >= from_date and t.modified_datetime < to_date + 1) loop'
        if filter_type == 'sid':
            select_statement = 'for rRec in (select * from rps.vendor t where t.sid in (' + sid_list + ')) loop'

    if resource_type == 'Receiving':
        if filter_type == 'date':
            select_statement = 'for rRec in (select * from rps.voucher t where t.held = 0 and t.publish_status = 0 and ((t.vou_class = 0 and t.status = 4) or (t.vou_class = 2 and t.status = 3)) and t.created_datetime >= from_date and t.created_datetime < to_date + 1) loop'
        if filter_type == 'sid':
            select_statement = 'for rRec in (select * from rps.voucher t where t.held = 0 and t.publish_status = 0 and ((t.vou_class = 0 and t.status = 4) or (t.vou_class = 2 and t.status = 3)) and t.sid in (' + sid_list + ')) loop'

    if resource_type == 'Transferslip':
        if filter_type == 'date':
            select_statement = 'for rRec in (select * from rps.slip t where t.held = 0 and t.status = 4 and t.created_datetime >= from_date and t.created_datetime < to_date + 1) loop'
        if filter_type == 'sid':
            select_statement = 'for rRec in (select * from rps.slip t where t.held = 0 and t.status = 4 and t.sid in (' + sid_list + ')) loop'

    if resource_type == 'Zoutcontrol':
        if filter_type == 'date':
            select_statement = 'for rRec in (select * from rps.zout_control t where t.post_date >= from_date and t.post_date < to_date + 1) loop'
        if filter_type == 'sid':
            select_statement = 'for rRec in (select * from rps.zout_control t where t.sid in (' + sid_list + ')) loop'

    if resource_type == 'Drawerevent':
        if filter_type == 'date':
            select_statement = 'for rRec in (select * from rpsods.drawer_event t where t.event_type in (3, 4, 5, 6) and t.created_datetime >= from_date and t.created_datetime < to_date + 1) loop'
        if filter_type == 'sid':
            select_statement = 'for rRec in (select * from rps.drawer_event t where t.sid in (' + sid_list + ')) loop'

    resend_script = """
    declare
        from_date date := date'""" + from_date + """';
        to_date date := date'""" + to_date + """';
        -- list of resource names could be found in resource_name column of rps.prism_resource table
        -- IMPORTANT: MUST BE IN LOWER CASE
        res_name varchar2(50) := '""" + resource_type.lower() + """';
        inserted integer;
        deSID number(19);
        res_namespace varchar2(100);
    begin
        -- loop by documents

        -- adjust this query to reflect what you want to re-send and what to filter it by

        """+ select_statement +"""

            inserted := 0;
            deSID := 0;

            -- loop by connections for requested resource
            for rConn in 
                (select cs.sid, r.resource_name, r.rps_entity_name, cs.controller_sid,
                    r.resource_name as true_name, r.sid as resource_sid
                from rps.rem_connection_subscr cs
                join rps.remote_connection c
                    on (cs.remote_connection_sid = c.sid)
                    and (c.active = 1)
                join rps.rem_subscription s
                    on (cs.subscription_sid = s.sid)
                    and (s.active = 1) and (s.subscription_type in (0, 1))
                join rps.rem_subscr_resource sr
                    on (s.sid = sr.rem_subscription_sid)
                join rps.prism_resource r
                    on (sr.prism_resource_sid = r.sid)
                    and lower(r.namespace) = 'replication'
                where lower(r.resource_name) = res_name)
            loop
            
                begin
                    select '/api/' || t.namespace || '/' || res_name || '/' into res_namespace from rps.prism_resource t
                    where lower(t.resource_name) = res_name and lower(t.namespace) <> 'replication' and rownum = 1;
                exception
                    when no_data_found then res_namespace := '/v1/rest/' || res_name || '/';
                end;

                -- insert data event record (one time only)
                if inserted = 0 then
                    deSID := rps.rps_common.GetSid;
                    insert into rps.pub_dataevent_queue t
                    (sid, created_by, created_datetime, post_date, controller_sid, origin_application, row_version,
                    resource_name, resource_sid, link, event_type,
                    attributes_affected, prism_resource_sid)
                    values
                    (deSID, 'PUBSUB', sysdate, sysdate, rRec.controller_sid, 'ReSendScript', 1,
                    upper(rConn.true_name), rRec.sid, res_namespace || rRec.sid, 2,
                    'ROW_VERSION,Status', rConn.resource_sid);
                    inserted := inserted + 1;
                end if;

                -- insert data notification record (one per subscriber)
                insert into rps.pub_notification_queue
                    (sid, created_by, created_datetime, post_date, controller_sid,
                    origin_application, row_version, dataevent_queue_sid, subscription_event_sid, transmit_status)
                values
                    (rps.rps_common.GetSid, 'PUBSUB', sysdate, sysdate, rRec.controller_sid,
                    'ReSendScript', 1, deSID, rConn.sid, 0);
      
            end loop;
            -- loop by connections

        end loop;
        -- loop by documents
      commit;
      end;
    """
    
    cursor.execute(resend_script)
    
    cursor.close()
    dbconnection.close()

def resend_mysql(resource_type, filter_type, from_date=None, to_date=None, sid_list=None, docnum_list=None, store_list=None, server_name='localhost'):
    
    if resource_type == 'Document':
        if filter_type == 'date':
            select_statement = """declare cRec cursor for
                                        select t.sid, t.controller_sid from rpsods.document t where t.status = 4 and coalesce(t.is_held, 0) = 0 and
                                        t.invc_post_date >= from_date and t.invc_post_date < to_date + 1;"""
        if filter_type == 'date_store':
            select_statement = """declare cRec cursor for
                                        select t.sid, t.controller_sid from rpsods.document t where t.status = 4 and coalesce(t.is_held, 0) = 0 and
                                        t.invc_post_date >= from_date and t.invc_post_date < to_date + 1 and store_code in (""" + store_list + """);"""
        if filter_type == 'sid':
            select_statement = """declare cRec cursor for
                                        select t.sid, t.controller_sid from rpsods.document t where t.status = 4 and t.sid in (""" + sid_list + """);"""
        if filter_type == 'docnum':
            select_statement = """declare cRec cursor for
                                        select t.sid, t.controller_sid from rpsods.document t where t.status = 4 and t.doc_no in (""" + docnum_list + """);"""

    if resource_type == 'Inventory':
        if filter_type == 'date':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.invn_sbs_item t where t.publish_status = 0 and
                                        t.modified_datetime >= from_date and t.modified_datetime < to_date + 1;"""
        if filter_type == 'sid':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.invn_sbs_item t where t.publish_status = 0 and
                                        t.sid in (""" + sid_list + """);"""

    if resource_type == 'Customer':
        if filter_type == 'date':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.customer t where
                                        t.modified_datetime >= from_date and t.modified_datetime < to_date + 1;"""
        if filter_type == 'sid':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.customer t where
                                       t.sid in (""" + sid_list + """);"""

    if resource_type == 'Vendor':
        if filter_type == 'date':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.vendor t where
                                        t.modified_datetime >= from_date and t.modified_datetime < to_date + 1;"""
        if filter_type == 'sid':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.vendor t where
                                        t.sid in (""" + sid_list + """);"""

    if resource_type == 'Receiving':
        if filter_type == 'date':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.voucher t where t.held = 0 and t.publish_status = 0 and
                                       ((t.vou_class = 0 and t.status = 4) or (t.vou_class = 2 and t.status = 3)) and 
                                       t.created_datetime >= from_date and t.created_datetime < to_date + 1;"""
        if filter_type == 'sid':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.voucher t where t.held = 0 and t.publish_status = 0 and
                                       ((t.vou_class = 0 and t.status = 4) or (t.vou_class = 2 and t.status = 3)) and 
                                       t.sid in (""" + sid_list + """);"""

    if resource_type == 'Transferslip':
        if filter_type == 'date':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.slip t where t.held = 0 and 
                                       t.status = 4 and t.created_datetime >= from_date and t.created_datetime < to_date + 1;"""
        if filter_type == 'sid':
            select_statement = """declare cRec cursor for
                                       select t.sid, t.controller_sid from rpsods.slip t where t.held = 0 and
                                       t.status = 4 and t.sid in (""" + sid_list + """);"""

    if resource_type == 'Zoutcontrol':
        if filter_type == 'date':
            select_statement = """declare cRec cursor for
                                        select t.sid, t.controller_sid from rpsods.zout_control t where
                                        t.post_date >= from_date and t.post_date < to_date + 1;"""
        if filter_type == 'sid':
            select_statement = """declare cRec cursor for
                                        select t.sid, t.controller_sid from rpsods.zout_control t where t.sid in (""" + sid_list + """);"""

    if resource_type == 'Drawerevent':
        if filter_type == 'date':
            select_statement = """declare cRec cursor for
                                        select t.sid, t.controller_sid from rpsods.drawer_event t where t.event_type in (3, 4, 5, 6) and 
			                            t.created_datetime >= from_date and t.created_datetime < to_date + 1;"""
        if filter_type == 'sid':
            select_statement = """declare cRec cursor for
                                        select t.sid, t.controller_sid from rpsods.drawer_event t where t.sid in (""" + sid_list + """);"""

    sql = """
    -- NOTE: this script is for Prism 1.10 or higher - it will NOT work on older version

    -- drop procedure resend_script;
    drop procedure if exists resend_script;
    SET SQL_SAFE_UPDATES = 0;
    delimiter $$
    create procedure resend_script()
    begin
        declare from_date date default date'""" + from_date + """';
        declare to_date date   default date'""" + to_date + """';
        -- list of resource names could be found in resource_name column of rpsods.prism_resource table
        -- IMPORTANT: MUST BE IN LOWER CASE
        declare res_name varchar(50) default '""" + resource_type.lower() + """';
        declare inserted int;
        declare deSID bigint;
        declare res_namespace varchar(100);
        declare rec_sid bigint;
        declare controller_sid bigint;

        -- loop by documents
        declare rec_loop_exit boolean;

        -- adjust this query to reflect what you want to re-send and what to filter it by

        """+ select_statement +"""

        declare continue handler for not found set rec_loop_exit = true;

        open cRec;

        document_loop: loop
            set inserted = 0;
            set deSID = 0;

            fetch cRec into rec_sid, controller_sid;
            if rec_loop_exit then
            close cRec;
            leave document_loop;
            end if;

            begin
            declare subscr_sid bigint;
            declare resource_name varchar(50);
            declare rps_entity_name varchar(50);
            declare subscr_contr_sid bigint;
            declare true_name varchar(50);
            declare res_sid bigint;
            declare res_namespace varchar(100);

            declare conn_loop_exit boolean;

            declare cConn cursor for
                select cs.sid, r.resource_name, r.rps_entity_name, cs.controller_sid,
                    r.resource_name as true_res_name, r.sid as resource_sid
                from rpsods.rem_connection_subscr cs
                join rpsods.remote_connection c
                    on (cs.remote_connection_sid = c.sid)
                    and (c.active = 1)
                join rpsods.rem_subscription s
                    on (cs.subscription_sid = s.sid)
                    and (s.active = 1) and (s.subscription_type in (0, 1))
                join rpsods.rem_subscr_resource sr
                    on (s.sid = sr.rem_subscription_sid)
                join rpsods.prism_resource r
                    on (sr.prism_resource_sid = r.sid)
                    and lower(r.namespace) = 'replication'
                where lower(r.resource_name) = res_name;

            declare continue handler for not found set conn_loop_exit = true;

            open cConn;

            -- loop by connections for requested resource

            conn_loop: loop
                fetch cConn into subscr_sid, resource_name, rps_entity_name, subscr_contr_sid, true_name, res_sid;
                if conn_loop_exit then
                leave conn_loop;
                end if;

                set res_namespace = concat('/v1/rest/', res_name, '/');
                begin
                declare continue handler for 1329 begin end;
                select concat('/api/', t.namespace, '/', res_name, '/')
                into res_namespace
                from rpsods.prism_resource t
                where lower(t.resource_name) = res_name
                    and lower(t.namespace) <> 'replication'
                limit 1;
                end;

                -- insert data event record (one time only)
                if inserted = 0 then
                set deSID = GetSid();
                insert into rpsods.pub_dataevent_queue
                    (sid, created_by, created_datetime, post_date, controller_sid, origin_application, row_version,
                    resource_name, resource_sid, link, event_type,
                    attributes_affected, prism_resource_sid)
                values
                    (deSID, 'PUBSUB', sysdate(), sysdate(), controller_sid, 'ReSendScript', 1,
                    upper(true_name), rec_sid, concat(res_namespace, rec_sid), 2,
                    'ROW_VERSION,Status', res_sid);
                set inserted = inserted + 1;
                end if;

                -- insert data notification record (one per subscriber)
                insert into rpsods.pub_notification_queue
                (sid, created_by, created_datetime, post_date, controller_sid,
                origin_application, row_version, dataevent_queue_sid, subscription_event_sid, transmit_status)
                values
                (GetSid(), 'PUBSUB', sysdate(), sysdate(), controller_sid,
                'ReSendScript', 1, deSID, subscr_sid, 0);

            end loop conn_loop;

            close cConn;
        end;
        end loop document_loop;
        -- loop by documents
        commit;
    end;
    $$
    delimiter ;
    call resend_script();
    drop procedure resend_script;

    -- SET SQL_SAFE_UPDATES = 1;                                  
    """
    sql_file = open('resend.sql', 'w')
    sql_file.write(sql)
    sql_file.close()
    path = os.getcwd()
    if dbtype == 'MySQL':
        mysql_exe = '\"' + mysql_path[0] + '\\bin\\mysql.exe' + '\"' 
        Popen(mysql_exe + ' -u' + config.mysql_user + ' -p' + config.mysql_pass + ' rpsods < "' + path + '\\resend.sql"', shell=True).communicate()
        os.remove('resend.sql')
    else:
        mysql_exe = '\"' + resource_path('mysql.exe') + '\"' 
        Popen(mysql_exe + ' -u' + config.mysql_user + ' -p' + config.mysql_pass + ' -h ' + server_name + ' rpsods < "' + path + '\\resend.sql"', shell=True).communicate()
        os.remove('resend.sql')

dbtype = get_prism_dbtype()
if dbtype == 'MySQL':
    mysql_path = get_mysql_path()

# Help Menu
menu_layout = [
    ['Help', 'About']
]

# layout
if dbtype == 'Oracle':
    layout = [ [sg.Menu(menu_layout)],
            [sg.Text('Database'), sg.Radio('Oracle', 'RADIO1', key='oracle', default=True, disabled=False, enable_events=True), sg.Radio('MySQL', 'RADIO1', key='mysql', disabled=False, enable_events=True)],
            [sg.Text('Server Hostname'), sg.Input(size=(50,1), key='server_name', do_not_clear=True, default_text='localhost', disabled=True)],  
            [sg.Text('Resource'), sg.InputCombo(['Document', 'Inventory', 'Customer', 'Vendor', 'Receiving', 'Transferslip', 'Zoutcontrol', 'Drawerevent'],enable_events=True, readonly=True, key='resource')],
            [sg.Text('Filter By'), sg.Radio('Date Range', 'RADIO2', default=True, key='date', enable_events=True) ,sg.Radio('Date Range + Store Code', 'RADIO2', default=False, key='date_store', enable_events=True), sg.Radio('SID', 'RADIO2', key='sid', enable_events=True), sg.Radio('Doc Number', 'RADIO2', key='docnum', enable_events=True)],
            [sg.Text('From Date (YYYY-MM-DD)'), sg.Input(size=(12,1), key='FromDate', do_not_clear=True), sg.Text('To Date (YYYY-MM-DD)'),  sg.Input(size=(12,1), key='ToDate', do_not_clear=True)],
            [sg.Text('SID, Doc Num, or Store Code'), sg.Multiline(default_text='Enter Comma Separated List', disabled=True, key='list', do_not_clear=True)],
            [sg.Button(button_text='Resend Data')]
            ]

elif dbtype == 'MySQL':
    layout = [ [sg.Menu(menu_layout)],
            [sg.Text('Database'), sg.Radio('Oracle', 'RADIO1', key='oracle', disabled=False, enable_events=True), sg.Radio('MySQL', 'RADIO1', key='mysql', disabled=False, default=True, enable_events=True)],
            [sg.Text('Server Hostname'), sg.Input(size=(50,1), key='server_name', do_not_clear=True, default_text='localhost')], 
            [sg.Text('Resource'), sg.InputCombo(['Document', 'Inventory', 'Customer', 'Vendor', 'Receiving', 'Transferslip', 'Zoutcontrol', 'Drawerevent'],enable_events=True, readonly=True, key='resource')],
            [sg.Text('Filter By'), sg.Radio('Date Range', 'RADIO2', default=True, key='date', enable_events=True) ,sg.Radio('Date Range + Store Code', 'RADIO2', key='date_store', enable_events=True), sg.Radio('SID', 'RADIO2', key='sid', enable_events=True), sg.Radio('Doc Number', 'RADIO2', key='docnum', enable_events=True)],
            [sg.Text('From Date (YYYY-MM-DD)'), sg.Input(size=(12,1), key='FromDate', do_not_clear=True), sg.Text('To Date (YYYY-MM-DD)'),  sg.Input(size=(12,1), key='ToDate', do_not_clear=True)],
            [sg.Text('SID, Doc Num, or Store Code'), sg.Multiline(default_text='Enter Comma Separated List', disabled=True, key='list', do_not_clear=True)],
            [sg.Button(button_text='Resend Data')]
            ]

else:
    layout = [ [sg.Menu(menu_layout)],
            [sg.Text('Database'), sg.Radio('Oracle', 'RADIO1', key='oracle', disabled=False, enable_events=True), sg.Radio('MySQL', 'RADIO1', key='mysql', disabled=False, default=True, enable_events=True)],
            [sg.Text('Server Hostname'), sg.Input(size=(50,1), key='server_name', do_not_clear=True, default_text='localhost')], 
            [sg.Text('Resource'), sg.InputCombo(['Document', 'Inventory', 'Customer', 'Vendor', 'Receiving', 'Transferslip', 'Zoutcontrol', 'Drawerevent'],enable_events=True, readonly=True, key='resource')],
            [sg.Text('Filter By'), sg.Radio('Date Range', 'RADIO2', default=True, key='date', enable_events=True) ,sg.Radio('Date Range + Store Code', 'RADIO2', default=False, key='date_store', enable_events=True), sg.Radio('SID', 'RADIO2', key='sid', enable_events=True), sg.Radio('Doc Number', 'RADIO2', key='docnum', enable_events=True)],
            [sg.Text('From Date (YYYY-MM-DD)'), sg.Input(size=(12,1), key='FromDate', do_not_clear=True), sg.Text('To Date (YYYY-MM-DD)'),  sg.Input(size=(12,1), key='ToDate', do_not_clear=True)],
            [sg.Text('SID, Doc Num, or Store Code'), sg.Multiline(default_text='Enter Comma Separated List', disabled=True, key='list', do_not_clear=True)],
            [sg.Button(button_text='Resend Data', disabled=False)]
            ]
    #sg.PopupError('No Prism Database Found.')
        

# create the window
#window = sg.Window('Prism Resend Data').Layout(layout)
window = sg.Window('Prism Resend Data', layout, use_default_focus=False).Finalize()
window.SetIcon(resource_path('prism.ico'))

# read the window

while True:
    print = sg.EasyPrint
    button, values = window.Read()
    
    if button is None:
        break

    if button == 'About':
        sg.Popup(about_text)

    resource_type = values['resource']
    if resource_type != 'Document':
        window.FindElement('docnum').Update(disabled=True)
        window.FindElement('date_store').Update(disabled=True)
    else:
        window.FindElement('docnum').Update(disabled=False)
        window.FindElement('date_store').Update(disabled=False)

    date_filter = values['date']
    date_store_filter = values['date_store']
    if date_filter == True:
        window.FindElement('list').Update(disabled=True)
        window.FindElement('FromDate').Update(disabled=False)
        window.FindElement('ToDate').Update(disabled=False)
    elif date_store_filter == True:
        window.FindElement('list').Update(disabled=False)
        window.FindElement('FromDate').Update(disabled=False)
        window.FindElement('ToDate').Update(disabled=False)
    else:
        window.FindElement('list').Update(disabled=False)
        window.FindElement('FromDate').Update(disabled=True)
        window.FindElement('ToDate').Update(disabled=True)

    db_oracle = values['oracle']
    db_mysql = values['mysql']
    if db_oracle == True:
        window.FindElement('server_name').Update('localhost')
        window.FindElement('server_name').Update(disabled=True)
    if db_mysql == True:
        window.FindElement('server_name').Update(disabled=False)

    if button == 'Resend Data':
        db_oracle = values['oracle']
        resource_type = values['resource']
        filter_date = values['date']
        date_store_filter = values['date_store']
        filter_sid = values['sid']
        filter_docnum = values['docnum']
        server_name = values['server_name']
        if db_oracle == True:
            if filter_date == True:
                from_date = values['FromDate']
                to_date = values['ToDate']
                resend_oracle(resource_type, 'date', from_date, to_date)
            if date_store_filter == True:
                from_date = values['FromDate']
                to_date = values['ToDate']
                store_list = values['list']
                resend_oracle(resource_type, 'date_store', from_date, to_date, store_list=store_list)
            if filter_sid == True:
                sid_list = values['list']
                resend_oracle(resource_type, 'sid','2018-01-01','2018-01-01', sid_list)
            if filter_docnum == True:
                docnum_list = values['list']
                resend_oracle(resource_type, 'docnum', '2018-01-01','2018-01-01', docnum_list=docnum_list)
        if db_oracle == False:
            if filter_date == True:
                from_date = values['FromDate']
                to_date = values['ToDate']
                resend_mysql(resource_type, 'date', from_date, to_date, server_name=server_name)
            if date_store_filter == True:
                from_date = values['FromDate']
                to_date = values['ToDate']
                store_list = values['list']
                resend_mysql(resource_type, 'date_store', from_date, to_date, store_list=store_list, server_name=server_name)
            if filter_sid == True:
                sid_list = values['list']
                resend_mysql(resource_type, 'sid','2018-01-01','2018-01-01', sid_list, server_name=server_name)
            if filter_docnum == True:
                docnum_list = values['list']
                resend_mysql(resource_type, 'docnum', '2018-01-01','2018-01-01', docnum_list=docnum_list, server_name=server_name)
        sg.Popup('Attempt to resend data complete.')