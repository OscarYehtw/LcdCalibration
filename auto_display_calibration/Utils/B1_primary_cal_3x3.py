
import numpy as np
from numpy.linalg import inv
import pandas as pd
#from colour.utilities import dot_vector
import numpy as np
import sys
import os
from time import sleep
from datetime import date
import colour
import re
import subprocess
import threading
from math import log


## Helper function
def xyY2XYZ_func( xyz_list ):
    X=xyz_list[2]/xyz_list[1]*xyz_list[0]
    Z=xyz_list[2]/xyz_list[1]*(1-xyz_list[0]-xyz_list[1])

    xyz_list[0]=X
    xyz_list[1]=xyz_list[2]
    xyz_list[2]=Z

    return xyz_list

def LM_mul(test_color, Mf, max_RGB_dc):
    RGB_in = np.array( [test_color] ).reshape((3,1))
    RGBp = np.matmul(Mf, RGB_in)
    RGBp[RGBp<0]=0

    RGBp_dc = np.round((RGBp**(1/2.2))/max_RGB_dc*255)
    RGBp_dc[RGBp_dc>255]=255

    temp = RGBp_dc.squeeze().tolist()
    RGBp_hex = [hex(int(x)) for x in temp]

    return RGBp_dc, RGBp_hex

def LM_3x3(device_dict , target_dict):
    # B1
    rxyY1 = device_dict['r']
    gxyY1 = device_dict['g']
    bxyY1 = device_dict['b']
    wxyY1 = device_dict['w']

    # Target
    xyzr = target_dict['r']
    xyzg = target_dict['g']
    xyzb = target_dict['b']
    xyzw = target_dict['w']
    xyYw = [xyzw[0], xyzw[1], wxyY1[2]]

    gamma = 2.2

    a = np.array( [[xyzr[0]/xyzr[1], xyzg[0]/xyzg[1], xyzb[0]/xyzb[1]], [1.0, 1.0, 1.0], [xyzr[2]/xyzr[1], xyzg[2]/xyzg[1], xyzb[2]/xyzb[1]]] )
    XYZw = np.array( [xyzw[0]/xyzw[1]*xyYw[2], xyYw[2], xyzw[2]/xyzw[1]*xyYw[2]] ).reshape((3, 1))

    Yrgb = np.matmul(inv(a), XYZw)
    Yrgb.reshape((3, 1))

    print("rxyY1: ")
    print(rxyY1, "\n")
    print("gxyY1: ")
    print(gxyY1, "\n")
    print("bxyY1: ")
    print(bxyY1, "\n")
    print("wxyY1: ")
    print(wxyY1, "\n")

    print("xyzr: ")
    print(xyzr, "\n")
    print("xyzg: ")
    print(xyzg, "\n")
    print("xyzb: ")
    print(xyzb, "\n")
    print("xyzw: ")
    print(xyzw, "\n")
    print("xyYw: ")
    print(xyYw, "\n")

    print("a: ")
    print(a, "\n")
    print("XYZw: ")
    print(XYZw, "\n")
    print("Yrgb: ")
    print(Yrgb, "\n")


    R =  np.array( [ [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 0.0, 1.0] ] )
    T =  np.array( [ [XYZw[0][0], Yrgb[0][0]*xyzr[0]/xyzr[1], Yrgb[1][0]*xyzg[0]/xyzg[1], Yrgb[2][0]*xyzb[0]/xyzb[1]], [XYZw[1][0], Yrgb[0][0],Yrgb[1][0],Yrgb[2][0]], [XYZw[2][0], Yrgb[0][0]*xyzr[2]/xyzr[1], Yrgb[1][0] * xyzg[2]/xyzg[1], Yrgb[2][0]*xyzb[2]/xyzb[1]] ] )
    TT = inv(np.dot(T, T.transpose()))
    C = np.dot(R, np.dot(T.transpose(), TT))
    C_inv = inv(C)

