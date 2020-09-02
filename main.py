#  coding: utf-8

import argparse
import control as c
import sys
import consts
import logdb
import sundry as s

class MyArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None):
        # logger = consts.glo_log()
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            msg = ('unrecognized arguments: %s')
            # logger.write_to_log('INFO','error','exit','args error',(msg % ' '.join(argv)))
            self.error(msg % ' '.join(argv))
        return args

    def print_usage(self, file=None):
        logger = consts.glo_log()
        cmd = ' '.join(sys.argv[1:])
        logger.write_to_log('F','DATA', 'INFO', 'cmd_input', '', {'valid':'0','cmd':cmd})
        logger.write_to_log('T', 'INFO', 'INFO', 'finish','', 'print usage')
        if file is None:
            file = sys.stdout
        self._print_message(self.format_usage(), file)

    def print_help(self, file=None):
        logger = consts.glo_log()
        logger.write_to_log('T', 'INFO', 'INFO', 'finish','', 'print help')
        if file is None:
            file = sys.stdout
        self._print_message(self.format_help(), file)

    def _print_message(self, message, file=None):
        if message:
            if file is None:
                file = sys.stderr
            file.write(message)


class HydraArgParse():
    '''
    Hydra project
    parse argument for auto max lun test program
    '''
    def __init__(self):
        # -m:可能在某个地方我们要打印出来这个ID,哦,collect debug log时候就需要这个.但是这个id是什么时候更新的??理一下
        self.ctrl = c.HydraControl()
        self.argparse_init()


    def argparse_init(self):
        self.parser = MyArgumentParser(prog='Hydra',
                                              description='Auto test max supported LUNs/Hosts/Replicas on VersaRAID-SDS')
        sub_parser = self.parser.add_subparsers(dest='l1')
        self.parser_version = sub_parser.add_parser(
            'version',
            help='Output current hydra version'
        )

        #replay or re
        self.parser_replay = sub_parser.add_parser(
            'rpl',
            #aliases=['replay'],
            formatter_class=argparse.RawTextHelpFormatter,
            help='Replay the Hydra program'
        )
        self.parser_replay.add_argument(
            '-t',
            '--transactionid',
            dest='tid',
            metavar='',
            help='The transaction id for replay'
        )
        self.parser_replay.add_argument(
            '-d',
            '--date',
            dest='date',
            metavar='',
            nargs=2,
            help='The time period for replay'
        )
        self.parser_replay.add_argument(
            '-a',
            '--all',
            dest='all',
            action="store_true",
            help='Replay all'
        )
        #lun or maxlun
        self.parser_maxlun = sub_parser.add_parser(
            'lun',
            #aliases=['maxlun'],
            help='Do the max supported LUNs test'
        )
        self.parser_maxlun.add_argument(
            '-id',
            required=True,
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        self.parser_maxlun.add_argument(
            '-s',
            required=True,
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming"
        )


        #iqn
        self.parser_iqn = sub_parser.add_parser(
            'iqn',
            help = 'Do the max supported Hosts test with one LUN or N LUNs'
        )
        parser_iqn_sub = self.parser_iqn.add_subparsers(dest='l2')
        #iqn otm
        self.parser_iqn_o2n = parser_iqn_sub.add_parser(
            'o2n',
            help = 'Do the max supported Hosts test with one LUN'
        )
        #iqn mtm
        self.parser_iqn_n2n = parser_iqn_sub.add_parser(
            'n2n',
            help='Do the max supported Hosts test with N LUNs'
        )
        self.parser_iqn_n2n.add_argument(
            '-id',
            required=True,
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        self.parser_iqn_n2n.add_argument(
            '-c',
            required=True,
            action="store",
            dest="capacity",
            type=int,
            help="The capacity of each Lun, which represents the number of hosts that can be mapped"
        )
        self.parser_iqn_n2n.add_argument(
            '-n',
            action="store",
            type=int,
            dest="random_number",
            help='The number of hosts which is select for test'
        )
        #del or delete
        self.parser_delete_re = sub_parser.add_parser(
            'del',
            #aliases=['delete'],
            help='Confirm to delete LUNs'
        )
        self.parser_delete_re.add_argument(
            '-id',
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        self.parser_delete_re.add_argument(
            '-s',
            action="store",
            dest="uniq_str",
            help="The unique string for this test, affects related naming"
        )
        self.parser_test = sub_parser.add_parser(
            'test',
            help="just for test"
        )


        self.parser_version.set_defaults(func=self.ctrl.run_show_version)
        self.parser_maxlun.set_defaults(func=self.ctrl.run_lun)
        self.parser_iqn.set_defaults(func=self.iqn_print_help)
        self.parser_iqn_o2n.set_defaults(func=self.ctrl.run_iqn_o2n)
        self.parser_iqn_n2n.set_defaults(func=self.ctrl.run_iqn_n2n)
        self.parser_delete_re.set_defaults(func=self.ctrl.delete_resource)
        self.parser_replay.set_defaults(func=self.replay)


    def iqn_print_help(self,*args):
        self.parser_iqn.print_help()


    def replay(self, args):
        consts.set_glo_rpl('yes')
        consts.set_glo_log_switch('no')
        logdb.prepare_db()
        db = consts.glo_db()
        tid_list = self.ctrl.get_tid_list(args, db)
        if not tid_list:
            self.parser_replay.print_help()
            return
        print('* MODE : REPLAY *')
        for tid in tid_list:
            consts.set_glo_tsc_id(tid)
            via_cmd_dict = eval(db.get_cmd_via_tid(tid))
            if via_cmd_dict['valid'] == '1':
                via_args = self.parser.parse_args(via_cmd_dict['cmd'].split(' '))
                via_args.func(via_args)  # 调用argparse绑定函数
            else:
                print(f'事务:{consts.glo_tsc_id()} 不满足replay条件，所执行的命令为：python main.py {via_cmd_dict["cmd"]}')

    def start(self):
        args = self.parser.parse_args()
        cmd = ' '.join(sys.argv[1:])
        logger = consts.glo_log()

        if args.l1:
            logger.write_to_log('T', 'DATA', 'input', 'user_input', '', {'valid':'1','cmd':cmd})
            args.func(args)

        else:
            logger.write_to_log('T', 'DATA', 'input', 'user_input', '', {'valid':'1','cmd':cmd})
            print(self.parser.print_help())


        # if args.l1 == 'lun':
        #     ctrl.log_user_input(args)
        #     ctrl.run_lun(args)
        # elif args.l1 == 'iqn':
        #     if args.l2 == 'o2n':
        #         ctrl.log_user_input(args)
        #         ctrl.run_iqn_o2n()
        #     elif args.l2 == 'n2n':
        #         ctrl.log_user_input(args)
        #         ctrl.run_iqn_n2n(args)
        #     else:
        #         self.parser_iqn.print_help()
        # elif args.l1 == 'del':
        #     ctrl.log_user_input(args)
        #     ctrl.delete_resource(args)
        # elif args.l1 == 'rpl':
        #     ctrl.replay_parser()
        #     if args.tid:
        #         ctrl.run_rpl_tid(args, self.parser)
        #     elif args.date:
        #         ctrl.run_rpl_date(args, self.parser)
        #     elif args.all:
        #         ctrl.run_rpl_all(args, self.parser)
        #     else:
        #         self.parser_replay.print_help()
        # elif args.l1 == 'version':
        #     pass
        #     ctrl.run_show_version()
        # elif args.l1 == 'test':
        #     ctrl.run_test()
        # else:
        #     self.parser.print_help()


if __name__ == '__main__':

    obj = HydraArgParse()
    obj.start()

