#coding:utf-8

import consts
import time
import vplx
import storage
import host_initiator as host
import sundry as s
import log
import logdb
import traceback

import debug_log

class HydraControl():
    def __init__(self):
        consts.glo_init()
        self.transaction_id = s.get_transaction_id()
        consts.set_glo_tsc_id(f'{self.transaction_id}')
        #log
        self.logger = log.Log(self.transaction_id)
        consts.set_glo_log(self.logger)

    #初始化功能类
    def initialize_class(self):
        # Initialize connection
        self._netapp = storage.Storage()
        self._drbd = vplx.VplxDrbd()
        self._crm = vplx.VplxCrm()
        self._host = host.HostTest()

    #更新功能类中的属性
    def update_attribute(self, *args):
        if 'id' in args:
            self._netapp.id = consts.glo_id()
            self._drbd.id = consts.glo_id()
            self._crm.id = consts.glo_id()
        if 'str' in args:
            self._netapp.str = consts.glo_str()
            self._drbd.str = consts.glo_str()
            self._crm.str = consts.glo_str()

    @s.record_exception
    def lun(self, args):
        self.initialize_class()

        # wirte consts id_range and uiq_str
        id_list = s.id_str_to_list(args.id_range)
        consts.set_glo_str(args.uniq_str)

        self.update_attribute('str')
        iqn = s.generate_iqn('0')
        consts.append_glo_iqn_list(iqn)

        format_width = 105 if consts.glo_rpl() == 'yes' else 80

        host.change_iqn(iqn)
        for lun_id in id_list:
            consts.set_glo_id(lun_id)
            self.update_attribute('id')
            print(f'**** Start working for ID {lun_id} ****'.center(format_width, '='))
            try:
                self._netapp.create_map()
                self._drbd.cfg()
                self._crm.cfg()
                self._host.io_test()
                print(f'{"":-^{format_width}}', '\n')
            except consts.ReplayExit:
                print(f'{"":-^{format_width}}', '\n')

    @s.record_exception
    def iqn_o2n(self, args):
        self.initialize_class()
        num = 0
        format_width = 105 if consts.glo_rpl() == 'yes' else 80
        consts.set_glo_str('maxhost')
        self.update_attribute('id', 'str')
        try:
            self._netapp.create_map()
            self._drbd.cfg()
            while True:
                s.prt(f'The current IQN number of max supported hosts test is {num}')
                iqn = s.generate_iqn(num)
                consts.append_glo_iqn_list(iqn)
                if num == 0:
                    self._crm.cfg()
                elif num > 0:
                    self._drbd.status_verify(f'res_{consts.glo_str()}_{consts.glo_id()}')
                    self._crm.modify_initiator_and_verify()
                print(f'{"":-^{format_width}}', '\n')
                host.change_iqn(iqn)
                self._host.io_test()
                num += 1
        except consts.ReplayExit:
            print(f'{"":-^{format_width}}', '\n')

    @s.record_exception
    def iqn_n2n(self, args):
        self.initialize_class()

        # wirte consts id_range and uiq_str
        id_list = s.id_str_to_list(args.id_range)
        consts.set_glo_id_list(id_list)
        consts.set_glo_str('maxhost')

        random_number = args.random_number \
            if args.random_number and args.capacity>args.random_number \
            else args.capacity

        self.update_attribute('str')

        format_width = 105 if consts.glo_rpl() == 'yes' else 80

        for lun_id in id_list:
            consts.set_glo_id(lun_id)
            self.update_attribute('id')
            s.generate_iqn_list(args.capacity)

            print(f'**** Start working for ID {lun_id} ****'.center(format_width, '='))
            try:
                self._netapp.create_map()
                self._drbd.cfg()
                self._crm.cfg()
                for iqn in s.pick_iqns_random(random_number):
                    host.change_iqn(iqn)
                    self._host.io_test()
                    print(f'{"":-^{format_width}}', '\n')
            except consts.ReplayExit:
                print(f'{"":-^{format_width}}', '\n')

    def delete_resource(self, args):
        '''
        User determines whether to delete and execute delete method
        '''
        # wirte consts id_range and uiq_str
        self.initialize_class()
        if args.id_range:
            id_list = s.id_str_to_list(args.id_range)
            consts.set_glo_id_list(id_list)
        if args.uniq_str:
            consts.set_glo_str(args.uniq_str)

        self.update_attribute('id')
        self.update_attribute('str')
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

            answer = s.get_answer('\n\nDo you want to delete these resource? (yes/y/no/n):')

            if answer.strip() == 'yes' or answer.strip() == 'y':
                self._crm.del_crms(crm_to_del_list)
                self._drbd.del_drbds(drbd_to_del_list)
                self._netapp.del_luns(lun_to_del_list)
                s.pwl('Start to remove all deleted disk device on netapp vplx host', 0)
                # remove all deleted disk device on vplx and host
                self._crm.vplx_rescan_r()
                self._host.host_rescan_r()
                print(f'{"":-^80}', '\n')
            else:
                s.pwe('User canceled deleting proccess ...', 2, 2)
        else:
            print()
            s.pwe('No qualified resources to be delete.', 2, 2)

    def replay(self, args, replay_obj, parser_obj):
        consts.set_glo_rpl('yes')
        consts.set_glo_log_switch('no')
        logdb.prepare_db()
        db = consts.glo_db()
        tid_list = s.get_tid_list(args, db)
        if not tid_list:
            replay_obj.print_help()
            return
        print('* MODE : REPLAY *')
        for tid in tid_list:
            consts.set_glo_tsc_id(tid)
            via_cmd_dict = eval(db.get_cmd_via_tid(tid))
            if via_cmd_dict['valid'] == '1':
                via_args = parser_obj.parse_args(via_cmd_dict['cmd'].split())
                try:
                    via_args.func(via_args)  # 调用argparse绑定函数
                except consts.ReplayExit:
                    print('该事务replay结束')
                except Exception:
                    print(str(traceback.format_exc()))
            else:
                print(f'事务:{tid} 不满足replay条件，所执行的命令为：python main.py {via_cmd_dict["cmd"]}')

    def show_version(self,*args):
        print(f'Hydra {consts.VERSION}')

    def run_test(self, *args):
        debug_log.collect_debug_log()
