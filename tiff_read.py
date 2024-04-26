from PIL import Image
import numpy
import sys
import json
import cv2 
import math 
from matplotlib import pyplot as plt
sys.setrecursionlimit(1000000)
import os 

#load coordinates from JSON file and image id to match with TIFF file
with open("coordinates.json", 'r') as f:
     coords = json.load(f)




#tolerance for localization
tolerance = 7

min_thresh = 26.5

#Used for adjusting coordinates
padding_width = 640




#Function recursively flood fills our second array with the values we should include in our localization 
def localize_ff(x, y, min, max):
    me = imarray[y][x]
    check = ff_array[y][x]
    if(me <= max and me > min and check == 0 and y < 287 and x < 383):
        # print("works")
        # print("x:" + str(x))
        # print("y:" + str(y))
        ff_array[y][x] = me
        localize_ff(x, y+1, min, max)
        localize_ff(x+1, y, min, max)
        localize_ff(x, y-1, min, max)
        localize_ff(x-1, y, min, max)


#Localizes according to specified key point
def localize_keypoint_ff(i):
    values = convert_point(i)
    x = values[0]
    y = values[1]
    threshold = imarray[y][x]
    min = threshold - tolerance
    max = threshold + tolerance

    localize_ff(x, y, min, max)


def convert_point(i):
    i -= 1
    img_x = points[i*3]
    img_y = points[i*3+1]
    #correct coordinates to smaller arraimg_y from large image with padding
    img_x -= padding_width/2
    img_x *= 1/5
    img_y *= 1/5
    img_x = round(img_x)
    img_y = round(img_y)
    return [img_x, img_y]


def calculate_box():
    tl = convert_point(1)
    tr = convert_point(6)
    bm = convert_point(13)

    width = tr[0] - tl[0]
    height = bm[1] - tr[1]
    tl_corner = tl
    br_corner = [tl[0]+width,tl[1]+height]

    return[br_corner, tl_corner, [width, height]]


def threshold():
    row = 0
    col = 0
    corners = calculate_box()
    width = corners[2][0]
    height = corners[2][1]
    Threshold = [[0 for i in range(width)] for j in range(height)]

    for i in range(corners[1][1], corners[0][1]):
        for j in range(corners[1][0], corners[0][0]):
            value = imarray[i][j]
            if(value < min_thresh):
                Threshold[row][col] = min_thresh
            else:
                Threshold[row][col] = value
            col += 1
        col = 0
        row += 1
    return Threshold

def combine():
    corners = calculate_box()
    width = corners[2][0]
    height = corners[2][1]
    start = corners[1]
    left = start[0]
    top = start[1]
    for i in range(height):
        for j in range(width):
            point = [j+left ,i + top]
            left_eye = convert_point(9)
            right_eye = convert_point(8)
            if(in_distance(25, point, left_eye) or in_distance(25, point, right_eye)):
                otsu_array[top + i][left + j] = Threshold[i][j]


def in_distance(n, first, second):
    a = abs(first[0]-second[0])
    b = abs(first[1]-second[1])
    if(math.sqrt(a**2 + b**2) <= n):
        return True
    else:
        return False



directories = ["original", "Whole_Image_OTSU","FF_method", "Face_OTSU"]

for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)

for index in range(30):
    points = coords[index]["points"]
    id = coords[index]["id"]
    id = id.replace('0', "")

    path = ('/media/ethan/Expansion/Thermal/12_19_data/0064_Video_Frame_' + id + '.tiff')
    im = Image.open(path)
    imarray = numpy.array(im)

    #empty array for FF method
    ff_array = [[0 for i in range(384)] for j in range(288)]
    #empty array for OTSU method
    otsu_array = [[0 for i in range(384)] for j in range(288)]

    #right
    localize_keypoint_ff(8)
    #left
    localize_keypoint_ff(9)

    #Returns matrix of just cows face for OTSU method
    Threshold = threshold()

    #Convert to numpy arrays
    Threshold = numpy.array(Threshold)
    ff_array = numpy.array(ff_array)
    otsu_array = numpy.array(otsu_array)

    #For gray scale
    imarray = imarray.astype("uint8") #Whole image
    Threshold = Threshold.astype("uint8") #Just Face

    #OTSU Thresholding
    ret, thresh = cv2.threshold(imarray, 1, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) 
    ret, Threshold = cv2.threshold(Threshold, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU) 

    combine()

    #Write results to folders
    n = str(index+1)
    cv2.imwrite("original/" + n + ".png", imarray)
    cv2.imwrite("Whole_Image_OTSU/" + n + ".png", thresh)
    cv2.imwrite("FF_method/" + n + ".png", ff_array)
    cv2.imwrite("Face_OTSU/" + n + ".png", otsu_array)
