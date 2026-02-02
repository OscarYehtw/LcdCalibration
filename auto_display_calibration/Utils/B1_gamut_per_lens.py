#-----------------------import my color lib -------------
import sys
if "../.." not in sys.path:
    sys.path.append("..")
from Utils.analysis_module import *
from Utils.color_spec_generator import generate_color_spec
import Utils.primary_cal_3x3 as primary_cal
# -------------------------------------------------------
import numpy as np
from numpy.linalg import inv
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from colour.plotting import plot_chromaticity_diagram_CIE1976UCS
from colour.plotting import plot_chromaticity_diagram_CIE1931



filter_w_gray = [
    {'key':'category', 'value':'gamma', 'op':'=='},
]

filter_r_gray = [
    {'key':'category', 'value':'gray_r', 'op':'=='},
]

filter_g_gray = [
    {'key':'category', 'value':'gray_g', 'op':'=='},
]

filter_b_gray = [
    {'key':'category', 'value':'gray_b', 'op':'=='},
]

dottlined_labels = ['target', 'spec', 'ref']
de2000_labels = ['DE2000', 'E2000']

p3_gamut_uv = np.array(
    [[0.49635036, 0.52554745],
     [0.09860465, 0.57767442],
     [0.1754386, 0.15789474],
     [0.49635036, 0.52554745]])

p3_gamut_xy = np.array(
    [[0.68, 0.32],
     [0.265, 0.69],
     [0.15, 0.06],
     [0.68, 0.32]])

# filter
def get_rgbw_gamma_data(df_data):
    dict_data = {
        'w': None,
        'red': None,
        'green': None,
        'blue': None
    }
    df_data = pre_processing_mes_data(df_data)
    if 'gamma' in df_data['category'].unique():
        df_data_w = dataframe_filter(df_data, filter_w_gray)
        df_data_w = pre_processing_mes_data(df_data_w)
        df_data_w = calculate_gamma_value(df_data_w)
        dict_data['w'] = df_data_w

    if 'gray_r' in df_data['category'].unique():
        df_data_r = dataframe_filter(df_data,
                                     filter_r_gray)
        calculate_gamma_value_v2(df_data_r,
                                 test_color='r')
        dict_data['red'] = df_data_r

    if 'gray_g' in df_data['category'].unique():
        df_data_g = dataframe_filter(df_data,
                                     filter_g_gray)
        calculate_gamma_value_v2(df_data_g,
                                 test_color='g')
        dict_data['green'] = df_data_g

    if 'gray_b' in df_data['category'].unique():
        df_data_b = dataframe_filter(df_data,
                                     filter_b_gray)
        calculate_gamma_value_v2(df_data_b,
                                 test_color='b')
        dict_data['blue'] = df_data_b

    return dict_data

def check_string_in_key(check_strings, key):
    for string in check_strings:
        if string in key:
            return True

    return False

def get_string_in_key(check_strings, key):
    for string in check_strings:
        if string in key:
            return string

    return None

def string_to_label_convert(src_name):
    name = src_name.lower()
    if 'lab' == name:
        return 'CIE Lab'
    elif 'lch' == name:
        return 'CIE Lch'
    elif 'a' == name:
        return 'a*'
    elif 'b' == name:
        return 'b*'
    elif 'e2000' == name:
        return 'DE2000'
    elif 'l' == name:
        return 'L*'
    else:
        return src_name

def plot_grey_tracking_wrgb_gamma(gamma_dict, x_range=None, y_range=None,
                                  title="", figsize=None):
    if figsize:
        plt.figure(figsize=figsize)
    else:
        plt.figure()

    for key, data in gamma_dict.items():

        if data is None or 'gamma' not in data.columns:
            continue

        if check_string_in_key(dottlined_labels, key):
            plt.plot(data['G'], data['gamma'], label=key, linestyle="--")
        else:
            m_color = None
            if 'red' in key:
                m_color = 'R'
            elif 'green' in key:
                m_color = 'G'
            elif 'blue' in key:
                m_color = 'B'

            if m_color is not None:
                plt.plot(data[m_color], data['gamma'], label=key, c=m_color)
            else:
                plt.plot(data['G'], data['gamma'], label=key)

    plt.xlabel('gray')
    plt.ylabel('gamma')

    plt.title('gray tracking: gamma analysis: {}'.format(title))
    plt.legend()

    if x_range:
        plt.xlim(x_range)
    if y_range:
        plt.ylim(y_range)
    plt.show()

