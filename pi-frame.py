#!/usr/bin/env python3

from random import sample
import gpiod
import gpiodevice
from gpiod.line import Bias, Direction, Edge
import time
import os
import argparse
import logging
from PIL import Image
from inky.auto import auto
from inky.inky_uc8159 import CLEAN


picdir = os.path.join(os.path.dirname(__file__), 'images')
photo_count = 642
random_number_array = sample(range(0, photo_count), photo_count)
photo_array = []
picture_syntax = {'color':'A','BW':"B"}
default_picture_syntax = "color"
photo_format = ".jpg"
wait_time_for_next_photo = 3600

logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser()
parser.add_argument("--saturation", "-s", type=float, default=0.5, help="Colour palette saturation")
args, _ = parser.parse_known_args()
saturation = args.saturation
inky = auto(ask_user=True, verbose=True)

buttons = [5, 6, 16, 24]
labels = ["A", "B", "C", "D"]
input = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, edge_detection=Edge.FALLING)
chip = gpiodevice.find_chip_by_platform()
offsets = [chip.line_offset_from_id(id) for id in buttons]
line_config = dict.fromkeys(offsets, input)
request = chip.request_lines(consumer="inky7-buttons", config=line_config)


def initalise_photo_array():
    for i in range(0,len(random_number_array)):
        if random_number_array[i] < 10:
            photo_array.append('0000' + str(random_number_array[i]) + photo_format)
        if random_number_array[i] >= 10 and random_number_array[i] < 100:
            photo_array.append('000' + str(random_number_array[i]) + photo_format)
        if random_number_array[i] >= 100:
            photo_array.append('00' + str(random_number_array[i]) + photo_format)
    logging.info("created photo array")

def clean():
    logging.info("Clear display started")
    for _ in range(2):
        for y in range(inky.height - 1):
            for x in range(inky.width - 1):
                inky.set_pixel(x, y, CLEAN)

    inky.show()
    time.sleep(1.0)
    logging.info("Clear display finished")

def wait_unless_button_pressed(minutes):
    global default_picture_syntax
    logging.info('waiting ' + str(wait_time_for_next_photo/60) + ' Minutes')
    for i in range(minutes):
        try:
            time.sleep(1)
        finally:
            get_button_status = request.get_values()
            if str(get_button_status[0]).strip("Value.") != "ACTIVE":
                index = offsets.index(buttons[0])
                label = labels[index]
                logging.info('button ' + label + ' was pressed, next photo')
                return 1
            elif str(get_button_status[1]).strip("Value.") != "ACTIVE":
                index = offsets.index(buttons[1])
                label = labels[index]
                logging.info('button ' + label + ' was pressed, previous photo')
                return 2
            elif str(get_button_status[2]).strip("Value.") != "ACTIVE":
                index = offsets.index(buttons[2])
                label = labels[index]
                if default_picture_syntax == 'color':
                    default_picture_syntax = 'BW'
                    logging.info('button ' + label + ' was pressed, changed photos to black and white')
                else:
                    default_picture_syntax = 'color' 
                    logging.info('button ' + label + ' was pressed, changed photos to color')
                return 3
            elif str(get_button_status[3]).strip("Value.") != "ACTIVE":
                index = offsets.index(buttons[3])
                label = labels[index]
                logging.info('button ' + label + ' was pressed, rebooting')
                return 4
    return '0'


def update(int):
        image_location = picdir + '/' +  default_picture_syntax + '/' + picture_syntax[default_picture_syntax] + photo_array[int]
        logging.info('displaying image: ' + image_location + ', image number in array: ' + str(int) + '/' + str(photo_count))
        image = Image.open(image_location)
        resizedimage = image.resize(inky.resolution)
        
        try:
            inky.set_image(resizedimage, saturation=saturation)
        except TypeError:
            inky.set_image(resizedimage)

        inky.show()
        logging.info('display image finished')
        
    
def main():
    logging.info("initalising...")
    initalise_photo_array()
    clean()
    i = 0
    try:
        while i <= photo_count:
            update(i)
            result = wait_unless_button_pressed(wait_time_for_next_photo)
            if result == 2:
                i-= 2
            elif result == 3:
                i-= 1
            elif result == 4:
                break
            if i == photo_count:
                i = 0
            else:
                i+= 1

    finally:
        logging.info("clearing screen before shutdown")
        clean()
        os.system('sudo reboot')


if __name__ == '__main__':
    main()