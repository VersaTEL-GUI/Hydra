#coding:utf-8

import consts
import time
import vplx
import storage
import host_initiator as h
import sundry as s
import log
import sys
import logdb

class HydraControl():
    def __init__(self):
        consts._init()

        self.transaction_id = s.get_transaction_id()
        consts.set_glo_tsc_id(f'{self.transaction_id}s')
        #log

        self.logger = log.Log(self.transaction_id)
        consts.set_glo_log(self.logger)

    def instantiation_class(self):
        # Initialize connection
        self._netapp = storage.Storage()
        self._drbd = vplx.VplxDrbd()
        self._crm = vplx.VplxCrm()
        self._host = h.HostTest()

    def delete_resource(self, args):
        '''
        User determines whether to delete and execute delete method
        '''
        # wirte consts id_range and uiq_str
        id_list = s.change_id_range_to_list(args.id_range)
        consts.set_glo_id_list(id_list)
        consts.set_glo_str(args.uniq_str)

        crm_to_del_list = s.get_to_del_list(self._crm.get_all_cfgd_res())
        drbd_to_del_list = s.get_to_del_list(self._drbd.get_all_cfgd_drbd())
        lun_to_del_list = s.get_to_del_list(self._netapp.get_all_cfgd_lun())
        if crm_to_del_list:
            s.prt_res_to_del('\nCRM resource', crm_to_del_list)
        if drbd_to_del_list:
            s.prt_res_to_del('\nDRBD resource', drbd_to_del_list)
        if lun_to_del_list:
            s.prt_res_to_del('\nStorage LUN', lun_to_del_list)
        if crm_to_del_list or drbd_to_del_list or lun_to_del_list:
            answer = input('\n\nDo you want to delete these resource? (yes/y/no/n):')
            if answer.strip() == 'yes' or answer.strip() == 'y':
                self._crm.del_crms(crm_to_del_list)
                self._drbd.del_drbds(drbd_to_del_list)
                self._netapp.del_luns(lun_to_del_list)
                s.pwl('Start to remove all deleted disk device on netapp\vplx\host', 0)
                # remove all deleted disk device on vplx and host
                self._crm.vplx_rescan_r()
                self._host.host_rescan_r()
                print(f'{"":-^80}', '\n')
            else:
                s.pwe('User canceled deleting proccess ...', 2, 2)
        else:
            print()
            s.pwe('No qualified resources to be delete.', 2, 2)

    @s.record_exception
    def run_iqn_mtm(self, args):
        self.instantiation_class()

        # wirte consts id_range and uiq_str
        id_list = s.change_id_range_to_list(args.id_range)
        consts.set_glo_id_list(id_list)
        consts.set_glo_str('maxhost')

        format_width = 105 if consts.glo_rpl() == 'yes' else 80

        for lun_id in id_list:
            consts.set_glo_iqn_list([])

            consts.set_glo_id(lun_id)
            s.generate_iqn_list(args.capacity)
            print(f'**** Start working for ID {lun_id} ****'.center(format_width, '='))
            try:
                self._netapp.lun_create_map()
                time.sleep(0.5)
                self._drbd.drbd_cfg()
                time.sleep(0.5)
                self._crm.crm_cfg()
                time.sleep(0.5)
                for iqn in s.host_random_iqn(args.random_number):
                    self._host.modify_host_iqn(iqn)
                    self._host.io_test()
            except consts.ReplayExit:
                print(f'{"":-^{format_width}}', '\n')

    @s.record_exception
    def run_lun(self, args):
        self.instantiation_class()

        # wirte consts id_range and uiq_str
        id_list = s.change_id_range_to_list(args.id_range)
        consts.set_glo_id_list(id_list)
        consts.set_glo_str(args.uniq_str)

        iqn = s.generate_iqn('0')
        consts.append_glo_iqn_list(iqn)

        format_width = 105 if consts.glo_rpl() == 'yes' else 80
        self._host.modify_host_iqn(iqn)
        for lun_id in consts.glo_id_list():
            consts.set_glo_id(lun_id)
            print(f'**** Start working for ID {lun_id} ****'.center(format_width, '='))
            try:
                self._netapp.lun_create_map()
                time.sleep(1.5)
                self._drbd.drbd_cfg()
                self._crm.crm_cfg()
                time.sleep(1.5)
                print(f'{"":-^{format_width}}', '\n')
                time.sleep(1.5)
                self._host.io_test()
            except consts.ReplayExit:
                print(f'{"":-^{format_width}}', '\n')

    @s.record_exception
    def run_iqn_otm(self):
        num = 0
        format_width = 105 if consts.glo_rpl() == 'yes' else 80
        consts.set_glo_str('maxhost')
        print(f'**** Start working for ID {num} ****'.center(format_width, '='))
        try:
            self._netapp.lun_create_map()
            time.sleep(0.5)
            self._drbd.drbd_cfg()
            time.sleep(0.5)
            while True:
                s.prt(f'The current IQN number of max supported hosts test is {num}')
                iqn = s.generate_iqn(num)
                consts.append_glo_iqn_list(iqn)
                if num == 0:
                    self._crm.crm_cfg()
                elif num > 0:
                    self._drbd.drbd_status_verify()
                    self._crm.modify_initiator_and_verify()
                time.sleep(0.5)
                print(f'{"":-^{format_width}}', '\n')
                self._host.modify_host_iqn(iqn)
                self._host.io_test()
                num += 1
        except consts.ReplayExit:
            print(f'{"":-^{format_width}}', '\n')

    def run_re(self, args):
        consts.set_glo_rpl('yes')
        consts.set_glo_log_switch('no')
        logdb.prepare_db()
        db = consts.glo_db()
        print('* MODE : REPLAY *')

        list_tid = db.get_all_transaction()

        for tid in list_tid:
            args.tid=tid
            self.run_re_tid(args)

        #ctrl.prepare_replay(args)

    def run_re_tid(self, args):
        consts.set_glo_rpl('yes')
        consts.set_glo_log_switch('no')
        logdb.prepare_db()
        db = consts.glo_db()
        print('* MODE : REPLAY *')
        cmd_args = db.get_cmd_via_tid(args.tid)
        if cmd_args.type1 == 'lun':
            self.run_lun(cmd_args)
        elif cmd_args.type1 == 'iqn':
            if cmd_args.type2 == 'otm':
                self.run_iqn_otm(cmd_args)
            elif cmd_args.type2 == 'mtm':
                self.run_iqn_mtm(cmd_args)

    def run_re_date(self, args):
        consts.set_glo_rpl('yes')
        consts.set_glo_log_switch('no')
        logdb.prepare_db()
        db = consts.glo_db()
        print('* MODE : REPLAY *')

        list_tid = db.get_transaction_id_via_date(args.date[0], args.date[1])

        for tid in list_tid:
            args.tid=tid
            self.run_re_tid(args)

    #将命令写入log，此处需要将命令转化为字典
    #原格式：cmd = [main.py mxh -id 1 3 -c 5 -n 2]
    #字典格式：
    # cmd = [{
    #     'type1' : 'mxh',
    #     'type2' : '',
    #     'id_range' : [1, 3],
    #     'capacity' : 5,
    # }]
    def log_user_input(self, args):
        if args.type1 == 're':
            return
        if sys.argv:
            cmd = vars(args)
            if consts.glo_rpl() == 'no':
                self.logger.write_to_log(
                    'T', 'DATA', 'input', 'user_input', '', args)

    def get_valid_transaction(self, list_transaciont):
        db = consts.glo_db()
        lst_tid = list_transaciont[:]
        for tid in lst_tid:
            consts.set_glo_tsc_id(tid)
            string, id = db.get_string_id(tid)
            if string and id:
                self.dict_id_str.update({id: string})
            else:
                self.list_tid.remove(tid)
                cmd = db.get_cmd_via_tid(tid)
                print(f'事务:{tid} 不满足replay条件，所执行的命令为：{cmd}')
        print(f'Transaction to be executed: {" ".join(self.list_tid)}')
        return self.dict_id_str

    #搜集id， str
    def prepare_replay(self, args):
        db = consts.glo_db()
        arg_tid = args.tid
        arg_date = args.date
        print('* MODE : REPLAY *')
        time.sleep(1.5)
        if arg_tid:
            string, id = db.get_string_id(arg_tid)
            if not all([string, id]):
                cmd = db.get_cmd_via_tid(arg_tid)
                print(
                    f'事务:{arg_tid} 不满足replay条件，所执行的命令为：{cmd}')
                return
            consts.set_glo_tsc_id(arg_tid)
            self.dict_id_str.update({id: string})
            print(f'Transaction to be executed: {arg_tid}')
            # self.replay_run(args.transactionid)
        elif arg_date:
            self.list_tid = db.get_transaction_id_via_date(
                arg_date[0], arg_date[1])
            self.get_valid_transaction(self.list_tid)
        elif arg_tid and arg_date:
            print('Please specify only one type of data for replay')
        else:
            # 执行日志全部的事务
            self.list_tid = db.get_all_transaction()
            self.get_valid_transaction(self.list_tid)