def plot_grey_tracking_whitebalance(gamma_dict, x_range=None, y_range=None, title=None,
                                    figsize=None):
    if figsize:
        plt.figure(figsize=figsize)
    else:
        plt.figure()

    for key, df_data in gamma_dict.items():

        if 'CCT' not in df_data.columns:
            continue

        if check_string_in_key(dottlined_labels, key):
            plt.plot(df_data['G'], df_data['CCT'], label=key, linestyle="--")
        else:
            plt.plot(df_data['G'], df_data['CCT'], label=key)

    plt.xlabel('gray')
    plt.ylabel('CCT')

    plt.title('gray tracking analysis: {}'.format(title))
    plt.legend()

    if x_range:
        plt.xlim(x_range)
    if y_range:
        plt.ylim(y_range)
    plt.show()

def plot_grey_tracking_wrgb_DE2000(gamma_dict, x_range=None, y_range=None,
                                   title="", figsize=None):
    if figsize:
        plt.figure(figsize=figsize)
    else:
        plt.figure()

    for key, data in gamma_dict.items():

        if data is None or check_string_in_key(['spec', 'target'], key):
            continue

        DE2000_label = get_string_in_key(de2000_labels, data.columns)
        if DE2000_label is None:
            continue

        m_color = None
        if 'red' in key:
            m_color = 'R'
        elif 'green' in key:
            m_color = 'G'
        elif 'blue' in key:
            m_color = 'B'

        if m_color is not None:
            plt.plot(data[m_color], data[DE2000_label], label=key, c=m_color)
        else:
            plt.plot(data['G'], data[DE2000_label], label=key)

    plt.xlabel('gray')
    plt.ylabel('DE2000')

    plt.title('gray tracking: gamma analysis: {}'.format(title))
    plt.legend()

    if x_range:
        plt.xlim(x_range)
    if y_range:
        plt.ylim(y_range)
    plt.show()

def plot_grey_tracking_wrgb_JNCD(gamma_dict, x_range=None, y_range=None,
                                 title="", figsize=None):
    if figsize:
        plt.figure(figsize=figsize)
    else:
        plt.figure()

    for key, data in gamma_dict.items():

        if data is None or check_string_in_key(['spec', 'target'], key):
            continue

        if 'JNCD' not in data.columns:
            continue

        m_color = None
        if 'red' in key:
            m_color = 'R'
        elif 'green' in key:
            m_color = 'G'
        elif 'blue' in key:
            m_color = 'B'

        if m_color is not None:
            plt.plot(data[m_color], data['JNCD'], label=key, c=m_color)
        else:
            plt.plot(data['G'], data['JNCD'], label=key)

    plt.xlabel('gray')
    plt.ylabel('JNCD')

    plt.title('gray tracking: gamma analysis: {}'.format(title))
    plt.legend()

    if x_range:
        plt.xlim(x_range)
    if y_range:
        plt.ylim(y_range)
    plt.show()

def plot_grey_tracking_brightness_v2(gamma_dict,
                                     x_range=None,
                                     y_range=None,
                                     title=None,
                                     figsize=None,
                                     with_scatter=False,
                                     gray='G',
                                     normalize_Y=False):
    if figsize:
        plt.figure(figsize=figsize)
    else:
        plt.figure()

    for key, df_data in gamma_dict.items():

        if df_data is None or 'Y' not in df_data.columns:
            continue

        Y_label = 'Y'
        if normalize_Y:
            # preprocess the Y_nor
            df_data['Y_nor'] = df_data['Y'] / df_data['Y'].max()
            Y_label = 'Y_nor'

        if check_string_in_key(dottlined_labels, key):
            plt.plot(df_data[gray], df_data[Y_label], label=key, linestyle='--')
        #             plt.scatter(df_data[gray], df_data['Y'], edgecolor = 'k')
        else:
            plt.plot(df_data[gray], df_data[Y_label], label=key)

            if with_scatter:
                plt.scatter(df_data[gray], df_data[Y_label], edgecolor='k')

    plt.xlabel('gray')

    if normalize_Y:
        plt.ylabel('brightness %')
    else:
        plt.ylabel('nits')

    plt.title('gray tracking analysis: Brightness {}'.format(title))
    plt.legend()

    if x_range:
        plt.xlim(x_range)
    if y_range:
        plt.ylim(y_range)
    plt.show()

