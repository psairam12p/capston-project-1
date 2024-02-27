import pymongo
import pandas as pd
import mysql.connector
import streamlit as st
from datetime import datetime
import isodate
from googleapiclient.discovery import build

#API key connection
def Api_connect():
    Api_Id="AIzaSyDOIQtivwwRBq3kCy_9ri5a7zONq6yE0rE"

    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name,api_version,developerKey=Api_Id)
    return youtube
youtube=Api_connect()
#get channel information
def get_channel_details(channel_id):
    
    request = youtube.channels().list(part = "snippet,contentDetails,Statistics",id = channel_id)
            
    response1=request.execute()
    
    for i in range(0,len(response1["items"])):
        data = dict(
                    Channel_Name = response1["items"][i]["snippet"]["title"],
                    Channel_Id = response1["items"][i]["id"],
                    Subscription_Count = response1["items"][i]["statistics"]["subscriberCount"],
                    Views = response1["items"][i]["statistics"]["viewCount"],
                    Total_Videos = response1["items"][i]["statistics"]["videoCount"],
                    Channel_Description = response1["items"][i]["snippet"]["description"],
                    Playlist_Id = response1["items"][i]["contentDetails"]["relatedPlaylists"]["uploads"]
        )
        
    return data
#get Youtube channel video ids
def get_video_ids(channel_id):
    video_ids = []
    # ------------------------get Uploads  id after using  id u get the all the video ids-----------------------------------
    res = youtube.channels().list(id=channel_id, part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    next_page = True
    while next_page:
        request = youtube.playlistItems().list(part = 'snippet',playlistId = playlist_id, maxResults = 50,pageToken = next_page_token)
        response = request.execute()
        for i in range(len(response['items'])):
            video_ids.append(response['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = response.get('nextPageToken')
        
        if next_page_token is None:
            next_page=False
    return video_ids
#get video information
def get_video_info(video_ids):

    video_data = []

    for video_id in video_ids:
        request = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id= video_id)
        response = request.execute()

        for item in response["items"]:
            data = dict(Channel_Name = item['snippet']['channelTitle'],
                        Channel_Id = item['snippet']['channelId'],
                        Video_Id = item['id'],
                        Title = item['snippet']['title'],
                        Tags = item['snippet'].get('tags'),
                        Thumbnail = item['snippet']['thumbnails']['default']['url'],
                        Description = item['snippet']['description'],
                        Published_Date = item['snippet']['publishedAt'],
                        Duration = item['contentDetails']['duration'],
                        Views = item['statistics']['viewCount'],
                        Likes = item['statistics'].get('likeCount'),
                        Comments = item['statistics'].get('commentCount'),
                        Favorite_Count = item['statistics']['favoriteCount'],
                        Definition = item['contentDetails']['definition'],
                        Caption_Status = item['contentDetails']['caption']
                        )
            video_data.append(data)
    return video_data
#get comment information
def get_comment_info(video_ids):
        Comment_Information = []
        try:
                for video_id in video_ids:

                        request = youtube.commentThreads().list(part = "snippet",videoId = video_id,maxResults = 50)
                        response5 = request.execute()
                        
                        for item in response5["items"]:
                                comment_information = dict(
                                        Comment_Id = item["snippet"]["topLevelComment"]["id"],
                                        Video_Id = item["snippet"]["videoId"],
                                        Comment_Text = item["snippet"]["topLevelComment"]["snippet"]["textOriginal"],
                                        Comment_Author = item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                                        Comment_Published = item["snippet"]["topLevelComment"]["snippet"]["publishedAt"])

                                Comment_Information.append(comment_information)
        except:
                pass
                
        return Comment_Information
#MongoDB Connection
client = pymongo.MongoClient("mongodb+srv://psairam12p:Sairam123@cluster0.3k9xchw.mongodb.net/")
db = client["Youtube_data"]
#_____________________________________________________________________________________________________________________________________________
# upload to MongoDB

def channel_details(channel_id):
    ch_details = get_channel_details(channel_id)
    vi_ids = get_video_ids(channel_id)
    vi_details = get_video_info(vi_ids)
    com_details = get_comment_info(vi_ids)

    coll1 = db["channel_details"]
    coll1.insert_one({"channel_information":ch_details,"video_information":vi_details,"comment_information":com_details})
    
    return "upload completed successfully"
def channels_table():
    mydb = mysql.connector.connect(host="localhost",user="root",password="9391674255",database="guvi")
    cursor = mydb.cursor()


    try:
        create_query = '''create table channels(Channel_Name varchar(225),
                        Channel_Id varchar(225) primary key, 
                         
                        Views int,
                        Total_Videos int,
                        Channel_Description text,
                        Playlist_Id varchar(225))'''
        cursor.execute(create_query)
        mydb.commit()
    except:
        st.write("Channels Table alredy created")    


    ch_list = []
    db = client["Youtube_data"]
    coll1 = db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df = pd.DataFrame(ch_list)

    for index,row in df.iterrows():
        insert_query = '''INSERT into channels(Channel_Name,
                                                    Channel_Id,
                                                    
                                                    Views,
                                                    Total_Videos,
                                                    Channel_Description,
                                                    Playlist_Id)
                                        VALUES(%s,%s,%s,%s,%s,%s)'''
            

        values =(
                row['Channel_Name'],
                row['Channel_Id'],
                
                row['Views'],
                row['Total_Videos'],
                row['Channel_Description'],
                row['Playlist_Id'])
        cursor.execute(insert_query,values)
        mydb.commit()

        
def videos_table():

    mydb = mysql.connector.connect(host="localhost",user="root",password="9391674255",database="guvi")
    cursor = mydb.cursor()

   
    try:
        create_query = '''create table videos(
                        Channel_Name varchar(225),
                        Channel_Id varchar(225),
                        Video_Id varchar(225) primary key, 
                        Title varchar(225), 
                        Tags text,
                        Thumbnail varchar(225),
                        Description text, 
                        Published_Date DATETIME,
                        Duration int, 
                        Views int, 
                        Likes int,
                        Comments int,
                        Favorite_Count int, 
                        Definition varchar(225), 
                        Caption_Status varchar(225) 
                        )''' 
                        
        cursor.execute(create_query)             
        mydb.commit()
    except:
        st.write("videos Table alredy created")    


    vi_list = []
    db = client["Youtube_data"]
    coll1 = db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    df2 = pd.DataFrame(vi_list)
        

    for index, row in df2.iterrows():
        insert_query = '''
                    INSERT INTO videos (Channel_Name,
                        Channel_Id,
                        Video_Id, 
                        Title, 
                        Tags,
                        Thumbnail,
                        Description, 
                        Published_Date,
                        Duration, 
                        Views, 
                        Likes,
                        Comments,
                        Favorite_Count, 
                        Definition, 
                        Caption_Status 
                        )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)

                '''
        values = (
                    row['Channel_Name'],
                    row['Channel_Id'],
                    row['Video_Id'],
                    row['Title'],
                    str(row['Tags']),
                    row['Thumbnail'],
                    row['Description'],
                    datetime.fromisoformat(row['Published_Date'][:-1]),
                    isodate.parse_duration(row['Duration']).total_seconds(),
                    row['Views'],
                    row['Likes'],
                    row['Comments'],
                    row['Favorite_Count'],
                    row['Definition'],
                    row['Caption_Status'])
        
        cursor.execute(insert_query,values)
        mydb.commit()
            

        
def comments_table():
    
    mydb = mysql.connector.connect(host="localhost",user="root",password="9391674255",database="guvi")
    cursor = mydb.cursor()

   
   
    #mydb.commit()

    try:
        create_query = '''create table comments(Comment_Id varchar(225),
                        Video_Id varchar(225),
                        Comment_Text text, 
                        Comment_Author varchar(225),
                        Comment_Published DATETIME)'''
        cursor.execute(create_query)
        mydb.commit()
    except:
        st.write("comment table is already existed")    

    com_list = []
    db = client["Youtube_data"]
    coll1 = db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df3 = pd.DataFrame(com_list)


    for index, row in df3.iterrows():
            insert_query = '''
                INSERT INTO comments (Comment_Id,
                                    Video_Id ,
                                    Comment_Text,
                                    Comment_Author,
                                    Comment_Published)
                VALUES (%s, %s, %s, %s, %s)

            '''
            values = (
                row['Comment_Id'],
                row['Video_Id'],
                row['Comment_Text'],
                row['Comment_Author'],
                datetime.fromisoformat(row['Comment_Published'][:-1])
            )
            cursor.execute(insert_query,values)
            mydb.commit()


def tables():
    channels_table()
    videos_table()
    comments_table()
    return "Tables Created successfully"

def show_channels_table():
    ch_list = []
    db = client["Youtube_data"]
    coll1 = db["channel_details"] 
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    channels_table = st.dataframe(ch_list)
    return channels_table
def show_videos_table():
    vi_list = []
    db = client["Youtube_data"]
    coll2 = db["channel_details"]
    for vi_data in coll2.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    videos_table = st.dataframe(vi_list)
    return videos_table
def show_comments_table():
    com_list = []
    db = client["Youtube_data"]
    coll3 = db["channel_details"]
    for com_data in coll3.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    comments_table = st.dataframe(com_list)
    return comments_table
with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("SKILL TAKE AWAY")
    st.caption('Python scripting')
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption(" Data Managment using MongoDB and SQL")
channel_id = st.text_input("Enter the Channel id")
channels = channel_id.split(',')
channels = [ch.strip() for ch in channels if ch]

if st.button("Collect and Store data"):
    for channel in channels:
        ch_ids = []
        db = client["Youtube_data"]
        coll1 = db["channel_details"]
        for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
            ch_ids.append(ch_data["channel_information"]["Channel_Id"])
        if channel in ch_ids:
            st.success("Channel details of the given channel id: " + channel + " already exists")
        else:
            output = channel_details(channels)
            st.success(output)
            
if st.button("Migrate to SQL"):
    display = tables()
    st.success(display)
    
show_table = st.radio("SELECT THE TABLE FOR VIEW",(":green[channels]",":red[videos]",":blue[comments]"))

if show_table == ":green[channels]":
    show_channels_table()
elif show_table ==":red[videos]":
    show_videos_table()
elif show_table == ":blue[comments]":
    show_comments_table()

#SQL connection
mydb = mysql.connector.connect(host="localhost",user="root",password="9391674255",database="guvi")
cursor = mydb.cursor()
question = st.selectbox(
    'Please Select Your Question',
    ('1.	What are the names of all the videos and their corresponding channels?',
     '2.	Which channels have the most number of videos, and how many videos do they have?',
     '3.	What are the top 10 most viewed videos and their respective channels?',
     '4.	How many comments were made on each video, and what are their corresponding video names?',
     '5.	Which videos have the highest number of likes, and what are their corresponding channel names?',
     '6.	What is the total number of likes and dislikes for each video, and what are their corresponding video names?',
     '7.	What is the total number of views for each channel, and what are their corresponding channel names?',
     '8.	What are the names of all the channels that have published videos in the year 2022?',
     '9.	What is the average duration of all videos in each channel, and what are their corresponding channel names?',
     '10.Which videos have the highest number of comments, and what are their corresponding channel names?'))
mydb = mysql.connector.connect(host="localhost",user="root",password="9391674255",database="guvi")
cursor = mydb.cursor()
if question == '1.	What are the names of all the videos and their corresponding channels?':
    query1 = "select Title as videos, Channel_Name as ChannelName from videos;"
    cursor.execute(query1)
    #mydb.commit()
    t1=cursor.fetchall()
    st.write(pd.DataFrame(t1, columns=["Video Title","Channel Name"]))

elif question == '2.	Which channels have the most number of videos, and how many videos do they have?':
    query2 = "select Channel_Name as ChannelName,Total_Videos as NO_Videos from channels order by Total_Videos desc;"
    cursor.execute(query2)
    #mydb.commit()
    t2=cursor.fetchall()
    st.write(pd.DataFrame(t2, columns=["Channel Name","No Of Videos"]))

elif question == '3.	What are the top 10 most viewed videos and their respective channels?':
    query3 = '''select Views as views , Channel_Name as ChannelName,Title as VideoTitle from videos 
                        where Views is not null order by Views desc limit 10;'''
    cursor.execute(query3)
    #mydb.commit()
    t3 = cursor.fetchall()
    st.write(pd.DataFrame(t3, columns = ["views","channel Name","video title"]))

elif question == '4.	How many comments were made on each video, and what are their corresponding video names?':
    query4 = "select Comments as No_comments ,Title as VideoTitle from videos where Comments is not null;"
    cursor.execute(query4)
    #mydb.commit()
    t4=cursor.fetchall()
    st.write(pd.DataFrame(t4, columns=["No Of Comments", "Video Title"]))

elif question == '5.	Which videos have the highest number of likes, and what are their corresponding channel names?':
    query5 = '''select Title as VideoTitle, Channel_Name as ChannelName, Likes as LikesCount from videos 
                       where Likes is not null order by Likes desc;'''
    cursor.execute(query5)
    #mydb.commit()
    t5 = cursor.fetchall()
    st.write(pd.DataFrame(t5, columns=["video Title","channel Name","like count"]))

elif question == '6.	What is the total number of likes for each video, and what are their corresponding video names?':
    query6 = '''select Likes as likeCount,Title as VideoTitle from videos;'''
    cursor.execute(query6)
    #mydb.commit()
    t6 = cursor.fetchall()
    st.write(pd.DataFrame(t6, columns=["like count","video title"]))

elif question == '7.	What is the total number of views for each channel, and what are their corresponding channel names?':
    query7 = "select Channel_Name as ChannelName, Views as Channelviews from channels;"
    cursor.execute(query7)
    #mydb.commit()
    t7=cursor.fetchall()
    st.write(pd.DataFrame(t7, columns=["channel name","total views"]))

elif question == '8.	What are the names of all the channels that have published videos in the year 2022?':
    query8 = '''select Title as Video_Title, Published_Date as VideoRelease, Channel_Name as ChannelName from videos 
                where extract(year from Published_Date) = 2022;'''
    cursor.execute(query8)
    #mydb.commit()
    t8=cursor.fetchall()
    st.write(pd.DataFrame(t8,columns=["Name", "Video Publised On", "ChannelName"]))

elif question == '9.	What is the average duration of all videos in each channel, and what are their corresponding channel names?':
    query9 =  "SELECT Channel_Name as ChannelName, AVG(Duration) AS average_duration FROM videos GROUP BY Channel_Name;"
    cursor.execute(query9)
    #mydb.commit()
    t9=cursor.fetchall()
    t9 = pd.DataFrame(t9, columns=['ChannelTitle', 'Average Duration'])
    T9=[]
    for index, row in t9.iterrows():
        channel_title = row['ChannelTitle']
        average_duration = row['Average Duration']
        average_duration_str = str(average_duration)
        T9.append({"Channel Title": channel_title ,  "Average Duration": average_duration_str})
    st.write(pd.DataFrame(T9))

elif question == '10.Which videos have the highest number of comments, and what are their corresponding channel names?':
    query10 = '''select Title as VideoTitle, Channel_Name as ChannelName, Comments as Comments from videos 
                       where Comments is not null order by Comments desc;'''
    cursor.execute(query10)
    #mydb.commit()
    t10=cursor.fetchall()
    st.write(pd.DataFrame(t10, columns=['Video Title', 'Channel Name', 'NO Of Comments']))
