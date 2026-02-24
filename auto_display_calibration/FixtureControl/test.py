

def test_1():
    print(111)
    return 11

eval('test_%s()'%(1))
# import os
# log_path = os.path.join(os.path.expanduser('~'), 'Test_Log/1111111111')
# if os.path.exists(log_path) == False:
#     os.makedirs(log_path)