def plot_cie_color_xyuv(gamma_dict,
                        x_range=None,
                        y_range=None,
                        title=None,
                        gray='G',
                        color_xy=['x', 'y']):
    plt.figure()

    if isinstance(color_xy, str):
        color_xy = [color_xy]

    for key, df_data in gamma_dict.items():

        if df_data is None or not check_string_in_key(color_xy, df_data.columns):
            continue

        if check_string_in_key(dottlined_labels, key):
            for label_xy in color_xy:
                plt.plot(df_data[gray],
                         df_data[label_xy],
                         label=key + '_' + label_xy,
                         linestyle="--")
        else:
            for label_xy in color_xy:
                plt.plot(df_data[gray],
                         df_data[label_xy],
                         label=key + '_' + label_xy)

    plt.xlabel('gray')
    label_y = 'cie '
    for label_xy in color_xy:
        label_y += label_xy
    plt.ylabel(label_y)

    plt.title('{}'.format(title))
    plt.legend()

    if x_range:
        plt.xlim(x_range)
    if y_range:
        plt.ylim(y_range)
    plt.show()

def plot_color_diff_in_histgoram(df_data, diff='E2000', x_range=None, y_range=None, Title=""):
    bar_width = 2

    ax = plt.figure(figsize=(35, 20)).gca()
    for i in range(len(df_data)):
        H = int(df_data.loc[i, 'H'])
        delta_val = df_data.loc[i, diff]
        R = df_data.loc[i, 'R']
        G = df_data.loc[i, 'G']
        B = df_data.loc[i, 'B']

        plt.bar(H, delta_val, color=(R / 255.0, G / 255.0, B / 255.0),
                width=bar_width,
                edgecolor='black',
                align='center')

    plt.plot([0, 360], [0, 0], c='black', ls='--')

    if x_range:
        plt.xlim(x_range)
    if y_range:
        plt.ylim(y_range)

    plt.title('{} average"{},max:{}, {}'.format(diff,
                                                df_data[diff].mean(),
                                                df_data[diff].max(),
                                                Title))
    plt.xlabel('digital hue')
    plt.ylabel('{}'.format(diff))
    plt.show()


def plot_pie_de2000(df_data, title=''):
    plt.figure()

    DE2000_label = get_string_in_key(de2000_labels, df_data.columns)
    if DE2000_label is None:
        print('ERROR!, no DE2000 data')
        return

    hist, bins = np.histogram(df_data[DE2000_label].ravel(), bins=[0, 1, 2, 3, 50])
    labels = ['DE < 1', 'DE:1~2', 'DE:2~3', 'DE:> 3']
    plt.pie(hist, autopct='%1.1f%%', labels=labels)
    plt.title('{}, DE2000 distribution, avg:{}\n \
            DE<1:{}\n \
            DE1~2:{}\n \
            DE2~3:{}\n \
            DE>3:{}'.format(title,
                            df_data[DE2000_label].mean(),
                            hist[0],
                            hist[1],
                            hist[2],
                            hist[3]
                            ))
    plt.tight_layout()
    plt.show()


def plot_pie_JNCD(df_data):
    plt.figure()
    hist, bins = np.histogram(df_data['JNCD'].ravel(), bins=[0, 1, 2, 3, 50])
    labels = ['JNCD < 1', 'JNCD:1~2', 'JNCD:2~3', 'JNCD:> 3']
    plt.pie(hist, autopct='%1.1f%%', labels=labels)
    plt.title('JNCD distribution\n \
            JNCD<1:{}\n \
            JNCD1~2:{}\n \
            JNCD2~3:{}\n \
            JNCD>3:{}'.format(
        hist[0], hist[1], hist[2], hist[3]
    ))
    plt.tight_layout()
    plt.show()

