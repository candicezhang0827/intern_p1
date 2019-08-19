#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 16:43:06 2019

@author: candicezhang1997
"""
import csv
import pandas as pd
import pymysql 

object_width=1.9    #width of object car
left_lane_dist={}
right_lane_dist={}
dtlc_change=[]  
vehicle_curv={}
object_trajectory_raw={}
object_trajectory=[]
front_car={}
cutin=[]

#lane_data: list of dictionary representation of lane_data.csv
def set_lane_dist(lane_data):
    for row in lane_data:
        time=row['time']
        index=row['index']
        dtlc=row['dtlc']
        if (time!='' and index!='' and dtlc!=''):
            t=float(time)
            #convert t to 1 d.p. float
            ti=int(t*10)
            t=float(ti)/10
            ID=int(index)
            dist=float(dtlc)
            if (ID==0):
                left_lane_dist[t]=dist
            else:
                right_lane_dist[t]=dist


def set_dtlc_change():
    val=0
    for time in left_lane_dist:
        temp=left_lane_dist[time]
        if (val==0 and temp>-0.3 and temp<0):
            val=temp
        elif (val <0 and temp>0):
            dtlc_change.append(time)
            val=0
            
    val=0
    for time in right_lane_dist:
        temp=right_lane_dist[time]
        if (val==0 and temp>-0.3 and temp<0):
            val=temp
        elif (val <0 and temp>0):
            dtlc_change.append(time)
            val=0
    
    dtlc_change.sort()
    
def within_bound(temp_t):
    lb=temp_t-5
    ub=temp_t+5
    lo=0
    hi=len(dtlc_change)
    found=False
    while lo<hi and not found:
        mid=(lo+hi)/2
        val=dtlc_change[mid]
        if (val>=lb and val<=ub):
            found=True
        elif (val>ub):
            hi=mid
        else:
            lo=mid+1
    return found
            
        
def set_curv(vehicle_data):
    for row in vehicle_data:
        time=row['time']
        curvature=row['curvature']
        if (time!='' and curvature!=''):
            t=float(time)
            #convert t to 1 d.p. float
            ti=int(t*10)
            t=float(ti)/10
            curv=float(curvature)
            vehicle_curv[t]=curv
            

#returns 0 if target car and object car are not in the same lane, 1 if they are in the same lane, 2 if not sure
def detect_same_lane(target_width,y,time):
    delta=0.1
    #convert time to 1 d.p. float
    t=int(time*10)
    time=float(t)/10
    
    if (y>0):
        if (time not in right_lane_dist.keys()):
            return 2
        dtlc=right_lane_dist[time]
        if (dtlc<0):
            return 2
        if (y-target_width/2>=object_width/2+dtlc+delta):
            return 0
        elif (y-target_width/2<object_width/2+dtlc-delta):
            return 1
        else:
            return 2
        
    else:
        if (time not in left_lane_dist.keys()):
            return 2
        dtlc=left_lane_dist[time]
        if (dtlc<0):
            return 2
        if (-y-target_width/2>=object_width/2+dtlc+delta):
            return 0
        elif (-y-target_width/2<object_width/2+dtlc-delta):
            return 1
        else:
            return 2

def reassign_id():
    for ID in object_trajectory_raw:
        prev_time=-1
        tra=object_trajectory_raw[ID]
        for entry in tra:
            time=entry['time']
            if (prev_time==-1 or time-prev_time>1):
                list=[]
                list.append(entry)
                object_trajectory.append(list)
            else:
                n=len(object_trajectory)-1
                object_trajectory[n].append(entry)
            prev_time=time
                
        
def proc_object_data(object_data):
    r=0
    smallest_pos_x=1000
    prev_time=-1
    for row in object_data:
        time=row['time']
        raw_id=row['raw_id']
        closest_x=row['cloet_point_x']
        y_position=row['poition_y']
        object_width=row['width']
        rel_speed=row['relative_velocity_x']
        abs_speed=row['abolute_velocity_x']
        
        speed=2
        velocity=0
        if (rel_speed!='' and abs_speed!=''):
            speed=float(abs_speed)
            velocity=float(rel_speed)
            
        t=float(time)
        ID=int(raw_id)
        x=float(closest_x)
        y=float(y_position)
        width=float(object_width)
        same_lane=detect_same_lane(width,y,t)
        
        if (ID not in object_trajectory_raw.keys()):
            object_trajectory_raw[ID]=[]
        entry={}
        entry['id']=ID
        entry['row']=r
        entry['time']=t
        entry['x']=x
        entry['y']=y
        entry['width']=width
        entry['velocity']=velocity
        entry['speed']=speed
        entry['same_lane']=same_lane
        object_trajectory_raw[ID].append(entry)
        
        if (t==prev_time):
            if (same_lane==1 and x>0 and x<smallest_pos_x):
                smallest_pos_x=x
                front_car[t]=ID
        else:
            prev_time=t
            if (same_lane==1 and x>0):
                front_car[t]=ID
                smallest_pos_x=x
            else:
                smallest_pos_x=1000
                front_car[prev_time]=-1
    
    reassign_id()

            
        
def detect_cutin():
    for tra in object_trajectory:
        i=0
        prev_diff_lanes=False
        jump=False
        while i<len(tra) and not jump:
            passed=False
            entry=tra[i]
            t=entry['time']
            ID=entry['id']
            speed=entry['speed']
            velocity=entry['velocity']
            same_lane=entry['same_lane']
            if (same_lane==1):
                if (prev_diff_lanes and front_car[t]==ID and speed>1 and speed-velocity>1):
                    temp=int(t*10)
                    temp_t=float(temp)/10
                    if (not within_bound(temp_t)):
                        if (temp_t in vehicle_curv.keys()):
                            curv=vehicle_curv[temp_t]
                            if (curv>-0.01 and curv<0.01):
                                passed=True
                init_time=t
                final_time=0
                prev_diff_lanes=False
                i+=1
                while (i<len(tra) and not prev_diff_lanes):
                    entry=tra[i]
                    t=entry['time']
                    same_lane=entry['same_lane']
                    if (same_lane==0 or same_lane==2):
                        final_time=t
                    if (same_lane==0):
                        prev_diff_lanes=True
                    i+=1
                if (passed and final_time-init_time>3):
                    cutin.append({})
                    n=len(cutin)-1
                    cutin[n]['ID']=ID
                    cutin[n]['time']=init_time
                    jump=True
            elif (same_lane==0):
                prev_diff_lanes=True
            else:
                prev_diff_lanes=False
            i+=1
        
        
def data_conn():
    return 0    

def get_data(conn,session,data):
    sql=''
    table=pd.read_sql(sql,conn)
    return table.to_dict('records')
            
if __name__ == "__main__":
    session=''
    data='lane_data'
    conn=data_conn()
    lane_data=get_data(conn,session,data)
    set_lane_dist(lane_data)
    set_dtlc_change()
    
    data='vehicle'
    vehicle_data=get_data(conn,session,data)
    set_curv(vehicle_data)
    
    object_data='lidar_object_data'
    proc_object_data(object_data)
    
    detect_cutin()
    
    with open('cutin.csv','a+') as output:
        output_writer=csv.writer(output)
        row=0
        for ci in cutin:
            time=ci['time']
            ID=ci['ID']
            output.writerow([9,row,session,time-15,time+15,'D',ID,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    output.close()
    
            
        
    
    
    

    
            
        


  #with open('/Users/candicezhang1997/Desktop/employee_file.csv', mode='w+') as employee_file:
    #employee_writer = csv.writer(employee_file, delimiter=',')
    #employee_writer.writerow(['John Smith', 'Accounting', 'November'])
    #employee_writer.writerow(['Alan Turing', 'CS', 'November'])
    