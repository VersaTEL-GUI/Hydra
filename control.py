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
    def instantiation_class(self):
        # Initialize connection
        self._netapp = storage.Storage()
        self._drbd = vplx.VplxDrbd()
        self._crm = vplx.VplxCrm()
        self._host = h.HostTest()

    #更新功能类中的属性
    def update_attribute(self, attr):
        if attr == 'id':
            self._netapp.id = consts.glo_id()
            self._drbd.id = consts.glo_id()
            self._crm.id = consts.glo_id()
        if attr == 'str':
            self._netapp.str = consts.glo_str()
            self._drbd.str = consts.glo_str()
            self._crm.str = consts.glo_str()

    def get_tid_list(self, args, db_obj):
        tid_list=[]
        if args.tid:
            tid_list.append(args.tid)
        elif args.date:
            tid_list = db_obj.get_transaction_id_via_date(
                args.date[0], args.date[1])
        elif args.all:
            tid_list = db_obj.get_all_transaction()
        return tid_list

    @s.record_exception
    def run_lun(self, args):
        self.instantiation_class()

        # wirte consts id_range and uiq_str
        id_list = s.change_id_range_to_list(args.id_range)
        consts.set_glo_id_list(id_list)
        consts.set_glo_str(args.uniq_str)

        self.update_attribute('str')
        iqn = s.generate_iqn('0')
        consts.append_glo_iqn_list(iqn)
        format_width = 105 if consts.glo_rpl() == 'yes' else 80
        self._host.modify_host_iqn(iqn)
        for lun_id in consts.glo_id_list():
            consts.set_glo_id(lun_id)
            self.update_attribute('id')
            print(f'**** Start working for ID {lun_id} ****'.center(format_width, '='))
            try:
                self._netapp.create_map()
                time.sleep(0.5)
                self._drbd.cfg()
                self._crm.cfg()
                time.sleep(0.5)
                print(f'{"":-^{format_width}}', '\n')
                time.sleep(0.5)
                self._host.io_test()
            except consts.ReplayExit:
                print(f'{"":-^{format_width}}', '\n')

    @s.record_exception
    def run_iqn_o2n(self):
        self.instantiation_class()
        num = 0
        format_width = 105 if consts.glo_rpl() == 'yes' else 80
        consts.set_glo_str('maxhost')
        self.update_attribute('id')
        self.update_attribute('str')
        print(f'**** Start working for ID {num} ****'.center(format_width, '='))
        try:
            self._netapp.create_map()
            time.sleep(0.5)
            self._drbd.cfg()
            time.sleep(0.5)
            while True:
                s.prt(f'The current IQN number of max supported hosts test is {num}')
                iqn = s.generate_iqn(num)
                consts.append_glo_iqn_list(iqn)
                if num == 0:
                    self._crm.cfg()
                elif num > 0:
                    self._drbd.status_verify(f'res_{consts.glo_str()}_{consts.glo_id()}')
                    self._crm.modify_initiator_and_verify()
                time.sleep(0.5)
                print(f'{"":-^{format_width}}', '\n')
                self._host.modify_host_iqn(iqn)
                self._host.io_test()
                num += 1
        except consts.ReplayExit:
            print(f'{"":-^{format_width}}', '\n')

    @s.record_exception
    def run_iqn_n2n(self, args):
        self.instantiation_class()

        # wirte consts id_range and uiq_str
        id_list = s.change_id_range_to_list(args.id_range)
        consts.set_glo_id_list(id_list)
        consts.set_glo_str('maxhost')

        random_number = args.random_number if args.random_number else 3

        self.update_attribute('str')

        format_width = 105 if consts.glo_rpl() == 'yes' else 80

        for lun_id in id_list:
            consts.set_glo_iqn_list([])
            consts.set_glo_id(lun_id)
            self.update_attribute('id')
            s.generate_iqn_list(args.capacity)
            print(f'**** Start working for ID {lun_id} ****'.center(format_width, '='))
            try:
                self._netapp.create_map()
                time.sleep(0.5)
                self._drbd.cfg()
                time.sleep(0.5)
                self._crm.cfg()
                time.sleep(0.5)
                for iqn in s.host_random_iqn(random_number):
                    print(f'{"":-^{format_width}}', '\n')
                    self._host.modify_host_iqn(iqn)
                    self._host.io_test()
            except consts.ReplayExit:
                print(f'{"":-^{format_width}}', '\n')

    def delete_resource(self, args):
        '''
        User determines whether to delete and execute delete method
        '''
        # wirte consts id_range and uiq_str
        self.instantiation_class()
        if args.id_range:
            id_list = s.change_id_range_to_list(args.id_range)
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
            answer = input('\n\nDo you want to delete these resource? (yes/y/no/n):')
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

    def run_show_version(self,*args):
        print(f'Hydra {consts.VERSION}')

    def run_test(self):
        debug_log.collect_debug_log()