### Matrix test : Linear domain

    # Test
    RGB_test_in = np.array( [[1,0,0]] ).reshape((3,1))
    Test = np.matmul(C_inv, RGB_test_in)
    print("Test vector R: \n ")
    Test_r_xyz = Test/sum(Test)
    print("Post Cal result in linear domain: ")
    print(Test_r_xyz, "\n")

    RGB_test_in = np.array( [[0,1,0]] ).reshape((3,1))
    Test = np.matmul(C_inv, RGB_test_in)
    print("Test vector G:  \n ")
    Test_g_xyz = Test/sum(Test)
    print("Post Cal result in linear domain: ")
    print(Test_g_xyz, "\n")

    RGB_test_in = np.array( [[0,0,1]] ).reshape((3,1))
    Test = np.matmul(C_inv, RGB_test_in)
    print("Test vector B:  \n ")
    Test_b_xyz = Test/sum(Test)
    print("Post Cal result in linear domain: ")
    print(Test_b_xyz, "\n")

    RGB_test_in = np.array( [[1,1,1]] ).reshape((3,1))
    Test = np.matmul(C_inv, RGB_test_in)
    print("Test vector W:  \n ")
    Test_w_xyz = Test/sum(Test)
    print("Post Cal result in linear domain: ")
    print(Test_w_xyz, "\n")

    print("Target : ")
    print(xyzr)
    print(xyzg)
    print(xyzb)
    print(xyzw)


####

    M = C_inv
    MI = C

    rXYZ = xyY2XYZ_func(rxyY1)
    gXYZ = xyY2XYZ_func(gxyY1)
    bXYZ = xyY2XYZ_func(bxyY1)

    Md = np.array( [rXYZ, gXYZ, bXYZ] )
    Md = Md.transpose()
    Mf =  np.matmul(inv(Md), M)

    # Find maximum value for normalization
    RGB_in = np.array( [[1,1,1]] ).reshape((3,1))
    RGBp = np.matmul(Mf, RGB_in)
    max_RGB = np.max(RGBp)
    max_RGB_dc = max_RGB **(1/2.2)

    print("max_RGB_dc",max_RGB_dc)


    ## RGB to RGB mapping
    test_color =[1,0,0]
    test_color2 = [number ** 2 for number in test_color]
    r_dc, r_hex = LM_mul(test_color2, Mf, max_RGB_dc)

    test_color =[0,1,0]
    test_color2 = [number ** 2 for number in test_color]
    g_dc, g_hex = LM_mul(test_color2, Mf, max_RGB_dc)

    test_color =[0,0,1]
    test_color2 = [number ** 2 for number in test_color]
    b_dc, b_hex = LM_mul(test_color2, Mf, max_RGB_dc)

    test_color =[1,1,1]
    test_color2 = [number ** 2 for number in test_color]
    w_dc, w_hex = LM_mul(test_color2, Mf, max_RGB_dc)

    test_color =[1.0, 0.4314, 0.251]
    test_color2 = [number ** 2 for number in test_color]
    nr_dc, nr_hex = LM_mul(test_color2, Mf, max_RGB_dc)

    test_color =[0.29, 0.688, 0.9333]
    test_color2 = [number ** 2 for number in test_color]
    nb_dc, nb_hex = LM_mul(test_color2, Mf, max_RGB_dc)

    dict_post_cal_val_pattern = {'r_dc':r_dc,
                            'g_dc':g_dc,
                            'b_dc':b_dc,
                            'w_dc':w_dc,
                            'nr_dc':nr_dc,
                            'nb_dc':nb_dc,
                            'r_hex':r_hex,
                            'g_hex':g_hex,
                            'b_hex':b_hex,
                            'w_hex':w_hex,
                            'nr_hex':nr_hex,
                            'nb_hex':nb_hex
                            }

    return dict_post_cal_val_pattern, M, Md, Mf, max_RGB_dc
