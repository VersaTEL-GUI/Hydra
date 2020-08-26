#coding:utf-8

import consts
import time
import vplx
import storage
import host_initiator as h
import sundry as s
import log
import sys


class HydraControl():
    def __init__(self):
        consts._init()

        self.transaction_id = s.get_transaction_id()
        consts.set_glo_tsc_id(f'{self.transaction_id}s')
        #log
        self.logger = log.Log(self.transaction_id)
        consts.set_glo_log(self.logger)

        self.capacity = None
        self.random_num=3

    def instantiation_class(self):
        # Initialize connection
        self._netapp = storage.Storage()
        self._drbd = vplx.VplxDrbd()
        self._crm = vplx.VplxCrm()
        self._host = h.HostTest()

    def _storage(self):
        '''
        Connect to NetApp Storage, Create LUN and Map to VersaPLX
        '''
        netapp = storage.Storage()
        netapp.lun_create()
        netapp.lun_map()

    def _vplx_drbd(self):
        '''
        Connect to VersaPLX, Config DRDB resource
        '''
        # drbd.discover_new_lun() # 查询新的lun有没有map过来，返回path
        drbd = vplx.VplxDrbd()
        drbd.prepare_config_file()  # 创建配置文件
        drbd.drbd_cfg()  # run
        drbd.drbd_status_verify()  # 验证有没有启动（UptoDate）

    def _vplx_crm(self):
        '''
        Connect to VersaPLX, Config iSCSI Target
        '''
        crm = vplx.VplxCrm()
        crm.crm_cfg()
        crm.crm_status_verify()

    def delete_resource(self):
        '''
        User determines whether to delete and execute delete method
        '''
        crm = vplx.VplxCrm()
        drbd = vplx.VplxDrbd()
        stor = storage.Storage()
        host = host_initiator.HostTest()

        crm_to_del_list = s.get_to_del_list(crm.get_all_cfgd_res())
        drbd_to_del_list = s.get_to_del_list(drbd.get_all_cfgd_drbd())
        lun_to_del_list = s.get_to_del_list(stor.get_all_cfgd_lun())
        if crm_to_del_list:
            s.prt_res_to_del('\nCRM resource', crm_to_del_list)
        if drbd_to_del_list:
            s.prt_res_to_del('\nDRBD resource', drbd_to_del_list)
        if lun_to_del_list:
            s.prt_res_to_del('\nStorage LUN', lun_to_del_list)
        if crm_to_del_list or drbd_to_del_list or lun_to_del_list:
            answer = input('\n\nDo you want to delete these resource? (yes/y/no/n):')
            if answer.strip() == 'yes' or answer.strip() == 'y':
                crm.del_crms(crm_to_del_list)
                drbd.del_drbds(drbd_to_del_list)
                stor.del_luns(lun_to_del_list)
                s.pwl('Start to remove all deleted disk device on vplx and host', 0)
                # remove all deleted disk device on vplx and host
                crm.vplx_rescan_r()
                host.host_rescan_r()
                print(f'{"":-^80}', '\n')
            else:
                s.pwe('User canceled deleting proccess ...', 2, 2)
        else:
            print()
            s.pwe('No qualified resources to be delete.', 2, 2)

    def run_mxh(self):
        self.instantiation_class()

        id_list = consts.glo_id_list()
        consts.set_glo_str('maxhost')

        for id in id_list:
            consts.set_glo_iqn_list([])
            consts.set_glo_id(id)
            s.generate_iqn_list(self.capacity)
            self._storage()
            self._vplx_drbd()
            self._vplx_crm()
            host = host_initiator.HostTest()
            for iqn in s.host_random_iqn(self.random_num):
                host.modify_host_iqn(iqn)
                host.iscsi.login()
                host.start_test()

    @s.record_exception
    def run_maxlun(self, args):
        self.instantiation_class()

        # wirte consts id_range and uiq_str
        id_list = s.change_id_range_to_list(args.id_range)
        consts.set_glo_id_list(id_list)
        consts.set_glo_str(args.uniq_str)

        iqn = s.generate_iqn('0')
        consts.append_glo_iqn_list(iqn)
        rpl = consts.glo_rpl()

        format_width = 105 if rpl == 'yes' else 80

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

    #架构上继续改进
    def run_iqn_otm(self):
        num = 0
        consts.set_glo_str('maxhost')
        self._netapp.lun_create_map()
        self._drbd.drbd_cfg()

        while True:
            s.prt(f'The current IQN number of max supported hosts test is {num}')
            iqn = s.generate_iqn(num)
            consts.append_glo_iqn_list(iqn)

            if num == 0:
                self._crm.crm_cfg()
            elif num > 1:
                self._drbd.drbd_status_verify()
                self._crm.modify_initiator_and_verify()

            self._host.modify_host_iqn(iqn)
            self._host.io_test()
            num += 1

    #将命令写入log，此处需要将命令转化为字典
    #原格式：cmd = [main.py mxh -id 1 3 -c 5 -n 2]
    #字典格式：
    # cmd = [{
    #     'type1' : 'mxh',
    #     'type2' : '',
    #     'id_range' : [1, 3],
    #     'capacity' : 5,
    #
    # }]
    def log_user_input(self, args):
        if args.type1 == 're':
            return
        if sys.argv:
            cmd = vars(args)
            if consts.glo_rpl() == 'no':
                self.logger.write_to_log(
                    'T', 'DATA', 'input', 'user_input', '', cmd)

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


