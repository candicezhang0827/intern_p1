//
//  main.cpp
//  read_file
//
//  Created by candicezhang1997 on 7/3/19.
//  Copyright © 2019 candicezhang1997. All rights reserved.
//

#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
#include <algorithm>
using namespace std;

vector<int> labels;

//reads in the entire database, and returns a 2D vector representation of that database
//col_num stores which fields in the database will be stored into the 2D vector
vector<vector<string>> process_data(string filename, vector<int> col_num){
    ifstream file(filename);
    string line, field;
    vector<vector<string>> data;
    vector<string> temp;
    int i = 0;  //row number in the original csv file
    while (getline(file,line)){
        i++;
        temp.clear();
        string a = to_string(i);
        temp.push_back(a);
        stringstream ss(line);
        int j = 0;  //col number in the csv file
        int k = 0; //index into col_num
        while (getline(ss,field,',')) {
            if (j==col_num[k]){
                temp.push_back(field);
                k++;
            }
            j++;
        }
        data.push_back(temp);
    }
    return data;
}

//returns true when v1 should be before v2
bool comparator(vector<string> v1, vector<string> v2){
    int v1_ID = stoi(v1[2]);
    int v2_ID = stoi(v2[2]);
    double v1_time = stod(v1[1]);
    double v2_time = stod(v2[1]);
    if (v1_ID < v2_ID) return true;
    else if (v1_ID == v2_ID && v1_time < v2_time)   return true;
    else return false;
}

//TODO: How to determine two different intervals for the same ID? What's the threshold?
//sorts objects_data by ID, time
//then groups records by ID
vector<vector<vector<string>>> sort_data(vector<vector<string>> objects_data){
    vector<vector<vector<string>>> result;
    vector<vector<string>> temp;
    int prev_ID = -1;
    int curr_ID;
    for (int i = 0; i < objects_data.size(); i++){
        curr_ID = stoi(objects_data[i][2]);
        if (prev_ID == -1)  prev_ID=curr_ID;
        if (curr_ID==prev_ID)  temp.push_back(objects_data[i]);
        else{
            prev_ID = curr_ID;
            result.push_back(temp);
            temp.clear();
            temp.push_back(objects_data[i]);
        }
        
    }
    
    return result;
}

vector<double> get_timestamps(vector<vector<string>> objects_data){
    double curr_time;
    double prev_time = -1;
    int i = 0;
    vector<double> timestamps;
    while (i<objects_data.size()){
        curr_time = stod(objects_data[i][1]);
        if (curr_time!=prev_time) {
            prev_time = curr_time;
            timestamps.push_back(curr_time);
        }
    }
    return timestamps;
}

//get the (timestamp, ID) tuple of the front car for every timestamp. If no front car detected at a particular timestamp, then set ID value to -1.
vector<int> get_frontcars(vector<vector<string>> objects_data){
    vector<int> frontcars;
    int i = 0;
    while (i < objects_data.size()){
        double curr_time =stod(objects_data[i][1]);
        double shortest_dist = 10000;
        int temp;
        while (stod(objects_data[i][1])==curr_time){
            double x_val = stod(objects_data[i][3]);
            double y_val = stod(objects_data[i][4]);
            if (y_val<=2.2 && y_val>=-2.2 && x_val>0 && x_val<shortest_dist){
                temp=stoi(objects_data[i][2]);
            }
            i++;
        }
        frontcars.push_back(temp);
    }
    return frontcars;
}

double in_two_lanes(double thresh_dist, double cars_distance){
    if (cars_distance>=thresh_dist) return true;
    else return false;
}

void analyze_data(vector<vector<vector<string>>> objects_groups, vector<vector<string>> lane_data, vector<double> timestamps, vector<int> front_cars){
    for (int i = 0; i < objects_groups.size();i++){ //ith car
        int j = 0;  //jth timestamp
        while (j < objects_groups[i].size()){
            double cars_distance = stod(objects_groups[i][j][4]);
            if (in_two_lanes(2.2,cars_distance)){   //at some instance in two different lanes
                int k = j+1;
                while (k < objects_groups[i].size()){
                    cars_distance = stod(objects_groups[i][j][4]);
                    if (!in_two_lanes(2.2,cars_distance)){  //at some later time instance in same lane
                        double time = stod(objects_groups[i][j][1]);
                        int ID = stoi(objects_groups[i][j][2]);
                        std::vector<double>::iterator it;
                        //check if it's right in front of my car
                        it=find(timestamps.begin(),timestamps.end(),time);
                        int frontcar_ID =  front_cars[*it];
                        if (frontcar_ID==ID) labels.push_back(stoi(objects_groups[i][j][0]));
                    }
                }
            }
        }
    }
        
}

int main(int argc, const char * argv[]) {
    vector<vector<string>> objects_data;
    //objects_data: time(1) ID(2) cloet_point_x(11) cloet_point_y(12)
    vector<int> col_num = {1,2,11,12};
    objects_data = process_data("objects.csv",col_num);
    //lane_data: time(1) lane_width car_width
    col_num = {1};
    vector<vector<string>> lane_data;
    lane_data = process_data("lane.csv",col_num);
    vector<vector<vector<string>>> objects_groups = sort_data(objects_data);
    vector<double> timestamps=get_timestamps(objects_data);
    vector<int> front_cars = get_frontcars(objects_data);
    
    
}
