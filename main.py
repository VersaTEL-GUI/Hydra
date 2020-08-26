#  coding: utf-8

import consts
import argparse
import sundry as s
import logdb
import debug_log
import control as c


class HydraArgParse():
    '''
    Hydra project
    parse argument for auto max lun test program
    '''
    def __init__(self):
        # -m:可能在某个地方我们要打印出来这个ID,哦,collect debug log时候就需要这个.但是这个id是什么时候更新的??理一下
        self.argparse_init()

    def argparse_init(self):
        self.parser = argparse.ArgumentParser(prog='Hydra',
                                              description='Auto test max supported LUNs/Hosts/Replicas on VersaRAID-SDS')
        # self.parser.add_argument(
        #     '-t',
        #     action="store_true",
        #     dest="test",
        #     help="just for test"
        # )
        self.parser.add_argument(
            '-v',
            '--version',
            dest='version',
            action='store',
            help='version mode'
        )
        sub_parser = self.parser.add_subparsers(dest='type1')
        #replay  or re
        parser_replay = sub_parser.add_parser(
            're',
            #aliases=['replay'],
            formatter_class=argparse.RawTextHelpFormatter,
            help='Replay the Hydra program'
        )
        parser_replay.add_argument(
            '-t',
            '--transactionid',
            dest='tid',
            metavar='',
            help='The transaction id for replay'
        )
        parser_replay.add_argument(
            '-d',
            '--date',
            dest='date',
            metavar='',
            nargs=2,
            help='The time period for replay'
        )
        self.parser_replay = parser_replay
        #lun or maxlun
        parser_maxlun = sub_parser.add_parser(
            'lun',
            #aliases=['maxlun'],
            help='Do the max supported LUNs test'
        )
        parser_maxlun.add_argument(
            '-id',
            required=True,
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        parser_maxlun.add_argument(
            '-s',
            required=True,
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming"
        )
        #iqn
        parser_iqn = sub_parser.add_parser(
            'iqn',
            help = 'Do the max supported Hosts test with one LUN or N LUNs'
        )
        parser_iqn_sub = parser_iqn.add_subparsers(dest='type2')
        #iqn otm
        parser_iqn_otm = parser_iqn_sub.add_parser(
            'otm',
            help = 'Do the max supported Hosts test with one LUN'
        )
        #iqn mtm
        parser_iqn_mtm = parser_iqn_sub.add_parser(
            'mtm',
            help='Do the max supported Hosts test with N LUNs'
        )
        parser_iqn_mtm.add_argument(
            '-id',
            required=True,
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        parser_iqn_mtm.add_argument(
            '-c',
            required=True,
            action="store",
            dest="capacity",
            type=int,
            help="The capacity of each Lun, which represents the number of hosts that can be mapped"
        )
        parser_iqn_mtm.add_argument(
            '-n',
            action="store",
            type=int,
            dest="random_number",
            help='The number of hosts which is select for test'
        )
        #del or delete
        parser_delete_re = sub_parser.add_parser(
            'del',
            #aliases=['delete'],
            help='Confirm to delete LUNs'
        )
        parser_delete_re.add_argument(
            '-id',
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        parser_delete_re.add_argument(
            '-s',
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming"
        )


    def start(self):
        ctrl = c.HydraControl()
        args = self.parser.parse_args()

        if args.type1 == 'lun':
            ctrl.log_user_input(args)
            #ctrl.run_maxlun(args)

        elif args.type1 == 'iqn':
            if args.type2 == 'otm':
                ctrl.log_user_input(args)
                #ctrl.run_iqn_otm()

            elif args.type2 == 'mtm':
                ctrl.log_user_input(args)
                ctrl.capacity = args.capacity
                if args.random_number:
                    ctrl.random_num = args.random_number
                #ctrl.run_mxh()

        elif args.type1 == 'del':
            pass
            #ctrl.delete_resource()

        elif args.type1 == 're':
            consts.set_glo_rpl('yes')
            consts.set_glo_log_switch('no')
            logdb.prepare_db()
            ctrl.prepare_replay(args)
            ctrl.run_maxlun()

        else:
            self.parser.print_help()

        # if args.test:
        #     debug_log.collect_debug_log()
        #     return


if __name__ == '__main__':
    obj = HydraArgParse()
    obj.start()

