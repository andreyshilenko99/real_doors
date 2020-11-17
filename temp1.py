import datetime
import math
import sqlite3
from test_yolo.tf import YOLOv4
import cv2
import time
import os
import tensorflow as tf
import threading
from downloader import download
from downloader import r8
import subprocess
from urllib.error import HTTPError
from downloader import r8_short

# os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"] = "8"
gpus = tf.config.experimental.list_physical_devices('GPU')

if gpus:
    try:
        # Currently, memory growth needs to be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)


def stat(label, frame1, x, y):
    cv2.putText(frame1, "Status: {}".format(label), (x, y), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 0, 255), 3,
                cv2.LINE_AA)


cntr = 0
status = ["...", "..."]
switch = {'count': 0, 'exit': 0, 'counter': 0, 'enter': 0, 'record': 0, 'timer': 40, 'true': 0, 'video': 0}
result = 0
temp_name = ''
temp_channel = ''
temp_time = ''
dirs = {'ch01': 0, 'ch04': 0, 'ch06': 0, 'ch07': 0, 'ch08': 0}
w_door = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0, '7': 0, '8': 0}
record_frames_before = []
record_frames_after = []
center = []
det = []
temp_temp = 0
times = 0
super_list = []

_frame = []
persons = []
last_exit = 0