def plot_LCH_ab_to_DE2000(df_data, DE2000_samlpes=[0, 1, 2, 3, 4, 5, 100],
                          size_samples=[8, 8, 50, 200, 300, 400, 500],
                          alpha_samples=[30, 60, 100, 200, 255, 255, 255],
                          color_space='Lch',
                          x_range=None,
                          y_range=None,
                          figsize=None,
                          title=''):
    if 'Lch' in color_space:
        label_x = 'LCH_C*'
        label_y = 'L'
    elif 'Lab' in color_space:
        label_x = 'a'
        label_y = 'b'

    # E2000 vs size
    f_size = interp1d(DE2000_samlpes, size_samples)
    # E2000 vs alpha
    #     alpha_samples = [255, 255, 255, 255, 255, 255, 255]
    f_alpha = interp1d(DE2000_samlpes, alpha_samples)

    DE2000_label = get_string_in_key(de2000_labels, df_data.columns)
    if DE2000_label is None:
        print('ERROR!, no DE2000 data')
        return

    de2000 = df_data[DE2000_label].values
    size = f_size(de2000)
    df_data['A'] = f_alpha(de2000)
    rgba = df_data[['R', 'G', 'B', 'A']].values

    if figsize is None:
        figsize = plt.rcParams['figure.figsize']

    plt.figure(figsize=figsize)
    plt.scatter(df_data[label_x], df_data[label_y],
                color=rgba / 255.0,
                s=size,
                edgecolor='k')

    # Here we create a legend:
    for i in range(len(DE2000_samlpes) - 1):
        sample = DE2000_samlpes[i]
        plt.scatter([], [], c='red', alpha=f_alpha(sample) / 255.0, s=f_size(sample),
                    label='DE2000_{}'.format(sample), edgecolor='k')

    plt.legend(scatterpoints=1, frameon=False, labelspacing=1, title='DE2000 label')
    plt.xlabel(string_to_label_convert(label_x))
    plt.ylabel(string_to_label_convert(label_y))

    if x_range:
        plt.xlim(x_range)

    if y_range:
        plt.ylim(y_range)

    plt.title('{}, {} to DE2000'.format(title, string_to_label_convert(color_space)))
    plt.show()


def plot_LCH_ab_to_JNCD(df_data, JNCD_samlpes=[0, 1, 2, 3, 4, 5, 1000],
                        size_samples=[8, 8, 50, 200, 300, 400, 500],
                        alpha_samples=[30, 60, 100, 200, 255, 255, 255],
                        color_space='Lch',
                        x_range=None,
                        y_range=None,
                        figsize=None,
                        title=''):
    if 'Lch' in color_space:
        label_x = 'LCH_C*'
        label_y = 'L'
    elif 'Lab' in color_space:
        label_x = 'a'
        label_y = 'b'

    # E2000 vs size
    f_size = interp1d(JNCD_samlpes, size_samples)
    # E2000 vs alpha
    #     alpha_samples = [255, 255, 255, 255, 255, 255, 255]
    f_alpha = interp1d(JNCD_samlpes, alpha_samples)

    diff = df_data['JNCD'].values

    # clamp
    diff = np.clip(diff, 0, np.max(JNCD_samlpes))
    size = f_size(diff)
    df_data['A'] = f_alpha(diff)
    rgba = df_data[['R', 'G', 'B', 'A']].values

    if figsize is None:
        figsize = plt.rcParams['figure.figsize']

    plt.figure(figsize=figsize)
    plt.scatter(df_data[label_x], df_data[label_y],
                color=rgba / 255.0,
                s=size,
                edgecolor='k')

    # Here we create a legend:
    for i in range(len(JNCD_samlpes) - 1):
        sample = JNCD_samlpes[i]
        plt.scatter([], [], c='red', alpha=f_alpha(sample) / 255.0, s=f_size(sample),
                    label='JNCD_{}'.format(sample), edgecolor='k')

    plt.legend(scatterpoints=1, frameon=False, labelspacing=1, title='JNCD label')
    plt.xlabel(string_to_label_convert(label_x))
    plt.ylabel(string_to_label_convert(label_y))

    if x_range:
        plt.xlim(x_range)

    if y_range:
        plt.ylim(y_range)

    plt.title('{},{} to JNCD'.format(title, string_to_label_convert(color_space)))
    plt.show()

