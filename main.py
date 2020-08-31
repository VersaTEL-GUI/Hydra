#  coding: utf-8

import argparse
import control as c
import sys
import consts

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
        logger.write_to_log('F','DATA', 'INFO', 'cmd_input', '', {'valid':'1','cmd':cmd})
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
        self.argparse_init()
        self.start()

    def argparse_init(self):
        self.parser = MyArgumentParser(prog='Hydra',
                                              description='Auto test max supported LUNs/Hosts/Replicas on VersaRAID-SDS')
        sub_parser = self.parser.add_subparsers(dest='l1')
        parser_version = sub_parser.add_parser(
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
            help='The time period for replay'
        )
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
        self.parser_iqn = sub_parser.add_parser(
            'iqn',
            help = 'Do the max supported Hosts test with one LUN or N LUNs'
        )
        parser_iqn_sub = self.parser_iqn.add_subparsers(dest='l2')
        #iqn otm
        parser_iqn_o2n = parser_iqn_sub.add_parser(
            'o2n ',
            help = 'Do the max supported Hosts test with one LUN'
        )
        #iqn mtm
        parser_iqn_n2n = parser_iqn_sub.add_parser(
            'n2n',
            help='Do the max supported Hosts test with N LUNs'
        )
        parser_iqn_n2n.add_argument(
            '-id',
            required=True,
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        parser_iqn_n2n.add_argument(
            '-c',
            required=True,
            action="store",
            dest="capacity",
            type=int,
            help="The capacity of each Lun, which represents the number of hosts that can be mapped"
        )
        parser_iqn_n2n.add_argument(
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
        parser_test = sub_parser.add_parser(
            'test',
            help="just for test"
        )


    def start(self):
        ctrl = c.HydraControl()
        args = self.parser.parse_args()
        if args.l1 == 'lun':
            ctrl.log_user_input(args)
            ctrl.run_lun(args)
        elif args.l1 == 'iqn':
            if args.l2 == 'o2n':
                ctrl.log_user_input(args)
                ctrl.run_iqn_o2n()
            elif args.l2 == 'n2n':
                ctrl.log_user_input(args)
                ctrl.run_iqn_n2n(args)
            else:
                self.parser_iqn.print_usage()
        elif args.l1 == 'del':
            ctrl.log_user_input(args)
            ctrl.delete_resource(args)
        elif args.l1 == 'rpl':
            if args.tid:
                ctrl.run_rpl_tid(args, self.parser)
            elif args.date:
                ctrl.run_rpl_date(args)
            elif args.all:
                ctrl.run_rpl_all(args)
            else:
                self.parser_replay.print_help()
        elif args.l1 == 'version':
            ctrl.run_show_version()
        elif args.l1 == 'test':
            ctrl.run_test()
        else:
            self.parser.print_help()


if __name__ == '__main__':
    obj = HydraArgParse()

