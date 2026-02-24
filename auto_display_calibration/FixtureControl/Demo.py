
from FixtureControl.DisplayInterface import DisplayInterface
displayinterface = DisplayInterface()
# displayinterface.reset()# control reset

# displayinterface.check_DUT_position_status() #check position
# #
# displayinterface.typec_test()#typec
#
# print(displayinterface.move_to(0))# move to 0
# import time
# time.sleep(1)
# print(displayinterface.move_to(30))# move to 30

displayinterface.light_open()# open light
# time.sleep(1)
# displayinterface.light_close()# close light

displayinterface.setbrightness()# set light value (if need)

displayinterface.reset() #reset