def plot_1931_color_comparison(dict_data, gamut_boundary, title=""):
    plot_chromaticity_diagram_CIE1931(standalone=False,
                                         title=False,
                                         tight_layout=True)

    for key, data in dict_data.items():

        if 'x' not in data.columns or 'y' not in data.columns:
            continue

        if check_string_in_key(dottlined_labels, key):
            plt.scatter(data['x'], data['y'], label=key, edgecolor='white',
                        marker='s', s=60, facecolors='none')
        else:
            plt.scatter(data['x'], data['y'], label=key, edgecolor='black')

    plt.plot(gamut_boundary[:, 0], gamut_boundary[:, 1], c='black')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.title('CIE1931 color, {}'.format(title))
    plt.tight_layout()
    plt.legend(facecolor='#AAAAAAAA')
    #plt.show()

def plot_1931_color_comparison_v2(data, gamut_boundary , hue, title=""):
    plot_chromaticity_diagram_CIE1931(standalone=False,
                                         title=False,
                                         tight_layout=True)

    sns.scatterplot(x='x', y='y', data=data , hue = hue)

    plt.plot(gamut_boundary[:, 0], gamut_boundary[:, 1], c='black')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.title('CIE1931 color, {}'.format(title))
    plt.tight_layout()
    plt.legend(facecolor='#AAAAAAAA')
    #plt.show()

def plot_1931_color_comparison_v3(data, gamut_boundary1, gamut_boundary2, hue , title=""):
    plot_chromaticity_diagram_CIE1931(standalone=False,
                                         title=False,
                                         tight_layout=True)

    sns.scatterplot(x='x', y='y', data=data , hue = hue)

    plt.plot(gamut_boundary1[:, 0], gamut_boundary1[:, 1], c='black')
    plt.plot(gamut_boundary2[:, 0], gamut_boundary2[:, 1], c='black')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.title('CIE1931 color, {}'.format(title))
    plt.tight_layout()
    plt.legend(facecolor='#AAAAAAAA')



    #plt.show()

def plot_1976_color_comparison_V2(dict_data, title=""):
    plot_chromaticity_diagram_CIE1976UCS(standalone=False,
                                         title=False,
                                         tight_layout=True)

    for key, data in dict_data.items():

        if 'u' not in data.columns or 'v' not in data.columns:
            continue

        if check_string_in_key(dottlined_labels, key):
            plt.scatter(data['u'], data['v'], label=key, edgecolor='white',
                        marker='s', s=60, facecolors='none')
        else:
            plt.scatter(data['u'], data['v'], label=key, edgecolor='black')

    plt.plot(p3_gamut_uv[:, 0], p3_gamut_uv[:, 1], c='black')
    plt.xlim([0, 0.7])
    plt.ylim([0, 0.7])
    plt.title('CIE1976 color, {}'.format(title))
    plt.tight_layout()
    plt.legend(facecolor='#AAAAAAAA')
    plt.show()

def color_analysis_by_group(df, color, title, hue="color"):
    df_color = df[df["ID"]==color]
    df_r = df_color[df_color["color"]=="R"]
    df_g = df_color[df_color["color"]=="G"]
    df_b = df_color[df_color["color"]=="B"]
    df_w = df_color[df_color["color"]=="W"]
    df_nr = df_color[df_color["color"]=="NR"]
    df_nb = df_color[df_color["color"]=="NB"]


    plt.figure(figsize=(15,5))
    plt.subplot(121)
    ax = sns.boxplot(x="color", hue = hue, y="x", data=df_color)
    plt.title('CIE1931 color, {}'.format(title))
    plt.subplot(122)
    ax = sns.boxplot(x="color", hue = hue, y="y", data=df_color)
    plt.title('CIE1931 color, {}'.format(title))

    #plt.show()

    dict_color = {'df_r':df_r,
                  'df_g':df_g,
                  'df_b':df_b,
                  'df_w':df_w,
                  'df_nr':df_nr,
                  'df_nb':df_nb
                }

    return df_color, dict_color

