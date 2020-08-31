import argparse, logdb

db = logdb.LogDB()
db.get_logdb()

cmd_args = db.get_cmd_via_tid(1598407662)

cmd=eval(cmd_args)

ns = argparse.Namespace(**cmd)

print(type(cmd))
print(ns)