def for_frame(frame_number, output_array, return_detected_frame, x1_door_area,
              x2_door_area, video, channel, _name, image, start_time):  # добавить сброс на закрытую дверь
    print(time.strftime("%H:%M:%S", time.localtime()), " frame", frame_number)
    conn = sqlite3.connect("mydatabase.db")
    cursor = conn.cursor()
    if len(output_array) == 0:
        status[0] = "..."

    # def calculate(x__1, y__1, x__2, y__2, w, h):
    #     sq = (((x__1 - x__2) * (y__2 - y__1)) / (h * w)) * 100
    #     cv2.putText(image, str(sq),
    #                 (round((x__1 + x__2) / 2), round((y__1 + y__2) / 2)),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    #     cv2.rectangle(image, (x__1, y__1), (x__2, y__2), (0, 0, 255),
    #                   4)
    #     return sq

    square = {'ch01': [70, 55, 13], 'ch06': [73, 50, 13], 'ch04': [90, 90], 'ch07': [90, 90], 'ch08': [60, 60, 13]}
    detection_rects = {'ch06': [[300, 0, 380, 209], [399, 32, 471, 387], [0, 427, 640, 480]],
                       'ch01': [[105, 15, 219, 365], [278, 60, 375, 400], [0, 427, 640, 480]],
                       'ch04': [[380, 30, 490, 355], [130, 0, 290, 480]],
                       'ch07': [[400, 20, 476, 300], [140, 0, 310, 480]],
                       'ch08': [[265, 27, 392, 350], [508, 11, 600, 400], [0, 427, 640, 480]]}
    tempr = detection_rects.get(channel)
    cv2.rectangle(image, (tempr[0][0], tempr[0][1]), (tempr[0][2], tempr[0][3]),
                  (0, 255, 0), 1)
    cv2.rectangle(image, (tempr[1][0], tempr[1][1]), (tempr[1][2], tempr[1][3]),
                  (0, 255, 0), 1)
    cv2.rectangle(image, (0, 427), (640, 427),
                  (0, 255, 0), 1)
    if frame_number == 0:
        i = 0
        det.clear()
        while i < len(tempr):
            i += 1
            det.append([])

    if output_array:

        for person in output_array:
            x_1 = person[0]
            x_2 = person[2]
            y_1 = person[1]
            y_2 = person[3]

            def calculate(x__1, y__1, x__2, y__2, w, h):
                sq = (((x__1 - x__2) * (y__2 - y__1)) / ((x_1 - x_2) * (y_1 - y_2))) * 100
                cv2.putText(image, str(sq),
                            (round((x__1 + x__2) / 2), round((y__1 + y__2) / 2)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.rectangle(image, (x__1, y__1), (x__2, y__2), (0, 0, 255),
                              4)
                return sq

            i = 0
            for door in tempr:
                if door[1] <= y_1 <= door[3] <= y_2:  # в массиве door точки
                    if x_1 <= door[0] <= x_2 <= door[2]:
                        det[i].append(calculate(door[0], y_1, x_2, door[3], door[2] - door[0], door[3] - door[1]))
                    elif door[0] <= x_1 <= x_2 <= door[2]:
                        det[i].append(calculate(x_1, y_1, x_2, door[3], door[2] - door[0], door[3] - door[1]))
                    elif door[0] <= x_1 <= door[2] <= x_2:
                        det[i].append(calculate(x_1, y_1, door[2], door[3], door[2] - door[0], door[3] - door[1]))
                elif door[1] <= y_1 <= y_2 <= door[3]:
                    if x_1 <= door[0] <= x_2 <= door[2]:
                        det[i].append(calculate(door[0], y_1, x_2, y_2, door[2] - door[0], door[3] - door[1]))
                    elif door[0] <= x_1 <= door[2] <= x_2:
                        det[i].append(calculate(x_1, y_1, door[2], y_2, door[2] - door[0], door[3] - door[1]))
                    elif door[0] <= x_1 <= x_2 <= door[2]:
                        det[i].append(calculate(x_1, y_1, x_2, y_2, door[2] - door[0], door[3] - door[1]))
                elif y_1 <= door[1] <= y_2 <= door[3]:
                    if x_1 <= door[0] <= x_2 <= door[2]:
                        det[i].append(calculate(door[0], door[1], x_2, y_2, door[2] - door[0], door[3] - door[1]))
                    elif door[0] <= x_1 <= door[2] <= x_2:
                        det[i].append(calculate(x_1, door[1], door[2], y_2, door[2] - door[0], door[3] - door[1]))
                    elif door[0] <= x_1 <= x_2 <= door[2]:
                        det[i].append(calculate(x_1, door[1], x_2, y_2, door[2] - door[0], door[3] - door[1]))
                elif y_1 <= door[1] <= door[3] <= y_2:
                    if x_1 <= door[0] <= x_2 <= door[2]:
                        det[i].append(calculate(door[0], door[1], x_2, door[3], door[2] - door[0], door[3] - door[1]))
                    elif door[0] <= x_1 <= door[2] <= x_2:
                        det[i].append(calculate(x_1, door[1], door[2], door[3], door[2] - door[0], door[3] - door[1]))
                    elif door[0] <= x_1 <= x_2 <= door[2]:
                        det[i].append(calculate(x_1, door[1], x_2, door[3], door[2] - door[0], door[3] - door[1]))

                if len(det[i]) > 3:
                    det[i].pop(0)
                i += 1

            if (x1_door_area <= x_1 <= x2_door_area) or (x1_door_area <= x_2 <= x2_door_area):
                status[0] = "Somebody in door area"
            else:
                status[0] = "..."
    else:
        for i in det:
            if len(i) == 3:
                i.pop(0)
                i.append(0)

    global last_exit

    if len(det[len(det) - 1]) != 0:
        if math.fabs(round(det[len(det) - 1][len(det[len(det) - 1]) - 1])) > 10:
            last_exit = math.fabs(round(det[len(det) - 1][len(det[len(det) - 1]) - 1]))
        cursor.execute("INSERT INTO logs VALUES(?,?,?)",
                       (frame_number, len(output_array),
                        last_exit))
        conn.commit()
    else:
        cursor.execute("INSERT INTO logs VALUES(?,?,?)",
                       (frame_number, len(output_array), 0))
        conn.commit()

    def avg():
        sq = square.get(channel)
        avg1 = 0
        avg2 = 0
        ln = 0
        count1 = 0
        count2 = 0
        while ln < len(det) - 1:
            if len(det[ln]) == 0:
                ln += 1
                continue
            for u in det[ln]:
                if ln == 0:
                    if u != 0:
                        avg1 += math.fabs(u)
                        count1 += 1
                else:
                    if u != 0:
                        count2 += 1
                        avg2 += math.fabs(u)
            ln += 1
        if count1 != 0 and count2 != 0:
            if avg1 / count1 > avg2 / count2 and avg1 / count1 > sq[0]:
                if channel == 'ch08':
                    w_door['1'] = 1
                elif channel == 'ch06':
                    w_door['5'] = 1
                elif channel == 'ch01':
                    w_door['8'] = 1
                return 1
            elif avg1 / count1 < avg2 / count2 and avg2 / count2 > sq[1]:
                if channel == 'ch08':
                    w_door['2'] = 1
                elif channel == 'ch06':
                    w_door['4'] = 1
                elif channel == 'ch01':
                    w_door['7'] = 1
                return 2
        elif count1 != 0 and count2 == 0:
            if avg1 / count1 > 80 and len(tempr) == 2:
                if channel == 'ch04':
                    w_door['6'] = 1
                elif channel == 'ch07':
                    w_door['3'] = 1
                return 5
        elif count1 != 0 and count2 == 0:
            if avg1 / count1 > sq[0] and len(tempr) == 3:
                if channel == 'ch08':
                    w_door['1'] = 1
                elif channel == 'ch06':
                    w_door['5'] = 1
                elif channel == 'ch01':
                    w_door['8'] = 1
                return 3
        elif count1 == 0 and count2 != 0:
            if avg2 / count2 > sq[1] and len(tempr) == 3:
                if channel == 'ch08':
                    w_door['2'] = 1
                elif channel == 'ch06':
                    w_door['4'] = 1
                elif channel == 'ch01':
                    w_door['7'] = 1
                return 4
        else:
            return 0

    if avg() != 0 and avg() is not None:
        super_list.append(avg())
    if len(super_list) > 3:
        super_list.pop(0)
    super_c = 0
    if len(super_list) == 3:
        for i in super_list:
            if super_list[0] == i:
                super_c += 1
            if super_c == 3:
                super_list.clear()
                persons.append(len(output_array))
                _frame.append(frame_number)
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", super_list)

    if len(_frame) != 0 and frame_number == _frame[0] + 20:
        i = 0
        while i < len(_frame):
            cursor.execute('''SELECT * FROM logs WHERE frame=?;''', (int(_frame[i] + 10),))
            temporary0 = cursor.fetchone()
            cursor.execute('''SELECT * FROM logs WHERE frame=?;''', (int(_frame[i] + 15),))
            temporary1 = cursor.fetchone()
            cursor.execute('''SELECT * FROM logs WHERE frame=?;''', (int(_frame[i] + 20),))
            temporary2 = cursor.fetchone()
            try:
                if temporary0[1] < persons[i] and temporary0[2] > 10 and temporary1[1] < persons[i] \
                        and temporary1[2] > 10 and temporary2[1] < persons[i] and temporary2[2] > 10:
                    print("looooooooooooooooooooooooooooooool")
                    switch['exit'] = 1
                    _frame.remove(_frame[i])
                    persons.remove(persons[i])
                else:
                    _frame[i] += 10

            except TypeError:
                pass
            i += 1
    if frame_number == 1:
        status[1] = "..."
        switch['exit'] = 0
        switch['enter'] = 0
        switch['counter'] = 0
        switch['count'] = 0
    if switch.get('exit') == 1:
        status[1] = "Somebody came/left (into) the room"
        # switch['exit'] = 0
        switch['count'] = 20
    if switch.get('enter') == 1:
        status[1] = "Somebody came/left (into) the room"
        switch['enter'] = 0
        switch['counter'] = 20

    if switch.get('count') > 0:
        switch['count'] -= 1
    if switch.get('counter') > 0:
        switch['counter'] -= 1
    if switch.get('counter') == 0 and switch.get('count') == 0:
        status[1] = "..."

    frame_width = int(video.get(3))
    frame_height = int(video.get(4))
    stat(status[1], return_detected_frame, 10, 60)
    stat(status[0], return_detected_frame, 10, 100)
    size = (frame_width, frame_height)

    global result
    now = datetime.datetime.now()
    global temp_name
    global temp_channel
    global temp_time
    global temp_temp
    clock = datetime.datetime.now()
    today = clock.strftime("%Y-%m-%d")
    if status[0] == "Somebody in door area" and switch.get('record') == 0:
        dlist = os.listdir('analized')
        yes = 0
        for i in dlist:
            if i == today:
                yes = 1
        if not yes:
            os.mkdir(os.path.join('analized', today))
            temp = 'analized' + '\\' + today
            os.mkdir(os.path.join(temp, 'ch01'))
            os.mkdir(os.path.join(temp, 'ch04'))
            os.mkdir(os.path.join(temp, 'ch06'))
            os.mkdir(os.path.join(temp, 'ch07'))
            os.mkdir(os.path.join(temp, 'ch08'))
        temp_name = _name
        temp_channel = channel
        temp_time = now.strftime("%Y-%m-%d %H:%M:%S")
        cv2.imwrite(os.path.join('analized' + '\\' + start_time[:10] + '\\' + channel, temp_name + '.jpg'),
                    return_detected_frame)
        result = cv2.VideoWriter(os.path.join('analized' + '\\' + start_time[:10] + '\\' + channel, temp_name),
                                 cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                 10.0, size)
        switch['record'] = 1
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    if len(record_frames_before) < 100:
        record_frames_before.append(return_detected_frame)
    if len(record_frames_before) == 100:
        record_frames_before.pop(0)
    if status[1] == "Somebody came/left (into) the room" and switch.get('record') == 1 and switch.get('true') == 0:
        if len(record_frames_before) != 0:
            for i in record_frames_before:
                result.write(i)
        switch['true'] = 1
    if switch.get('true') == 1 and switch.get('record') == 1 and frame_number < length - 3 and switch.get(
            'timer') != 0:
        if switch.get('exit') == 1:
            switch['timer'] += 20
        switch['timer'] -= 1
        result.write(return_detected_frame)
    if switch.get('true') == 1 and switch.get('record') == 1 and (switch.get(
            'timer') == 0 or frame_number > length - 5):
        switch['timer'] = 40
        switch['video'] = 1
        switch['record'] = 0
        switch['true'] = 0
        result.release()

        post = r'C:\Users\user\Desktop\video\analized' + '\\' + start_time[:10] + '\\' + channel
        pre = r'ffmpeg -i C:\Users\user\Desktop\video\analized' + '\\' + start_time[:10] + '\\' + channel
        command = pre + '\\' + temp_name + ' ' + post + '\\' + temp_name + str(frame_number) + '.mp4'
        subprocess.call(str(command))
        os.chdir(r"C:\Users\user\Desktop\video\analized" + '\\' + start_time[:10] + '\\' + channel)
        download(channel, temp_name + str(frame_number) + '.mp4')
        download(channel, temp_name + '.jpg')
        temp = ''
        os.chdir(r"C:\Users\user\Desktop\video")
        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM requests WHERE sent=0;")
        conn.commit()
        not_sent = cursor.fetchall()
        if len(not_sent) != 0:
            for i in not_sent:
                print(i[0])
                if r8_short(i[0]) is not None:
                    cursor.execute('''UPDATE requests SET sent = 1 WHERE request=?;''', (i[0],))
                    conn.commit()

        for key in w_door:
            if w_door.get(key) == 1:
                r8(channel, start_time, temp_name + str(frame_number) + '.mp4', temp_name + '.jpg', key)
                w_door[key] = 0

        conn.close()
        # os.chdir(r"C:\Users\user\Desktop\video")
        if status[0] == "Somebody in door area":
            pass
        else:
            global cntr
            cntr += 1

    switch['exit'] = 0


def main():
    try:
        status[1] = ''
        status[0] = ''
        dictionary_of_cords = {'ch01': [47, 450, 200, 33, 329, 67], 'ch04': [339, 535, 410, 27, 0, 0],
                               'ch06': [233, 587, 371, 5, 461, 13],
                               'ch07': [351, 540, 412, 23, 0, 0], 'ch08': [190, 634, 344, 29, 586, 31]}
        cont_or_nor = 0
        _name = ''
        os.chdir(r"C:\Users\user\Desktop\video")
        ccounter = 0
        record_time = 0
        _counter = 0
        while True:
            all_dirs = os.listdir('all')
            if ccounter == len(all_dirs):
                ccounter = 0
            while True:
                array_of_dates = os.listdir(os.path.join('all', all_dirs[ccounter]))
                # print(all_dirs)
                # print(array_of_dates)
                if _counter == len(array_of_dates):
                    _counter = 0
                    break
                while True:  # добавить break для выхода в основной цикл
                    array_of_video_names = os.listdir(
                        os.path.join('all' + '\\' + all_dirs[ccounter],
                                     array_of_dates[_counter]))  # имя папки и имя папок
                    counter = 0

                    while counter < len(array_of_video_names):
                        conn = sqlite3.connect("mydatabase.db")
                        sql_select = '''SELECT * FROM names WHERE video_name=? AND anal=?;'''
                        cursor = conn.cursor()
                        cursor.execute(sql_select, (array_of_video_names[counter], 0))
                        fetch = cursor.fetchone()
                        conn.commit()
                        try:
                            if fetch is not None and fetch[0] == (array_of_video_names[counter]):
                                record_time = fetch[2]
                                print(record_time)
                                cont_or_nor = 1
                                _name = array_of_video_names[counter]
                                break
                            counter += 1
                        except Exception as e:
                            print('error!')

                    if counter == len(array_of_video_names):
                        break
                    if not cont_or_nor:
                        continue
                    video = cv2.VideoCapture(
                        os.path.join('all' + '\\' + all_dirs[ccounter] + '\\' + array_of_dates[_counter], _name))
                    switch['enter'] = 0
                    switch['enter'] = 0

                    yolo = YOLOv4()
                    yolo.classes = "coco.names"
                    yolo.make_model()
                    yolo.load_weights("yolov4.weights", weights_type="yolo")
                    if not video.isOpened():
                        print("Error reading video file")

                    prev_time = time.time()
                    number = 0
                    count = 0
                    global temp_name
                    global temp_channel
                    global temp_time
                    temp_time = ''
                    temp_name = ''
                    temp_channel = ''
                    conn = sqlite3.connect("mydatabase.db")
                    cursor = conn.cursor()
                    cursor.execute("delete from logs;")
                    conn.commit()

                    record_frames_before.clear()
                    record_frames_after.clear()
                    center.clear()
                    det.clear()
                    global times
                    times = 0
                    switch['video'] = 0
                    super_list.clear()
                    _frame.clear()
                    persons.clear()
                    global last_exit
                    last_exit = 0
                    for key in w_door:
                        if w_door.get(key) == 1:
                            w_door[key] = 0

                    while True:

                        ret, frame = video.read()

                        if ret:

                            count += 1
                            start_time = time.time()
                            bboxes = yolo.predict(frame)
                            print()
                            exec_time = time.time() - start_time
                            print("time: {:.2f} ms".format(exec_time * 1000))

                            image = yolo.draw_bboxes(frame, bboxes, 10)
                            predict_start_time = time.time()

                            predict_exec_time = time.time() - predict_start_time

                            curr_time = time.time()

                            cv2.putText(
                                image,
                                "preidct: {:.2f} ms, fps: {:.2f}".format(
                                    predict_exec_time * 1000,
                                    1 / (curr_time - prev_time),
                                ),
                                org=(5, 20),
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=0.6,
                                color=(50, 255, 0),
                                thickness=2,
                                lineType=cv2.LINE_AA,
                            )
                            prev_time = curr_time
                            door_cords = dictionary_of_cords.get(array_of_dates[_counter])
                            for_frame(number, yolo.get_cords(), image, door_cords[0], door_cords[1], video,
                                      array_of_dates[_counter], _name, image, record_time)

                            stat(status[1], image, 10, 60)
                            stat(status[0], image, 10, 100)
                            number += 1
                            if len(center) != 0:
                                cv2.rectangle(image, (center[0], center[1]), (center[0] + 20, center[1] + 20),
                                              (255, 0, 0),
                                              1)
                            cv2.imshow('Frame', image)
                            center.clear()

                            # Press S on keyboard
                            # to stop the process

                            if cv2.waitKey(1) & 0xFF == ord('&'):
                                break
                        # cv2.waitKey(0)
                        # Break the loop
                        else:
                            cursor.execute('''UPDATE names SET anal = 1 WHERE video_name=?;''', (_name,))
                            conn.commit()
                            conn.close()
                            cv2.destroyAllWindows()
                            os.chdir(r"C:\Users\user\Desktop\video")
                            break
                _counter += 1
            ccounter += 1
    except FileNotFoundError:
        f = open('text.txt', 'w')
        f.write('\n' + 'exception')
        f.close()
        pass


if __name__ == '__main__':  # write restart
    while True:
        try:
            main()
        except FileNotFoundError:
            f = open('text.txt', 'w')
            f.write('\n' + 'exception')
            f.close()
            main()