def LM_gen_per_len(df_r, df_g, df_b, df_w, unit_number):
    rd = df_r[df_r['unit_num']==unit_number]
    gd = df_g[df_g['unit_num']==unit_number]
    bd = df_b[df_b['unit_num']==unit_number]
    wd = df_w[df_w['unit_num']==unit_number]

    # Device RGB
    rxyY1 = [rd['x'].tolist()[0], rd['y'].tolist()[0], rd['Y'].tolist()[0]]
    gxyY1 = [gd['x'].tolist()[0], gd['y'].tolist()[0], gd['Y'].tolist()[0]]
    bxyY1 = [bd['x'].tolist()[0], bd['y'].tolist()[0], bd['Y'].tolist()[0]]
    wxyY1 = [wd['x'].tolist()[0], wd['y'].tolist()[0], wd['Y'].tolist()[0]]

    ## Target white : take the mean from the distribution
    w_x_target = df_w.describe().loc[['mean']]['x'][0].astype(float)
    w_y_target = df_w.describe().loc[['mean']]['y'][0].astype(float)

    ## Target RGB for warm gold : take minimum from the distribution

    r_x_target = df_r.describe().loc[['min']]['x'][0].astype(float)
    r_y_target = df_r.describe().loc[['mean']]['y'][0].astype(float)

    g_x_target = df_g.describe().loc[['mean']]['x'][0].astype(float)
    g_y_target = df_g.describe().loc[['min']]['y'][0].astype(float)

    b_x_target = df_b.describe().loc[['max']]['x'][0].astype(float)
    b_y_target = df_b.describe().loc[['mean']]['y'][0].astype(float)
    # Target RGB for warm gold
    xyzr = [r_x_target, r_y_target, 1 - r_x_target - r_y_target ]
    xyzg = [g_x_target, g_y_target, 1 - g_x_target - g_y_target ]
    xyzb = [b_x_target, b_y_target, 1 - b_x_target - b_y_target ]
    xyzw = [w_x_target, w_y_target, 1 - w_x_target - w_y_target ]

    dict_target_rgb = {'r':xyzr,
                        'g':xyzg,
                        'b':xyzb,
                        'w':xyzw
                    }

    dict_device_rgb = {'r':rxyY1,
                    'g':gxyY1,
                    'b':bxyY1,
                    'w':wxyY1
                    }

    dict_post_cal_val_pattern , M, Md, Mf, max_RGB_dc = primary_cal.LM_3x3(dict_device_rgb , dict_target_rgb)

    return dict_post_cal_val_pattern, M, Md, Mf, max_RGB_dc


def XYZ_to_device_RGB(Md, target_XYZ, max_RGB_dc):
    # input argument format: target_XYZ = [x, x, x]

    XYZ_in = np.array( [target_XYZ] ).reshape((3,1))
    RGBp = np.matmul(inv(Md), XYZ_in)
    RGBp[RGBp<0]=0

    #max_RGB_dc = 1.0
    RGBp_dc = np.round((RGBp**(1/2.2))/max_RGB_dc*255)
    RGBp_dc[RGBp_dc>255]=255

    temp = RGBp_dc.squeeze().tolist()
    RGBp_hex = [hex(int(x)) for x in temp]

    return RGBp_dc, RGBp_hex



## Main

## Data reading abd example plot
df_color_factory = pd.read_csv('Bismuth_rgbwk_per_lens.csv', encoding = 'big5')

# initialise data of lists.

p3_gamut_xy = np.array(
    [[0.68, 0.32],
     [0.265, 0.69],
     [0.15, 0.06],
     [0.68, 0.32]])

NTSC_gamut_xy = np.array(
    [[0.67, 0.33],
     [0.21, 0.71],
     [0.14, 0.08],
     [0.67, 0.33]])

sRGB_gamut_xy = np.array(
    [[0.64, 0.33],
     [0.3, 0.6],
     [0.15, 0.06],
     [0.64, 0.33]])

