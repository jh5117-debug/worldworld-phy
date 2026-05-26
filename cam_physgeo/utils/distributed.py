import os
def rank() -> int: return int(os.environ.get('RANK', os.environ.get('LOCAL_RANK','0')))
def is_main_process() -> bool: return rank()==0
