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
        sub_parser = self.parser.add_subparsers(dest='subcommand')
        parser_replay = sub_parser.add_parser(
            're',
            aliases=['replay'],
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
        parser_maxlun = sub_parser.add_parser(
            'mxl',
            aliases=['maxlun'],
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
        parser_maxhost_lun = sub_parser.add_parser(
            'mh',
            help = 'Do the max supported Hosts test with one LUN'
        )
        parser_maxhost_luns = sub_parser.add_parser(
            'mxh',
            help='Do the max supported Hosts test with N LUNs'
        )
        parser_maxhost_luns.add_argument(
            '-id',
            required=True,
            action="store",
            default='',
            dest="id_range",
            nargs='+',
            help='ID or ID range'
        )
        parser_maxhost_luns.add_argument(
            '-c',
            required=True,
            action="store",
            dest="capacity",
            type=int,
            help="The capacity of each Lun, which represents the number of hosts that can be mapped"
        )
        parser_maxhost_luns.add_argument(
            '-n',
            action="store",
            type=int,
            dest="random_number",
            help='The number of hosts which is select for test'
        )
        parser_delete_re = sub_parser.add_parser(
            'del',
            aliases=['delete'],
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
        control = c.HydraControl()
        args = self.parser.parse_args()
        print('args',args)
        control.log_user_input(args)

        if args.subcommand:
            pass

        try:
            if args.id_range:
                id_list = s.change_id_range_to_list(args.id_range)
                consts.set_glo_id_list(id_list)
        except:
            pass
        try:
            if args.uniq_str:
                consts.set_glo_str(args.uniq_str)
        except:
            pass

        if args.subcommand in ['mxl','maxlun']:
            id_list = consts.glo_id_list()
            for id_ in id_list:
                control.dict_id_str.update({id_: args.uniq_str})
            print('self.cont.dict_id_str', control.dict_id_str)
            #control.run_maxlun(control.dict_id_str)
        elif args.subcommand == 'mh':
            control.run_maxhost()
        elif args.subcommand == 'mxh':
            control.capacity = args.capacity
            if args.random_number:
                control.random_num = args.random_number
            #control.run_mxh()
        elif args.subcommand in ['del', 'delete']:
            control.delete_resource()
        elif args.subcommand in ['re', 'replay']:
            consts.set_glo_rpl('yes')
            consts.set_glo_log_switch('no')
            logdb.prepare_db()
            control.prepare_replay(args)

            #mxl
            control.run_maxlun(control.dict_id_str)


        else:
            self.parser.print_help()
        # args.func(args)

        # if args.test:
        #     debug_log.collect_debug_log()
        #     return


if __name__ == '__main__':
    obj = HydraArgParse()
    obj.start()