data_spec_xy = {'x':[0.64, 0.3, 0.15],
        'y':[0.33, 0.6, 0.06]}

data_NTSC_xy = {'x':[0.67, 0.21, 0.14],
        'y':[0.33, 0.71, 0.08]}

# Create DataFrame
df_spec_xy = pd.DataFrame(data_spec_xy)
df_spec_xy['ID'] = "target"

print("df_color_factory",df_color_factory)
print("df_spec xy",df_spec_xy)

dict_color_xy = {
    'ref-target-sRGB':df_spec_xy,
    'B1 Primary':df_color_factory
}


plot_1931_color_comparison_v2(df_color_factory, gamut_boundary = sRGB_gamut_xy, hue= "ID", title= "precal gamut all lens")
plot_1931_color_comparison_v3(df_color_factory, gamut_boundary1 = sRGB_gamut_xy, gamut_boundary2 = NTSC_gamut_xy, hue= "ID",  title="precal gamut all lens")

#########################################################
##
## Warm gold data analysis and 3x3 matrix generation
##
#########################################################

# Create DataFrame
df_spec_xy = pd.DataFrame(data_spec_xy)
df_spec_xy['ID'] = "sRGB"
df_NTSC_xy = pd.DataFrame(data_NTSC_xy)
df_NTSC_xy['ID'] = "NTSC"
#print(df_color_factory[df_color_factory["ID"]=="g"])

dict_color_xy = {
    'ref-target-sRGB':df_spec_xy,
    'ref-target-NTSC':df_NTSC_xy,
    'Bismuth Primary':df_color_factory[df_color_factory["ID"]=="gold"]
}

plot_1931_color_comparison(dict_color_xy, gamut_boundary = NTSC_gamut_xy, title= "precal_warm_gold")

### Color distribution
df_gold_color, dict_color = color_analysis_by_group(df_color_factory, "gold", title = "PreCal color distribution")

df_gold_r = dict_color["df_r"]
df_gold_g = dict_color["df_g"]
df_gold_b = dict_color["df_b"]
df_gold_w = dict_color["df_w"]
df_gold_nr = dict_color["df_nr"]
df_gold_nb = dict_color["df_nb"]

df_gold_r.describe().to_csv('./r_describe.csv', encoding='utf-8')
df_gold_g.describe().to_csv('./g_describe.csv', encoding='utf-8')
df_gold_b.describe().to_csv('./b_describe.csv', encoding='utf-8')

# This function takes care of matrix generation
# M, Md, Mf = LM_gen_per_len(df_gold_r, df_gold_g, df_gold_b, df_gold_w, unit_number)


## warm gold unit 0

for i in range(4):

    unit_number = i
    ## check post cal RGBW pattern
    dict_post_cal_val_pattern, M, Md, Mf, max_RGB_dc = LM_gen_per_len(df_gold_r, df_gold_g, df_gold_b, df_gold_w, unit_number)
    print("Unit_number: ", unit_number)
    print(dict_post_cal_val_pattern)

    ## Estimated nest red and blue RGB for given XYZ target
    df_gold_nr_unit = df_gold_nr[df_gold_nr['unit_num']==unit_number]
    #t_xyY = [df_gold_nr_unit['x'].tolist()[0], df_gold_nr_unit['y'].tolist()[0], df_gold_nr_unit['Y'].tolist()[0]]
    t_xyY = [0.575, 0.377, df_gold_nr_unit['Y'].tolist()[0]]
    t_XYZ = [ t_xyY[0]/t_xyY[1] * t_xyY[2] , t_xyY[2], (1 - t_xyY[0]-t_xyY[1])/t_xyY[1] * t_xyY[2] ]
    RGBp_dc, RGBp_hex = XYZ_to_device_RGB(Md, t_XYZ, max_RGB_dc)
    print("Estimated NR RGB basedon target XYZ: ",t_XYZ, RGBp_dc, RGBp_hex)

    df_gold_nb_unit = df_gold_nb[df_gold_nb['unit_num']==unit_number]
    #t_xyY = [df_gold_nb_unit['x'].tolist()[0], df_gold_nb_unit['y'].tolist()[0], df_gold_nb_unit['Y'].tolist()[0]]
    t_xyY = [0.2484, 0.3087, df_gold_nb_unit['Y'].tolist()[0]]
    t_XYZ = [ t_xyY[0]/t_xyY[1] * t_xyY[2] , t_xyY[2], (1 - t_xyY[0]-t_xyY[1])/t_xyY[1] * t_xyY[2] ]
    RGBp_dc, RGBp_hex = XYZ_to_device_RGB(Md, t_XYZ, max_RGB_dc)
    print("Estimated NB RGB basedon target XYZ: ",t_XYZ, RGBp_dc, RGBp_hex)



## Post cal data plot
df_color = pd.read_csv('Bismuth_rgbwk_per_lens_post_cal.csv', encoding = 'big5')
df_color_post = df_color[df_color["sequence"]=="post"]
dict_color_xy = {
    'ref-target-sRGB':df_spec_xy,
    'ref-target-NTSC':df_NTSC_xy,
    'Bismuth Primary':df_color_post[df_color_post["ID"]=="gold"]
}
plot_1931_color_comparison_v2(df_color_post, gamut_boundary = sRGB_gamut_xy , hue= "ID", title ="post_cal gamut all lens")
plot_1931_color_comparison_v3(df_color_post, gamut_boundary1 = sRGB_gamut_xy, gamut_boundary2 = NTSC_gamut_xy,  hue= "ID", title="post_cal gamut all lens")
plot_1931_color_comparison_v3(df_color, gamut_boundary1 = sRGB_gamut_xy, gamut_boundary2 = NTSC_gamut_xy,  hue= "sequence", title="pre and post_cal gamut all lens")
plot_1931_color_comparison(dict_color_xy, gamut_boundary = NTSC_gamut_xy,  title ="post_cal gamut : warm gold")


## Pre-Post-new Color comparison for warm gold
df_color_post = pd.read_csv('Bismuth_rgbwk_per_lens_pre_post_cal_comparison.csv', encoding = 'big5')
dict_color_xy = {
    'ref-target-sRGB':df_spec_xy,
    'ref-target-NTSC':df_NTSC_xy,
    'Bismuth Primary':df_color_post[df_color_post["ID"]=="gold"]
}
plot_1931_color_comparison_v2(df_color_post, gamut_boundary = sRGB_gamut_xy,  hue= "sequence",)
plot_1931_color_comparison_v3(df_color_post, gamut_boundary1 = sRGB_gamut_xy, gamut_boundary2 = NTSC_gamut_xy,  hue= "sequence",)
plot_1931_color_comparison(dict_color_xy, gamut_boundary = NTSC_gamut_xy,  title =" Pre-Post-New Color comparison : warm gold")


df_color_post_R = df_color_post[df_color_post["color"]=="R"]
df_color_post_G = df_color_post[df_color_post["color"]=="G"]
df_color_post_B = df_color_post[df_color_post["color"]=="B"]
df_color_post_W = df_color_post[df_color_post["color"]=="W"]
df_color_post_NR = df_color_post[df_color_post["color"]=="NR"]
df_color_post_NB = df_color_post[df_color_post["color"]=="NB"]

### Color distribution
df_gold_color, dict_color = color_analysis_by_group(df_color_post, "gold", hue = "sequence", title = " Color distribution comparison")
df_gold_color, dict_color = color_analysis_by_group(df_color_post_R, "gold", hue = "sequence", title = "Color distribution : Red")
df_gold_color, dict_color = color_analysis_by_group(df_color_post_G, "gold", hue = "sequence", title = "Color distribution : Green")
df_gold_color, dict_color = color_analysis_by_group(df_color_post_B, "gold", hue = "sequence", title = "Color distribution : Blue")
df_gold_color, dict_color = color_analysis_by_group(df_color_post_W, "gold", hue = "sequence", title = "Color distribution : White")
df_gold_color, dict_color = color_analysis_by_group(df_color_post_NR, "gold", hue = "sequence", title = "Color distribution : Nest Red")
df_gold_color, dict_color = color_analysis_by_group(df_color_post_NB, "gold", hue = "sequence", title = "Color distribution : Nest Blue")

plt.show()
